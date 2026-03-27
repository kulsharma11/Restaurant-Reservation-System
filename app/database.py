# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# This creates (or connects to) restaurant.db in the project root
DATABASE_URL = "mysql+pymysql://restaurant_user:password@localhost/restaurant_db"

engine = create_engine(DATABASE_URL)

# SessionLocal is a factory — calling it creates a new session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base is the parent class all ORM models will inherit from
# Using the modern SQLAlchemy 2.0 style (DeclarativeBase class)
class Base(DeclarativeBase):
    pass


def get_db():
    """
    FastAPI dependency. Opens a DB session, yields it to the endpoint,
    then closes it when the request is done — even if an error occurred.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
