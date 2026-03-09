from db.models import Menu
import pandas as pd
from app.scraper import scrape_and_save
from app.categorizer import categorize_hall_dish

def fetch_items(db, time, all_data=True):
    if all_data:
        scrape_and_save()
        categorize_hall_dish()

    items = db.query(Menu).all()
    df = pd.DataFrame([{
        "Dish": item.dish,
        "Category": item.category,
        "Hall": item.hall,
        "Time": item.time,
        "Calories": item.calories,
        "Serving Size": item.serving_size,
        "FinalStation": item.final_station,
        "Role": item.role
    } for item in items])
    return df