from sqlmodel import create_engine, Session
from finance_api.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
)


def get_session() -> Session:
    with Session(engine) as session:
        yield session  # type: ignore[misc]
