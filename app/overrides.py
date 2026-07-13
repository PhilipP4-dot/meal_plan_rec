from db.database import SessionLocal
from db.models import RoleOverride, StationOverride
import pandas as pd


_ROLE_FALLBACK_MAP = {
    "main": "entree",
    "entree": "entree",
    "side": "addon",
    "addon": "addon",
    "protein": "protein",
    "base": "base",
    "veg": "veg",
    "veg_topping": "veg_topping",
    "sauce": "sauce",
    "extra": "extra",
    "dessert": "dessert",
    "beverage": "beverage",
    "drink": "beverage",
}



def apply_role_overrides(menu):

    db = SessionLocal()
    role_overrides = {o.item_name: o.correct_role for o in db.query(RoleOverride).all()}
    items = db.query(menu).all()

    for item in items:
        item.role = role_overrides.get(item.item_name, item.auto_category)

    db.commit()
    db.close()    

def apply_station_overrides(menu):
    db = SessionLocal()
    station_overrides = {o.raw_station: o.correct_station for o in db.query(StationOverride).all()}
    items = db.query(menu).all()

    for item in items:
        item.final_station = station_overrides.get(item.hall, item.hall)

    db.commit()
    db.close()


def apply_overrides(menu):
    """Apply manual overrides to a DataFrame fixture or a SQLAlchemy model class.

    The tests and older code paths use this as a convenience wrapper. For DataFrames,
    it normalizes the common fallback columns used by the recommender:
    - Role from AutoCategory / role
    - FinalStation from station / station overrides / a default grill fallback
    - FinalCategory from category / AutoCategory
    """
    if isinstance(menu, pd.DataFrame):
        df = menu.copy()

        if "FinalCategory" not in df.columns:
            if "AutoCategory" in df.columns:
                df["FinalCategory"] = df["AutoCategory"]
            elif "role" in df.columns:
                df["FinalCategory"] = df["role"]
            elif "Role" in df.columns:
                df["FinalCategory"] = df["Role"]
            elif "category" in df.columns:
                df["FinalCategory"] = df["category"]
            elif "Category" in df.columns:
                df["FinalCategory"] = df["Category"]

        if "Role" not in df.columns:
            if "role" in df.columns:
                df["Role"] = df["role"]
            elif "AutoCategory" in df.columns:
                df["Role"] = df["AutoCategory"].astype(str).str.lower().map(_ROLE_FALLBACK_MAP).fillna(df["AutoCategory"])
            elif "FinalCategory" in df.columns:
                df["Role"] = df["FinalCategory"]

        if "FinalStation" not in df.columns:
            if "final_station" in df.columns:
                df["FinalStation"] = df["final_station"]
            elif "station" in df.columns:
                df["FinalStation"] = df["station"]
            elif "Station" in df.columns:
                df["FinalStation"] = df["Station"]
            else:
                df["FinalStation"] = "grill"

        if "station" not in df.columns and "FinalStation" in df.columns:
            df["station"] = df["FinalStation"]
        if "final_station" not in df.columns and "FinalStation" in df.columns:
            df["final_station"] = df["FinalStation"]
        if "role" not in df.columns and "Role" in df.columns:
            df["role"] = df["Role"]

        return df

    apply_role_overrides(menu)
    apply_station_overrides(menu)
    return menu

def update_role_override(dish, final_station, correct_role):
    db = SessionLocal()
    obj = db.query(RoleOverride).filter(RoleOverride.item_name == dish).first()

    if obj:
        obj.correct_role = correct_role
    else:
        obj = RoleOverride(item_name=dish, final_station=final_station, correct_role=correct_role)
        db.add(obj)

    db.commit()
    db.close()

def update_station_override(raw_station, correct_station):
    db = SessionLocal()
    obj = db.query(StationOverride).filter(StationOverride.raw_station == raw_station).first()

    if obj:
        obj.correct_station = correct_station
    else:
        obj = StationOverride(raw_station=raw_station, correct_station=correct_station)
        db.add(obj)

    db.commit()
    db.close()

# def update_override(dish, correct_category, override_file=OVERRIDE_FILE):
#     """
#     Add/update a manual override for a dish.
#     """
#     try:
#         overrides = pd.read_csv(override_file)
#     except FileNotFoundError:
#         overrides = pd.DataFrame(columns=["Dish", "CorrectCategory"])
    
#     # Remove any old entry for this dish
#     overrides = overrides[overrides["Dish"] != dish]
    
#     # Add new correction
#     overrides = pd.concat(
#         [overrides, pd.DataFrame([{"Dish": dish, "CorrectCategory": correct_category}])]
#     )
    
#     overrides.to_csv(override_file, index=False)
