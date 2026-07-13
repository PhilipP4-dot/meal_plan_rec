from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from db.database import Base, engine

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String,   index=True)
    category = Column(String)
    time = Column(String)
    hall = Column(String)
    calories = Column(Float)
    serving_size = Column(String)
    station = Column(String)
    final_station = Column(String)
    role = Column(String)
    description = Column(String)
    allergens = Column(String)
    dietary_preferences = Column(String)
    calories_percent_daily_value = Column(Float)
    total_fat_g = Column(Float)
    total_fat_g_percent_daily_value = Column(Float)
    saturated_fat_g = Column(Float)
    saturated_fat_g_percent_daily_value = Column(Float)
    trans_fat_g = Column(Float)
    trans_fat_g_percent_daily_value = Column(Float)
    cholesterol_mg = Column(Float)
    cholesterol_mg_percent_daily_value = Column(Float)
    sodium_mg = Column(Float)
    sodium_mg_percent_daily_value = Column(Float)
    total_carbohydrate_g = Column(Float)
    total_carbohydrate_g_percent_daily_value = Column(Float)
    total_sugars_g = Column(Float)
    added_sugars_g = Column(Float)
    added_sugars_g_percent_daily_value = Column(Float)
    dietary_fiber_g = Column(Float)
    dietary_fiber_g_percent_daily_value = Column(Float)
    protein_g = Column(Float)
    protein_g_percent_daily_value = Column(Float)
    potassium_mg = Column(Float)
    potassium_mg_percent_daily_value = Column(Float)
    calcium_mg = Column(Float)
    calcium_mg_percent_daily_value = Column(Float)
    iron_mg = Column(Float) 
    iron_mg_percent_daily_value = Column(Float)
    vitamin_d_mcg = Column(Float)
    vitamin_d_mcg_percent_daily_value = Column(Float)


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