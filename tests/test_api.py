import os
os.environ["ENV"] = "test"

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db
from app.db.database import Base, engine
from sqlalchemy.orm import sessionmaker

client = TestClient(app)


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


def register_user(username: str, password: str):
    response = client.post("/register", json={"username": username, "password": password})
    return response.json(), response.status_code

def login_user(username: str, password: str):
    response = client.post("/login", data={"username": username, "password": password})
    return response.json(), response.status_code

def create_driver(token: str, name: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/drivers/", json={"name": name}, headers=headers)
    return response.json(), response.status_code

def create_location(token: str, name: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/locations/", json={"name": name}, headers=headers)
    return response.json(), response.status_code

def create_route(token: str, start_id: int, end_id: int, time: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/routes/", json={
        "start_location_id": start_id,
        "end_location_id": end_id,
        "time": time
    }, headers=headers)
    return response.json(), response.status_code

def create_time_matrix(token: str, from_id: int, to_id: int, travel_time: float):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/time-matrix/", json={
        "from_location_id": from_id,
        "to_location_id": to_id,
        "travel_time": travel_time
    }, headers=headers)
    return response.json(), response.status_code




def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_register_and_login():
    user_data, code = register_user("testuser", "testpass")
    assert code == 200
    assert user_data["username"] == "testuser"

    token_data, code = login_user("testuser", "testpass")
    assert code == 200
    assert "access_token" in token_data

def test_crud_operations():
    token_data, _ = login_user("testuser", "testpass")
    token = token_data["access_token"]

    # Создание водителя
    driver_data, code = create_driver(token, "Водитель 1")
    assert code == 200
    assert driver_data["name"] == "Водитель 1"

    # Создание локаций
    loc_a, code = create_location(token, "Локация A")
    assert code == 200
    loc_b, code = create_location(token, "Локация B")
    assert code == 200

    # Создание матрицы времени
    tm_data, code = create_time_matrix(token, loc_a["id"], loc_b["id"], 20)
    assert code == 200

    # Создание маршрута
    route_data, code = create_route(token, loc_a["id"], loc_b["id"], "09:00")
    assert code == 200

def test_get_all_drivers():
    register_user("testuser", "testpass")
    token_data, _ = login_user("testuser", "testpass")
    token = token_data["access_token"]

    response = client.get("/drivers/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    drivers = response.json()
    assert len(drivers) == 1
    assert (drivers["name"] == "Водитель 1" for d in drivers)


def test_get_all_locations():
    token_data, _ = login_user("testuser", "testpass")
    token = token_data["access_token"]

    response = client.get("/locations/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    locations = response.json()
    assert len(locations) == 2
    assert any(l["name"] == "Локация A" for l in locations)
    assert any(l["name"] == "Локация B" for l in locations)


def test_time_matrix():
    token_data, _ = login_user("testuser", "testpass")
    token = token_data["access_token"]

    response = client.get("/time-matrix/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    matrices = response.json()
    assert len(matrices) == 1
    assert any(m["travel_time"] == 20 for m in matrices)


def test_get_all_routes():
    token_data, _ = login_user("testuser", "testpass")
    token = token_data["access_token"]

    response = client.get("/routes/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    routes = response.json()
    assert len(routes) == 1
    # assert any(r["start_location_id"] == loc_a["id"] for r in routes)
    # assert any(r["end_location_id"] == loc_b["id"] for r in routes)

def test_generate_schedule():
    token_data, _ = login_user("testuser", "testpass")
    token = token_data["access_token"]

    response = client.get("/generate-schedule", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    result = response.json()
    assert "schedule" in result

def test_get_schedule():
    token_data, _ = login_user("testuser", "testpass")
    token = token_data["access_token"]

    response = client.get("/get-schedule", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    schedule = response.json()
    assert isinstance(schedule, list)