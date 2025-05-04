"""
Создаём шаблоны таблиц в БД
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from passlib.context import CryptContext

class Driver(Base):
    """
    Таблица водителей
    Атрибуты:
        id (int): Уникальный идентификатор водителя.
        name (str): Имя водителя (уникальное).
        user_id (int): Идентификатор пользователя.
        user: Пользователь.
    """
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

class Location(Base):
    """
    Таблица возможных пунктов назначения
    Атрибуты:
        id (int): Уникальный идентификатор пункта назначения.
        name (str): Название  пункта назначения (уникальное).
        user_id (int): Идентификатор пользователя.
        user: Пользователь.
    """
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

class TimeMatrix(Base):
    """
    Таблица времени в дороге между двумя пунктами,
    задаёт длительность любых маршрутов, а также время, которое водитель тратит
    между маршрутами, чтобы принять следующий маршрут.

    Атрибуты:
        id (int): Уникальный идентификатор матричного элемента.
        from_location_id (int): Идентификатор стартовой локации.
        to_location_id (int): Идентификатор конечной локации.
        travel_time (float): Время в пути (в минутах)
        from_location: Cтартовая локация.
        to_location: Конечная локация.
        user_id (int): Идентификатор пользователя.
        user: Пользователь.
    """
    __tablename__ = "time_matrix"
    id = Column(Integer, primary_key=True)
    from_location_id = Column(Integer, ForeignKey("locations.id"))
    to_location_id = Column(Integer, ForeignKey("locations.id"))
    travel_time = Column(Float)
    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

class Route(Base):
    """
    Таблица маршрутов - сюда отправляются маршруты,
    которые необходимо выполнить за день.

    Атрибуты:
        id (int): Уникальный идентификатор маршрута.
        start_location_id (int): Идентификатор стартовой локации.
        end_location_id (int): Идентификатор конечной локации.
        time (str): Время отправления (формат HH:MM)
        start_location (Location): Стартовая локация.
        end_location (Location): Конечная локация.
        user_id (int): Идентификатор пользователя.
        user: Пользователь.
    """
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True)
    start_location_id = Column(Integer, ForeignKey("locations.id"))
    end_location_id = Column(Integer, ForeignKey("locations.id"))
    time = Column(String)
    start_location = relationship("Location", foreign_keys=[start_location_id])
    end_location = relationship("Location", foreign_keys=[end_location_id])
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

class Schedule(Base):
    """
    Таблица-расписание, содержит распределение всех маршрутов из Route по водителям.

    Атрибуты:
        id (int): Уникальный идентификатор элемента таблицы.
        driver_name (str): Имя водителя.
        route_id (int): Идентификатор маршрута.
        time (str): Время отправления (формат HH:MM).
        end_time (str): Время прибытия (формат HH:MM).
        end_location_id (int): Идентификатор конечной локации.
        start_location (str): Название стартовой локации.
        end_location (str): Название конечной локации.
        user_id (int): Идентификатор пользователя.
        user: Пользователь.
    """
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True)
    driver_name = Column(String)
    route_id = Column(Integer, ForeignKey("routes.id"))
    time = Column(String)
    end_time = Column(String)
    route = relationship("Route", foreign_keys=[route_id])
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
