import sys
import os
import re

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify, render_template
from app.services.recommendations import fetch_plan, fetch_meals
from app.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

app = Flask(__name__)

_TIME_SUFFIX_RE = re.compile(
    r"\s*(\([^)]*\)|\d{1,2}(?::\d{2})?(?:am|pm)\s*-\s*\d{1,2}(?::\d{2})?(?:am|pm))\s*$",
    re.IGNORECASE,
)


def normalize_meal_label(label):
    return _TIME_SUFFIX_RE.sub("", (label or "")).strip()


def _parse_clock_time(value):
    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", str(value), re.IGNORECASE)
    if not match:
        return None

    hour = int(match.group(1)) % 12
    minute = int(match.group(2) or 0)
    meridiem = match.group(3).lower()
    if meridiem == "pm":
        hour += 12
    return hour * 60 + minute


def _extract_time_bounds(time_range):
    parts = str(time_range).replace("(", "").replace(")", "").split("-")
    if len(parts) < 2:
        start = _parse_clock_time(time_range)
        return start, start

    start = _parse_clock_time(parts[0])
    end = _parse_clock_time(parts[-1])
    return start, end


def _meal_form_key(label):
    return re.sub(r"[^a-z0-9]+", "_", str(label).strip().lower()).strip("_")


def build_meal_options():
    df = fetch_meals().rename(columns={
        "Category": "category",
        "Time": "time",
        "Hall": "hall",
    })[["category", "time", "hall"]].drop_duplicates()
    df = df.dropna(subset=["category", "time", "hall"])
    df = df.sort_values(by=["category", "time", "hall"])

    meals = []
    for meal in df["category"].unique():
        meal_df = df[df["category"] == meal]
        times = meal_df["time"].drop_duplicates().tolist()
        halls = sorted(meal_df["hall"].drop_duplicates().tolist())
        time_bounds = [_extract_time_bounds(time) for time in times]

        start_candidates = [start for start, _ in time_bounds if start is not None]
        end_candidates = [end for _, end in time_bounds if end is not None]

        earliest_start = min(start_candidates) if start_candidates else 24 * 60
        latest_end = max(end_candidates) if end_candidates else earliest_start

        if len(times) == 1:
            label = f"{meal} {times[0]}"
        else:
            earliest_time = min(times, key=lambda t: (_extract_time_bounds(t)[0] is None, _extract_time_bounds(t)[0] or 24 * 60))
            latest_time = max(times, key=lambda t: (_extract_time_bounds(t)[1] is None, _extract_time_bounds(t)[1] or -1))
            start = str(earliest_time).replace("(", "").replace(")", "").split("-")[0].strip()
            end = str(latest_time).replace("(", "").replace(")", "").split("-")[-1].strip()
            label = f"{meal} ({start}-{end})"

        meals.append({
            "label": label,
            "key": _meal_form_key(label),
            "halls": halls,
            "sort_start": earliest_start,
            "sort_end": latest_end,
        })

    meals.sort(key=lambda m: (m["sort_start"], m["sort_end"], normalize_meal_label(m["label"]).lower()))

    for meal in meals:
        meal.pop("sort_start", None)
        meal.pop("sort_end", None)

    return meals

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.get("/")
def index():
    meals = build_meal_options()
    return render_template("index.html", meals=meals)

@app.post("/recommendations")
def recommendations():
    meals = build_meal_options()
    meal_lookup = {
        meal.get("key", _meal_form_key(meal["label"])): meal["label"]
        for meal in meals
    }
    label_lookup = {
        meal["label"]: meal.get("key", _meal_form_key(meal["label"]))
        for meal in meals
    }

    daily_calories = int(request.form.get("daily_calories", 2000))
    top_n = int(request.form.get("top_n", 2))
    macro_focus = request.form.get("macro_focus", "balanced")
    # optional tuning parameter for macro scaling (kcal per score unit)
    macro_scale_raw = request.form.get("macro_scale")
    try:
        macro_scale = float(macro_scale_raw) if macro_scale_raw is not None and macro_scale_raw != "" else None
    except Exception:
        macro_scale = None
    required_preference = request.form.get("required_preference", "Any")
    exclude_allergens = request.form.getlist("exclude_allergens")

    selected_meal_tokens = request.form.getlist("meal_times")
    if not selected_meal_tokens:
        return render_template("index.html", meals=meals, error="Please select at least one meal time.")

    selected_meal_labels = [meal_lookup.get(token, token) for token in selected_meal_tokens]
    meal_times = [normalize_meal_label(meal) for meal in selected_meal_labels]

    # Process calorie ratios
    meal_ratios = {}
    total_ratio = 0
    for raw_meal_token, raw_meal_label, normalized_meal in zip(selected_meal_tokens, selected_meal_labels, meal_times):
        ratio_value = request.form.get(f"{raw_meal_token}_ratio")
        if ratio_value is None:
            ratio_value = request.form.get(f"{label_lookup.get(raw_meal_label, raw_meal_label)}_ratio", 0)
        ratio = int(ratio_value or 0)
        meal_ratios[normalized_meal] = meal_ratios.get(normalized_meal, 0) + ratio
        total_ratio += ratio
    
    if total_ratio == 0:
        meal_ratios = None
    elif total_ratio != 100:
        return render_template("index.html", meals=meals, error="Calorie split must total 100% or be all zero.")
    else:
        for meal in meal_ratios:
            meal_ratios[meal] = meal_ratios[meal] / total_ratio
    
    # Process preferred halls
    preferred_halls = {}
    for raw_meal_token, raw_meal_label, normalized_meal in zip(selected_meal_tokens, selected_meal_labels, meal_times):
        hall = request.form.get(f"{raw_meal_token}_hall")
        if hall is None:
            hall = request.form.get(f"{label_lookup.get(raw_meal_label, raw_meal_label)}_hall", "Any")
        if hall != "Any":
            preferred_halls[normalized_meal] = hall

    diet_preferences = {
        "macro_focus": macro_focus,
        "exclude_allergens": exclude_allergens,
        "required_preferences": [] if required_preference == "Any" else [required_preference],
        "macro_scale": macro_scale,
    }


    plan = fetch_plan(
        meal_times=meal_times,
        daily_calorie_limit=daily_calories,
        top_n=top_n,
        meal_ratios=meal_ratios,
        preferred_halls=preferred_halls
        ,diet_preferences=diet_preferences
        
    )

    meal_reports = plan.get("MealReports")
    if meal_reports is not None:
        plan_is_satisfied = all(
            report.get("Status") == "complete" and report.get("BudgetWithinBuffer", True)
            for report in meal_reports
        )
        if not plan_is_satisfied:
            return render_template(
                "index.html",
                meals=meals,
                error="Your selected goals could not be met with the available menu. Try a lower calorie target, loosen a hall preference, or select fewer meal periods.",
            )

    return render_template("results.html", plan=plan)


if __name__ == "__main__":
    import os
    
    # Use environment variables for configuration
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    port = int(os.getenv("FLASK_PORT", "5000"))
    
    app.run(debug=debug_mode, port=port, host="127.0.0.1")