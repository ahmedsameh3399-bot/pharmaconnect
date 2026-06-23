"""SQLAlchemy engine, session factory, and declarative Base.

The session is exposed as a FastAPI dependency (`get_db` in `deps.py`) so every
request gets its own session that's closed on completion.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# pool_pre_ping avoids the classic "MySQL/Postgres has gone away" error after
# the DB restarts or a connection is idle past the server's timeout.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Single declarative base every model inherits from."""


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
