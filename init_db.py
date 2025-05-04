"""
Модуль для записи тестовых данных в БД
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

# Подключение к базе данных
engine = create_engine("sqlite:///./transport.db")
Session = sessionmaker(bind=engine)
session = Session()

#Данные для тестового ввода в БД
locations = ["автостанция", "завод", "школа", "больница", "лесопарк", "дачный посёлок"]

time_matrix = [
    [0,  15, 20, 25, 30, 40],   # автостанция
    [15, 0,  10, 20, 25, 35],   # завод
    [20, 10,  0, 15, 20, 30],   # школа
    [25, 20, 15,  0, 10, 25],   # больница
    [30, 25, 20, 10,  0, 15],   # лесопарк
    [40, 35, 30, 25, 15,  0]    # дачный посёлок
]

drivers = ["Алексей", "Борис", "Василий", "Пётр", "Артём"]

routes = [
    {"start": "автостанция", "end": "школа", "time": "08:00"},
    {"start": "завод", "end": "больница", "time": "08:15"},
    {"start": "школа", "end": "лесопарк", "time": "08:30"},
    {"start": "больница", "end": "дачный посёлок", "time": "08:45"},
    {"start": "дачный посёлок", "end": "автостанция", "time": "09:00"},
    {"start": "школа", "end": "автостанция", "time": "09:15"},
    {"start": "завод", "end": "автостанция", "time": "09:30"},
    {"start": "лесопарк", "end": "школа", "time": "09:45"},
    {"start": "больница", "end": "завод", "time": "10:00"},
    {"start": "автостанция", "end": "завод", "time": "10:15"},
    {"start": "дачный посёлок", "end": "школа", "time": "10:30"},
    {"start": "школа", "end": "завод", "time": "10:45"},
    {"start": "автостанция", "end": "больница", "time": "11:00"},
    {"start": "завод", "end": "лесопарк", "time": "11:15"},
    {"start": "лесопарк", "end": "больница", "time": "11:30"},
    {"start": "школа", "end": "дачный посёлок", "time": "11:45"},
    {"start": "больница", "end": "автостанция", "time": "12:00"},
    {"start": "дачный посёлок", "end": "лесопарк", "time": "12:15"},
    {"start": "автостанция", "end": "школа", "time": "12:30"},
    {"start": "завод", "end": "лесопарк", "time": "12:45"}
]

#Очистка старых данных
models.Base.metadata.drop_all(engine)
models.Base.metadata.create_all(engine)



for name in locations:
    location = models.Location(name=name)
    session.add(location)
session.commit()


#ID локаций
location_id_map = {loc.name: loc.id for loc in session.query(models.Location).all()}



for i, from_name in enumerate(locations):
    for j, to_name in enumerate(locations):
        if i<j:
            travel_time = time_matrix[i][j]
            tm = models.TimeMatrix(
                from_location_id=location_id_map[from_name],
                to_location_id=location_id_map[to_name],
                travel_time=travel_time
            )
            session.add(tm)
session.commit()



for name in drivers:
    driver = models.Driver(name=name)
    session.add(driver)
session.commit()



for route in routes:
    START_LOC = route["start"]
    END_LOC = route["end"]
    ROUTE_TIME = route["time"]
    start_id = location_id_map[START_LOC]
    end_id = location_id_map[END_LOC]

    db_route = models.Route(
        start_location_id=start_id,
        end_location_id=end_id,
        time=ROUTE_TIME
    )
    session.add(db_route)
session.commit()
session.close()
