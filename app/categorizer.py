import pandas as pd
from app.overrides import apply_overrides
from db.models import Menu, BarOverride, RoleOverride
from db.database import SessionLocal
from sentence_transformers import SentenceTransformer
import json
import numpy as np
import re

#==================================================================================================================
# Categorize by station keywords with manual overrides

df = pd.read_csv("data/menu_data.csv")

DESSERT_BEV = ["bakery", "pastries", "pastry", "dessert", "sweets", "treats", "ice cream",
               "beverage", "drink", "coffee", "tea", "juice", "milk", "smoothie", "velvet", "shake", "hydration"]

PIZZA = ["pizza", "flatbread"]
SOUP = ["soup", "chili", "broth", "ramen", "pho"]

GRILL = ["classics", "grill", "burger", "sandwich", "panini", "deli", "wrap"]

# breakfast-only signals
BYO_BREAKFAST = ["toasted", "omelet", "waffle", "pancake", "oatmeal", "grits", "cereal", "toast", "bagel", "fruit", "yogurt"]

BYO_SALAD = ["salad", "greens", "produce", "market"]

BYO_BOWL = ["entree", "rooted", "fueld", "allgood", "build your own", "bowl", "rice", "grain", "taco", "gyro", "poke", "plate", "mediterranean", "greek", "street eats"]

HOT_ENTREE = ["entrée", "chef", "special", "kitchen"] 

def keyword_categorize_station(s):

    # must maintain order of checks
    if any(k in s for k in DESSERT_BEV):
        return "dessert_beverage"
    elif any(k in s for k in PIZZA):
        return "pizza"
    elif any(k in s for k in SOUP):
        return "soup"
    elif any(k in s for k in GRILL):
        return "grill"

    elif any(k in s for k in BYO_BREAKFAST):
        return "byo_breakfast"

    elif any(k in s for k in BYO_SALAD):
        return "byo_salad"
    elif any(k in s for k in BYO_BOWL):
        return "byo_bowl"

    elif any(k in s for k in HOT_ENTREE):
        return "hot_entree"

    # default fallback:
    return "unknown"

def categorize_station(df):
    df = df.copy()
    bars = {}
    db = SessionLocal()
    overrides = {o.raw_bar: o.correct_bar for o in db.query(BarOverride).all()}
    db.close()
    for i in df['Station'].unique().tolist():
        if i in overrides:
            bars[i] = overrides[i]
        else:
            bars[i] = keyword_categorize_station(i)
    df['FinalStation'] = df['Station'].apply(lambda x: bars[x])
    return df

df = categorize_station(df)
unknowns = df[df["FinalStation"] == "unknown"]["Station"].value_counts().head(20)
print("Top unknown stations:\n", unknowns)



#==================================================================================================================

#==================================================================================================
# Assign role per station

def _canon(s: str):
    s = "" if s is None else str(s)
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# Keyword sets (starter; tune with your menu vocabulary)
PROTEIN = {
    "chicken","beef","pork","turkey","ham","bacon","sausage","salmon","tuna","shrimp",
    "tofu","tempeh","egg","eggs","falafel","lentil","lentils","bean","beans","chickpea","chickpeas", "kielbasa"
}
BASE = {
    "rice","quinoa","grain","grains","noodle","noodles","pasta","couscous","bread","bun", "plantain", "spaghetti", "macaroni",
    "tortilla","wrap","potato","potatoes","fries","oatmeal","grits","cereal","waffle","pancake","bagel","toast", "biscuit", "pizza", "mac"
}
GREENS = {"lettuce","spring mix","romaine","kale","spinach","greens"}
VEG = {
    "salad","broccoli","cauliflower","brussels","sprout","sprouts","cabbage","onions","tomato","cucumber",
    "pepper","peppers","carrot","carrots","zucchini","mushroom","mushrooms","corn","bean","beans"
}
SAUCE = {
    "sauce","dressing","vinaigrette","tzatziki","aioli","mayo","pesto","salsa","oil","vinegar","soy","gravy","dip"
}
EXTRA = {"feta","cheese","olives","parsley","cilantro","lime","lemon","pickled","crumbs","seeds","nuts"}

def assign_role(row):
    station = row.get("FinalStation")
    dish_raw = row.get("Dish")
    dish = _canon(dish_raw)

    # check overrides first
    db = SessionLocal()
    override = db.query(RoleOverride).filter_by(dish=dish, final_station=station).first()
    db.close()
    if override is not None:
        return override.role

    # quick helpers
    def has_any(words): 
        return any(w in dish for w in words)
    if station == "dessert_beverage":
        if has_any({"cake","cookie","brownie","pudding","ice cream","pie","muffin","scone","donut","tart","sweet","dessert","bakery","pastry", "roll"}):
            return "dessert"
        elif has_any({"coffee","tea","juice","milk","smoothie","drink","beverage"}):
            return "beverage"
        else:
            return "topping"

    # 2) Non-BYO stations: coarse roles
    elif station in {"hot_entree", "pizza", "soup", "grill"}:
        if has_any(SAUCE):
            return "addon"
        elif has_any({"bread"}):
            return "addon"
        # If it's tiny garnish-like, treat as addon.
        elif (has_any(EXTRA) or has_any(VEG) or has_any(GREENS)) and not has_any(PROTEIN) and not has_any(BASE):
            return "addon"
        return "entree"

    # 3) BYO stations: station-specific roles
    elif station == "byo_bowl":
        if has_any(SAUCE):
            return "sauce"
        elif has_any(PROTEIN):
            return "protein"
        elif has_any(BASE):
            return "base"
        elif has_any(VEG):
            return "veg"
        elif has_any(EXTRA):
            return "extra"
        return "unknown"

    elif station == "byo_salad":
        if has_any(SAUCE):
            return "dressing"
        elif has_any(PROTEIN):
            return "protein"
        elif has_any(GREENS):
            return "base"
        elif has_any(VEG):
            return "veg_topping"
        elif has_any(EXTRA):
            return "extra"
        return "unknown"

    elif station == "byo_breakfast":
        if has_any(SAUCE):
            return "sauce"
        elif has_any(PROTEIN):
            return "protein"
        elif has_any({"yogurt","waffle","pancake","oatmeal","grits","cereal","bagel","toast", "bread", "bun"}):
            return "base"
        elif has_any({"fruit","berry","granola", "cantaloupe","banana","apple", "orange","grapefruit","melon", "grapes"}):
            return "topping"
        elif has_any(EXTRA):
            return "extra"
        elif has_any(VEG):
            return "veg"
        return "unknown"

    return "unknown"


df["Role"] = df.apply(lambda r: assign_role(r), axis=1)
print(df[df["Role"]=="unknown"].groupby("FinalStation").size())

# Save the result
df.to_csv("data/categorized_menu_data.csv", index=False)
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
        role=row["Role"],
        station=row["Station"],
        final_station=row["FinalStation"]
    )
    db.add(item)
db.commit()
db.close()

#==============================================================================================








# Precompute embeddings for keywords



# Define keyword dictionary
# CATEGORY_KEYWORDS = {
#     "main": ["burger", "chicken", "pasta", "beef", "fish", "tofu", "stew", "omelet", "scrambled", "egg", "sausage", "bacon", "soup"],
#     "side": ["rice", "bread", "bun", "fries", "potato", "salad", "vegetable", "beans", "corn", "coleslaw"],
#     "dessert": ["cake", "cookie", "brownie", "pudding", "ice cream", "pie", "muffin", "scone", "donut", "tart"],
#     "beverage": ["milk", "juice", "tea", "coffee", "soda", "water", "smoothie", "lemonade"],
# }

# # Categorization function
# def categorize_dish_simple(name):
#     name_lower = name.lower()
#     for category, keywords in CATEGORY_KEYWORDS.items():
#         if any(keyword in name_lower for keyword in keywords):
#             return category
#     return "other"

# # Apply categorization
# df["AutoCategory"] = df["Dish"].apply(categorize_dish_simple)

# # Save the result
# db = SessionLocal()
# db.query(Menu).delete()  # Clear existing entries
# for _, row in df.iterrows():
#     item = Menu(
#         dish=row["Dish"],
#         category=row["Category"],
#         hall=row["Hall"],
#         time=row["Time"],
#         calories=row["Calories"],
#         serving_size=row["Serving Size"],
#         auto_category=row["AutoCategory"],
#         final_category=None  # will fill after overrides
#     )
#     db.add(item)
# db.commit()
# db.close()
# apply_overrides(Menu)
# print("Categorization complete! Saved to menu.db")


