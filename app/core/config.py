from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "TaskFlow Backend API"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str
    DB_ECHO: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()