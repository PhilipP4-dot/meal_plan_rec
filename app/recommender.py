import pandas as pd
import random
import re

external_calorie_fraction = 0.6
internal_calorie_fraction = 0.88
fallback_buffer = 150  # wider than buffer
MACRO_SCALE = 32.0  # kcal scaling when converting macro distance to score (tunable)

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

_ALLERGEN_ALIASES = {
    "egg": "eggs",
    "eggs": "eggs",
    "milk": "milk",
    "dairy": "milk",
    "soy": "soy",
    "wheat": "wheat",
    "gluten": "wheat",
    "peanut": "peanut",
    "tree_nut": "tree_nuts",
    "tree_nuts": "tree_nuts",
    "fish": "fish",
    "shellfish": "shellfish",
    "sesame": "sesame",
}

_PREFERENCE_ALIASES = {
    "vegetarian": "Vegetarian",
    "vegan": "Vegan",
    "made_without_gluten": "Made Without Gluten",
    "gluten_free": "Made Without Gluten",
    "gluten-free": "Made Without Gluten",
}


def _clean_token(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _split_values(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = re.split(r"[,;/|]", str(value))
    return [item.strip() for item in values if str(item).strip()]


def _normalize_allergen(value):
    token = _clean_token(value)
    return _ALLERGEN_ALIASES.get(token, token)


def _normalize_preference(value):
    token = _clean_token(value)
    return _PREFERENCE_ALIASES.get(token, str(value).strip())


def _to_float(value):
    if value is None:
        return 0.0
    try:
        if pd.isna(value):
            return 0.0
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return 0.0


def _normalize_diet_preferences(diet_preferences):
    normalized = {
        "exclude_allergens": set(),
        "required_preferences": set(),
        "macro_focus": "balanced",
        "macro_scale": MACRO_SCALE,
    }
    if not diet_preferences:
        return normalized

    if isinstance(diet_preferences, str):
        diet_preferences = {"macro_focus": diet_preferences}

    for allergen in _split_values(diet_preferences.get("exclude_allergens")):
        normalized["exclude_allergens"].add(_normalize_allergen(allergen))

    for preference in _split_values(diet_preferences.get("required_preferences")):
        normalized["required_preferences"].add(_normalize_preference(preference))

    macro_focus = diet_preferences.get("macro_focus") or diet_preferences.get("focus") or "balanced"
    normalized["macro_focus"] = _clean_token(macro_focus) or "balanced"
    # optional numeric override for macro scaling (kcal per score unit)
    try:
        if diet_preferences.get("macro_scale") is not None:
            normalized["macro_scale"] = float(diet_preferences.get("macro_scale"))
    except Exception:
        pass
    return normalized


def _row_allergens(row):
    return {
        _normalize_allergen(allergen)
        for allergen in _split_values(row.get("allergens"))
    }


def _row_preferences(row):
    return {
        _normalize_preference(preference)
        for preference in _split_values(row.get("dietary_preferences"))
    }


def _row_matches_diet_preferences(row, diet_preferences):
    if not diet_preferences:
        return True

    if diet_preferences["exclude_allergens"] & _row_allergens(row):
        return False

    required_preferences = diet_preferences["required_preferences"]
    if required_preferences and not required_preferences.issubset(_row_preferences(row)):
        return False

    return True


def _macro_value(row, macro_focus):
    if macro_focus == "protein_heavy":
        return _to_float(row.get("protein_g"))
    if macro_focus == "carb_heavy":
        return _to_float(row.get("total_carbohydrate_g"))
    return 0.0
    
def build_byo_option(df_bowl, bev_pool,calorie_target, role_limits, used_dishes=None, used_proteins=None, buffer=50, max_attempts=30, diet_preferences=None):
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
    hall = df_bowl["hall"].iloc[0] if "hall" in df_bowl.columns and len(df_bowl) else None
    meal = df_bowl["category"].iloc[0] if "category" in df_bowl.columns and len(df_bowl) else None

    proteins = df_bowl[df_bowl["role"] == "protein"].copy()
    bases    = df_bowl[df_bowl["role"] == "base"].copy()

    normalized_diet_preferences = _normalize_diet_preferences(diet_preferences)

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
        proteins["pen"] = proteins["item_name"].apply(lambda d: 1 if d in local_used_proteins else 0)
        proteins["macro"] = proteins.apply(lambda row: -_macro_value(row, normalized_diet_preferences["macro_focus"]), axis=1)
        p_cands = proteins.sort_values(["pen", "macro", "calories"]).head(min(8, len(proteins))).to_dict("records")
        protein = [random.choice(p_cands) for i in range(role_limits["protein"])]

        bases["pen"] = bases["item_name"].apply(lambda d: 1 if d in local_used_dishes else 0)
        bases["macro"] = bases.apply(lambda row: -_macro_value(row, normalized_diet_preferences["macro_focus"]), axis=1)
        b_cands = bases.sort_values(["pen", "macro", "calories"]).head(min(8, len(bases))).to_dict("records")
        base = [random.choice(b_cands) for i in range(role_limits["base"])]    
        chosen = protein + base
        total = sum(float(p["calories"]) for p in protein) + sum(float(b["calories"]) for b in base)
        local_used_dishes.update(b["item_name"] for b in base)
        local_used_proteins.update(p["item_name"] for p in protein)

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
                dish = item["item_name"]
                cal = float(item["calories"])
                if dish in local_used_dishes:
                    continue
                if total + cal <= calorie_target + buffer:
                    chosen.append(item)
                    total += cal
                    local_used_dishes.add(dish)
                    count += 1

        # fill optional roles
        for role in OPTIONAL_ROLE_ORDER[df_bowl["final_station"].iloc[0]]:
            pool = df_bowl[df_bowl["role"] == role].copy()
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
            used_dishes.update([i["item_name"] for i in base])
            used_proteins.update(p["item_name"] for p in protein)

            return {
                "Hall": hall,
                "Station": df_bowl["final_station"].iloc[0],
                "Calories": int(round(total)),
                "Nutrition": {
                    "Protein_g": round(sum(_to_float(i.get("protein_g")) for i in chosen), 2),
                    "Carbohydrate_g": round(sum(_to_float(i.get("total_carbohydrate_g")) for i in chosen), 2),
                },
                "Items": [{"Dish": i["item_name"], "Calories": int(round(float(i["calories"]))), "Serving Size": i["serving_size"], "Role": i["role"]} for i in chosen],
            }



    if best is None:
        return None

    chosen, total = best
    return {
        "Hall": hall,
        "Station": df_bowl["final_station"].iloc[0],
        "Calories": int(round(total)),
        "Nutrition": {
            "Protein_g": round(sum(_to_float(i.get("protein_g")) for i in chosen), 2),
            "Carbohydrate_g": round(sum(_to_float(i.get("total_carbohydrate_g")) for i in chosen), 2),
        },
        "Items": [{"Dish": i["item_name"], "Calories": int(round(float(i["calories"]))), "Serving Size": i["serving_size"], "Role": i["role"]} for i in chosen],
    }

#print(build_byo_bowl_option(df[(df['hall']=='Huffman') & (df['final_station']=='byo_bowl') & (df['category'] == 'Lunch')], bev, 1000))


def build_entree_option(df_entrees, bev_pool, calorie_target, role_limits, used_dishes=None, buffer=50, max_attempts=30, diet_preferences=None):
    """
    df: already filtered to one meal-time + one hall + FinalStation == 'entree'
    calorie_target: target calories for the meal (e.g. 650)
    used_dishes: set of dish names used earlier in the day/week (variety)
    buffer: allow exceeding target by up to this many calories
    """
    used_dishes = used_dishes or set()

    # must be same hall+meal already; we'll reuse these for bev filtering
    hall = df_entrees["hall"].iloc[0] if "hall" in df_entrees.columns and len(df_entrees) else None
    meal = df_entrees["category"].iloc[0] if "category" in df_entrees.columns and len(df_entrees) else None

    entrees = df_entrees[df_entrees["role"] == "entree"].copy()
    addons  = df_entrees[df_entrees["role"] == "addon"].copy()

    normalized_diet_preferences = _normalize_diet_preferences(diet_preferences)

    if entrees.empty:
        return None



    best = None
    best_gap = float("inf")

    for attempt in range(max_attempts):
        # vary randomness per attempt
        random.seed(None)

        local_used_dishes = set(used_dishes).copy()

        # prefer unused entrees
        entrees["pen"] = entrees["item_name"].apply(lambda d: 1 if d in local_used_dishes else 0)
        entrees["macro"] = entrees.apply(lambda row: -_macro_value(row, normalized_diet_preferences["macro_focus"]), axis=1)
        e_cands = entrees.sort_values(["pen", "macro", "calories"]).head(min(8, len(entrees))).to_dict("records")
        entree = [random.choice(e_cands) for i in range(role_limits["entree"])]

        chosen = entree
        total = sum(float(e["calories"]) for e in entree)
        local_used_dishes.update(e["item_name"] for e in entree)
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
                dish = item["item_name"]
                cal = float(item["calories"])
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
            used_dishes.update(i["item_name"] for i in entree)

            return {
                "Hall": hall,
                "Station": "entree",
                "Calories": int(round(total)),
                "Nutrition": {
                    "Protein_g": round(sum(_to_float(i.get("protein_g")) for i in chosen), 2),
                    "Carbohydrate_g": round(sum(_to_float(i.get("total_carbohydrate_g")) for i in chosen), 2),
                },
                "Items": [{"Dish": i["item_name"], "Calories": int(round(float(i["calories"]))), "Serving Size": i["serving_size"], "Role": i["role"]} for i in chosen],
            }

    if best is None:
        return None

    chosen, total = best
    return {
        "Hall": hall,
        "Station": "entree",
        "Calories": int(round(total)),
        "Nutrition": {
            "Protein_g": round(sum(_to_float(i.get("protein_g")) for i in chosen), 2),
            "Carbohydrate_g": round(sum(_to_float(i.get("total_carbohydrate_g")) for i in chosen), 2),
        },
        "Items": [{"Dish": i["item_name"], "Calories": int(round(float(i["calories"]))), "Serving Size": i["serving_size"], "Role": i["role"]} for i in chosen],
    }

#print(build_entree_option(df[(df['hall']=='Huffman') & ((df['final_station']=='grill') | (df['final_station']=="pizza")) & (df['category'] == 'Lunch')], bev, 600, ROLE_LIMITS_ENTREES))
# def build_entrees_option(df_entrees, calorie_target, used_dishes=None, buffer=50, max_attempts=30):


def _coerce_calories(df):
    df = df.copy()
    rename_map = {
        "Dish": "item_name",
        "Category": "category",
        "Time": "time",
        "Hall": "hall",
        "Calories": "calories",
        "Serving Size": "serving_size",
        "Role": "role",
        "FinalStation": "final_station",
    }
    for source, target in rename_map.items():
        if source in df.columns and target not in df.columns:
            df = df.rename(columns={source: target})
    df["calories"] = pd.to_numeric(df["calories"], errors="coerce")
    df = df.dropna(subset=["calories"])
    return df


_TIME_SUFFIX_RE = re.compile(
    r"\s*(\([^)]*\)|\d{1,2}(?::\d{2})?(?:am|pm)\s*-\s*\d{1,2}(?::\d{2})?(?:am|pm))\s*$",
    re.IGNORECASE,
)


def _normalize_meal_label(label):
    return _TIME_SUFFIX_RE.sub("", (label or "")).strip()

def generate_daily_plan(menu_df, meal_times, daily_calorie_limit, top_n,
                        meal_ratios=None, preferred_halls=None, diet_preferences=None):
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
    normalized_meal_times = [_normalize_meal_label(meal) for meal in meal_times]
    normalized_meal_ratios = (
        {_normalize_meal_label(meal): ratio for meal, ratio in meal_ratios.items()}
        if meal_ratios
        else None
    )
    normalized_preferred_halls = (
        {_normalize_meal_label(meal): hall for meal, hall in preferred_halls.items()}
        if preferred_halls
        else None
    )

    normalized_diet_preferences = _normalize_diet_preferences(diet_preferences)

    plan, chosen_mains, chosen_proteins, total_calories = [], set(), set(), 0
    meal_reports = []
    missing_meals = []

    for meal in normalized_meal_times:

        # per-meal budget
        cal_per_meal = (daily_calorie_limit * normalized_meal_ratios.get(meal)
                if normalized_meal_ratios and meal in normalized_meal_ratios
                else daily_calorie_limit / max(1, len(normalized_meal_times)))

        # filter: meal slot + realistic calories
        meal_opts = df[df["category"].astype(str).str.contains(meal, case=False, na=False)]
        meal_opts = meal_opts[meal_opts.apply(lambda row: _row_matches_diet_preferences(row, normalized_diet_preferences), axis=1)]
        meal_opts = meal_opts[meal_opts["calories"].between(10, 2000)]
        if meal_opts.empty:
            missing_meals.append({
                "Meal": meal,
                "Reason": "No menu items match this meal after dietary filtering.",
                "RequestedHall": normalized_preferred_halls.get(meal) if normalized_preferred_halls else None,
            })
            continue
     
        halls = [normalized_preferred_halls[meal]] if (normalized_preferred_halls and meal in normalized_preferred_halls) \
                else meal_opts["hall"].dropna().unique()
        candidates = []

        def safe_max(df_role):
            m = pd.to_numeric(df_role["calories"], errors="coerce").max()
            return 0.0 if pd.isna(m) else float(m)

        meal_found = False

        for hall in halls:
            hall_items = meal_opts[meal_opts["hall"] == hall].copy()
            if hall_items.empty:
                continue
            meal_found = True
            time_values = hall_items["time"].dropna().unique()
            if len(time_values) > 0:
                time = time_values[0]
            else:
                fallback_times = meal_opts["time"].dropna().unique()
                time = fallback_times[0] if len(fallback_times) > 0 else meal
            bev = hall_items[(hall_items["role"] == "dessert") | (hall_items["role"] == "beverage")]
            bowl = hall_items[hall_items["final_station"] == "byo_bowl"]
            ent = hall_items[hall_items["final_station"].isin(["grill", "pizza", "hot_entree"])]
            salad = hall_items[hall_items["final_station"] == "byo_salad"]
            breakfast = hall_items[hall_items["final_station"] == "byo_breakfast"]

            bowl_limits = ROLE_LIMITS_BYO_BOWL.copy()
            salad_limits = ROLE_LIMITS_BYO_SALAD.copy()
            breakfast_limits = ROLE_LIMITS_BYO_BREAKFAST.copy()
            entree_limits = ROLE_LIMITS_ENTREES.copy()

            num_of_incr = 0
            while safe_max(bowl[bowl["role"]=="protein"]) * bowl_limits["protein"] + safe_max(bowl[bowl["role"]=="base"]) * bowl_limits["base"] + safe_max(bowl[bowl["role"]=="veg"]) * bowl_limits["veg"] \
                + safe_max(bowl[bowl["role"]=="extra"]) * bowl_limits["extra"] < external_calorie_fraction *cal_per_meal and num_of_incr<2:
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
            while safe_max(ent[ent["role"]=="entree"]) * entree_limits["entree"] + safe_max(ent[ent["role"]=="addon"]) * entree_limits["addon"] < external_calorie_fraction *cal_per_meal and num_of_incr < 2:
                if num_of_incr > 0:
                    entree_limits["entree"] +=1
                    entree_limits["addon"] +=1
                    num_of_incr +=1
                    continue
                entree_limits["addon"] +=1
                num_of_incr +=1
            
            num_of_incr = 0
            while safe_max(salad[salad["role"]=="protein"]) * salad_limits["protein"] + safe_max(salad[salad["role"]=="base"]) * salad_limits["base"] + safe_max(salad[salad["role"]=="veg_topping"]) * salad_limits["veg_topping"] \
                + safe_max(salad[salad["role"]=="extra"]) * salad_limits["extra"] < external_calorie_fraction *cal_per_meal and num_of_incr < 2:
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
            while safe_max(breakfast[breakfast["role"]=="protein"]) * breakfast_limits["protein"] + safe_max(breakfast[breakfast["role"]=="base"]) * breakfast_limits["base"] + safe_max(breakfast[breakfast["role"]=="topping"]) * breakfast_limits["topping"] \
                + safe_max(breakfast[breakfast["role"]=="extra"]) * breakfast_limits["extra"] < external_calorie_fraction *cal_per_meal and num_of_incr < 2:
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
                    used_proteins=chosen_proteins,
                    diet_preferences=normalized_diet_preferences,
                )
                if byo_bowl_option:
                    # compute macro closeness penalty (use calories from macros)
                    if normalized_diet_preferences["macro_focus"] == "protein_heavy":
                        macro_target_cal = cal_per_meal * 0.20
                        macro_total_cal = _to_float(byo_bowl_option.get("Nutrition", {}).get("Protein_g")) * 4.0
                    elif normalized_diet_preferences["macro_focus"] == "carb_heavy":
                        macro_target_cal = cal_per_meal * 0.45
                        macro_total_cal = _to_float(byo_bowl_option.get("Nutrition", {}).get("Carbohydrate_g")) * 4.0
                    else:
                        macro_target_cal = None
                        macro_total_cal = 0.0
                    macro_scale = normalized_diet_preferences.get("macro_scale", MACRO_SCALE)
                    macro_penalty = abs(macro_target_cal - macro_total_cal) / macro_scale if macro_target_cal is not None else 0.0
                    candidates.append({
                        "Hall": hall,
                        "Calories": byo_bowl_option["Calories"],
                        "Time": time,
                        "Items": byo_bowl_option["Items"],      
                        "Score": abs(cal_per_meal - byo_bowl_option["Calories"]) + (50 if byo_bowl_option["Items"][-1]["Role"] == "dessert" or byo_bowl_option["Items"][-1]["Role"] == "beverage" else 0) + macro_penalty
                    })
                      # prefer BYO Bowl if available
                # Entree option
                entree_option = build_entree_option(
                    ent,
                    bev,
                    cal_per_meal,
                    role_limits=entree_limits,
                    used_dishes=chosen_mains,
                    diet_preferences=normalized_diet_preferences,
                )
                if entree_option:
                    # compute macro closeness penalty (use calories from macros)
                    if normalized_diet_preferences["macro_focus"] == "protein_heavy":
                        macro_target_cal = cal_per_meal * 0.20
                        macro_total_cal = _to_float(entree_option.get("Nutrition", {}).get("Protein_g")) * 4.0
                    elif normalized_diet_preferences["macro_focus"] == "carb_heavy":
                        macro_target_cal = cal_per_meal * 0.45
                        macro_total_cal = _to_float(entree_option.get("Nutrition", {}).get("Carbohydrate_g")) * 4.0
                    else:
                        macro_target_cal = None
                        macro_total_cal = 0.0
                    macro_scale = normalized_diet_preferences.get("macro_scale", MACRO_SCALE)
                    macro_penalty = abs(macro_target_cal - macro_total_cal) / macro_scale if macro_target_cal is not None else 0.0
                    candidates.append({
                        "Hall": hall,
                        "Calories": entree_option["Calories"],
                        "Time": time,
                        "Items": entree_option["Items"],
                        "Score": abs(cal_per_meal - entree_option["Calories"]) + (50 if entree_option["Items"][-1]["Role"] == "dessert" or entree_option["Items"][-1]["Role"] == "beverage" else 0) + macro_penalty
                    })
                      # prefer Entree if available
                # BYO Salad option
                byo_salad_option = build_byo_option(
                    salad,
                    bev,
                    cal_per_meal,
                    role_limits=salad_limits,
                    used_dishes=chosen_mains,
                    used_proteins=chosen_proteins,
                    diet_preferences=normalized_diet_preferences,
                )
                if byo_salad_option:
                    # compute macro closeness penalty (use calories from macros)
                    if normalized_diet_preferences["macro_focus"] == "protein_heavy":
                        macro_target_cal = cal_per_meal * 0.20
                        macro_total_cal = _to_float(byo_salad_option.get("Nutrition", {}).get("Protein_g")) * 4.0
                    elif normalized_diet_preferences["macro_focus"] == "carb_heavy":
                        macro_target_cal = cal_per_meal * 0.45
                        macro_total_cal = _to_float(byo_salad_option.get("Nutrition", {}).get("Carbohydrate_g")) * 4.0
                    else:
                        macro_target_cal = None
                        macro_total_cal = 0.0
                    macro_scale = normalized_diet_preferences.get("macro_scale", MACRO_SCALE)
                    macro_penalty = abs(macro_target_cal - macro_total_cal) / macro_scale if macro_target_cal is not None else 0.0
                    candidates.append({
                        "Hall": hall,
                        "Calories": byo_salad_option["Calories"],
                        "Time": time,
                        "Items": byo_salad_option["Items"],
                        "Score": abs(cal_per_meal - byo_salad_option["Calories"]) + (50 if byo_salad_option["Items"][-1]["Role"] == "dessert" or byo_salad_option["Items"][-1]["Role"] == "beverage" else 0) + macro_penalty
                    })
                      # prefer BYO Salad if available
                # BYO Breakfast option
                byo_breakfast_option = build_byo_option(
                    breakfast,
                    bev,
                    cal_per_meal,
                    role_limits=breakfast_limits,
                    used_dishes=chosen_mains,
                    used_proteins=chosen_proteins,
                    diet_preferences=normalized_diet_preferences,
                )
                if byo_breakfast_option:
                    # compute macro closeness penalty (use calories from macros)
                    if normalized_diet_preferences["macro_focus"] == "protein_heavy":
                        macro_target_cal = cal_per_meal * 0.20
                        macro_total_cal = _to_float(byo_breakfast_option.get("Nutrition", {}).get("Protein_g")) * 4.0
                    elif normalized_diet_preferences["macro_focus"] == "carb_heavy":
                        macro_target_cal = cal_per_meal * 0.45
                        macro_total_cal = _to_float(byo_breakfast_option.get("Nutrition", {}).get("Carbohydrate_g")) * 4.0
                    else:
                        macro_target_cal = None
                        macro_total_cal = 0.0
                    macro_scale = normalized_diet_preferences.get("macro_scale", MACRO_SCALE)
                    macro_penalty = abs(macro_target_cal - macro_total_cal) / macro_scale if macro_target_cal is not None else 0.0
                    candidates.append({
                        "Hall": hall,
                        "Calories": byo_breakfast_option["Calories"],
                        "Time": time,
                        "Items": byo_breakfast_option["Items"],      
                        "Score": abs(cal_per_meal - byo_breakfast_option["Calories"]) + (50 if byo_breakfast_option["Items"][-1]["Role"] == "dessert" or byo_breakfast_option["Items"][-1]["Role"] == "beverage" else 0) + macro_penalty
                    })
                      # prefer BYO Breakfast if available
           
            

            
             
        if candidates:
            candidates.sort(key=lambda c: c["Score"], reverse=False)
            top = candidates[:top_n]
            first = top[0]
            requested_hall = normalized_preferred_halls.get(meal) if normalized_preferred_halls else None
            meal_report = {
                "Meal": meal,
                "RequestedHall": requested_hall,
                "SelectedHall": first["Hall"],
                "CalBudget": round(cal_per_meal),
                "SelectedCalories": first["Calories"],
                "BudgetDelta": round(first["Calories"] - cal_per_meal),
                "BudgetWithinBuffer": abs(first["Calories"] - cal_per_meal) <= fallback_buffer,
                "HallMatched": requested_hall is None or first["Hall"] == requested_hall,
                "Status": "complete",
            }
            meal_reports.append(meal_report)
            plan.append({"Meal": meal, "Cal_budget": round(cal_per_meal), "Options": top, "Status": meal_report})

            # update variety + running total using first option
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
        else:
            missing_meals.append({
                "Meal": meal,
                "Reason": "No viable plan found for the selected hall(s) after all constraints.",
                "RequestedHall": normalized_preferred_halls.get(meal) if normalized_preferred_halls else None,
            })
            meal_reports.append({
                "Meal": meal,
                "RequestedHall": normalized_preferred_halls.get(meal) if normalized_preferred_halls else None,
                "SelectedHall": None,
                "CalBudget": round(cal_per_meal),
                "SelectedCalories": None,
                "BudgetDelta": None,
                "BudgetWithinBuffer": False,
                "HallMatched": False,
                "Status": "unmet",
                "Reason": "No viable plan found for the selected hall(s) after all constraints.",
            })

    return {
        "Plan": plan,
        "Total_calories": total_calories,
        "MealReports": meal_reports,
        "MissingMeals": missing_meals,
        "IsComplete": len(missing_meals) == 0 and len(plan) == len(normalized_meal_times),
    }

#=======================================================================================================================
# Meal Generation Parameters
# ADJUST PARAMETERS FOR YOUR MEAL RECOMMENDATION PREFERENCES
# Adjust Meal times(Breakfast, Lunch, Dinner), Daily Calorie Limit, Meal Ratios(for a total of 100%), Preferred Halls
# for each meal period and number of options you want made available to you
#=======================================================================================================================
# meal_times = ["Dinner"]  # options: Breakfast, Lunch, Brunch, Dinner
# daily_calorie_limit = 700
# meal_ratios = {}   # custom split
# preferred_halls = {"Dinner": "Curtis"}                        # force hall for dinner

# top_n = 10  # number of options per meal
# # # #=======================================================================================================================
# from db.repositories import fetch_items
# from db.database import SessionLocal
# db = SessionLocal()
# df = fetch_items(db, time="2026-01-27")  # dummy db session
# daily_plan = generate_daily_plan(df, meal_times, daily_calorie_limit, top_n=top_n, meal_ratios=meal_ratios, preferred_halls=preferred_halls)
# print(daily_plan)