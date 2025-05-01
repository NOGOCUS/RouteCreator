from sqlalchemy import Column, Integer, String
from database import Base

#Таблица водителей
class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)

#Таблица возможных пунктов назначения
class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
