from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Caldwell Symphony API"
    API_V1_STR: str = "/api/v1"

    SQLALCHEMY_DATABASE_URL: str = ""

    # JWT
    SECRET_KEY: str = Field(...)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Supabase Storage
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # ===================== SECURITY / ENVIRONMENT =====================
    DEBUG: bool = Field(default=True)

    # Stored as comma-separated strings in .env
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000"
    )
    ALLOWED_HOSTS: str = Field(
        default="localhost,127.0.0.1"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()