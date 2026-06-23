"""Shared test fixtures.

Tests run against an in-memory SQLite database. This is fine because we
never use Postgres-specific SQL in the services we test (ranking, FSM,
forecast all use ORM-level queries that work on SQLite too).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
