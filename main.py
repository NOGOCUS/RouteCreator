from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import engine, SessionLocal, Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/drivers/", response_model=schemas.DriverResponse)
def create_driver(driver: schemas.DriverCreate, db: Session = Depends(get_db)):
    db_driver = models.Driver(**driver.dict())
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver


@app.get("/drivers/", response_model=List[schemas.DriverResponse])
def read_drivers(db: Session = Depends(get_db)):
    drivers = db.query(models.Driver).all()
    return drivers

@app.delete("/drivers/{driver_id}")
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Водитель не найден")
    db.delete(driver)
    db.commit()
    return {"status": "Успешно удален", "driver_id": driver_id}


@app.post("/locations/", response_model=schemas.LocationResponse)
def create_location(location: schemas.LocationCreate, db: Session = Depends(get_db)):
    db_location = models.Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


@app.get("/locations/", response_model=List[schemas.LocationResponse])
def read_locations(db: Session = Depends(get_db)):
    locations = db.query(models.Location).all()
    return locations


@app.post("/time-matrix/", response_model=schemas.TimeMatrixResponse)
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


@app.get("/time-matrix/", response_model=List[schemas.TimeMatrixResponse])
def read_time_matrix(db: Session = Depends(get_db)):
    times = db.query(models.TimeMatrix).all()
    return times

@app.put("/time-matrix/update", response_model=schemas.TimeMatrixResponse)
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


@app.post("/routes/", response_model=schemas.RouteResponse)
def create_route(route: schemas.RouteCreate, db: Session = Depends(get_db)):
    db_route = models.Route(**route.dict())
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


@app.get("/routes/", response_model=List[schemas.RouteResponse])
def read_routes(db: Session = Depends(get_db)):
    routes = db.query(models.Route).all()
    return routes


@app.delete("/routes/{route_id}")
def delete_route(route_id: int, db: Session = Depends(get_db)):
    route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Маршрут не найден")
    db.delete(route)
    db.commit()
    return {"status": "Успешно удален", "route_id": route_id}