from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from db.database import Base, engine

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String,   index=True)
    category = Column(String)
    time = Column(String)
    hall = Column(String)
    calories = Column(String)
    serving_size = Column(String)
    station = Column(String)
    final_station = Column(String)
    role = Column(String)
    description = Column(String)
    allergens = Column(String)
    dietary_preferences = Column(String)
    calories_percent_daily_value = Column(String)
    total_fat_g = Column(String)
    total_fat_g_percent_daily_value = Column(String)
    saturated_fat_g = Column(String)
    saturated_fat_g_percent_daily_value = Column(String)
    trans_fat_g = Column(String)
    trans_fat_g_percent_daily_value = Column(String)
    cholesterol_mg = Column(String)
    cholesterol_mg_percent_daily_value = Column(String)
    sodium_mg = Column(String)
    sodium_mg_percent_daily_value = Column(String)
    total_carbohydrate_g = Column(String)
    total_carbohydrate_g_percent_daily_value = Column(String)
    total_sugars_g = Column(String)
    added_sugars_g = Column(String)
    added_sugars_g_percent_daily_value = Column(String)
    dietary_fiber_g = Column(String)
    dietary_fiber_g_percent_daily_value = Column(String)
    protein_g = Column(String)
    protein_g_percent_daily_value = Column(String)
    potassium_mg = Column(String)
    potassium_mg_percent_daily_value = Column(String)
    calcium_mg = Column(String)
    calcium_mg_percent_daily_value = Column(String)
    iron_mg = Column(String) 
    iron_mg_percent_daily_value = Column(String)
    vitamin_d_mcg = Column(String)
    vitamin_d_mcg_percent_daily_value = Column(String)


class StationOverride(Base):
    __tablename__ = "station_overrides"

    id = Column(Integer, primary_key=True, index=True)
    raw_station = Column(String, index=True)
    correct_station = Column(String)

class RoleOverride(Base):
    __tablename__ = "role_overrides"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, index=True)              # canonical item name
    final_station = Column(String, index=True)    # e.g. byo_bowl, byo_salad
    correct_role = Column(String)                      # protein/base/veg/sauce/extra/etc.

    __table_args__ = (
        UniqueConstraint("item_name", "final_station", name="uq_item_name_station_role"),
    )
Base.metadata.create_all(bind=engine, tables=[Menu.__table__, StationOverride.__table__, RoleOverride.__table__])