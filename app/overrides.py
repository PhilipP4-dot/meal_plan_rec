from db.database import SessionLocal
from db.models import RoleOverride, StationOverride



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
