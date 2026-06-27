"""Database setup (SQLAlchemy).

This configures the connection to the users database. Thanks to SQLAlchemy, the
exact same code works on SQLite (local dev) and PostgreSQL (production) - only
the DATABASE_URL changes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import config

# SQLite needs a special flag to be usable from FastAPI's worker threads.
# PostgreSQL and other databases do not need it.
connect_args = (
    {"check_same_thread": False}
    if config.DATABASE_URL.startswith("sqlite")
    else {}
)

# The engine is the core connection to the database.
engine = create_engine(config.DATABASE_URL, connect_args=connect_args)

# A session factory - each request gets its own short-lived session.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base class that our ORM models inherit from.
Base = declarative_base()


def get_db():
    # FastAPI dependency: provide a database session and always close it after.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Create the database tables if they do not exist yet.
    # Importing models here makes sure they are registered on Base first.
    import db.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
