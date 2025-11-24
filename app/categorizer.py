import pandas as pd
from app.overrides import apply_overrides
from db.models import Menu
from db.database import SessionLocal


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
db = SessionLocal()
db.query(Menu).delete()  # Clear existing entries
for _, row in df.iterrows():
    item = Menu(
        dish=row["Dish"],
        category=row["Category"],
        hall=row["Hall"],
        time=row["Time"],
        calories=row["Calories"],
        serving_size=row["Serving Size"],
        auto_category=row["AutoCategory"],
        final_category=None  # will fill after overrides
    )
    db.add(item)
db.commit()
db.close()
apply_overrides(Menu)
print("Categorization complete! Saved to menu.db")


