from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str
    type: str # e.g., "Finance"

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int # Vital for ownership logic
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