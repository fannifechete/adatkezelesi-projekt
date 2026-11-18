from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import total_ordering


class Entity(ABC):
    @staticmethod
    @abstractmethod
    def collection_name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def field_names() -> list[str]:
        pass

    @staticmethod
    @abstractmethod
    def from_sequence(seq: list[str]):
        pass

    @abstractmethod
    def to_sequence(self) -> list[str]:
        pass


@dataclass(unsafe_hash=True)
@total_ordering
class Person(Entity):
    id: str = field(hash=True)
    name: str = field(compare=False)
    age: int = field(compare=False)
    male: bool = field(compare=False, default=True)

    def __post_init__(self):
        # 1. Típusellenőrzés (ha véletlenül nem számként érkezne)
        if not isinstance(self.age, int):
            raise TypeError(f"Az életkornak egész számnak kell lennie, kapott: {type(self.age)}")

        # 2. Értéktartomány validálása
        if not (0 <= self.age <= 120):
            raise ValueError(f"Érvénytelen életkor: {self.age} (0 és 120 között kell lennie)")

        # 3. Név ellenőrzése (nem lehet üres vagy csak szóköz)
        if not str(self.name).strip():
            raise ValueError("A név mező nem lehet üres!")

    def __lt__(self, o: object) -> bool:
        if not isinstance(o, Person):
            return NotImplemented
        return self.id < o.id

    @staticmethod
    def collection_name() -> str:
        return "people"

    @staticmethod
    def field_names() -> list[str]:
        return ["id", "name", "age", "male"]

    @staticmethod
    def from_sequence(seq: list[str]):
        # A fájlokból beolvasott szöveges logikai értékek pontos kezelése
        is_male = seq[3].strip().lower() in ("true", "1") if isinstance(seq[3], str) else bool(seq[3])
        return Person(str(seq[0]), str(seq[1]), int(seq[2]), is_male)

    def to_sequence(self) -> list[str]:
        return [self.id, self.name, str(self.age), str(self.male)]


@dataclass(unsafe_hash=True)
class Rental(Entity):
    id: str = field(hash=True)
    person_id: str = field(compare=False)  # Idegen kulcs: Person.id (1:N kapcsolat)
    rental_date: str = field(compare=False)
    status: str = field(compare=False)

    @staticmethod
    def collection_name() -> str:
        return "rentals"

    @staticmethod
    def field_names() -> list[str]:
        return ["id", "person_id", "rental_date", "status"]

    @staticmethod
    def from_sequence(seq: list[str]):
        return Rental(str(seq[0]), str(seq[1]), str(seq[2]), str(seq[3]))

    def to_sequence(self) -> list[str]:
        return [self.id, self.person_id, self.rental_date, self.status]


@dataclass(unsafe_hash=True)
class RentalItem(Entity):
    id: str = field(hash=True)
    rental_id: str = field(compare=False)  # Idegen kulcs: Rental.id (1:N kapcsolat)
    item_name: str = field(compare=False)
    daily_rate: float = field(compare=False)

    def __post_init__(self):
        if self.daily_rate < 0:
            raise ValueError(f"A bérleti díj nem lehet negatív: {self.daily_rate}")
        if not str(self.item_name).strip():
            raise ValueError("A bérlemény neve nem lehet üres!")

    @staticmethod
    def collection_name() -> str:
        return "rental_items"

    @staticmethod
    def field_names() -> list[str]:
        return ["id", "rental_id", "item_name", "daily_rate"]

    @staticmethod
    def from_sequence(seq: list[str]):
        return RentalItem(str(seq[0]), str(seq[1]), str(seq[2]), float(seq[3]))

    def to_sequence(self) -> list[str]:
        return [self.id, self.rental_id, self.item_name, str(self.daily_rate)]


# --- Tesztelési blokk az 1. lépés ellenőrzésére ---
if __name__ == "__main__":
    # 1. Person teszt
    person = Person("P-000001", "Kovács János", 28, True)
    print(f"Person to_sequence: {person.to_sequence()}")
    p_restored = Person.from_sequence(["P-000001", "Kovács János", "28", "True"])
    assert person == p_restored

    # 2. Rental teszt
    rental = Rental("R-000001", person.id, "2024-03-01", "ACTIVE")
    print(f"Rental to_sequence: {rental.to_sequence()}")
    r_restored = Rental.from_sequence(["R-000001", "P-000001", "2024-03-01", "ACTIVE"])
    assert rental == r_restored

    # 3. RentalItem teszt
    item = RentalItem("RI-000001", rental.id, "Fúrókalapács", 4500.0)
    print(f"RentalItem to_sequence: {item.to_sequence()}")
    i_restored = RentalItem.from_sequence(["RI-000001", "R-000001", "Fúrókalapács", "4500.0"])
    assert item == i_restored

    print("Minden modell és konverziós metódus hibátlanul működik!")