import pandas as pd
from db.database import SessionLocal
from db.models import Menu, RoleOverride, StationOverride


def seed_menu(csv_path="data/menu_data_categorized.csv"):
    """Load the categorized menu CSV into the shared database."""
    df = pd.read_csv(csv_path)
    db = SessionLocal()

    for _, row in df.iterrows():
        item = Menu(
            item_name=row["Dish"],
            category=row["Category"],
            time=row["Time"],
            hall=row["Hall"],
            calories=row["Calories"],
            serving_size=row["Serving Size"],
            station=row["Station"],
            final_station=None,
            role=None,
            description=None,
            allergens=None,
            dietary_preferences=None,
        )
        db.add(item)

    db.commit()
    db.close()

def seed_overrides(csv_path="data/manual_overrides.csv"):
    """Load manual role overrides into the shared database."""
    df = pd.read_csv(csv_path)
    db = SessionLocal()

    for _, row in df.iterrows():
        override = RoleOverride(
            item_name=row["Dish"],
            final_station=None,
            correct_role=row["CorrectCategory"],

        )
        db.add(override)

    db.commit()
    db.close()


if __name__ == "__main__":
    seed_menu()
    seed_overrides()
    print("Database seeded successfully.")