from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.core.database import engine, Base, get_db
from app.models import project as models
from app.schemas import project as schemas
import shutil
import os
import pandas as pd
import json
import numpy as np

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
    project_in: schemas.ProjectCreate,
    db: Session = Depends(get_db)
):
    db_project = models.Project(name = project_in.name, type = project_in.type)
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

@app.post("/projects/{project_id}/upload/")
async def upload_dataset(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Verify Project Exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Save File to Disk
    file_location = f"data/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract Metadata using Pandas
    try:
        # Read only the header to be fast
        df = pd.read_csv(file_location, nrows=0)
        columns = df.columns.tolist()

        # Get row count (slightly slower but necessary)
        with open(file_location) as f:
            row_count = sum(1 for line in f) - 1
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {str(e)}")
    
    # Save Record to DB
    db_dataset = models.Dataset(
        filename = file.filename,
        file_path = file_location,
        row_count = row_count,
        columns = columns, # Storing list as JSON
        project_id = project_id
    )
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)

    return {
        "filename": file.filename,
        "columns": columns,
        "row": row_count,
        "status": "Uploaded"
    }

@app.get("/projects/{project_id}/eda/")
async def get_project_eda(
    project_id: int,
    db: Session = Depends(get_db)
):
    # Dataset path
    dataset = db.query(models.Dataset).filter(models.Dataset.project_id == project_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Load Data
    try:
        df = pd.read_csv(dataset.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read file: {str(e)}")
    
    # Calculate "Power BI" Style Status
    summary = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "numeric_summary": df.describe().replace({np.nan: None}).to_dict()
    }

    # Get a sample for the "Data Grid" view
    # Replace NaN with None so JSON doesn't break
    sample_data = df.head(5).replace({np.nan: None}).to_dict(orient="records")

    return {
        "summary": summary,
        "sample": sample_data
    }
