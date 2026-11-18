import random
from faker import Faker

from model import Person, Rental, RentalItem


# --- 1. Típus: Person generátor ---
def generate_people(
    n: int,
    male_ratio: float = 0.5,
    locale: str = "hu_HU",
    unique: bool = False,
    min_age: int = 18,
    max_age: int = 80,
) -> list[Person]:
    assert n > 0
    assert 0 <= male_ratio <= 1
    assert 0 <= min_age <= max_age <= 120

    people = []
    fake = Faker(locale)
    fake_source = fake.unique if unique else fake

    for i in range(n):
        male = random.random() < male_ratio
        person = Person(
            id=f"P-{str(i + 1).zfill(6)}",
            name=fake_source.name_male() if male else fake_source.name_female(),
            age=random.randint(min_age, max_age),
            male=male,
        )
        people.append(person)
    return people


# --- 2. Típus: Rental generátor (összeköti a Rental-t a Person-nel 1:N módon) ---
def generate_rentals(
    people: list[Person],
    min_rentals: int = 1,
    max_rentals: int = 3,
    locale: str = "hu_HU",
) -> list[Rental]:
    assert len(people) > 0
    assert 0 <= min_rentals <= max_rentals

    fake = Faker(locale)
    rentals = []
    rental_id = 1
    statuses = ["ACTIVE", "RETURNED", "OVERDUE", "RESERVED"]

    for person in people:
        # Minden emberhez generálunk 1-3 bérlést
        count = random.randint(min_rentals, max_rentals)
        for _ in range(count):
            rentals.append(
                Rental(
                    id=f"R-{str(rental_id).zfill(6)}",
                    person_id=person.id,  # Idegen kulcs beállítása
                    rental_date=str(fake.date_between(start_date="-1y", end_date="today")),
                    status=random.choice(statuses),
                )
            )
            rental_id += 1
    return rentals


# --- 3. Típus: RentalItem generátor (összeköti a tételt a Rental-lal 1:N módon) ---
def generate_rental_items(
    rentals: list[Rental],
    min_items: int = 1,
    max_items: int = 3,
) -> list[RentalItem]:
    assert len(rentals) > 0
    assert 0 <= min_items <= max_items

    catalog = [
        ("Ipari Fúrógép", 4500.0),
        ("Kärcher Magasnyomású Mosó", 7500.0),
        ("Fűkasza Benzinmotoros", 6000.0),
        ("Létrás Állvány 4m", 3500.0),
        ("Hőlégfúvó", 2200.0),
        ("Betonkeverő", 8500.0),
        ("Lapvibrátor", 9000.0),
    ]

    items = []
    item_id = 1
    for rental in rentals:
        # Minden bérléshez rendelünk tételeket
        count = random.randint(min_items, max_items)
        for _ in range(count):
            name, price = random.choice(catalog)
            items.append(
                RentalItem(
                    id=f"RI-{str(item_id).zfill(6)}",
                    rental_id=rental.id,  # Idegen kulcs beállítása
                    item_name=name,
                    daily_rate=price,
                )
            )
            item_id += 1
    return items


# --- Fő generátor ---
def generate_dataset(size: int) -> tuple[list[Person], list[Rental], list[RentalItem]]:
    people = generate_people(size)
    rentals = generate_rentals(people)
    items = generate_rental_items(rentals)
    return people, rentals, items


# --- Tesztfuttatás a generátor ellenőrzésére ---
if __name__ == "__main__":
    test_size = 5
    p_list, r_list, i_list = generate_dataset(test_size)

    print(f"Generált személyek száma: {len(p_list)}")
    print(f"Példa személy: {p_list[0]}")

    print(f"\nGenerált bérlések száma: {len(r_list)}")
    print(f"Példa bérlés (FK a személyre): {r_list[0]}")

    print(f"\nGenerált tételek száma: {len(i_list)}")
    print(f"Példa tétel (FK a bérlésre): {i_list[0]}")

    # Kapcsolatok ellenőrzése
    person_ids = {p.id for p in p_list}
    rental_ids = {r.id for r in r_list}

    assert all(r.person_id in person_ids for r in r_list), "Hibás Person idegen kulcs a bérlésekben!"
    assert all(i.rental_id in rental_ids for i in i_list), "Hibás Rental idegen kulcs a tételekben!"

    print("\n[OK] Az adathalmaz és az idegen kulcsos kapcsolatok hibátlanul létrejöttek!")