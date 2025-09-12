import pandas as pd
import os


df = pd.read_csv("menu_data.csv")

# Define keyword dictionary
CATEGORY_KEYWORDS = {
    "main": ["burger", "chicken", "pasta", "beef", "fish", "tofu", "stew", "omelet", "scrambled", "egg", "sausage", "bacon", "soup"],
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
df["AutoCategory"] = df["Dish"].apply(categorize_dish_simple)

# Save the result


print("Categorization complete! Saved to menu_data_categorized.csv")


OVERRIDE_FILE = "manual_overrides.csv"

def apply_overrides(menu_df, override_file=OVERRIDE_FILE):
    """
    Apply manual category corrections to the menu_df.
    Adds/overwrites a FinalCategory column.
    """
    if not os.path.exists(override_file):
        # No overrides yet → just copy AutoCategory
        menu_df["FinalCategory"] = menu_df["AutoCategory"]
        return menu_df

    overrides = pd.read_csv(override_file)
    override_map = overrides.set_index("Dish")["CorrectCategory"].to_dict()

    # Apply overrides if found, otherwise fall back to AutoCategory
    menu_df["FinalCategory"] = menu_df.apply(
        lambda row: override_map.get(row["Dish"], row["AutoCategory"]), axis=1
    )
    return menu_df


def update_override(dish, correct_category, override_file=OVERRIDE_FILE):
    """
    Add/update a manual override for a dish.
    """
    try:
        overrides = pd.read_csv(override_file)
    except FileNotFoundError:
        overrides = pd.DataFrame(columns=["Dish", "CorrectCategory"])
    
    # Remove any old entry for this dish
    overrides = overrides[overrides["Dish"] != dish]
    
    # Add new correction
    overrides = pd.concat(
        [overrides, pd.DataFrame([{"Dish": dish, "CorrectCategory": correct_category}])]
    )
    
    overrides.to_csv(override_file, index=False)
df = apply_overrides(df)
df.to_csv("menu_data_categorized.csv", index=False)
