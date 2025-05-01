from pydantic import BaseModel
from typing import List

# --- Водитель ---
class DriverBase(BaseModel):
    name: str

class DriverCreate(DriverBase):
    pass

class DriverResponse(DriverBase):
    id: int
    class Config:
        orm_mode = True

# --- Пункт назначения ---
class LocationBase(BaseModel):
    name: str

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: int
    class Config:
        orm_mode = True


# --- Время в пути ---
class TimeMatrixBase(BaseModel):
    from_location_id: int
    to_location_id: int
    travel_time: float

class TimeMatrixCreate(TimeMatrixBase):
    pass

class TimeMatrixResponse(TimeMatrixBase):
    id: int
    class Config:
        orm_mode = True


# --- Маршрут ---
class RouteBase(BaseModel):
    start_location_id: int
    end_location_id: int
    time: str

class RouteCreate(RouteBase):
    pass

class RouteResponse(RouteBase):
    id: int
    class Config:
        orm_mode = True