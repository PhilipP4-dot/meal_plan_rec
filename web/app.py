import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify, render_template
from app.services.recommendations import fetch_plan, fetch_meals
from app.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

app = Flask(__name__)


def build_meal_options():
    df = fetch_meals()[["Category", "Time", "Hall"]].drop_duplicates()
    df = df.dropna(subset=["Category", "Time", "Hall"])
    df = df.sort_values(by=["Category", "Time", "Hall"])

    meals = []
    for meal in df["Category"].unique():
        meal_df = df[df["Category"] == meal]
        times = meal_df["Time"].drop_duplicates().tolist()
        halls = sorted(meal_df["Hall"].drop_duplicates().tolist())

        if len(times) == 1:
            label = f"{meal} {times[0]}"
        else:
            start = ""
            end = ""
            for time in times:
                start_time = time.split("-")[0][1:]
                end_time = time.split("-")[-1][:-1]
                # choose the earliest start time and latest end time
                if "pm" in start and "am" in start_time:
                    start = start_time
                if "am" in end and "pm" in end_time:
                    end = end_time
                if start == "" or int(start_time[:-2].split(":")[0]) < int(start[:-2].split(":")[0]):
                    start = start_time
                elif int(start_time[:-2].split(":")[0]) == int(start[:-2].split(":")[0]) and int(start_time[:-2].split(":")[-1]) < int(start[:-2].split(":")[-1]):
                    start = start_time
                if end == "" or int(end_time[:-2].split(":")[0]) > int(end[:-2].split(":")[0]):
                    end = end_time
                elif int(end_time[:-2].split(":")[0]) == int(end[:-2].split(":")[0]) and int(end_time[:-2].split(":")[-1]) > int(end[:-2].split(":")[-1]):
                    end = end_time
            label = f"{meal} ({start}-{end})"

        meals.append({"label": label, "halls": halls})

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

    daily_calories = int(request.form.get("daily_calories", 2000))
    top_n = int(request.form.get("top_n", 2))

    meal_times = request.form.getlist("meal_times")
    if not meal_times:
        return render_template("index.html", meals=meals, error="Please select at least one meal time.")


    # Process calorie ratios
    meal_ratios = {}
    total_ratio = 0
    for meal in meal_times:
        ratio = int(request.form.get(f"{meal}_ratio", 0))
        meal_ratios[meal] = ratio
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
    for meal in meal_times:
        hall = request.form.get(f"{meal}_hall", "Any")
        if hall != "Any":
            preferred_halls[meal] = hall


    plan = fetch_plan(
        meal_times=meal_times,
        daily_calorie_limit=daily_calories,
        top_n=top_n,
        meal_ratios=meal_ratios,
        preferred_halls=preferred_halls
        
    )

    return render_template("results.html", plan=plan)


if __name__ == "__main__":
    import os
    
    # Use environment variables for configuration
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    port = int(os.getenv("FLASK_PORT", "5000"))
    
    app.run(debug=debug_mode, port=port, host="127.0.0.1")