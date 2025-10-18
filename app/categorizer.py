import pandas as pd


df = pd.read_csv("data/menu_data.csv")

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
df.to_csv("data/menu_data_categorized.csv", index=False)

print("Categorization complete! Saved to menu_data_categorized.csv")


