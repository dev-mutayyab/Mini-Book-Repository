# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
import os  # You might need this for some older env var setups, but pydantic-settings handles most


class Settings(BaseSettings):
    # This is the ONLY configuration you should have for Pydantic v2 settings.
    # The 'extra='ignore'' is good for allowing other env variables not explicitly
    # defined as fields in your Settings class.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Your settings fields go here
    # Add other settings from your .env here
    DATABASE_URL: str = "sqlite:///./books_repository.db"
    REDIS_URL: str = None
    JWT_SECRET: str = (
        "e2c24482effd2741d998d8a3d31359a3e0f8f76b432d081310a4fdfd315c1835fd2c177546e2c17ba6d06094dc994716bb9cb034fa7d7cd55dae53844ea134d4"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1

    # Example of a field with a default value (useful for optional env vars)
    # DEBUG: bool = False


settings = Settings()
