"""
Основной файл, через который происходит запуск приложения
"""
from fastapi import FastAPI
from app.db.database import engine, Base
from app.crud.auth import router as auth_router
from app.crud.crud import router as crud_router
from app.crud.schedule import router as schedule_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RouteCreator",
    description="Система для генерации и хранения расписания, основанная на генетическом алгоритме"
        )


app.include_router(auth_router)
app.include_router(crud_router)
app.include_router(schedule_router)
