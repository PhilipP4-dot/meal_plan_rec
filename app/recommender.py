import pandas as pd
import random

external_calorie_fraction = 0.6
internal_calorie_fraction = 0.88
fallback_buffer = 150  # wider than buffer

ROLE_LIMITS_BYO_BOWL = {
    "protein": 1,
    "base": 1,
    "veg": 2,
    "sauce": 1,
    "extra": 2,
    "dessert_beverage": 1
}

ROLE_LIMITS_BYO_SALAD = {
    "protein": 1,
    "base": 1,
    "veg_topping": 2,
    "dressing": 1,
    "extra": 2,
    "dessert_beverage": 1
}

ROLE_LIMITS_BYO_BREAKFAST = {
    "protein": 1,
    "base": 1,
    "topping": 2,
    "sauce": 1,
    "extra": 2,
    "dessert_beverage": 1
}

ROLE_LIMITS_ENTREES = {
    "entree": 1,
    "addon": 2,
    "dessert_beverage": 1
}


OPTIONAL_ROLE_ORDER = {"byo_bowl":["veg", "sauce", "extra"],
                       "byo_salad":["veg_topping", "dressing", "extra"],
                       "byo_breakfast":["topping", "sauce", "extra"]}
    
def build_byo_option(df_bowl, bev_pool,calorie_target, role_limits, used_dishes=None, used_proteins=None, buffer=50, max_attempts=30):
    """
    df: already filtered to one meal-time + one hall + FinalStation == 'byo_bowl'
    calorie_target: target calories for the meal (e.g. 650)
    used_dishes: set of dish names used earlier in the day/week (variety)
    used_proteins: set of protein dish names used earlier (stronger variety)
    buffer: allow exceeding target by up to this many calories
    """
    used_dishes = used_dishes or set()
    used_proteins = used_proteins or set()

    # must be same hall+meal already; we'll reuse these for bev filtering
    hall = df_bowl["Hall"].iloc[0] if "Hall" in df_bowl.columns and len(df_bowl) else None
    meal = df_bowl["Category"].iloc[0] if "Category" in df_bowl.columns and len(df_bowl) else None

    proteins = df_bowl[df_bowl["Role"] == "protein"].copy()
    bases    = df_bowl[df_bowl["Role"] == "base"].copy()

    if proteins.empty or bases.empty:
        return None



    best = None
    best_gap = float("inf")

    for attempt in range(max_attempts):
        # vary randomness per attempt
        random.seed(None)

        local_used_dishes = set(used_dishes).copy()
        local_used_proteins = set(used_proteins).copy()

        # prefer unused proteins
        proteins["pen"] = proteins["Dish"].apply(lambda d: 1 if d in local_used_proteins else 0)
        p_cands = proteins.sort_values(["pen", "Calories"]).head(min(8, len(proteins))).to_dict("records")
        protein = [random.choice(p_cands) for i in range(role_limits["protein"])]

        bases["pen"] = bases["Dish"].apply(lambda d: 1 if d in local_used_dishes else 0)
        b_cands = bases.sort_values(["pen", "Calories"]).head(min(8, len(bases))).to_dict("records")
        base = [random.choice(b_cands) for i in range(role_limits["base"])]    
        chosen = protein + base
        total = sum(float(p["Calories"]) for p in protein) + sum(float(b["Calories"]) for b in base)
        local_used_dishes.update(b["Dish"] for b in base)
        local_used_proteins.update(p["Dish"] for p in protein)

        def try_add(pool_df, max_count):
            nonlocal total, chosen
            if pool_df.empty:
                return
            candidates = pool_df.to_dict("records")
            random.shuffle(candidates)
            count = 0
            for item in candidates:
                if count >= max_count:
                    break
                dish = item["Dish"]
                cal = float(item["Calories"])
                if dish in local_used_dishes:
                    continue
                if total + cal <= calorie_target + buffer:
                    chosen.append(item)
                    total += cal
                    local_used_dishes.add(dish)
                    count += 1

        # fill optional roles
        for role in OPTIONAL_ROLE_ORDER[df_bowl["FinalStation"].iloc[0]]:
            pool = df_bowl[df_bowl["Role"] == role].copy()
            try_add(pool, role_limits[role])

        # optional top-up only if still notably short but not hopelessly short
        gap = calorie_target - total
        if 100 <= gap <= 250:
            try_add(bev_pool, role_limits["dessert_beverage"])

        # evaluate
        gap2 = abs(calorie_target - total)
        if gap2 < best_gap:
            best = (chosen, total)
            best_gap = gap2

        if calorie_target - buffer <= total <= calorie_target + buffer:
            # success: only now should you update global used sets
            used_dishes.update([i["Dish"] for i in base])
            used_proteins.update(p["Dish"] for p in protein)

            return {
                "Hall": hall,
                "Station": df_bowl["FinalStation"].iloc[0],
                "Calories": int(round(total)),
                "Items": [{"Dish": i["Dish"], "Calories": int(round(float(i["Calories"]))), "Serving Size": i["Serving Size"], "Role": i["Role"]} for i in chosen],
            }



    if best is None:
        return None

    chosen, total = best
    if abs(calorie_target - total) <= fallback_buffer and total >= calorie_target * internal_calorie_fraction:
        return {
            "Hall": hall,
            "Station": df_bowl["FinalStation"].iloc[0],
            "Calories": int(round(total)),
            "Items": [{"Dish": i["Dish"], "Calories": int(round(float(i["Calories"]))), "Serving Size": i["Serving Size"], "Role": i["Role"]} for i in chosen],
        }
    return None

#print(build_byo_bowl_option(df[(df['Hall']=='Huffman') & (df['FinalStation']=='byo_bowl') & (df['Category'] == 'Lunch')], bev, 1000))


def build_entree_option(df_entrees, bev_pool, calorie_target, role_limits, used_dishes=None, buffer=50, max_attempts=30):
    """
    df: already filtered to one meal-time + one hall + FinalStation == 'entree'
    calorie_target: target calories for the meal (e.g. 650)
    used_dishes: set of dish names used earlier in the day/week (variety)
    buffer: allow exceeding target by up to this many calories
    """
    used_dishes = used_dishes or set()

    # must be same hall+meal already; we'll reuse these for bev filtering
    hall = df_entrees["Hall"].iloc[0] if "Hall" in df_entrees.columns and len(df_entrees) else None
    meal = df_entrees["Category"].iloc[0] if "Category" in df_entrees.columns and len(df_entrees) else None

    entrees = df_entrees[df_entrees["Role"] == "entree"].copy()
    addons  = df_entrees[df_entrees["Role"] == "addon"].copy()

    if entrees.empty:
        return None



    best = None
    best_gap = float("inf")

    for attempt in range(max_attempts):
        # vary randomness per attempt
        random.seed(None)

        local_used_dishes = set(used_dishes).copy()

        # prefer unused entrees
        entrees["pen"] = entrees["Dish"].apply(lambda d: 1 if d in local_used_dishes else 0)
        e_cands = entrees.sort_values(["pen", "Calories"]).head(min(8, len(entrees))).to_dict("records")
        entree = [random.choice(e_cands) for i in range(role_limits["entree"])]

        chosen = entree
        total = sum(float(e["Calories"]) for e in entree)
        local_used_dishes.update(e["Dish"] for e in entree)
        def try_add(pool_df, max_count):
            nonlocal total, chosen
            if pool_df.empty:
                return
            candidates = pool_df.to_dict("records")
            random.shuffle(candidates)
            count = 0
            for item in candidates:
                if count >= max_count:
                    break
                dish = item["Dish"]
                cal = float(item["Calories"])
                if dish in local_used_dishes:
                    continue
                if total + cal <= calorie_target + buffer:
                    chosen.append(item)
                    total += cal
                    local_used_dishes.add(dish)
                    count += 1

        # fill optional roles
        try_add(addons, role_limits["addon"])
        # optional top-up only if still notably short but not hopelessly short
        gap = calorie_target - total
        if 100 <= gap <= 250:
            try_add(bev_pool, role_limits["dessert_beverage"])
        # evaluate
        gap2 = abs(calorie_target - total)
        if gap2 < best_gap:
            best = (chosen, total)
            best_gap = gap2
        if calorie_target - buffer <= total <= calorie_target + buffer:
            # success: only now should you update global used sets
            used_dishes.update(i["Dish"] for i in entree)

            return {
                "Hall": hall,
                "Station": "entree",
                "Calories": int(round(total)),
                "Items": [{"Dish": i["Dish"], "Calories": int(round(float(i["Calories"]))), "Serving Size": i["Serving Size"], "Role": i["Role"]} for i in chosen],
            }

#print(build_entree_option(df[(df['Hall']=='Huffman') & ((df['FinalStation']=='grill') | (df['FinalStation']=="pizza")) & (df['Category'] == 'Lunch')], bev, 600, ROLE_LIMITS_ENTREES))
# def build_entrees_option(df_entrees, calorie_target, used_dishes=None, buffer=50, max_attempts=30):


def _coerce_calories(df):
    df = df.copy()
    df["Calories"] = pd.to_numeric(df["Calories"], errors="coerce")
    df = df.dropna(subset=["Calories"])
    return df

def generate_daily_plan(menu_df, meal_times, daily_calorie_limit, top_n,
                        meal_ratios=None, preferred_halls=None):
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
    plan, chosen_mains, chosen_proteins, total_calories = [], set(), set(), 0

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
        print(type(preferred_halls))
        halls = [preferred_halls[meal]] if (preferred_halls and meal in preferred_halls) \
                else meal_opts["Hall"].dropna().unique()
        candidates = []

        def safe_max(df_role):
            m = pd.to_numeric(df_role["Calories"], errors="coerce").max()
            return 0.0 if pd.isna(m) else float(m)

        for hall in halls:
            # time = meal_opts[meal_opts["Hall"] == hall]["Time"].mode()
            # time = time.values[0] if not time.empty else ""
            # print(f"Evaluating meal '{meal}' at hall '{hall}' during '{time}'")
            time = menu_df[(menu_df['Category'] == meal) & (menu_df['Hall'] == hall)]['Time'].unique()[0]
            hall_items = meal_opts[meal_opts["Hall"] == hall].copy()
            if hall_items.empty:
                continue
            bev = hall_items[(hall_items["Role"] == "dessert") | (hall_items["Role"] == "beverage")]
            bowl = hall_items[hall_items["FinalStation"] == "byo_bowl"]
            ent = hall_items[hall_items["FinalStation"].isin(["grill", "pizza", "hot_entree"])]
            salad = hall_items[hall_items["FinalStation"] == "byo_salad"]
            breakfast = hall_items[hall_items["FinalStation"] == "byo_breakfast"]

            bowl_limits = ROLE_LIMITS_BYO_BOWL.copy()
            salad_limits = ROLE_LIMITS_BYO_SALAD.copy()
            breakfast_limits = ROLE_LIMITS_BYO_BREAKFAST.copy()
            entree_limits = ROLE_LIMITS_ENTREES.copy()

            num_of_incr = 0
            while safe_max(bowl[bowl["Role"]=="protein"]) * bowl_limits["protein"] + safe_max(bowl[bowl["Role"]=="base"]) * bowl_limits["base"] + safe_max(bowl[bowl["Role"]=="veg"]) * bowl_limits["veg"] \
                + safe_max(bowl[bowl["Role"]=="extra"]) * bowl_limits["extra"] < external_calorie_fraction *cal_per_meal and num_of_incr<2:
                if num_of_incr > 0:
                    bowl_limits["protein"] +=1
                    bowl_limits["veg"] +=1
                    bowl_limits["extra"] +=1
                    num_of_incr +=1
                    continue
                bowl_limits["veg"] +=1
                bowl_limits["extra"] +=1
                bowl_limits["sauce"] +=1
                bowl_limits["base"] +=1
                num_of_incr +=1
            
            num_of_incr = 0
            while safe_max(ent[ent["Role"]=="entree"]) * entree_limits["entree"] + safe_max(ent[ent["Role"]=="addon"]) * entree_limits["addon"] < external_calorie_fraction *cal_per_meal and num_of_incr < 2:
                if num_of_incr > 0:
                    entree_limits["entree"] +=1
                    entree_limits["addon"] +=1
                    num_of_incr +=1
                    continue
                entree_limits["addon"] +=1
                num_of_incr +=1
            
            num_of_incr = 0
            while safe_max(salad[salad["Role"]=="protein"]) * salad_limits["protein"] + safe_max(salad[salad["Role"]=="base"]) * salad_limits["base"] + safe_max(salad[salad["Role"]=="veg_topping"]) * salad_limits["veg_topping"] \
                + safe_max(salad[salad["Role"]=="extra"]) * salad_limits["extra"] < external_calorie_fraction *cal_per_meal and num_of_incr < 2:
                if num_of_incr > 0:
                    salad_limits["protein"] +=1
                    salad_limits["veg_topping"] +=1
                    salad_limits["extra"] +=1
                    num_of_incr +=1
                    continue
                salad_limits["veg_topping"] +=1
                salad_limits["extra"] +=1
                salad_limits["dressing"] +=1
                salad_limits["base"] +=1
                num_of_incr +=1
            
            num_of_incr = 0
            while safe_max(breakfast[breakfast["Role"]=="protein"]) * breakfast_limits["protein"] + safe_max(breakfast[breakfast["Role"]=="base"]) * breakfast_limits["base"] + safe_max(breakfast[breakfast["Role"]=="topping"]) * breakfast_limits["topping"] \
                + safe_max(breakfast[breakfast["Role"]=="extra"]) * breakfast_limits["extra"] < external_calorie_fraction *cal_per_meal and num_of_incr < 2:
                if num_of_incr > 0:
                    breakfast_limits["protein"] +=1
                    breakfast_limits["topping"] +=1
                    breakfast_limits["extra"] +=1
                    num_of_incr +=1
                    continue
                breakfast_limits["topping"] +=1
                breakfast_limits["extra"] +=1
                breakfast_limits["sauce"] +=1
                breakfast_limits["base"] +=1
                num_of_incr +=1
            for i in range(3):
            # BYO Bowl option
                byo_bowl_option = build_byo_option(
                    bowl,
                    bev,
                    cal_per_meal,
                    role_limits=bowl_limits,
                    used_dishes=chosen_mains,
                    used_proteins=chosen_proteins
                )
                if byo_bowl_option:
                    candidates.append({
                        #"Meal": meal,
                        "Hall": hall,
                        "Calories": byo_bowl_option["Calories"],
                        "Time": time,
                        "Items": byo_bowl_option["Items"],      
                        "Score": abs(cal_per_meal - byo_bowl_option["Calories"]) + (50 if byo_bowl_option["Items"][-1]["Role"] == "dessert" or byo_bowl_option["Items"][-1]["Role"] == "beverage" else 0)
                    })
                      # prefer BYO Bowl if available
                # Entree option
                entree_option = build_entree_option(
                    ent,
                    bev,
                    cal_per_meal,
                    role_limits=entree_limits,
                    used_dishes=chosen_mains
                )
                if entree_option:
                    candidates.append({
                        #"Meal": meal,
                        "Hall": hall,
                        "Calories": entree_option["Calories"],
                        "Time": time,
                        "Items": entree_option["Items"],
                        "Score": abs(cal_per_meal - entree_option["Calories"]) + (50 if entree_option["Items"][-1]["Role"] == "dessert" or entree_option["Items"][-1]["Role"] == "beverage" else 0)
                    })
                      # prefer Entree if available
                # BYO Salad option
                byo_salad_option = build_byo_option(
                    salad,
                    bev,
                    cal_per_meal,
                    role_limits=salad_limits,
                    used_dishes=chosen_mains,
                    used_proteins=chosen_proteins
                )
                if byo_salad_option:
                    candidates.append({
                        #"Meal": meal,
                        "Hall": hall,
                        "Calories": byo_salad_option["Calories"],
                        "Time": time,
                        "Items": byo_salad_option["Items"],
                        "Score": abs(cal_per_meal - byo_salad_option["Calories"]) + (50 if byo_salad_option["Items"][-1]["Role"] == "dessert" or byo_salad_option["Items"][-1]["Role"] == "beverage" else 0)
                    })
                      # prefer BYO Salad if available
                # BYO Breakfast option
                byo_breakfast_option = build_byo_option(
                    breakfast,
                    bev,
                    cal_per_meal,
                    role_limits=breakfast_limits,
                    used_dishes=chosen_mains,
                    used_proteins=chosen_proteins
                )
                if byo_breakfast_option:
                    candidates.append({
                        #"Meal": meal,
                        "Hall": hall,
                        "Calories": byo_breakfast_option["Calories"],
                        "Time": time,
                        "Items": byo_breakfast_option["Items"],      
                        "Score": abs(cal_per_meal - byo_breakfast_option["Calories"]) + (50 if byo_breakfast_option["Items"][-1]["Role"] == "dessert" or byo_breakfast_option["Items"][-1]["Role"] == "beverage" else 0)
                    })
                      # prefer BYO Breakfast if available
           
            

            
             
        if candidates:
            candidates.sort(key=lambda c: c["Score"], reverse=False)
            top = candidates[:top_n]
            plan.append({"Meal": meal, "Cal_budget": round(cal_per_meal), "Options": top})

            # update variety + running total using first option
            first = top[0]
            # get all roles
            roles = []
            for i in range(len(first["Items"])):
                if first["Items"][i]["Role"] not in roles:
                    roles.append(first["Items"][i]["Role"])
            for i in range(len(top)):
                for j in range(len(top[i]["Items"])):
                    if top[i]["Items"][j]["Role"] == roles[0]:  # assuming first role is main dish
                        chosen_proteins.add(top[i]["Items"][j]["Dish"])
                    elif top[i]["Items"][j]["Role"] == roles[1]:  # assuming second role is main dish
                        chosen_mains.add(top[i]["Items"][j]["Dish"])
   
            total_calories += first["Calories"]

    return {"Plan": plan, "Total_calories": total_calories}

#=======================================================================================================================
# Meal Generation Parameters
# ADJUST PARAMETERS FOR YOUR MEAL RECOMMENDATION PREFERENCES
# Adjust Meal times(Breakfast, Lunch, Dinner), Daily Calorie Limit, Meal Ratios(for a total of 100%), Preferred Halls
# for each meal period and number of options you want made available to you
#=======================================================================================================================
meal_times = ["Breakfast", "Dinner"]  # options: Breakfast, Lunch, Brunch, Dinner
daily_calorie_limit = 2500
meal_ratios = {}   # custom split
preferred_halls = {}                        # force hall for dinner

top_n = 2  # number of options per meal
# # #=======================================================================================================================
# from db.repositories import fetch_items
# from db.database import SessionLocal
# db = SessionLocal()
# df = fetch_items(db, time="2026-01-27")  # dummy db session
# daily_plan = generate_daily_plan(df, meal_times, daily_calorie_limit, meal_ratios, preferred_halls, top_n)
# print(daily_plan)