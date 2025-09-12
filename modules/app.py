import streamlit as st
import pandas as pd

menu_df = pd.read_csv("menu_data_categorized.csv")

from recommendation import generate_daily_plan


st.title("Meal Plan Recommendation System")

st.sidebar.header("Your Preferences")

meal_times = st.sidebar.multiselect("Select Meal Times", ["Breakfast", "Lunch", "Dinner"], default=["Breakfast", "Lunch", "Dinner"])

#order meal times
meal_times.sort()
if "Lunch" in meal_times and "Dinner" in meal_times:
    meal_times[meal_times.index("Lunch")] = "Dinner"
    meal_times[meal_times.index("Dinner")] = "Lunch"
daily_calorie_limit = st.sidebar.number_input("Daily Calorie Limit", min_value=1000, max_value=4000, value=2000, step=100)

st.sidebar.subheader("Calorie Split (optional but should total 100%)")
breakfast_ratio = st.sidebar.slider("Breakfast %", 0, 100, 25) / 100
lunch_ratio = st.sidebar.slider("Lunch %", 0, 100, 40) / 100
dinner_ratio = st.sidebar.slider("Dinner %", 0, 100, 35) / 100

total_ratio = breakfast_ratio + lunch_ratio + dinner_ratio
if total_ratio == 0:
    meal_ratios = None
elif total_ratio != 1 and total_ratio != 0:
    st.sidebar.error("Calorie split must total 100% or be all zero.")
    st.stop()
else:
    meal_ratios = {
        "Breakfast": breakfast_ratio / total_ratio,
        "Lunch": lunch_ratio / total_ratio,
        "Dinner": dinner_ratio / total_ratio
    }

st.sidebar.subheader("Dining Hall Preferences")
preferred_halls = {}
for meal in meal_times:
    choice  = st.sidebar.selectbox(f"Preferred Hall for {meal}", ["Any", "Curtis", "Huffman"], index=0)
    if choice != "Any":
        preferred_halls[meal] = choice

if st.sidebar.button("Generate Meal Plan"):
    daily_plan = generate_daily_plan(menu_df, meal_times, daily_calorie_limit, meal_ratios, preferred_halls, top_n=2)
    
    st.subheader("Your Meal Plan")
    for meal in daily_plan["Plan"]:
        st.markdown(f"### {meal['Meal']}  •  Budget: {meal['CalBudget']} cal")
        for i, opt in enumerate(meal["Options"], 1):
            with st.expander(f"Option {i} @ {opt['Hall']}  ({opt['Calories']} cal)"):
                listed_sum = 0
                for it in opt["Items"]:
                    st.write(f"- {it['Dish']} ({it['Serving Size'] or '1 serving'}): {int(it['Calories'])} cal")
                    listed_sum += it["Calories"]
                # sanity check in UI
                if int(listed_sum) != int(opt["Calories"]):
                    st.warning(f"Sum of items = {int(listed_sum)} cal (recomputed). Updating displayed total.")


    st.success(f"✅ Total Calories (first options): {daily_plan['TotalCalories']} kcal")