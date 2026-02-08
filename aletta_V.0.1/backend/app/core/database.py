from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import numpy as np

# Create the data directory if it doesn't exist
if not os.path.exists("./data"):
    os.makedirs

# Currently using the SQLite for initial setup later i will switch PgSQL
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/aletta.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
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
