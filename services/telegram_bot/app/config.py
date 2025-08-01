from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    RABBITMQ_URL: str
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: str
    TELEGRAM_SECRET_TOKEN: str
    METRICS_PORT: int = 8003

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()