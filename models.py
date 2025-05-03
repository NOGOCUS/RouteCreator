from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, Session
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

#Таблица времени в дороге между двумя пунктами
class TimeMatrix(Base):
    __tablename__ = "time_matrix"
    id = Column(Integer, primary_key=True)
    from_location_id = Column(Integer, ForeignKey("locations.id"))
    to_location_id = Column(Integer, ForeignKey("locations.id"))
    travel_time = Column(Float)
    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])

#Таблица маршрутов
class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True)
    start_location_id = Column(Integer, ForeignKey("locations.id"))
    end_location_id = Column(Integer, ForeignKey("locations.id"))
    time = Column(String)  # формат HH:MM
    start_location = relationship("Location", foreign_keys=[start_location_id])
    end_location = relationship("Location", foreign_keys=[end_location_id])

#Таблица-расписание
class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True)
    driver_name = Column(String)
    route_id = Column(Integer, ForeignKey("routes.id"))
    time = Column(String)  # время начала маршрута (HH:MM)
    end_time = Column(String)  # время окончания
    duration = Column(Integer)  # длительность в минутах
    route = relationship("Route", foreign_keys=[route_id])