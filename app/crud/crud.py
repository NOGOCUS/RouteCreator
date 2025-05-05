"""
CRUD-методы для работы с таблицами
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import models
from app.schemas import schemas
from app.db.database import get_db
from app.crud.auth import get_current_user

router = APIRouter(tags=["Работа с БД"])

#Водители
@router.post("/drivers/", response_model=schemas.DriverResponse)
def create_driver(driver: schemas.DriverCreate, db: Session = Depends(get_db),
                  current_user: dict = Depends(get_current_user)):
    db_driver = models.Driver(**driver.dict(), user_id=current_user.id)
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver


@router.get("/drivers/", response_model=list[schemas.DriverResponse])
def read_drivers(db: Session = Depends(get_db),
                 current_user: dict = Depends(get_current_user)):
    return db.query(models.Driver).filter(models.Driver.user_id == current_user.id).all()


@router.delete("/drivers/{driver_id}")
def delete_driver(driver_id: int, db: Session = Depends(get_db),
                  current_user: dict = Depends(get_current_user)):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id,
                                   models.Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Водитель не найден")
    db.delete(driver)
    db.commit()
    return {"status": "Успешно удален", "driver_id": driver_id}


#Локации
@router.post("/locations/", response_model=schemas.LocationResponse)
def create_location(location: schemas.LocationCreate, db: Session = Depends(get_db),
                    current_user: dict = Depends(get_current_user)):
    db_location = models.Location(**location.dict(), user_id=current_user.id)
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


@router.get("/locations/", response_model=list[schemas.LocationResponse])
def read_locations(db: Session = Depends(get_db),
                   current_user: dict = Depends(get_current_user)):
    return db.query(models.Location).filter(models.Location.user_id == current_user.id).all()


#Матрица времени
@router.post("/time-matrix/", response_model=schemas.TimeMatrixResponse)
def create_time_matrix(matrix: schemas.TimeMatrixCreate, db: Session = Depends(get_db),
                       current_user: dict = Depends(get_current_user)):
    from_id = matrix.from_location_id
    to_id = matrix.to_location_id
    if from_id == to_id:
        raise HTTPException(status_code=400, detail="from_id и to_id не могут совпадать")
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


@router.get("/time-matrix/", response_model=list[schemas.TimeMatrixResponse])
def read_time_matrix(db: Session = Depends(get_db),
                     current_user: dict = Depends(get_current_user)):
    return db.query(models.TimeMatrix).filter(models.TimeMatrix.user_id == current_user.id).all()


@router.put("/time-matrix/update", response_model=schemas.TimeMatrixResponse)
def update_time_matrix(matrix: schemas.TimeMatrixCreate, db: Session = Depends(get_db),
                       current_user: dict = Depends(get_current_user)):
    from_id = matrix.from_location_id
    to_id = matrix.to_location_id
    if from_id == to_id:
        raise HTTPException(status_code=400, detail="from_id и to_id не могут совпадать")
    a, b = sorted([from_id, to_id])
    db_entry = db.query(models.TimeMatrix).filter(
        models.TimeMatrix.from_location_id == a,
        models.TimeMatrix.to_location_id == b,
        models.TimeMatrix.user_id == current_user.id
    ).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    db_entry.travel_time = matrix.travel_time
    db.commit()
    db.refresh(db_entry)
    return db_entry


#Маршруты
@router.post("/routes/", response_model=schemas.RouteResponse)
def create_route(route: schemas.RouteCreate, db: Session = Depends(get_db),
                 current_user: dict = Depends(get_current_user)):
    db_route = models.Route(**route.dict(), user_id=current_user.id)
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


@router.get("/routes/", response_model=list[schemas.RouteResponse])
def read_routes(db: Session = Depends(get_db),
                current_user: dict = Depends(get_current_user)):
    return db.query(models.Route).filter(models.Route.user_id == current_user.id).all()


@router.delete("/routes/{route_id}")
def delete_route(route_id: int, db: Session = Depends(get_db),
                 current_user: dict = Depends(get_current_user)):
    route = db.query(models.Route).filter(
        models.Route.id == route_id,
        models.Route.user_id == current_user.id
    ).first()
    if not route:
        raise HTTPException(status_code=404, detail="Маршрут не найден")
    db.delete(route)
    db.commit()
    return {"status": "Успешно удален", "route_id": route_id}
