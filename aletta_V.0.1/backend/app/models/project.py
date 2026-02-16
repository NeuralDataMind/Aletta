from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
    # --- NEW: Data Science Context Fields ---
    problem_statement = Column(Text)  # e.g., "Predict customer churn"
    dataset_context = Column(Text)    # e.g., "12 months of usage logs"
    target_variable = Column(String, nullable=True) # e.g., "churn_label"
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to datasets
    owner = relationship("User", back_populates="projects")
    datasets = relationship("Dataset", back_populates="project")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String) 
    row_count = Column(Integer)
    columns = Column(JSON) 
    project_id = Column(Integer, ForeignKey("projects.id"))

    project = relationship("Project", back_populates="datasets")