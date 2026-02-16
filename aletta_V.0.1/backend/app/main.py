from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.database import engine, Base, get_db
from app.models import project as models
from app.core.ai import get_groq_analysis
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.project import User
from app.api import auth
from app import schemas
import shutil
import os
import pandas as pd
import json
import numpy as np

# Note: We will add 'eda_tools' and 'ml_tools' imports later when we build them.

models.Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

app = FastAPI(title="Aletta Data Science Hub", version="0.2.0")
app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
async def root():
    return {"message": "Aletta Data Engine Ready", "modes": ["Analysis", "Model", "Dashboard"]}

@app.post("/projects/", response_model=schemas.ProjectResponse)
def create_project(
    project_in: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Updated to save Metadata
    db_project = models.Project(
        name=project_in.name,
        problem_statement=project_in.problem_statement,
        dataset_context=project_in.dataset_context,
        target_variable=project_in.target_variable,
        owner_id=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=list[schemas.ProjectResponse])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = db.query(models.Project).filter(models.Project.owner_id == current_user.id).offset(skip).limit(limit).all()
    return projects

@app.post("/projects/{project_id}/upload/")
async def upload_dataset(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file_location = f"data/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        df = pd.read_csv(file_location, nrows=0)
        columns = df.columns.tolist()
        with open(file_location) as f:
            row_count = sum(1 for line in f) - 1
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {str(e)}")
    
    db_dataset = models.Dataset(
        filename=file.filename,
        file_path=file_location,
        row_count=row_count,
        columns=columns,
        project_id=project_id
    )
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return {"status": "Uploaded", "columns": columns}

@app.post("/projects/{project_id}/analyze")
async def analyze_project(
    project_id: int,
    mode: str = Body(..., embed=True), # "analysis", "model", or "dashboard"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch Project & Metadata
    project = db.query(models.Project).filter(
        models.Project.id == project_id, 
        models.Project.owner_id == current_user.id
    ).first()
    
    dataset = db.query(models.Dataset).filter(models.Dataset.project_id == project_id).first()
    if not dataset or not project:
        raise HTTPException(status_code=404, detail="Project or Dataset not found")
    
    df = pd.read_csv(dataset.file_path)
    
    # 2. MODE SWITCHING LOGIC
    # Depending on the mode, we will call different "Tools" in the future
    
    action_report = {}
    if mode == "analysis":
        # TODO: Call eda_tools.perform_cleaning(df)
        action_report = {"status": "EDA Complete", "missing_values_handled": True}
        system_instruction = "You are a Data Engineer. Explain the cleaning steps and data quality."
        
    elif mode == "model":
        # TODO: Call ml_tools.train_baseline(df, project.target_variable)
        action_report = {"status": "Baseline Model Trained", "algorithm": "RandomForest", "accuracy": 0.88}
        system_instruction = "You are an ML Engineer. Explain the model selection and performance."
        
    elif mode == "dashboard":
        action_report = {"status": "Dashboard Configured", "charts": ["Correlation Heatmap", "Distribution Plot"]}
        system_instruction = "You are a BI Specialist. Suggest key insights for the dashboard."
    
    else:
        raise HTTPException(status_code=400, detail="Invalid Mode. Use 'analysis', 'model', or 'dashboard'.")

    # 3. AI AGENT EXPLANATION
    system_prompt = f"""
    {system_instruction}
    
    PROJECT METADATA:
    Problem: {project.problem_statement}
    Context: {project.dataset_context}
    Target: {project.target_variable}
    
    TOOL OUTPUTS:
    {action_report}
    
    Explain the results to the user based on their problem statement.
    """
    
    # Simple Context for now
    data_sample = df.describe().to_string()
    
    ai_response = get_groq_analysis(system_prompt, data_sample)
    
    return {
        "mode": mode,
        "tool_results": action_report,
        "ai_insight": ai_response
    }