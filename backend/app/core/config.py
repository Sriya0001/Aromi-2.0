from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str = "your-super-secret-jwt-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    GROQ_API_KEY: str = ""
    YOUTUBE_API_KEY: str = ""
    SPOONACULAR_API_KEY: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/calendar/callback"

    # PostgreSQL — falls back to SQLite for local dev without Postgres
    DATABASE_URL: str = "sqlite:///./aromi.db"
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()
