from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import engine, SessionLocal, Base
from seed import seed_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="CS2 Stats Tracker API - Proiect BD2",
    description="Monitorizarea si inregistrarea statisticilor jucatorilor de CS2",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"status": "Online", "message": "Baza de date si Fixtures au fost initializate!"}