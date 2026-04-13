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
