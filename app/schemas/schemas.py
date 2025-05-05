"""
Модуль содержит Pydantic-модели для обработки данных в БД
"""
from pydantic import BaseModel

#Водитель
class DriverBase(BaseModel):
    name: str

class DriverCreate(DriverBase):
    pass

class DriverResponse(DriverBase):
    id: int
    class Config:
        from_attributes = True

#Пункт назначения
class LocationBase(BaseModel):
    name: str

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: int
    class Config:
        from_attributes = True


#Время в пути
class TimeMatrixBase(BaseModel):
    from_location_id: int
    to_location_id: int
    travel_time: float

class TimeMatrixCreate(TimeMatrixBase):
    pass

class TimeMatrixResponse(TimeMatrixBase):
    id: int
    class Config:
        from_attributes = True


#Маршрут
class RouteBase(BaseModel):
    start_location_id: int
    end_location_id: int
    time: str

class RouteCreate(RouteBase):
    pass

class RouteResponse(RouteBase):
    id: int
    class Config:
        from_attributes = True

#Расписание
class ScheduleBase(BaseModel):
    driver_name: str
    route_id: int
    time: str
    end_time: str



class ScheduleCreate(ScheduleBase):
    pass


class ScheduleResponse(ScheduleBase):
    id: int
    class Config:
        from_attributes = True


#Пользователь
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
