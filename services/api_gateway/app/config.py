from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    METRICS_PORT: int = 8000

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()