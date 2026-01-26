from db.models import Menu
import pandas as pd

def fetch_items(db, time):
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