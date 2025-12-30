import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "InsightFlow"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # DB
    MARIADB_SERVER: str
    MARIADB_PORT: int
    MARIADB_USER: str
    MARIADB_PASSWORD: str
    MARIADB_DB: str

    MONGODB_SERVER: str
    MONGODB_PORT: int
    MONGODB_USER: str
    MONGODB_PASSWORD: str

    REDIS_SERVER: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    MINIO_SERVER: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
