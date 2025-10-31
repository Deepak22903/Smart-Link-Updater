import os
from functools import lru_cache
from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    timezone: str = "Asia/Kolkata"
    redis_url: AnyUrl | None = os.getenv("REDIS_URL")
    mongodb_uri: str | None = os.getenv("MONGODB_URI")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    scraper_api_url: AnyUrl | None = os.getenv("SCRAPER_API_URL")
    scraper_api_key: str | None = os.getenv("SCRAPER_API_KEY")
    wp_base_url: AnyUrl
    wp_username: str
    wp_application_password: str

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
