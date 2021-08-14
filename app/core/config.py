import enum

from pydantic import BaseSettings


class Settings(BaseSettings):
    # Todo: Change for production
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    SUPPORTED_LANGUAGE: list = ("en", "fa")
    DEFAULT_LANGUAGE = "en"

    REDIS_HOST = "redis"
    REDIS_PORT = 6379
    REDIS_DB = 0

    CELERY_BROKER_URL = "redis://redis:6379"
    CELERY_RESULT_BACKEND = "redis://redis:6379"

    DB_USER = "rssreader"
    DB_PASS = "rssreaderpass"
    DB_HOST = "postgres"
    DB_PORT = 5432
    DB_NAME = "rssreader"

    CORS_ORIGINS: list = [
        "http://localhost:8000",
        "https://localhost:8000",
        "http://localhost:3000",
        "https://localhost:3000",
    ]

    class Config:
        env_file = ".env_data"
        env_file_encoding = "utf-8"


class ShowMessageType(str, enum.Enum):
    TOAST = "TOAST"
    NONE = "NONE"


settings = Settings()
