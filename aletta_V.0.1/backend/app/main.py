from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Body, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import shutil
import os
import pandas as pd
import json
import numpy as np

# Internal Imports
from app.core.database import engine, Base, get_db
from app.models import project as models
from app.core.ai import get_groq_analysis
from app.core.security import SECRET_KEY, ALGORITHM, pwd_context
from app.models.project import User
from app import schemas
from app.services import eda_tools, ml_tools 

# Initialize Database Tables
models.Base.metadata.create_all(bind=engine)

# OAuth2 Scheme - Fixed URL to match React frontend requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

app = FastAPI(title="Aletta Data Science Hub", version="0.2.0")

# --- CORS CONFIGURATION ---
# Necessary for your Vite/React frontend (5173) to communicate with FastAPI (8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTHENTICATION UTILITIES ---

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise credentials_exception
    except JWTError: raise credentials_exception
        
    user = db.query(User).filter(User.email == username).first()
    if user is None: raise credentials_exception
    return user

# --- AUTHENTICATION ROUTES (Prefix matches React api.js) ---
@app.post("/api/auth/register")
async def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = pwd_context.hash(user_in.password)
    # Automatically fallback to email if username is left blank
    actual_username = user_in.username if user_in.username else user_in.email
    
    new_user = User(email=user_in.email, hashed_password=hashed_pwd, username=actual_username)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@app.post("/api/auth/login")
async def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not pwd_context.verify(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# Get User profile details
@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the profile of the currently authenticated user."""
    return current_user

# --- PROJECT MANAGEMENT ROUTES ---

@app.get("/")
async def root():
    return {
        "message": "Aletta AI Engine Ready", 
        "modes": ["Analysis (Auto-EDA)", "Model (ML Building)", "Dashboard (BI)"]
    }

@app.post("/projects/", response_model=schemas.ProjectResponse)
def create_project(
    project_in: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
def read_projects(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return db.query(models.Project).filter(models.Project.owner_id == current_user.id).offset(skip).limit(limit).all()

@app.post("/projects/{project_id}/upload/")
async def upload_dataset(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    os.makedirs("data", exist_ok=True)
    file_location = f"data/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        df = pd.read_csv(file_location)
        columns = df.columns.tolist()
        row_count = len(df)
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

@app.get("/projects/{project_id}/eda/")
async def get_project_eda(project_id: int, db: Session = Depends(get_db)):
    dataset = db.query(models.Dataset).filter(models.Dataset.project_id == project_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        df = pd.read_csv(dataset.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read file: {str(e)}")
    
    summary = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "numeric_summary": df.describe().replace({np.nan: None}).to_dict()
    }
    sample_data = df.head(5).replace({np.nan: None}).to_dict(orient="records")

    return {"summary": summary, "sample": sample_data}

# --- 🧠 CORE INTELLIGENCE ENGINE ---

@app.post("/projects/{project_id}/analyze")
async def analyze_project(
    project_id: int,
    mode: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(models.Project).filter(
        models.Project.id == project_id, 
        models.Project.owner_id == current_user.id
    ).first()
    
    dataset = db.query(models.Dataset).filter(models.Dataset.project_id == project_id).first()
    
    if not project or not dataset:
        raise HTTPException(status_code=404, detail="Project or Data not found.")
    
    df = pd.read_csv(dataset.file_path)
    action_report = {}
    system_instruction = ""
    
    if mode == "analysis":
        processed_df, engineering_log = eda_tools.run_auto_prep(df, project.target_variable)
        output_path = dataset.file_path.replace(".csv", "_engineered.csv")
        processed_df.to_csv(output_path, index=False)
        
        # Extract the first 4 rows and convert to a JSON-safe dictionary
        sample_data = processed_df.head(4).fillna("").to_dict(orient="records")
        
        action_report = {
            "status": "Success",
            "original_shape": [dataset.row_count, len(dataset.columns)],
            "final_shape": processed_df.shape,
            "pipeline_log": engineering_log,
            "engineered_sample": sample_data  # <-- This is what the React table requires
        }
        system_instruction = "Summarize the cleaning and engineering steps based on the log."
        
    elif mode == "model":
        engineered_path = dataset.file_path.replace(".csv", "_engineered.csv")
        if not os.path.exists(engineered_path):
            raise HTTPException(status_code=400, detail="Run 'Analysis' mode first.")
        
        df_clean = pd.read_csv(engineered_path)
        modeling_report = ml_tools.run_auto_modeling(df_clean, project.target_variable, project.id)
        action_report = modeling_report
        system_instruction = "Explain the model accuracy and feature importance."
        
    else:
        raise HTTPException(status_code=400, detail="Invalid Mode.")

    system_prompt = f"{system_instruction}\n\nProblem: {project.problem_statement}\nLog: {json.dumps(action_report)}"
    ai_response = get_groq_analysis(system_prompt, df.describe().to_string())
    
    return {"mode": mode, "tool_results": action_report, "ai_insight": ai_response}

# --- FILE OPERATIONS ---

@app.get("/projects/{project_id}/download/{file_type}")
async def download_dataset(
    project_id: int,
    file_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.owner_id == current_user.id
    ).first()
    dataset = db.query(models.Dataset).filter(models.Dataset.project_id == project_id).first()
    
    if not project or not dataset:
        raise HTTPException(status_code=404, detail="Not found.")

    file_path = dataset.file_path
    if file_type == "engineered":
        file_path = dataset.file_path.replace(".csv", "_engineered.csv")
    elif file_type == "model":
        file_path = f"data/models/project_{project_id}.pkl"
        
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing.")

    return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type='application/octet-stream')

@app.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Unauthorized.")
    
    dataset = db.query(models.Dataset).filter(models.Dataset.project_id == project_id).first()
    if dataset:
        for suffix in ["", "_engineered.csv"]:
            path = dataset.file_path.replace(".csv", suffix)
            if os.path.exists(path): os.remove(path)
        model_path = f"data/models/project_{project_id}.pkl"
        if os.path.exists(model_path): os.remove(model_path)

    db.delete(project)
    db.commit()
    return None