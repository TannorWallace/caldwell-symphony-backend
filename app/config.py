from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Caldwell Symphony API"
    API_V1_STR: str = "/api/v1"
    SQLALCHEMY_DATABASE_URL: str = "sqlite+aiosqlite:///./caldwell_symphony.db"

    #JWT and OAUTH 
    SECRET_KEY: str = "ytlV!PX7jao6S\?7!/0T]lCJ9S.UY!6,V[zx9S&WqG2hYn4@"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7   # 7 days

    #SUPABASE CONFIG
    # SUPABASE CONFIG (using Service Role key for backend uploads)
    SUPABASE_URL: str = "https://yxkharrshmhyfkmsbdyy.supabase.co"
    SUPABASE_KEY: str = "sb_secret_3ih6E-3WM5jmKZr-JgF3RQ_EEPQwYt2"

settings = Settings()