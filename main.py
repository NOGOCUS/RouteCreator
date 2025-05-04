"""
Основной файл, через него происходит запуск веб-приложения,
здесь же (временно) хранятся методы CRUD и генетический алгоритм.
"""
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

import models
import schemas
from database import engine, SessionLocal, Base
from genetic.algorithm import run_genetic_algorithm


Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/drivers/", response_model=schemas.DriverResponse, tags=["Работа с БД"])
def create_driver(driver: schemas.DriverCreate, db: Session = Depends(get_db)):
    db_driver = models.Driver(**driver.dict())
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver


@app.get("/drivers/", response_model=List[schemas.DriverResponse], tags=["Работа с БД"])
def read_drivers(db: Session = Depends(get_db)):
    drivers = db.query(models.Driver).all()
    return drivers

@app.delete("/drivers/{driver_id}", tags=["Работа с БД"])
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Водитель не найден")
    db.delete(driver)
    db.commit()
    return {"status": "Успешно удален", "driver_id": driver_id}


@app.post("/locations/", response_model=schemas.LocationResponse, tags=["Работа с БД"])
def create_location(location: schemas.LocationCreate, db: Session = Depends(get_db)):
    db_location = models.Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


@app.get("/locations/", response_model=List[schemas.LocationResponse], tags=["Работа с БД"])
def read_locations(db: Session = Depends(get_db)):
    locations = db.query(models.Location).all()
    return locations


@app.post("/time-matrix/", response_model=schemas.TimeMatrixResponse, tags=["Работа с БД"])
def create_time_matrix(matrix: schemas.TimeMatrixCreate, db: Session = Depends(get_db)):
    from_id = matrix.from_location_id
    to_id = matrix.to_location_id

    if from_id == to_id:
        raise HTTPException(status_code=400, detail="from_id и to_id не могут совпадать")

    # Нормализуем порядок: всегда от меньшего к большему
    a, b = sorted([from_id, to_id])

    existing = db.query(models.TimeMatrix).filter(
        models.TimeMatrix.from_location_id == a,
        models.TimeMatrix.to_location_id == b
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Запись уже существует")

    db_matrix = models.TimeMatrix(
        from_location_id=a,
        to_location_id=b,
        travel_time=matrix.travel_time
    )
    db.add(db_matrix)
    db.commit()
    db.refresh(db_matrix)
    return db_matrix


@app.get("/time-matrix/", response_model=List[schemas.TimeMatrixResponse], tags=["Работа с БД"])
def read_time_matrix(db: Session = Depends(get_db)):
    times = db.query(models.TimeMatrix).all()
    return times

@app.put("/time-matrix/update", response_model=schemas.TimeMatrixResponse, tags=["Работа с БД"])
def update_time_matrix(matrix: schemas.TimeMatrixCreate, db: Session = Depends(get_db)):
    from_id = matrix.from_location_id
    to_id = matrix.to_location_id

    if from_id == to_id:
        raise HTTPException(status_code=400, detail="from_id и to_id не могут совпадать")

    # Используем симметрию: ищем по min, max
    a, b = sorted([from_id, to_id])

    db_entry = db.query(models.TimeMatrix).filter(
        models.TimeMatrix.from_location_id == a,
        models.TimeMatrix.to_location_id == b
    ).first()

    if not db_entry:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    # Обновляем время у найденной записи
    db_entry.travel_time = matrix.travel_time
    db.commit()
    db.refresh(db_entry)

    return db_entry


@app.post("/routes/", response_model=schemas.RouteResponse, tags=["Работа с БД"])
def create_route(route: schemas.RouteCreate, db: Session = Depends(get_db)):
    db_route = models.Route(**route.dict())
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


@app.get("/routes/", response_model=List[schemas.RouteResponse], tags=["Работа с БД"])
def read_routes(db: Session = Depends(get_db)):
    routes = db.query(models.Route).all()
    return routes


@app.delete("/routes/{route_id}", tags=["Работа с БД"])
def delete_route(route_id: int, db: Session = Depends(get_db)):
    route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Маршрут не найден")
    db.delete(route)
    db.commit()
    return {"status": "Успешно удален", "route_id": route_id}

#Расписание
@app.get("/get-schedule", tags=["Генерация и просмотр расписания"])
def get_schedule(db: Session = Depends(get_db)):
    schedule = db.query(models.Schedule).order_by(models.Schedule.driver_name,models.Schedule.time).all()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    return schedule

@app.post("/clear-schedule", tags=["Генерация и просмотр расписания"])
def clear_schedule(db: Session = Depends(get_db)):
    db.query(models.Schedule).delete()
    db.commit()
    return {"status": "Расписание очищено"}


@app.get("/generate-schedule", tags=["Генерация и просмотр расписания"])
def generate_schedule(db: Session = Depends(get_db)):
    drivers_db = db.query(models.Driver).all()
    locations_db = db.query(models.Location).all()
    time_matrix_db = db.query(models.TimeMatrix).all()
    routes_db = db.query(models.Route).all()

    try:
        result = run_genetic_algorithm(drivers_db, locations_db, time_matrix_db, routes_db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Очистка текущего расписания
    db.query(models.Schedule).delete()
    db.commit()

    # Сохранение нового расписания
    for driver_result in result:
        driver_name = driver_result["driver"]
        for route in driver_result["routes"]:
            schedule_entry = models.Schedule(
                driver_name=driver_name,
                route_id=route["route.id"],
                time=route["time"],
                end_time=route["end_time"]
            )
            db.add(schedule_entry)
    db.commit()

    return {"schedule": result}


@app.post("/register", response_model=schemas.UserResponse, tags=["Авторизация и безопасность"])
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Проверка на существование пользователя
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

    # Хэшируем пароль
    hashed_password = models.User.hash_password(user.password)

    # Создаем нового пользователя
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/login", tags=["Авторизация и безопасность"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Ищем пользователя по имени
    db_user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not db_user or not db_user.verify_password(form_data.password):
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"message": "Вход выполнен успешно", "username": db_user.username}