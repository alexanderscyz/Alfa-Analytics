import os

from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://alfa_admin:alfa_local_2026@database:5432/alfa_analytics",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)