from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database - MAIN (puerto 5432)
    DATABASE_URL: str = "postgresql://admin:admin123@localhost:5432/accesorios_dm_db"
    
    # JWT
    SECRET_KEY: str = "prod-secret-key-cambiar-en-produccion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Server
    PORT: int = 8888
    HOST: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"

settings = Settings()