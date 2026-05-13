from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database - PostgreSQL real
    DATABASE_URL: str = "postgresql://admin:admin123@localhost:5434/accesorios_dm_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Server
    PORT: int = 8890
    HOST: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"

settings = Settings()