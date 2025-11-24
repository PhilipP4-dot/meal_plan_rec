import pandas as pd
from db.models import Menu
from db.database import SessionLocal

db = SessionLocal()
items = db.query(Menu).all()
df = pd.DataFrame([{
    "Dish": item.dish,
    "Category": item.category,
    "Hall": item.hall,
    "Time": item.time,
    "Calories": item.calories,
    "Serving Size": item.serving_size,
    "AutoCategory": item.auto_category,
    "FinalCategory": item.final_category
} for item in items])
print(df.head())


def _coerce_calories(df):
    df = df.copy()
    df["Calories"] = pd.to_numeric(df["Calories"], errors="coerce")
    df = df.dropna(subset=["Calories"])
    return df

def generate_daily_plan(menu_df, meal_times, daily_calorie_limit, 
                        meal_ratios=None, preferred_halls=None, top_n=2):
    """
    Returns:
      {
        "Plan": [
          {
            "Meal": "Breakfast",
            "CalBudget": 616,              # per-meal budget used
            "Options": [
              {
                "Hall": "Huff",
                "Items": [
                  {"row_id": 123, "Dish":"Diced Turkey Sausage","Calories":90,"Serving Size":"1 patty","FinalCategory":"main","Hall":"Huff"},
                  {"row_id": 456, "Dish":"Twice Baked Breakfast Potatoes","Calories":330,"Serving Size":"1 serving","FinalCategory":"side","Hall":"Huff"},
                  ...
                ],
                "Calories": 600            # sum of Items' calories (source of truth)
              },
              ...
            ]
          },
          ...
        ],
        "TotalCalories": 1815              # sum of first options
      }
    """

    df = _coerce_calories(menu_df)
    plan, chosen_mains, total_calories = [], set(), 0

    for meal in meal_times:
        # normalize meal name
        if len(meal.split(" ")) > 1:
            meal = ' '.join(meal.split(' ')[0:-1])
        meal = meal.strip()

        # per-meal budget
        cal_per_meal = (daily_calorie_limit * meal_ratios.get(meal)
                        if meal_ratios and meal in meal_ratios
                        else daily_calorie_limit / max(1, len(meal_times)))

        # filter: meal slot + realistic calories
        meal_opts = df[df["Category"].str.contains(meal, case=False, na=False)]
        meal_opts = meal_opts[meal_opts["Calories"].between(10, 2000)]
        if meal_opts.empty:
            continue

        halls = [preferred_halls[meal]] if (preferred_halls and meal in preferred_halls) \
                else meal_opts["Hall"].dropna().unique()

        candidates = []

        for hall in halls:
            # time = meal_opts[meal_opts["Hall"] == hall]["Time"].mode()
            # time = time.values[0] if not time.empty else ""
            # print(f"Evaluating meal '{meal}' at hall '{hall}' during '{time}'")
            time = menu_df[(menu_df['Category'] == meal) & (menu_df['Hall'] == hall)]['Time'].unique()[0]
            hall_items = meal_opts[meal_opts["Hall"] == hall].copy()
            if hall_items.empty:
                continue
            
            mains = hall_items[hall_items["FinalCategory"] == "main"]
            # avoid regex bug when chosen_mains is empty
            if chosen_mains:
                mains = mains[~mains["Dish"].str.lower().str.contains("|".join(chosen_mains), na=False)]
            if mains.empty:
                continue

            # iterate mains
            for main_idx, main in mains.iterrows():
                chosen = [{
                    "row_id": int(main_idx),
                    "Dish": main["Dish"],
                    "Calories": float(main["Calories"]),
                    "Serving Size": main.get("Serving Size", ""),
                    "FinalCategory": main.get("FinalCategory", ""),
                    "Hall": main.get("Hall", "")
                }]

                # sides: max 2, distinct-ish by first token
                # soft cap of 2 sides to prevent overfitting to sides
                sides = hall_items[hall_items["FinalCategory"] == "side"]
                added_side_keys = set()
                for side_idx, side in sides.iterrows():
                    key = str(side["Dish"]).split()[0].lower() if isinstance(side["Dish"], str) else str(side_idx)
                    next_total = sum(i["Calories"] for i in chosen) + float(side["Calories"])
                    if key in added_side_keys or next_total > cal_per_meal:
                        continue
                    chosen.append({
                        "row_id": int(side_idx),
                        "Dish": side["Dish"],
                        "Calories": float(side["Calories"]),
                        "Serving Size": side.get("Serving Size", ""),
                        "FinalCategory": side.get("FinalCategory", ""),
                        "Hall": side.get("Hall", "")
                    })
                    added_side_keys.add(key)
                    if len(added_side_keys) >= 2:
                        break

                # extras: max 1 beverage; ignore zero-cal
                extras = hall_items[
                    hall_items["FinalCategory"].isin(["dessert", "beverage"])
                    & (hall_items["Calories"] > 0)
                ]
                beverage_added = False
                for ex_idx, ex in extras.iterrows():
                    if ex.get("FinalCategory") == "beverage" and beverage_added:
                        continue
                    next_total = sum(i["Calories"] for i in chosen) + float(ex["Calories"])
                    if next_total > cal_per_meal:
                        continue
                    chosen.append({
                        "row_id": int(ex_idx),
                        "Dish": ex["Dish"],
                        "Calories": float(ex["Calories"]),
                        "Serving Size": ex.get("Serving Size", ""),
                        "FinalCategory": ex.get("FinalCategory", ""),
                        "Hall": ex.get("Hall", "")
                    })
                    if ex.get("FinalCategory") == "beverage":
                        beverage_added = True

                # authoritative total from items
                meal_total = round(sum(i["Calories"] for i in chosen))
                if meal_total <= cal_per_meal:
                    candidates.append({
                        "Meal": meal,
                        "Hall": hall,
                        "Items": chosen,
                        "Calories": meal_total,
                        "Time": time
                    })

        if candidates:
            candidates.sort(key=lambda c: c["Calories"], reverse=True)
            top = candidates[:top_n]
            plan.append({"Meal": meal, "CalBudget": round(cal_per_meal), "Options": top})

            # update variety + running total using first option
            first = top[0]
            first_main_words = str(first["Items"][0]["Dish"]).lower().split()
            chosen_mains.update(first_main_words)
            total_calories += first["Calories"]

    return {"Plan": plan, "TotalCalories": total_calories}

#=======================================================================================================================
# Meal Generation Parameters
# ADJUST PARAMETERS FOR YOUR MEAL RECOMMENDATION PREFERENCES
# Adjust Meal times(Breakfast, Lunch, Dinner), Daily Calorie Limit, Meal Ratios(for a total of 100%), Preferred Halls
# for each meal period and number of options you want made available to you
#=======================================================================================================================
# meal_times = ["Breakfast", "Lunch ","Dinner "]
# daily_calorie_limit = 1850
# menu_df = pd.read_csv("data/menu_data_categorized.csv")
# meal_ratios = {}   # custom split
# preferred_halls = {}                        # force hall for breakfast

# top_n = 1  # number of options per meal
# # #=======================================================================================================================

# daily_plan = generate_daily_plan(menu_df, meal_times, daily_calorie_limit, meal_ratios, preferred_halls, top_n)
