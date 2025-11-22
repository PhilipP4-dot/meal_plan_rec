import pandas as pd
from app.categorizer import categorize_dish_simple



def test_apply_auto_category_dataframe():
    df = pd.DataFrame([
        {"Dish": "Grilled Chicken"},
        {"Dish": "Mashed Potato"},
        {"Dish": "Brownie"},
        {"Dish": "Orange Juice"},
        {"Dish": "Random Food XYZ"},
    ])

    df["AutoCategory"] = df["Dish"].apply(categorize_dish_simple)

    assert df.loc[0, "AutoCategory"] == "main"
    assert df.loc[1, "AutoCategory"] == "side"
    assert df.loc[2, "AutoCategory"] == "dessert"
    assert df.loc[3, "AutoCategory"] == "beverage"

    # no keyword match → should be 'other'
    assert df.loc[4, "AutoCategory"] == "other"