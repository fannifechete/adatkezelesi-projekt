import csv
import json
import os
from typing import Type
import openpyxl

from model import Entity, Person, Rental, RentalItem


class DataHandler:
    """Kezeli az adathalmazok kiírását és visszaolvasását CSV, JSON és XLSX formátumokban."""

    # =========================================================================
    # 1. CSV KEZELÉS (típusonként külön fájl, fejléc az első sorban)
    # =========================================================================
    @staticmethod
    def write_csv(entities: list[Entity],
                  path: str,
                  file_name: str = None,
                  delimiter: str = ";") -> None:
        if not entities:
            return

        os.makedirs(path, exist_ok=True)
        if file_name is None:
            file_name = entities[0].collection_name()

        full_path = os.path.join(path, f"{file_name}.csv")
        with open(full_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=delimiter)
            # 1. sor: Mezőnevek fejlécnek
            writer.writerow(entities[0].field_names())
            # Rekordok kiírása soronként
            for entity in entities:
                writer.writerow(entity.to_sequence())

    @staticmethod
    def read_csv(entity_type: Type[Entity],
                 path: str,
                 file_name: str = None,
                 delimiter: str = ";") -> list[Entity]:
        if file_name is None:
            file_name = entity_type.collection_name()

        full_path = os.path.join(path, f"{file_name}.csv")
        with open(full_path, "r", newline="", encoding="utf-8-sig") as file:
            reader = csv.reader(file, delimiter=delimiter)
            _ = next(reader)  # Fejléc átugrása
            entities = []
            for row in reader:
                if row:
                    entities.append(entity_type.from_sequence(row))
            return entities

    # =========================================================================
    # 2. JSON KEZELÉS (típusonként lista a rekordokból mint dokumentumokból)
    # =========================================================================
    @staticmethod
    def write_json(entities: list[Entity],
                   path: str,
                   file_name: str = None) -> None:
        if not entities:
            return

        os.makedirs(path, exist_ok=True)
        if file_name is None:
            file_name = entities[0].collection_name()

        full_path = os.path.join(path, f"{file_name}.json")
        # Mezőnév -> érték párokká alakítjuk az entitásokat
        data = [
            dict(zip(entity.field_names(), entity.to_sequence()))
            for entity in entities
        ]

        with open(full_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    @staticmethod
    def read_json(entity_type: Type[Entity],
                  path: str,
                  file_name: str = None) -> list[Entity]:
        if file_name is None:
            file_name = entity_type.collection_name()

        full_path = os.path.join(path, f"{file_name}.json")
        with open(full_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            entities = []
            for record in data:
                # Visszanyerjük a sorrendi sztringlistát a from_sequence számára
                seq = [str(record[name]) for name in entity_type.field_names()]
                entities.append(entity_type.from_sequence(seq))
            return entities

    # =========================================================================
    # 3. XLSX KEZELÉS (egy munkafüzet, minden típus külön munkalapon)
    # =========================================================================
    @staticmethod
    def write_xlsx(datasets: list[list[Entity]], file_path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Alapértelmezett üres munkalap eltávolítása

        for dataset in datasets:
            if not dataset:
                continue
            # A munkalap neve a gyűjtemény neve lesz (pl. people, rentals, rental_items)
            sheet_title = dataset[0].collection_name()
            ws = wb.create_sheet(title=sheet_title)

            # 1. sor: Fejlécek
            ws.append(dataset[0].field_names())

            # Adatsorok kiírása
            for entity in dataset:
                ws.append(entity.to_sequence())

        wb.save(file_path)

    @staticmethod
    def read_xlsx(entity_type: Type[Entity], file_path: str) -> list[Entity]:
        wb = openpyxl.load_workbook(file_path)
        sheet_name = entity_type.collection_name()

        if sheet_name not in wb.sheetnames:
            return []

        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []

        entities = []
        # Az 1. sor a fejléc, ezért rows[1:]
        for row in rows[1:]:
            if any(cell is not None for cell in row):
                seq = [str(cell) for cell in row]
                entities.append(entity_type.from_sequence(seq))
        return entities


# --- Tesztelési blokk: mentés és visszaolvasás mindhárom formátumból ---
if __name__ == "__main__":
    from generator import generate_dataset

    print("Adatok generálása a teszthez...")
    people, rentals, items = generate_dataset(3)

    output_dir = "test_output"
    excel_path = os.path.join(output_dir, "database.xlsx")

    # 1. CSV teszt
    print("\n--- CSV mentés és olvasás ---")
    DataHandler.write_csv(people, output_dir)
    DataHandler.write_csv(rentals, output_dir)
    DataHandler.write_csv(items, output_dir)
    csv_people = DataHandler.read_csv(Person, output_dir)
    print(f"CSV Person: {len(csv_people)} db visszaolvasva (eredeti: {len(people)})")
    assert len(csv_people) == len(people)

    # 2. JSON teszt
    print("\n--- JSON mentés és olvasás ---")
    DataHandler.write_json(people, output_dir)
    DataHandler.write_json(rentals, output_dir)
    DataHandler.write_json(items, output_dir)
    json_rentals = DataHandler.read_json(Rental, output_dir)
    print(f"JSON Rental: {len(json_rentals)} db visszaolvasva (eredeti: {len(rentals)})")
    assert len(json_rentals) == len(rentals)

    # 3. XLSX teszt
    print("\n--- XLSX mentés és olvasás ---")
    DataHandler.write_xlsx([people, rentals, items], excel_path)
    xlsx_items = DataHandler.read_xlsx(RentalItem, excel_path)
    print(f"XLSX RentalItem: {len(xlsx_items)} db visszaolvasva (eredeti: {len(items)})")
    assert len(xlsx_items) == len(items)

    print("\n[OK] Minden fájlformátum sikeresen kiírva és hiba nélkül visszaolvasva!")