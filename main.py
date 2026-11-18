import os
import sys
import getpass

try:
    import msvcrt
except ImportError:
    msvcrt = None

from model import Person, Rental, RentalItem
from generator import generate_dataset
from handler import DataHandler
from oracle_handler import OracleHandler


def input_password(prompt: str = "Oracle jelszó: ") -> str:

    if msvcrt is not None and sys.stdin.isatty():
        print(prompt, end="", flush=True)
        chars = []
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                print()
                return "".join(chars)
            elif ch == "\x08":  # Backspace (törlés)
                if chars:
                    chars.pop()
                    print("\b \b", end="", flush=True)
            elif ch == "\x03":  # Ctrl+C megszakítás
                raise KeyboardInterrupt
            else:
                chars.append(ch)
                print("*", end="", flush=True)
    else:
        print(prompt, end="", flush=True)
        return getpass.getpass("")


def main() -> None:
    print("=== Adatgeneráló és Adatkezelő Rendszer ===\n")

    # 1. Darabszám bekérése a felhasználótól
    while True:
        try:
            raw_count = input("Hány személyt (Person) generáljak? (pl. 10): ").strip()
            count = int(raw_count)
            if count <= 0:
                print("Kérlek, 0-nál nagyobb egész számot adj meg!")
                continue
            break
        except ValueError:
            print("Érvénytelen bevitel! Kérlek, egy egész számot írj be.")

    # 2. Egyszeri adatgenerálás (közös adathalmaz minden célhelyhez)
    print(f"\n[1/3] Adatok generálása ({count} személy alapján)...")
    people, rentals, items = generate_dataset(count)
    print(f" -> Generálva: {len(people)} személy, {len(rentals)} bérlés, {len(items)} tétel.")

    # 3. Mentés fájlokba (CSV, JSON, XLSX) a saját DataHandler osztályoddal
    output_dir = "output_data"
    excel_path = os.path.join(output_dir, "database.xlsx")
    print(f"\n[2/3] Mentés fájlokba ({output_dir}/)...")

    DataHandler.write_csv(people, output_dir)
    DataHandler.write_csv(rentals, output_dir)
    DataHandler.write_csv(items, output_dir)

    DataHandler.write_json(people, output_dir)
    DataHandler.write_json(rentals, output_dir)
    DataHandler.write_json(items, output_dir)

    DataHandler.write_xlsx([people, rentals, items], excel_path)
    print(" -> CSV, JSON és XLSX (database.xlsx) fájlok sikeresen elkészültek.")

    # 4. Oracle SQL feltöltés és visszaellenőrzés a saját OracleHandler osztályoddal
    print("\n[3/3] Oracle adatbázis műveletek")
    run_oracle = input("Szeretnéd feltölteni az adatokat az Oracle adatbázisba is? (i/n): ").strip().lower()

    if run_oracle in ("i", "igen", "y", "yes"):
        db_user = input("Oracle felhasználónév (pl. U_NEPTUNKOD): ").strip()
        db_password = input_password("Oracle jelszó: ")
        db_dsn = "codd.inf.unideb.hu:1521/ora21cp.inf.unideb.hu"

        db = OracleHandler(user=db_user, password=db_password, dsn=db_dsn)
        try:
            # Régi táblák eldobása és újak létrehozása (FK megszorításokkal)
            db.create_schema()

            # Adatok beszúrása a megfelelő sorrendben (szülő -> gyermek)
            db.insert_entities(people)
            db.insert_entities(rentals)
            db.insert_entities(items)

            # Visszaolvasás és darabszám-ellenőrzés
            db_people = db.fetch_entities(Person)
            db_rentals = db.fetch_entities(Rental)
            db_items = db.fetch_entities(RentalItem)
            print(
                f" -> Oracle visszaolvasás OK: {len(db_people)} személy, "
                f"{len(db_rentals)} bérlés, {len(db_items)} tétel."
            )
        except Exception as e:
            print(f"[HIBA] Oracle művelet sikertelen: {e}")
    else:
        print(" -> Oracle feltöltés kihagyva.")

    print("\n=== Program futása sikeresen befejeződött! ===")


if __name__ == "__main__":
    main()