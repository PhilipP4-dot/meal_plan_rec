import pandas as pd
from app.recommender import generate_daily_plan
from app.overrides import apply_overrides

def test_recommender_basic():
    # Fake menu with 1 main + 2 sides + 1 beverage
    df = pd.DataFrame([
            {"Dish": "Grilled Chicken", "Category": "Lunch", "Time": "12:00pm - 1:00pm", "Hall": "Curtis", "Serving Size": "1 piece", "Calories": 300, "AutoCategory": "main"},
            {"Dish": "Rice", "Category": "Lunch", "Time": "12:00pm - 1:30pm", "Hall": "Huffman", "Serving Size": "1 cup", "Calories": 200, "AutoCategory": "side"},
            {"Dish": "Salad", "Category": "Lunch", "Time": "12:00pm - 1:00pm", "Hall": "Curtis", "Serving Size": "1 bowl", "Calories": 50, "AutoCategory": "side"},
            {"Dish": "Orange Juice", "Category": "Lunch", "Time": "12:00pm - 1:00pm", "Hall": "Curtis", "Serving Size": "1 glass", "Calories":
 100, "AutoCategory": "beverage"},
        ])

    # Apply overrides (none here, but required for FinalCategory)
    df = apply_overrides(df)

    plan = generate_daily_plan(
        df,
        meal_times=["Lunch"],
        daily_calorie_limit=700,     # Enough for 300+200+50
        preferred_halls=None,
        top_n=1
    )

    # The meal should exist
    assert len(plan["Plan"]) == 1

    lunch = plan["Plan"][0]
    assert lunch["Meal"] == "Lunch"

    # Should have 1 option
    assert len(lunch["Options"]) == 1

    option = lunch["Options"][0]

    # Should be at Curtis
    assert option["Hall"] == "Curtis"

    # Should contain the main
    dishes = [item["Dish"] for item in option["Items"]]
    assert "Grilled Chicken" in dishes

    # Should fit under calorie limit
    assert option["Calories"] <= 700