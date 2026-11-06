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

    # EmailJS
    EMAILJS_SERVICE_ID: str = ""
    EMAILJS_TEMPLATE_ID: str = ""
    EMAILJS_PUBLIC_KEY: str = ""

    # ===================== SECURITY / ENVIRONMENT =====================
    DEBUG: bool = Field(default=True)

    # Stored as comma-separated strings in .env / Render
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000"
    )
    ALLOWED_HOSTS: str = Field(
        default="localhost,127.0.0.1"
    )

    FRONTEND_URL: str = Field(default="http://localhost:3000")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]


settings = Settings()