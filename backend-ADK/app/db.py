import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / '.env')
load_dotenv(BACKEND_DIR / '.env.local', override=True)


DATABASE_URL = os.getenv('DATABASE_URL')


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine) if engine else None


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
