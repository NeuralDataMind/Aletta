from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)   # "Finance", "Engineering", "Analysis"
    created_at = Column(DateTime, default = datetime.utcnow)

    # Relationship to datasets
    datasets = relationship("Dataset", back_populates="project")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String) # where the file will be saved (CSV)
    row_count = Column(Integer)
    columns = Column(JSON) # Stores list of column names: ["date", "sales", ...]
    project_id = Column(Integer, ForeignKey("projects.id"))

    project = relationship("Project", back_populates="datasets")