from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://darkatlas:darkatlas@db:5432/darkatlas"
    API_KEY: str = "changeme-secret-api-key"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
