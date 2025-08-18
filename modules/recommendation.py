import pandas as pd

# Load your menu CSV
menu_df = pd.read_csv("menu_data.csv")

# Define keyword dictionary
CATEGORY_KEYWORDS = {
    "main": ["burger", "chicken", "pasta", "beef", "fish", "tofu", "stew", "omelet", "scrambled", "egg", "sausage", "bacon"],
    "side": ["rice", "bread", "bun", "fries", "potato", "salad", "vegetable", "beans", "corn", "coleslaw"],
    "dessert": ["cake", "cookie", "brownie", "pudding", "ice cream", "pie", "muffin", "scone", "donut", "tart"],
    "beverage": ["milk", "juice", "tea", "coffee", "soda", "water", "smoothie", "lemonade"],
}

# Categorization function
def categorize_dish_simple(name):
    name_lower = name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in name_lower for keyword in keywords):
            return category
    return "other"

# Apply categorization
menu_df["AutoCategory"] = menu_df["Dish"].apply(categorize_dish_simple)

# Save the result
menu_df.to_csv("menu_data_categorized.csv", index=False)

print("Categorization complete! Saved to menu_data_categorized.csv")

def generate_daily_plan(menu_df, meal_times, daily_calorie_limit, 
                        meal_ratios=None, preferred_halls=None, top_n=2):
    """
    Generate a balanced daily meal plan across dining halls.
    
    Parameters:
        menu_df (DataFrame): columns ["Category","Dish","Calories","AutoCategory","Hall"]
        meal_times (list): e.g. ["Breakfast","Lunch","Dinner"]
        daily_calorie_limit (int): total daily calories allowed
        meal_ratios (dict): optional ratio per meal, e.g. {"Breakfast":0.25,"Lunch":0.40,"Dinner":0.35}
        preferred_halls (dict): optional hall selection per meal, e.g. {"Breakfast":"Curtis"}
        top_n (int): number of options to return per meal
    
    Returns:
        dict with plan and total calories
    """
    plan = []
    chosen_mains = set()
    total_calories = 0

    for meal in meal_times:
        # Calorie allocation
        if meal_ratios and meal in meal_ratios:
            cal_per_meal = daily_calorie_limit * meal_ratios[meal]
        else:
            cal_per_meal = daily_calorie_limit / len(meal_times)

        # Filter items for this meal
        meal_options = menu_df[menu_df["Category"].str.contains(meal, case=False)]
        if meal_options.empty:
            continue

        # Decide which halls to consider
        if preferred_halls and meal in preferred_halls:
            halls_to_check = [preferred_halls[meal]]
        else:
            halls_to_check = meal_options["Hall"].unique()

        meal_candidates = []

        for hall in halls_to_check:
            hall_items = meal_options[meal_options["Hall"] == hall]

            # Mains
            mains = hall_items[hall_items["AutoCategory"] == "main"]
            if chosen_mains:
                mains = mains[~mains["Dish"].str.lower().str.contains("|".join(chosen_mains), na=False)]

            if mains.empty:
                continue

            for _, main in mains.iterrows():
                meal_cal = main["Calories"]
                meal_list = [main["Dish"]]
                serving_size = [main["Serving Size"]]
                calorie = [main["Calories"]]


                # Add sides
                sides = hall_items[hall_items["AutoCategory"] == "side"]
                for _, side in sides.iterrows():
                    if meal_cal + side["Calories"] <= cal_per_meal:
                        meal_list.append(side["Dish"])
                        meal_cal += side["Calories"]
                        serving_size.append(side["Serving Size"])
                        calorie.append(side["Calories"])

                # Add extras
                extras = hall_items[hall_items["AutoCategory"].isin(["dessert","beverage"])]
                for _, extra in extras.iterrows():
                    if meal_cal + extra["Calories"] <= cal_per_meal:
                        meal_list.append(extra["Dish"])
                        meal_cal += extra["Calories"]
                        serving_size.append(extra["Serving Size"])
                        calorie.append(extra["Calories"])

                meal_candidates.append({
                    "Meal": meal,
                    "Hall": hall,
                    "Items": meal_list,
                    "Calories": meal_cal,
                    "Serving size": serving_size,
                    "Calories list": calorie
                })

        # Sort and keep top N
        if meal_candidates:
            meal_candidates = sorted(meal_candidates, key=lambda x: x["Calories"], reverse=True)[:top_n]
            plan.append({
                "Meal": meal,
                "Options": meal_candidates
            })
            # Take the first option as the "chosen" one for variety tracking
            chosen_mains.update(meal_candidates[0]["Items"][0].lower().split())
            total_calories += meal_candidates[0]["Calories"]

    return {
        "Plan": plan,
        "TotalCalories": total_calories
    }


#=======================================================================================================================
# Meal Generation Parameters
# ADJUST PARAMETERS FOR YOUR MEAL RECOMMENDATION PREFERENCES
# Adjust Meal times(Breakfast, Lunch, Dinner), Daily Calorie Limit, Meal Ratios(for a total of 100%), Preferred Halls
# for each meal period and number of options you want made available to you
#=======================================================================================================================
meal_times = ["Breakfast", "Lunch", "Dinner"]
daily_calorie_limit = 2000

meal_ratios = {"Breakfast":0.25, "Lunch":0.40, "Dinner":0.35}   # custom split
preferred_halls = {"Breakfast":"Curtis"}                        # force hall for breakfast

top_n = 1  # number of options per meal
#=======================================================================================================================

daily_plan = generate_daily_plan(menu_df, meal_times, daily_calorie_limit, meal_ratios, preferred_halls, top_n)

for meal in daily_plan["Plan"]:
    print(f"\n{meal['Meal']} Options:")
    for i, option in enumerate(meal["Options"], 1):
        print(f"  Option {i} @ {option['Hall']} ({option['Calories']} cal)")
        for item, serving, cals in zip(option["Items"], option["Serving size"], option["Calories list"]):
            print(f"   - {item} ({serving}): {cals} cal")

print(f"\nTOTAL DAILY CALORIES (based on chosen first options): {daily_plan['TotalCalories']}")