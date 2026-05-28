"""Database engine — normalises the URL to psycopg3 dialect."""

from collections.abc import Generator

from sqlmodel import Session, create_engine

from finance_api.core.config import settings


def _psycopg3_url(url: str) -> str:
    """Rewrite postgres:// or postgresql:// to postgresql+psycopg:// for psycopg3."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


engine = create_engine(
    _psycopg3_url(settings.database_url),
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    with Session(engine) as session:
        yield session
