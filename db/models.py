from sqlalchemy import Column, Integer, String, Float
from db.database import Base

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    dish = Column(String,   index=True)
    category = Column(String)
    time = Column(String)
    hall = Column(String)
    calories = Column(Float)
    serving_size = Column(String)
    auto_category = Column(String)
    final_category = Column(String)

class Override(Base):
    __tablename__ = "overrides"

    id = Column(Integer, primary_key=True, index=True)
    dish = Column(String, index=True)
    correct_category = Column(String)




