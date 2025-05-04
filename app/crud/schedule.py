from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import app.models.models as models
from app.db.database import get_db
from app.crud.auth import get_current_user

router = APIRouter(tags=["Генерация и просмотр расписания"])


@router.get("/get-schedule")
def get_schedule(db: Session = Depends(get_db),
                 current_user: dict = Depends(get_current_user)):
    schedule = db.query(models.Schedule).filter(models.Schedule.user_id == current_user.id).all()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    return schedule


@router.post("/clear-schedule")
def clear_schedule(db: Session = Depends(get_db),
                   current_user: dict = Depends(get_current_user)):
    db.query(models.Schedule).filter(models.Schedule.user_id == current_user.id).delete()
    db.commit()
    return {"status": "Расписание очищено"}


@router.get("/generate-schedule")
def generate_schedule(db: Session = Depends(get_db),
                      current_user: dict = Depends(get_current_user)):
    drivers_db = db.query(models.Driver).filter(models.Driver.user_id == current_user.id).all()
    locations_db = db.query(models.Location).filter(models.Location.user_id == current_user.id).all()
    time_matrix_db = db.query(models.TimeMatrix).filter(models.TimeMatrix.user_id == current_user.id).all()
    routes_db = db.query(models.Route).filter(models.Route.user_id == current_user.id).all()

    from app.genetic.algorithm import run_genetic_algorithm

    try:
        result = run_genetic_algorithm(drivers_db, locations_db, time_matrix_db, routes_db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.query(models.Schedule).filter(models.Schedule.user_id == current_user.id).delete()
    db.commit()

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