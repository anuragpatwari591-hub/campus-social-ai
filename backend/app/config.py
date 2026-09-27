"""
Central application configuration.

All settings are read from environment variables (see .env.example at the
repo root). Nothing sensitive is hard-coded here, and the defaults are safe
for local development only.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core ---
    APP_NAME: str = "Campus Social AI"
    ENV: str = "development"
    DEBUG: bool = True

    # --- Database ---
    # PostgreSQL is used in development/production. Tests override this via
    # the TEST_DATABASE_URL / conftest.py to run against SQLite for speed
    # and zero external dependencies.
    DATABASE_URL: str = (
        "postgresql+psycopg2://campus_app:campus_dev_pw@localhost:5432/campus_social"
    )

    # --- Auth / security ---
    JWT_SECRET_KEY: str = "dev-only-secret-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day, fine for a demo project

    # --- Rate limiting ---
    RATE_LIMIT_REQUESTS: int = 180
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # --- File uploads ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp,image/gif"
    ALLOWED_VIDEO_TYPES: str = "video/mp4,video/webm,video/quicktime"

    # --- AI provider ---
    # "mock" works out of the box with no API key so the project can always
    # be demonstrated. Set to "openai" (or another supported provider) and
    # supply AI_API_KEY to use a real model.
    AI_PROVIDER: str = "mock"
    AI_API_KEY: str = ""
    AI_TEXT_MODEL: str = "gpt-4o-mini"
    AI_IMAGE_MODEL: str = "dall-e-3"
    AI_DAILY_REQUEST_LIMIT_PER_USER: int = 50

    @property
    def allowed_image_types(self) -> list[str]:
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",")]

    @property
    def allowed_video_types(self) -> list[str]:
        return [t.strip() for t in self.ALLOWED_VIDEO_TYPES.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
