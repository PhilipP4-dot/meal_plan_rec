from db.repositories import fetch_items
import time
from db.database import SessionLocal
from app.recommender import generate_daily_plan

def fetch_plan(meal_times, daily_calorie_limit, meal_ratios=None, preferred_halls=None, top_n=2):
    """
    Generate a daily meal plan based on user preferences.
    
    Args:
        meal_times (list): List of selected meal times.
        daily_calorie_limit (int): Daily calorie limit.
        meal_ratios (list or None): List of calorie ratios for each meal time.
        
    Returns:
        dict: A dictionary containing the recommended meals for each meal time.
    """
    # Placeholder implementation
    db = SessionLocal()
    try:
        df = fetch_items(db, time=time.strftime("%Y-%m-%d"))
    finally:
        db.close()
    return generate_daily_plan(df, meal_times, daily_calorie_limit, meal_ratios, preferred_halls, top_n)

    