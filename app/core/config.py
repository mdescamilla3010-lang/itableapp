from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration, sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "itable app"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/itable"

    PARROT_API_BASE_URL: str = "https://api.parrotpos.com"

    # CORS: comma-separated list of allowed origins for the frontend (e.g. the
    # Vite dev server). "*" is a permissive default suitable for this MVP,
    # which has no auth yet; restrict it once real auth is in place.
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Fugas engine thresholds
    FUGAS_ZSCORE_HIGH_RISK: float = 2.0
    FUGAS_ZSCORE_MEDIUM_RISK: float = 1.0
    FUGAS_HIGH_RISK_MIN_AMOUNT: float = 1000.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
