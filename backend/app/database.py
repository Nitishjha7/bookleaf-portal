"""Engine and session setup."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

# sqlite complains about threads otherwise
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # a sleeping Neon database needs a moment to wake up
    connect_args = {"connect_timeout": 15}

engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """one session per request"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
