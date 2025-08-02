from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    RABBITMQ_URL: str
    GOOGLE_AI_API_KEY: str | None = None # Optional for now
    METRICS_PORT: int = 8002

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()