"""
Основной файл, через него происходит запуск веб-приложения,
здесь же (временно) хранятся методы CRUD и генетический алгоритм.
"""
from typing import List, Annotated
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext

import app.models.models as models
import app.schemas.schemas as schemas
from app.db.database import engine, SessionLocal, Base
from app.genetic.algorithm import run_genetic_algorithm


Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# === Загрузка из .env ===
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# === Пароли и OAuth2 ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


@app.post("/drivers/", response_model=schemas.DriverResponse, tags=["Работа с БД"])
def create_driver(driver: schemas.DriverCreate, db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    db_driver = models.Driver(**driver.model_dump(), user_id=current_user.id)
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver


@app.get("/drivers/", response_model=List[schemas.DriverResponse], tags=["Работа с БД"])
def read_drivers(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    drivers = db.query(models.Driver).filter(models.Driver.user_id == current_user.id).all()
    return drivers

@app.delete("/drivers/{driver_id}", tags=["Работа с БД"])
def delete_driver(driver_id: int, db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id,
                                            models.Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Водитель не найден")
    db.delete(driver)
    db.commit()
    return {"status": "Успешно удален", "driver_id": driver_id}


@app.post("/locations/", response_model=schemas.LocationResponse, tags=["Работа с БД"])
def create_location(location: schemas.LocationCreate, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    db_location = models.Location(**location.model_dump(), user_id=current_user.id)
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


@app.get("/locations/", response_model=List[schemas.LocationResponse], tags=["Работа с БД"])
def read_locations(db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    locations = db.query(models.Location).filter(models.Location.user_id == current_user.id).all()
    return locations


@app.post("/time-matrix/", response_model=schemas.TimeMatrixResponse, tags=["Работа с БД"])
def create_time_matrix(matrix: schemas.TimeMatrixCreate, db: Session = Depends(get_db),
                       current_user: models.User = Depends(get_current_user)):
    from_id = matrix.from_location_id
    to_id = matrix.to_location_id

    if from_id == to_id:
        raise HTTPException(status_code=400, detail="from_id и to_id не могут совпадать")

    # Нормализуем порядок: всегда от меньшего к большему
    a, b = sorted([from_id, to_id])

    existing = db.query(models.TimeMatrix).filter(
        models.TimeMatrix.from_location_id == a,
        models.TimeMatrix.to_location_id == b,
        models.TimeMatrix.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Запись уже существует")

    db_matrix = models.TimeMatrix(
        from_location_id=a,
        to_location_id=b,
        travel_time=matrix.travel_time,
        user_id=current_user.id
    )
    db.add(db_matrix)
    db.commit()
    db.refresh(db_matrix)
    return db_matrix


@app.get("/time-matrix/", response_model=List[schemas.TimeMatrixResponse], tags=["Работа с БД"])
def read_time_matrix(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    times = db.query(models.TimeMatrix).filter(models.TimeMatrix.user_id == current_user.id).all()
    return times

@app.put("/time-matrix/update", response_model=schemas.TimeMatrixResponse, tags=["Работа с БД"])
def update_time_matrix(matrix: schemas.TimeMatrixCreate, db: Session = Depends(get_db),
                       current_user: models.User = Depends(get_current_user)):
    from_id = matrix.from_location_id
    to_id = matrix.to_location_id

    if from_id == to_id:
        raise HTTPException(status_code=400, detail="from_id и to_id не могут совпадать")

    # Используем симметрию: ищем по min, max
    a, b = sorted([from_id, to_id])

    db_entry = db.query(models.TimeMatrix).filter(
        models.TimeMatrix.from_location_id == a,
        models.TimeMatrix.to_location_id == b,
        models.TimeMatrix.user_id == current_user.id
    ).first()

    if not db_entry:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    # Обновляем время у найденной записи
    db_entry.travel_time = matrix.travel_time
    db.commit()
    db.refresh(db_entry)

    return db_entry


@app.post("/routes/", response_model=schemas.RouteResponse, tags=["Работа с БД"])
def create_route(route: schemas.RouteCreate, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    db_route = models.Route(**route.model_dump(), user_id=current_user.id)
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


@app.get("/routes/", response_model=List[schemas.RouteResponse], tags=["Работа с БД"])
def read_routes(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    routes = db.query(models.Route).filter(models.Route.user_id == current_user.id).all()
    return routes


@app.delete("/routes/{route_id}", tags=["Работа с БД"])
def delete_route(route_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    route = db.query(models.Route).filter(
        models.Route.id == route_id,
        models.Route.user_id == current_user.id
    ).first()
    if not route:
        raise HTTPException(status_code=404, detail="Маршрут не найден")
    db.delete(route)
    db.commit()
    return {"status": "Успешно удален", "route_id": route_id}

#Расписание
@app.get("/get-schedule", tags=["Генерация и просмотр расписания"])
def get_schedule(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    schedule = db.query(models.Schedule).filter(
        models.Schedule.user_id == current_user.id
    ).order_by(models.Schedule.driver_name, models.Schedule.time).all()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    return schedule

@app.post("/clear-schedule", tags=["Генерация и просмотр расписания"])
def clear_schedule(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db.query(models.Schedule).filter(models.Schedule.user_id == current_user.id).delete()
    db.commit()
    return {"status": "Расписание очищено"}


@app.get("/generate-schedule", tags=["Генерация и просмотр расписания"])
def generate_schedule(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    drivers_db = db.query(models.Driver).filter(models.Driver.user_id == current_user.id).all()
    locations_db = db.query(models.Location).filter(models.Location.user_id == current_user.id).all()
    time_matrix_db = db.query(models.TimeMatrix).filter(models.TimeMatrix.user_id == current_user.id).all()
    routes_db = db.query(models.Route).filter(models.Route.user_id == current_user.id).all()

    try:
        result = run_genetic_algorithm(drivers_db, locations_db, time_matrix_db, routes_db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Очистка расписания только для текущего пользователя
    db.query(models.Schedule).filter(models.Schedule.user_id == current_user.id).delete()
    db.commit()

    # Сохранение нового расписания
    for driver_result in result:
        driver_name = driver_result["driver"]
        for route in driver_result["routes"]:
            schedule_entry = models.Schedule(
                driver_name=driver_name,
                route_id=route["route.id"],
                time=route["time"],
                end_time=route["end_time"],
                user_id=current_user.id
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


@app.post("/login", response_model=schemas.Token, tags=["Авторизация и безопасность"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Ищем пользователя
    db_user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not db_user or not db_user.verify_password(form_data.password):
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Генерируем токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}