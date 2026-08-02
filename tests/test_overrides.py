import pandas as pd
from app.overrides import apply_overrides


def test_apply_overrides_adds_recommender_columns_without_mutating_input():
    menu = pd.DataFrame(
        {
            "Dish": ["Grilled Chicken", "White Rice"],
            "AutoCategory": ["main", "side"],
        }
    )

    result = apply_overrides(menu)

    assert "FinalCategory" not in menu.columns
    assert result["FinalCategory"].tolist() == ["main", "side"]
    assert result["Role"].tolist() == ["entree", "addon"]
    assert result["FinalStation"].tolist() == ["grill", "grill"]


def test_apply_overrides_preserves_explicit_station_and_role():
    menu = pd.DataFrame(
        {
            "Dish": ["Tofu Bowl"],
            "role": ["protein"],
            "station": ["global"],
        }
    )

    result = apply_overrides(menu)

    assert result.loc[0, "Role"] == "protein"
    assert result.loc[0, "FinalStation"] == "global"
