import enum

from pydantic import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    SUPPORTED_LANGUAGE: list = ("en", "fa")
    DEFAULT_LANGUAGE = "en"

    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0

    CELERY_BROKER_URL = "redis://localhost:6379"
    CELERY_RESULT_BACKEND = "redis://localhost:6379"

    DB_USER = "rssreader"
    DB_PASS = "rssreaderpass"
    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_NAME = "rssreader"

    CORS_ORIGINS: list = [
        "http://localhost:8000",
        "https://localhost:8000",
        "http://localhost:3000",
        "https://localhost:3000",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ShowMessageType(str, enum.Enum):
    TOAST = "TOAST"
    NONE = "NONE"


settings = Settings()
