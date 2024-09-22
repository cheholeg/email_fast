import os
import secrets

from pydantic import BaseModel
from pydantic.v1 import BaseSettings, Field
from pydantic.v1.env_settings import EnvSettingsSource
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from starlette.templating import Jinja2Templates

from utils import datetimeformat

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.filters['datetimeformat'] = datetimeformat

class PostgresSettings(BaseModel):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str


class Settings(BaseSettings):
    POSTGRES: PostgresSettings | None = None
    SECRET_KEY: str = Field(default_factory=lambda: os.getenv('SECRET_KEY') or secrets.token_urlsafe(32))
    ALGORITHM: str = Field(default="HS256")

    model_config = EnvSettingsSource(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".", ".env"),
        env_file_encoding='utf-8',
    )

settings = Settings()


def get_db_url(async_db=False):
    if settings.POSTGRES:
        db_url = (
            f"postgresql{'' + '+asyncpg' if async_db else ''}://{settings.POSTGRES.DB_USER}:{settings.POSTGRES.DB_PASSWORD}@"
            f"{settings.POSTGRES.DB_HOST}:{settings.POSTGRES.DB_PORT}/{settings.POSTGRES.DB_NAME}"
        )
    else:
        sqlite_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sqlite_db.sqlite")
        db_url = f"sqlite{'' + '+aiosqlite' if async_db else ''}:///{sqlite_db_path}"
    return db_url


SQLALCHEMY_DATABASE_URL = get_db_url()
ASYNC_SQLALCHEMY_DATABASE_URL = get_db_url(async_db=True)

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Асинхронный движок и сессия
if ASYNC_SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    async_engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    async_engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


class Model(DeclarativeBase): pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session


def get_auth_data():
    return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}
