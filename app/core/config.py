from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

class Settings(BaseSettings):
    APP_NAME: str = "Luximus API"
    DATABASE_URL: str = DATABASE_URL

    class Config:
        env_file = ".env"

settings = Settings()

