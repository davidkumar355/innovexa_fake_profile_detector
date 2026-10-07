"""
Configuration settings for Innovexa Backend API
"""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Innovexa Fake Profile Detection API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ARTIFACTS_DIR: str = os.path.join(BASE_DIR, "artifacts")
    DATABASE_PATH: str = os.path.join(BASE_DIR, "detection_history.db")
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    
    class Config:
        case_sensitive = True

settings = Settings()
