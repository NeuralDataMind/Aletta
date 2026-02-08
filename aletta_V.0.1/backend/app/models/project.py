from sqlalchemy import Column, Integer, String, DataTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)   # "Finance", "Engineering", "Analysis"
    created_at = Column(DataTime, default = datetime.utc)

    # Relationship to datasets
    datasets = relationship("Dataset", back_populates="project")


