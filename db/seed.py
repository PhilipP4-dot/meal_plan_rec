import pandas as pd
from db.database import SessionLocal
from db.models import Menu, Override, BarOverride


def seed_menu(csv_path="data/menu_data_categorized.csv"):
    df = pd.read_csv(csv_path)
    db = SessionLocal()

    for _, row in df.iterrows():
        item = Menu(
            dish=row["Dish"],
            category=row["Category"],
            hall=row["Hall"],
            time=row["Time"],
            calories=row["Calories"],
            serving_size=row["Serving Size"],
            auto_category=row["AutoCategory"],
            final_category=None,  # will fill after overrides
            station=row["Station"],
            final_station=None  # will fill after overrides
        )
        db.add(item)
    

    db.commit()
    db.close()

def seed_overrides(csv_path="data/manual_overrides.csv"):
    df = pd.read_csv(csv_path)
    db = SessionLocal()

    for _, row in df.iterrows():
        override = Override(
            dish = row["Dish"],
            correct_category = row["CorrectCategory"]

        )
        db.add(override)

    db.commit()
    db.close()
def seed_bar_overrides():
    # create empty table for bar overrides
    db = SessionLocal()
    db.query(Menu).delete()
    db.commit()
    db.close()



seed_bar_overrides()
print("Database seeded successfully.")