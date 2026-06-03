import random
import io
import os
import sys
import cProfile
import pstats
import pandas as pd

# ensure project root is on path so 'app' package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.recommender import generate_daily_plan


def make_synthetic_menu(n_items=800):
    halls = ["Curtis", "Huffman", "Smith", "Curtis Annex"]
    categories = ["Lunch", "Dinner"]
    roles = ["protein", "base", "veg", "addon", "entree", "beverage", "dessert", "topping", "extra", "sauce"]
    stations = ["byo_bowl", "byo_salad", "byo_breakfast", "grill", "pizza", "hot_entree"]
    rows = []
    for i in range(n_items):
        hall = random.choice(halls)
        cat = random.choice(categories)
        role = random.choice(roles)
        station = random.choice(stations)
        rows.append({
            "item_name": f"Item {i}",
            "Dish": f"Item {i}",
            "hall": hall,
            "category": cat,
            "role": role,
            "final_station": station,
            "serving_size": "1 serving",
            "time": "12:00pm - 1:00pm",
            "calories": random.randint(50, 700),
        })
    return pd.DataFrame(rows)


def main():
    random.seed(0)
    df = make_synthetic_menu(900)

    pr = cProfile.Profile()
    pr.enable()
    # run multiple times to amplify hotspots
    for _ in range(15):
        generate_daily_plan(df, meal_times=["Lunch", "Dinner"], daily_calorie_limit=2000, top_n=3)
    pr.disable()

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(40)
    print(s.getvalue())


if __name__ == "__main__":
    main()
