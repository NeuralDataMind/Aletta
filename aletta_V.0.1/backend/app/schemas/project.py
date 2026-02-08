from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str
    type: str # e.g., "Finance"

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Dataset Schemas ---
class DatasetResponse(BaseModel):
    id: int
    filename: str
    row_count: int
    columns: List[str]
    class Config:
        from_attributes = True