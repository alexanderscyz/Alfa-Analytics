from fastapi import FastAPI
from sqlalchemy import text
from app.database import engine
from app.api.routes.cloud_accounts import router as cloud_accounts_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Alfa Analytics API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cloud_accounts_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "application": "Alfa Analytics",
        "status": "running"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/health/database")
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"database": "healthy"}



