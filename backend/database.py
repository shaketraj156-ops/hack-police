import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# The engine manages the actual connection to the database
engine = create_engine(DATABASE_URL)

# The session factory allows routes to request temporary database access
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class used to create our tables
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()