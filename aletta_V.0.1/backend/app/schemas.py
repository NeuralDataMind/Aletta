from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str
    problem_statement: str
    dataset_context: str
    target_variable: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
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