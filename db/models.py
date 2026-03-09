from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from db.database import Base, engine

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    dish = Column(String,   index=True)
    category = Column(String)
    time = Column(String)
    hall = Column(String)
    calories = Column(Float)
    serving_size = Column(String)
    station = Column(String)
    final_station = Column(String)
    role = Column(String)


class Override(Base):
    __tablename__ = "overrides"

    id = Column(Integer, primary_key=True, index=True)
    dish = Column(String, index=True)
    correct_category = Column(String)

class BarOverride(Base):
    __tablename__ = "bar_overrides"

    id = Column(Integer, primary_key=True, index=True)
    raw_bar = Column(String, index=True)
    correct_bar = Column(String)

class RoleOverride(Base):
    __tablename__ = "role_overrides"

    id = Column(Integer, primary_key=True, index=True)
    dish = Column(String, index=True)              # canonical dish name
    final_station = Column(String, index=True)    # e.g. byo_bowl, byo_salad
    correct_role = Column(String)                      # protein/base/veg/sauce/extra/etc.

    __table_args__ = (
        UniqueConstraint("dish", "final_station", name="uq_dish_station_role"),
    )
#Base.metadata.drop_all(bind=engine, tables=[Menu.__table__])
#Base.metadata.create_all(bind=engine, tables=[Menu.__table__])