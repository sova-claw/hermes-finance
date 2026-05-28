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

    telegram_bot_token: str | None = None
    telegram_finance_topic_id: int = 1192
    telegram_chat_id: int = -1003913424869


settings = Settings()  # type: ignore[call-arg]
