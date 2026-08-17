from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os
from collections.abc import Generator

load_dotenv()


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()