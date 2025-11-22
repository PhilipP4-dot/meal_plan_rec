import pandas as pd
from app.overrides import apply_overrides, update_override

def test_apply_update_overrides(tmp_path):
    """Test the apply_overrides and update_override functions."""
    override_file = tmp_path/"manual_overrides.csv"

    df = pd.DataFrame({'Dish': ['Chocolate Milk', 'White Rice'], 'AutoCategory': ['dessert', 'side']})

    update_override('Chocolate Milk', 'beverage', override_file=override_file)
    # Initially, no overrides
    overridden_df = apply_overrides(df, override_file=override_file)
    assert overridden_df.loc[overridden_df['Dish'] == 'Chocolate Milk', 'FinalCategory'].values[0] == 'beverage'
    assert overridden_df.loc[overridden_df['Dish'] == 'White Rice', 'FinalCategory'].values[0] == 'side'
    