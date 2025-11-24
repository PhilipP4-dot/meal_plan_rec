from db.database import SessionLocal
from db.models import Override



def apply_overrides(menu):

    db = SessionLocal()
    overrides = {o.dish: o.correct_category for o in db.query(Override).all()}
    items = db.query(menu).all()

    for item in items:
        item.final_category = overrides.get(item.dish, item.auto_category)

    db.commit()
    db.close()    

def update_override(dish, correct_category):
    db = SessionLocal()
    obj = db.query(Override).filter(Override.dish == dish).first()

    if obj:
        obj.correct_category = correct_category
    else:
        obj = Override(dish=dish, correct_category=correct_category)
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
