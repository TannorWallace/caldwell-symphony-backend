from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Caldwell Symphony API"
    API_V1_STR: str = "/api/v1"
    SQLALCHEMY_DATABASE_URL: str = "sqlite+aiosqlite:///./caldwell_symphony.db"

    # JWT
    SECRET_KEY: str = "ytlV!PX7jao6S\?7!/0T]lCJ9S.UY!6,V[zx9S&WqG2hYn4@"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Supabase - loaded securely from .env
    SUPABASE_URL: str
    SUPABASE_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()