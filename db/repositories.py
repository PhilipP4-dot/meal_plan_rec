from db.models import Menu
import pandas as pd
from app.scraper import scrape_and_save
from app.categorizer import categorize_hall_dish
from db.seed import ensure_schema

def fetch_items(db, time, all_data=True):
    ensure_schema()

    if all_data or db.query(Menu.id).first() is None:
        scrape_and_save()
        categorize_hall_dish()

    items = db.query(Menu).all()
    df = pd.DataFrame([{
        "dish": item.dish,
        "category": item.category,
        "hall": item.hall,
        "time": item.time,
        "calories": item.calories,
        "serving_size": item.serving_size,
        "final_station": item.final_station,
        "role": item.role,
        "description": item.description,
        "allergens": item.allergens,
        "dietary_preferences": item.dietary_preferences,
        "calories_percent_daily_value": item.calories_percent_daily_value,
        "total_fat_g": item.total_fat_g,
        "total_fat_g_percent_daily_value": item.total_fat_g_percent_daily_value,
        "saturated_fat_g": item.saturated_fat_g,
        "saturated_fat_g_percent_daily_value": item.saturated_fat_g_percent_daily_value,
        "trans_fat_g": item.trans_fat_g,
        "trans_fat_g_percent_daily_value": item.trans_fat_g_percent_daily_value,
        "cholesterol_mg": item.cholesterol_mg,
        "cholesterol_mg_percent_daily_value": item.cholesterol_mg_percent_daily_value,
        "sodium_mg": item.sodium_mg,
        "sodium_mg_percent_daily_value": item.sodium_mg_percent_daily_value,
        "total_carbohydrate_g": item.total_carbohydrate_g,
        "total_carbohydrate_g_percent_daily_value": item.total_carbohydrate_g_percent_daily_value,
        "total_sugars_g": item.total_sugars_g,
        "added_sugars_g": item.added_sugars_g,
        "added_sugars_g_percent_daily_value": item.added_sugars_g_percent_daily_value,
        "dietary_fiber_g": item.dietary_fiber_g,
        "dietary_fiber_g_percent_daily_value": item.dietary_fiber_g_percent_daily_value,
        "protein_g": item.protein_g,
        "protein_g_percent_daily_value": item.protein_g_percent_daily_value,
        "potassium_mg": item.potassium_mg,
        "potassium_mg_percent_daily_value": item.potassium_mg_percent_daily_value,
        "calcium_mg": item.calcium_mg,
        "calcium_mg_percent_daily_value": item.calcium_mg_percent_daily_value,
        "iron_mg": item.iron_mg,
        "iron_mg_percent_daily_value": item.iron_mg_percent_daily_value,
        "vitamin_d_mcg": item.vitamin_d_mcg,
        "vitamin_d_mcg_percent_daily_value": item.vitamin_d_mcg_percent_daily_value,
    } for item in items])
    return df