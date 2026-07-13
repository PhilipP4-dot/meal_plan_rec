import pandas as pd
from app.overrides import apply_role_overrides, apply_station_overrides, update_role_override, update_station_override
from db.models import Menu, StationOverride, RoleOverride
from db.database import SessionLocal
import re

#==================================================================================================================
# Categorize by station keywords with manual overrides

#df = pd.read_csv("data/menu_data.csv")

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
    overrides = {o.raw_station: o.correct_station for o in db.query(StationOverride).all()}
    db.close()
    for i in df['station'].unique().tolist():
        if i in overrides:
            bars[i] = overrides[i]
        else:
            bars[i] = keyword_categorize_station(i)
    df['final_station'] = df['station'].apply(lambda x: bars[x])
    return df

# df = categorize_station(df)
# unknowns = df[df["final_station"] == "unknown"]["station"].value_counts().head(20)
# print("Top unknown stations:\n", unknowns)



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
    station = row.get("final_station")
    dish_raw = row.get("item_name")
    dish = _canon(dish_raw)

    # check overrides first
    db = SessionLocal()
    override = db.query(RoleOverride).filter_by(item_name=dish, final_station=station).first() #check
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


# df["Role"] = df.apply(lambda r: assign_role(r), axis=1)
# print(df[df["Role"]=="unknown"].groupby("FinalStation").size())

# # Save the result
# df.to_csv("data/categorized_menu_data.csv", index=False)
# db = SessionLocal()
# db.query(Menu).delete()  # Clear existing entries
# for _, row in df.iterrows():
#     item = Menu(
#         item_name=row["item_name"],
#         category=row["category"],
#         hall=row["hall"],
#         time=row["time"],
#         calories=row["calories"],
#         serving_size=row["serving_size"],
#         role=row["role"],
#         station=row["station"],
#         final_station=row["final_station"]
#     )
#     db.add(item)
# db.commit()
# db.close()

#==============================================================================================


def categorize_hall_dish():
    df = pd.read_csv("data/menu_data.csv")
    df = categorize_station(df)
    unknowns = df[df["final_station"] == "unknown"]["station"].value_counts().head(20)
    print("Top unknown stations:\n", unknowns)

    # Save the result
    df["role"] = df.apply(lambda r: assign_role(r), axis=1)
    print(df[df["role"]=="unknown"].groupby("final_station").size())

    # Save the result
    df.to_csv("data/categorized_menu_data.csv", index=False)
    db = SessionLocal()
    db.query(Menu).delete()  # Clear existing entries
    for _, row in df.iterrows():
        item = Menu(
            item_name=row["item_name"],
            category=row["category"],
            hall=row["hall"],
            time=row["time"],
            calories=row["calories"],
            serving_size=row["serving_size"],
            role=row["role"],
            station=row["station"],
            final_station=row["final_station"],
            description = row["description"],
            allergens = row["allergens"],
            dietary_preferences = row["dietary_preferences"],
            calories_percent_daily_value = row["calories_percent_daily_value"],
            total_fat_g = row["total_fat_g"],
            total_fat_g_percent_daily_value = row["total_fat_g_percent_daily_value"],
            saturated_fat_g = row["saturated_fat_g"],
            saturated_fat_g_percent_daily_value = row["saturated_fat_g_percent_daily_value"],
            trans_fat_g = row["trans_fat_g"],
            trans_fat_g_percent_daily_value = row["trans_fat_g_percent_daily_value"],
            cholesterol_mg = row["cholesterol_mg"],
            cholesterol_mg_percent_daily_value = row["cholesterol_mg_percent_daily_value"],
            sodium_mg = row["sodium_mg"],
            sodium_mg_percent_daily_value = row["sodium_mg_percent_daily_value"],
            total_carbohydrate_g = row["total_carbohydrate_g"],
            total_carbohydrate_g_percent_daily_value = row["total_carbohydrate_g_percent_daily_value"],
            total_sugars_g = row["total_sugars_g"],
            added_sugars_g = row["added_sugars_g"],
            added_sugars_g_percent_daily_value = row["added_sugars_g_percent_daily_value"],
            dietary_fiber_g = row["dietary_fiber_g"],
            dietary_fiber_g_percent_daily_value = row["dietary_fiber_g_percent_daily_value"],
            protein_g = row["protein_g"],
            protein_g_percent_daily_value = row["protein_g_percent_daily_value"],
            potassium_mg = row["potassium_mg"],
            potassium_mg_percent_daily_value = row["potassium_mg_percent_daily_value"],
            calcium_mg = row["calcium_mg"],
            calcium_mg_percent_daily_value = row["calcium_mg_percent_daily_value"],
            iron_mg = row["iron_mg"],
            iron_mg_percent_daily_value = row["iron_mg_percent_daily_value"],
            vitamin_d_mcg = row["vitamin_d_mcg"],
            vitamin_d_mcg_percent_daily_value = row["vitamin_d_mcg_percent_daily_value"]
        )
        db.add(item)
        try:
            db.commit()
        except Exception:
            print(row)
            raise
    db.close()



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


