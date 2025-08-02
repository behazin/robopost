from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    RABBITMQ_URL: str
    FETCH_INTERVAL_SECONDS: int = 60

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()