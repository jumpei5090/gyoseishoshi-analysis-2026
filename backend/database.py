"""Database connection and initialization for the exam analysis tool."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'exam.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    from models import (  # noqa: F401
        Subject, Law, Topic, Question, Choice, QuestionTopic, KeywordMapping
    )
    Base.metadata.create_all(bind=engine)
