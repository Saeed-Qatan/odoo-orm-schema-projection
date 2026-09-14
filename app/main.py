from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine

app = FastAPI()


@app.get("/")
def root():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {
            "message": "FastAPI is running",
            "database": result.scalar()
        }