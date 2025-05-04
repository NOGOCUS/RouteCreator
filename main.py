"""
Основной файл, через него происходит запуск веб-приложения,
здесь же (временно) хранятся методы CRUD и генетический алгоритм.
"""
from datetime import datetime, timedelta
import random
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session


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

#Расписание
@app.get("/get-schedule")
def get_schedule(db: Session = Depends(get_db)):
    schedule = db.query(models.Schedule).order_by(models.Schedule.driver_name,models.Schedule.time).all()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    return schedule

@app.post("/clear-schedule")
def clear_schedule(db: Session = Depends(get_db)):
    db.query(models.Schedule).delete()
    db.commit()
    return {"status": "Расписание очищено"}


@app.get("/generate-schedule")
def generate_schedule(db: Session = Depends(get_db)):
    drivers_db = db.query(models.Driver).all()
    locations_db = db.query(models.Location).all()
    time_matrix_db = db.query(models.TimeMatrix).all()
    routes_db = db.query(models.Route).all()

    if not drivers_db or not locations_db or not time_matrix_db or not routes_db:
        raise HTTPException(status_code=400, detail="Недостающие данные для расчета")




    def create_individual():
        unsorted = list({
            "route.id": route.id,
            "start": route.start_location.name,
            "end": route.end_location.name,
            "time": route.time,
            "start.id": route.start_location_id,
            "end.id": route.end_location_id,
            "driver.id": None
        } for route in routes_db)
        for __ in unsorted:
            _=random.choice(drivers_db)
            __["driver.id"]=_.id
        individual=sorted(unsorted,key=lambda r: time_str_to_minutes(r["time"]))
        return individual

    def time_str_to_minutes(t):
        return datetime.strptime(t, "%H:%M")

    def minutes_to_time_str(dt):
        return dt.strftime("%H:%M")

    time_matrix = {}
    for tm in time_matrix_db:
        time_matrix[(tm.from_location_id, tm.to_location_id)] = tm.travel_time

    def get_travel_time(a, b):
        if a == b:
            return 0
        x, y = sorted([a, b])
        return time_matrix.get((x, y), 30)


    def grade(individual):
        score = 0
        penalty_per_time = 100
        penalty_per_number = 1
        extra_time=10

        ideal_per_driver = len(routes_db) / len(drivers_db)
        driver_count={}
        for _ in drivers_db:
            driver_count[_.id] = 0
        for _ in individual:
            driver_count[_["driver.id"]]+=1

        for _ in drivers_db:
            delta = abs(driver_count[_.id] - ideal_per_driver)
            if not {delta < 1}:
                score -= int(delta * penalty_per_number)

        last_end_time={}
        last_end_loc={}
        for _ in drivers_db:
            last_end_time[_.id] = None
            last_end_loc[_.id] = None

        for driver_route in individual:
            start_time = time_str_to_minutes(driver_route["time"])
            travel_duration = get_travel_time(driver_route["start.id"], driver_route["end.id"])
            end_time = start_time + timedelta(minutes=travel_duration)
            if (last_end_time[driver_route["driver.id"]] is not None and last_end_loc[driver_route["driver.id"]] is not None):
                transfer_time = get_travel_time(last_end_loc[driver_route["driver.id"]],driver_route["start.id"])
                expected_start = last_end_time[driver_route["driver.id"]] + timedelta(minutes=transfer_time + extra_time)
                if start_time < expected_start:
                    score -= penalty_per_time

            last_end_time[driver_route["driver.id"]] = end_time
            last_end_loc[driver_route["driver.id"]] = driver_route["end.id"]

        return score


    def crossover(parent1, parent2):
        child = list({} for _ in routes_db)
        i=0
        for _ in routes_db:
            if random.random() > 0.5:
                child[i] = parent1[i].copy()
            else:
                child[i] = parent2[i].copy()
            i+=1
        return child



    def mutate(individual):
        for _ in individual:
            if random.random() < mutation_prob:
                __=random.choice(individual)
                _["driver.id"],__["driver.id"]=__["driver.id"],_["driver.id"]
                break
        return individual


    def evolve(population):
        population.sort(key=lambda ind: grade(ind), reverse=True)
        next_gen = population[:population_size//5]  # элита

        while len(next_gen) < population_size:
            p1 = random.choice(population[:population_size//4])
            p2 = random.choice(population[:population_size//4])
            child = crossover(p1, p2)
            child = mutate(child)
            next_gen.append(child)
        return next_gen



    population_size = 200
    generations = 1000
    mutation_prob = 0.1


    population = [create_individual() for _ in range(population_size)]

    for generation in range(generations):
        population = evolve(population)

    best_list = max(population, key=grade)
    if grade(best_list)<-99:
        raise HTTPException(status_code=400, detail="Ошибка генерации: вероятно,недостаточно водителей")
    result = []
    for _ in drivers_db:
        driver_result = {
            "driver": _.name,
            "routes": []
        }

        for __ in best_list:
            if __["driver.id"]==_.id:
                start_time = time_str_to_minutes(__["time"])
                travel_duration = get_travel_time(__["start.id"], __["end.id"])
                end_time = start_time + timedelta(minutes=travel_duration)

                driver_result["routes"].append({
                    "route.id": __["route.id"],
                    "start": __["start"],
                    "end": __["end"],
                    "time": __["time"],
                    "end_time": minutes_to_time_str(end_time),
                })
        result.append(driver_result)

    db.query(models.Schedule).delete()
    db.commit()

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
