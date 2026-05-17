import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / '.env')
load_dotenv(BACKEND_DIR / '.env.local', override=True)


# Use DATABASE_URL from env, or fall back to local SQLite so hot-reload
# subprocesses never crash when the shell variable isn't inherited.
_raw_db_url = os.getenv('DATABASE_URL', '').strip()
DATABASE_URL: str = _raw_db_url if _raw_db_url.startswith(('sqlite', 'postgresql', 'postgres', 'mysql')) \
    else 'sqlite:///./vidda.db'


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine)


def get_session() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError('DATABASE_URL is not configured')

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_tables() -> None:
    if engine is None:
        return

    Base.metadata.create_all(bind=engine)
