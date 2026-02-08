from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.core.database import engine, Base, get_db
from app.models import project as models
from app.schemas import project as schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aletta AI Engine", version="0.1.0")

# Enable CORS for React (Vite default port is 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5173"], 
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Aletta Backend",
        "features": ["Dataset", "Dashboard", "Aletta Chart"],
        "status": "Ready"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

@app.post("/projects/", response_model = schemas.ProjectResponse)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db)
):
    db_project = models.Project(name = project.name, type = project.type)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project

@app.get("/projects/", response_model = list[schemas.ProjectResponse])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    projects = db.query(models.Project).offset(skip).limit(limit).all()

    return projects
