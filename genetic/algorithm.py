"""
Генетический алгоритм для генерации расписания
"""
import random
from datetime import datetime, timedelta


def time_str_to_minutes(t):
    return datetime.strptime(t, "%H:%M")


def minutes_to_time_str(dt):
    return dt.strftime("%H:%M")


def run_genetic_algorithm(drivers_db, locations_db, time_matrix_db, routes_db):
    if not drivers_db or not locations_db or not time_matrix_db or not routes_db:
        raise ValueError("Недостающие данные для расчета")

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
            _ = random.choice(drivers_db)
            __["driver.id"] = _.id
        individual = sorted(unsorted, key=lambda r: time_str_to_minutes(r["time"]))
        return individual

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
        extra_time = 10
        ideal_per_driver = len(routes_db) / len(drivers_db)
        driver_count = {}
        for _ in drivers_db:
            driver_count[_.id] = 0
        for _ in individual:
            driver_count[_["driver.id"]] += 1
        for _ in drivers_db:
            delta = abs(driver_count[_.id] - ideal_per_driver)
            if not {delta < 1}:
                score -= int(delta * penalty_per_number)
        last_end_time = {}
        last_end_loc = {}
        for _ in drivers_db:
            last_end_time[_.id] = None
            last_end_loc[_.id] = None
        for driver_route in individual:
            start_time = time_str_to_minutes(driver_route["time"])
            travel_duration = get_travel_time(driver_route["start.id"], driver_route["end.id"])
            end_time = start_time + timedelta(minutes=travel_duration)
            if (last_end_time[driver_route["driver.id"]] is not None and
                last_end_loc[driver_route["driver.id"]] is not None):
                transfer_time = get_travel_time(last_end_loc[driver_route["driver.id"]],
                                                driver_route["start.id"])
                expected_start = last_end_time[driver_route["driver.id"]] + timedelta(
                    minutes=transfer_time + extra_time)
                if start_time < expected_start:
                    score -= penalty_per_time
            last_end_time[driver_route["driver.id"]] = end_time
            last_end_loc[driver_route["driver.id"]] = driver_route["end.id"]
        return score

    def crossover(parent1, parent2):
        child = list({} for _ in routes_db)
        i = 0
        for _ in routes_db:
            if random.random() > 0.5:
                child[i] = parent1[i].copy()
            else:
                child[i] = parent2[i].copy()
            i += 1
        return child

    def mutate(individual):
        for _ in individual:
            if random.random() < mutation_prob:
                __ = random.choice(individual)
                _["driver.id"],__["driver.id"]=__["driver.id"],_["driver.id"]
                break
        return individual

    def evolve(population):
        population.sort(key=lambda ind: grade(ind), reverse=True)
        next_gen = population[:population_size//5]
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

    if grade(best_list) < -99:
        raise ValueError("Ошибка генерации: вероятно, недостаточно водителей")

    result = []
    for _ in drivers_db:
        driver_result = {
            "driver": _.name,
            "routes": []
        }
        for __ in best_list:
            if __["driver.id"] == _.id:
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

    return result