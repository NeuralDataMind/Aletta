from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# FIX 1: Actually call the function to create the directory
if not os.path.exists("./data"):
    os.makedirs("./data")

# Currently using SQLite for initial setup
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/aletta.db")

connect_args = {}
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    # FIX 2: Essential for concurrent ML processing requests in SQLite
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session in endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()