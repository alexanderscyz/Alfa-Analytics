from fastapi import FastAPI
from sqlalchemy import text
from app.database import engine
from app.api.routes.cloud_accounts import router as cloud_accounts_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.cloud_resources import router as cloud_resources_router
from app.api.routes.findings import router as findings_router
from app.api.routes.reports import router as reports_router
from app.api.routes.aws_discovery import router as aws_discovery_router

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
app.include_router(cloud_resources_router, prefix="/api/v1")
app.include_router(findings_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(aws_discovery_router, prefix="/api/v1")

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



