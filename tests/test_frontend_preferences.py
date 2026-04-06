import pandas as pd

from app import recommender


def _make_test_menu():
    rows = []
    for meal in ["Lunch", "Dinner"]:
        for hall in ["Curtis", "Huffman"]:
            rows.extend(
                [
                    {
                        "Dish": f"{meal} {hall} Entree",
                        "Category": meal,
                        "Time": "12:00pm - 1:00pm" if meal == "Lunch" else "5:00pm - 7:00pm",
                        "Hall": hall,
                        "Serving Size": "1 plate",
                        "Calories": 500,
                        "Role": "entree",
                        "FinalStation": "grill",
                    },
                    {
                        "Dish": f"{meal} {hall} Drink",
                        "Category": meal,
                        "Time": "12:00pm - 1:00pm" if meal == "Lunch" else "5:00pm - 7:00pm",
                        "Hall": hall,
                        "Serving Size": "1 cup",
                        "Calories": 100,
                        "Role": "beverage",
                        "FinalStation": "grill",
                    },
                ]
            )
    return pd.DataFrame(rows)


def test_frontend_meal_labels_apply_calorie_ratios(monkeypatch):
    df = _make_test_menu()

    def fake_byo(*args, **kwargs):
        return None

    def fake_entree(df_entrees, _bev_pool, calorie_target, *_args, **_kwargs):
        if df_entrees.empty:
            return None
        hall = df_entrees["Hall"].iloc[0]
        return {
            "Hall": hall,
            "Station": "entree",
            "Calories": int(round(calorie_target)),
            "Items": [
                {
                    "Dish": f"{hall} Entree",
                    "Calories": int(round(calorie_target)),
                    "Serving Size": "1 plate",
                    "Role": "entree",
                }
            ],
        }

    monkeypatch.setattr(recommender, "build_byo_option", fake_byo)
    monkeypatch.setattr(recommender, "build_entree_option", fake_entree)

    plan = recommender.generate_daily_plan(
        df,
        meal_times=["Lunch (12:00pm-1:00pm)", "Dinner (5:00pm-7:00pm)"],
        daily_calorie_limit=2000,
        top_n=1,
        meal_ratios={"Lunch (12:00pm-1:00pm)": 0.25, "Dinner (5:00pm-7:00pm)": 0.75},
        preferred_halls=None,
    )

    budgets = {entry["Meal"]: entry["Cal_budget"] for entry in plan["Plan"]}
    assert budgets["Lunch"] == 500
    assert budgets["Dinner"] == 1500


def test_frontend_meal_labels_apply_preferred_hall(monkeypatch):
    df = _make_test_menu()

    def fake_byo(*args, **kwargs):
        return None

    def fake_entree(df_entrees, _bev_pool, calorie_target, *_args, **_kwargs):
        if df_entrees.empty:
            return None
        hall = df_entrees["Hall"].iloc[0]
        return {
            "Hall": hall,
            "Station": "entree",
            "Calories": int(round(calorie_target)),
            "Items": [
                {
                    "Dish": f"{hall} Entree",
                    "Calories": int(round(calorie_target)),
                    "Serving Size": "1 plate",
                    "Role": "entree",
                }
            ],
        }

    monkeypatch.setattr(recommender, "build_byo_option", fake_byo)
    monkeypatch.setattr(recommender, "build_entree_option", fake_entree)

    plan = recommender.generate_daily_plan(
        df,
        meal_times=["Lunch 12:00pm - 1:00pm"],
        daily_calorie_limit=1200,
        top_n=5,
        meal_ratios=None,
        preferred_halls={"Lunch 12:00pm - 1:00pm": "Huffman"},
    )

    lunch_options = plan["Plan"][0]["Options"]
    assert lunch_options
    assert {option["Hall"] for option in lunch_options} == {"Huffman"}
