from typing import Type
import oracledb

from model import Entity, Person, Rental, RentalItem


class OracleHandler:
    def __init__(self, user: str, password: str, dsn: str):
        self.user = user
        self.password = password
        self.dsn = dsn

    def _get_connection(self):
        """Kapcsolatot nyit az Oracle adatbázishoz."""
        return oracledb.connect(
            user=self.user,
            password=self.password,
            dsn=self.dsn
        )

    def create_schema(self) -> None:
        """
        Létrehozza a relációs sémát DDL utasításokkal.
        Először eldobja a korábbi táblákat, ha léteznek, majd létrehozza a kulcsokat.
        """
        # FK függőségek miatt a törlés sorrendje: levél -> gyökér
        drop_statements = [
            "BEGIN EXECUTE IMMEDIATE 'DROP TABLE rental_items CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;",
            "BEGIN EXECUTE IMMEDIATE 'DROP TABLE rentals CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;",
            "BEGIN EXECUTE IMMEDIATE 'DROP TABLE people CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;",
        ]

        # Létrehozás sorrendje: gyökér -> levél
        create_statements = [
            """
            CREATE TABLE people (
                id VARCHAR2(20) PRIMARY KEY,
                name VARCHAR2(150) NOT NULL,
                age NUMBER(3) NOT NULL,
                male NUMBER(1) NOT NULL
            )
            """,
            """
            CREATE TABLE rentals (
                id VARCHAR2(20) PRIMARY KEY,
                person_id VARCHAR2(20) NOT NULL,
                rental_date VARCHAR2(30) NOT NULL,
                status VARCHAR2(30) NOT NULL,
                CONSTRAINT fk_rental_person FOREIGN KEY (person_id) REFERENCES people(id)
            )
            """,
            """
            CREATE TABLE rental_items (
                id VARCHAR2(20) PRIMARY KEY,
                rental_id VARCHAR2(20) NOT NULL,
                item_name VARCHAR2(150) NOT NULL,
                daily_rate NUMBER(10, 2) NOT NULL,
                CONSTRAINT fk_item_rental FOREIGN KEY (rental_id) REFERENCES rentals(id)
            )
            """,
        ]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                for drop_sql in drop_statements:
                    cur.execute(drop_sql)
                for create_sql in create_statements:
                    cur.execute(create_sql)
            conn.commit()
        print("[Oracle] Táblák és kulcs-kapcsolatok (DDL) sikeresen létrehozva.")

    def insert_entities(self, entities: list[Entity]) -> None:
        """Kötegelt beszúrás az adott entitáshalmazra."""
        if not entities:
            return

        table_name = entities[0].collection_name()
        field_count = len(entities[0].field_names())
        placeholders = ", ".join([f":{i+1}" for i in range(field_count)])
        sql = f"INSERT INTO {table_name} VALUES ({placeholders})"

        rows_to_insert = []
        for e in entities:
            seq = e.to_sequence()
            # Az Oracle SQL nem tárol natív booleant az oszlopban: konvertáljuk 1/0-ra
            if isinstance(e, Person):
                seq[3] = 1 if str(seq[3]).lower() == "true" else 0
            rows_to_insert.append(seq)

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, rows_to_insert)
            conn.commit()
        print(f"[Oracle] {len(entities)} rekord beszúrva a(z) '{table_name}' táblába.")

    def fetch_entities(self, entity_type: Type[Entity]) -> list[Entity]:
        """Adatok visszalekérdezése az adatbázisból és Entity objektumokká alakítása."""
        table_name = entity_type.collection_name()
        fields_str = ", ".join(entity_type.field_names())
        sql = f"SELECT {fields_str} FROM {table_name}"

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                entities = []
                for row in rows:
                    seq = [str(col) for col in row]
                    # Számból logikai visszakonvertálás
                    if entity_type is Person:
                        seq[3] = "True" if seq[3] == "1" else "False"
                    entities.append(entity_type.from_sequence(seq))
                return entities


# --- Tesztelési blokk ---
if __name__ == "__main__":
    from generator import generate_dataset

    DB_USER = "felhasználónév"
    DB_PASSWORD = "jelszó"
    DB_DSN = "codd.inf.unideb.hu:1521/ora21cp.inf.unideb.hu"

    FUTTATAS_TESZT = False

    if FUTTATAS_TESZT:
        db = OracleHandler(DB_USER, DB_PASSWORD, DB_DSN)

        print("1. Táblák felépítése...")
        db.create_schema()

        print("\n2. Adatok generálása és beszúrása...")
        people, rentals, items = generate_dataset(5)
        # Fontos a beszúrási sorrend az idegen kulcsok (FK) miatt:
        db.insert_entities(people)
        db.insert_entities(rentals)
        db.insert_entities(items)

        print("\n3. Visszaolvasás tesztelése...")
        read_people = db.fetch_entities(Person)
        read_rentals = db.fetch_entities(Rental)
        read_items = db.fetch_entities(RentalItem)

        print(f"Visszaolvasva -> Emberek: {len(read_people)}, Bérlések: {len(read_rentals)}, Tételek: {len(read_items)}")
        assert len(people) == len(read_people)
        print("\n[OK] Oracle kapcsolat, DDL és DML műveletek hibátlanul lefutottak!")
    else:
        print("Állítsd a FUTTATAS_TESZT = True-ra a saját kari adataiddal a teszteléshez!")