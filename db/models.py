import os

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
# `menus` is fully derived data: it is scraped and re-categorized on demand
# whenever it's empty (see app/services/recommendations.py::fetch_items), so it
# is always safe to drop and recreate on every startup. This guarantees the
# table schema always matches the current Menu model and clears out any rows
# left over from a previous schema (e.g. the old Float columns holding
# unparseable values that were crashing the app even after PR #10's
# safe_float() fix, because the underlying table itself was never dropped).
Base.metadata.drop_all(bind=engine, tables=[Menu.__table__])
Base.metadata.create_all(bind=engine, tables=[Menu.__table__])

# station_overrides / role_overrides hold manually curated corrections that
# cannot be regenerated automatically, so they are never dropped by default -
# doing so on every deploy would silently wipe out real work. If a schema
# mismatch ever needs to be forced for these tables too, set
# RESET_OVERRIDE_TABLES=true for a single deploy and then unset it again.
if os.getenv("RESET_OVERRIDE_TABLES", "false").lower() in ("1", "true", "yes"):
    Base.metadata.drop_all(bind=engine, tables=[StationOverride.__table__, RoleOverride.__table__])

Base.metadata.create_all(bind=engine, tables=[StationOverride.__table__, RoleOverride.__table__])