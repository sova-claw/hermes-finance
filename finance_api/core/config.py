"""Application settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All config comes from env vars. Required fields fail loud at startup."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"

    database_url: str
    db_pool_size: int = 5
    db_max_overflow: int = 10

    monobank_token: str
    sync_interval_hours: int = 1
    monobank_fetch_days: int = 730

    telegram_bot_token: str
    telegram_owner_id: int

    anthropic_api_key: str = ""


settings = Settings()  # type: ignore[call-arg]
