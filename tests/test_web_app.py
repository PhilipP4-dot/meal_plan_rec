import pandas as pd

from web import app as web_app


def test_build_meal_options_orders_by_time(monkeypatch):
    fake_df = pd.DataFrame(
        [
            {"Category": "Dinner", "Time": "(5:00pm-7:00pm)", "Hall": "Curtis"},
            {"Category": "Lunch", "Time": "(11:30am-1:30pm)", "Hall": "Curtis"},
            {"Category": "Breakfast", "Time": "(7:00am-10:00am)", "Hall": "Huffman"},
        ]
    )

    monkeypatch.setattr(web_app, "fetch_meals", lambda: fake_df)

    options = web_app.build_meal_options()
    labels = [option["label"] for option in options]

    assert labels[0].startswith("Breakfast")
    assert labels[1].startswith("Lunch")
    assert labels[2].startswith("Dinner")


def test_recommendations_route_forwards_diet_preferences(monkeypatch):
    fake_meals = pd.DataFrame(
        [
            {"Category": "Lunch", "Time": "(11:30am-1:30pm)", "Hall": "Curtis"},
        ]
    )
    captured = {}

    def fake_fetch_plan(**kwargs):
        captured.update(kwargs)
        return {"Plan": [], "Total_calories": 0}

    monkeypatch.setattr(web_app, "build_meal_options", lambda: [{"label": "Lunch", "halls": ["Curtis"]}])
    monkeypatch.setattr(web_app, "fetch_plan", fake_fetch_plan)

    client = web_app.app.test_client()
    response = client.post(
        "/recommendations",
        data={
            "meal_times": "Lunch",
            "Lunch_ratio": "100",
            "Lunch_hall": "Curtis",
            "daily_calories": "2000",
            "top_n": "1",
            "macro_focus": "protein_heavy",
            "required_preference": "Vegetarian",
            "exclude_allergens": ["milk", "egg"],
        },
    )

    assert response.status_code == 200
    assert captured["diet_preferences"]["macro_focus"] == "protein_heavy"
    assert captured["diet_preferences"]["required_preferences"] == ["Vegetarian"]
    assert set(captured["diet_preferences"]["exclude_allergens"]) == {"milk", "egg"}


def test_recommendations_route_prompts_when_plan_is_incomplete(monkeypatch):
    monkeypatch.setattr(web_app, "build_meal_options", lambda: [{"label": "Lunch", "key": "Lunch", "halls": ["Curtis"]}])

    def fake_fetch_plan(**kwargs):
        return {
            "Plan": [{"Meal": "Lunch", "Cal_budget": 1000, "Options": [], "Status": {"Status": "unmet", "BudgetWithinBuffer": False}}],
            "Total_calories": 1000,
            "MealReports": [{"Meal": "Lunch", "Status": "unmet", "BudgetWithinBuffer": False}],
            "MissingMeals": [{"Meal": "Lunch", "Reason": "No viable plan found."}],
            "IsComplete": False,
        }

    monkeypatch.setattr(web_app, "fetch_plan", fake_fetch_plan)

    client = web_app.app.test_client()
    response = client.post(
        "/recommendations",
        data={
            "meal_times": "Lunch",
            "Lunch_ratio": "100",
            "Lunch_hall": "Curtis",
            "daily_calories": "2000",
            "top_n": "1",
        },
    )

    assert response.status_code == 200
    assert b"Your selected goals could not be met" in response.data
