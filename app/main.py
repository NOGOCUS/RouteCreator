from fastapi import FastAPI
from app.db.database import engine, Base
from app.crud.auth import router as auth_router
from app.crud.crud import router as crud_router


Base.metadata.create_all(bind=engine)

app = FastAPI()


app.include_router(auth_router)
app.include_router(crud_router)
