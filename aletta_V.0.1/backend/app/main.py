from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.database import engine, Base, get_db
from app.models import project as models
from app.core.ai import get_groq_analysis
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.project import User
from app.api import auth
from app import schemas
from app.services import eda_tools, ml_tools  # <--- NEW: Import the Auto-Pilot Engine
import shutil
import os
import pandas as pd
import json
import numpy as np

# Create Tables
models.Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

app = FastAPI(title="Aletta Data Science Hub", version="0.2.0")
app.include_router(auth.router)

# CORS (Allow Frontend Access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DEPENDENCIES ---
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

# --- ROUTES ---

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

@app.get("/projects/{project_id}/eda/")
async def get_project_eda(project_id: int, db: Session = Depends(get_db)):
    dataset = db.query(models.Dataset).filter(models.Dataset.project_id == project_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        df = pd.read_csv(dataset.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read file: {str(e)}")
    
    # Safe summary for JSON
    summary = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "numeric_summary": df.describe().replace({np.nan: None}).to_dict()
    }
    sample_data = df.head(5).replace({np.nan: None}).to_dict(orient="records")

    return {"summary": summary, "sample": sample_data}

# --- 🧠 THE CORE INTELLIGENCE ENDPOINT ---
@app.post("/projects/{project_id}/analyze")
async def analyze_project(
    project_id: int,
    mode: str = Body(..., embed=True), # Expecting: "analysis", "model", or "dashboard"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verification
    project = db.query(models.Project).filter(
        models.Project.id == project_id, 
        models.Project.owner_id == current_user.id
    ).first()
    
    dataset = db.query(models.Dataset).filter(models.Dataset.project_id == project_id).first()
    
    if not project or not dataset:
        raise HTTPException(status_code=404, detail="Project or Data not found.")
    
    # Load Data
    df = pd.read_csv(dataset.file_path)
    
    action_report = {}
    system_instruction = ""
    
    # 2. MODE EXECUTION
    
    if mode == "analysis":
        # --- AUTO-PILOT ENGAGED ---
        # 1. Run the Smart Pipeline (Cleaning + Engineering + Scaling)
        processed_df, engineering_log = eda_tools.run_auto_prep(df)
        
        # 2. Save the result so ML can use it later
        output_filename = dataset.filename.replace(".csv", "_engineered.csv")
        output_path = dataset.file_path.replace(".csv", "_engineered.csv")
        processed_df.to_csv(output_path, index=False)
        
        action_report = {
            "status": "Success",
            "original_shape": [dataset.row_count, len(dataset.columns)],
            "final_shape": processed_df.shape,
            "new_file": output_filename,
            "pipeline_log": engineering_log
        }
        
        system_instruction = """
        You are Aletta, an Autonomous Data Engineer.
        You have successfully executed a Python pipeline to clean and feature engineer the user's dataset.
        
        Review the 'pipeline_log' below. 
        Summarize the actions taken (e.g., "I imputed missing values..." or "I extracted date features...").
        Explain WHY these steps prepare the data for the user's specific 'Problem Statement'.
        """
        
    elif mode == "model":
        #1. LOCATE ENGINEERED DATA
        # We MUST use the file created by "Analysis Mode" (it has numbers, not strings)
        engineered_path = dataset.file_path.replace(".csv", "_engineered.csv")

        if not os.path.exists(engineered_path):
            raise HTTPException(status_code=400, detail="Please run 'Analysis' mode first to clean and encode the data.")
        
        # Load data
        df_clean = pd.read_csv(engineered_path)

        # 2. RUN MODELING ENGINE
        if not project.target_variable:
            raise HTTPException(status_code=400, detail="Target Variable is missing. Please update project settings.")
        
        try:
            modeling_report = ml_tools.run_auto_modeling(
                df_clean,
                project.target_variable,
                project.id
            )
            action_report = modeling_report
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Modeling Failed: {str(e)}")
        
        # 3. AI EXPLANATION
        system_instruction = f"""
        You are an Expert Machine Learning Engineer.
        You have just trained a model to predict: '{project.target_variable}'.
        
        MODELING REPORT:
        {json.dumps(modeling_report, indent=2)}
        
        TASK:
        1. Identify the 'Best Model' and its score.
        2. Explain the 'Top Features' (Which columns are most important?).
        3. Explain what this means for the user (e.g., "This means we can predict species with 95% accuracy").
        """
        
    elif mode == "dashboard":
        # Placeholder for Phase 3
        action_report = {"status": "Pending Dashboard Engine"}
        system_instruction = "You are a BI Specialist. Suggest key charts."
    
    else:
        raise HTTPException(status_code=400, detail="Invalid Mode. Use 'analysis', 'model', or 'dashboard'.")

    # 3. AI EXPLANATION
    system_prompt = f"""
    {system_instruction}
    
    PROJECT METADATA:
    Problem: {project.problem_statement}
    Context: {project.dataset_context}
    
    TOOL EXECUTION LOG (Ground Truth):
    {json.dumps(action_report, indent=2)}
    
    Report to the user in a professional, "Done-for-you" tone.
    """
    
    # We send a small sample of the *processed* data if available, else raw
    if mode == "analysis":
        data_context = processed_df.describe().to_string()
    else:
        data_context = df.describe().to_string()
    
    ai_response = get_groq_analysis(system_prompt, data_context)
    
    return {
        "mode": mode,
        "tool_results": action_report,
        "ai_insight": ai_response
    }

@app.get("/projects/{project_id}/download/{file_type}")
async def download_dataset(
    project_id: int,
    file_type: str, # Options: "raw", "engineered", "model" <--- NEW OPTION
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. SECURITY: Verify Ownership
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.owner_id == current_user.id
    ).first()
    
    dataset = db.query(models.Dataset).filter(models.Dataset.project_id == project_id).first()
    
    if not project or not dataset:
        raise HTTPException(status_code=404, detail="Project not found.")

    # 2. DETERMINE FILE PATH
    file_path = dataset.file_path
    filename = dataset.filename

    if file_type == "engineered":
        file_path = dataset.file_path.replace(".csv", "_engineered.csv")
        filename = dataset.filename.replace(".csv", "_engineered.csv")
    
    elif file_type == "model":  # <--- NEW LOGIC
        # The ML Tool saves models as "data/models/project_{id}.pkl"
        file_path = f"data/models/project_{project_id}.pkl"
        filename = f"model_project_{project_id}.pkl"
        
        if not os.path.exists(file_path):
             raise HTTPException(status_code=400, detail="Model not found. Please run 'Model' mode first.")

    # 3. SERVE FILE
    return FileResponse(
        path=file_path, 
        filename=filename, 
        media_type='application/octet-stream' # Standard for binary files like .pkl
    )

@app.delete("/projects/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify the project exist or not
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.owner_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized.")
    
    # Find the associated dataset
    dataset = db.query(models.Dataset).filter(models.Dataset.project_id == project_id).first()

    # Nuke the physical File 
    if dataset:
        try:
            raw_path = dataset.file_path
            engineered_path = raw_path.replace(".csv", "_engineered.csv")
            model_path = f"data/models/project_{project_id}.pkl"

            files_to_delete = [raw_path, engineered_path, model_path]

            for file_path in files_to_delete:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted physical file: {file_path}")
        except Exception as e:
            print(f"Warning: Could not delete some physcial files: {e}")

    # Nuke the Project Record
    db.delete(project)
    db.commit()

    # 204 No Content means success, but nothing to return 
    return None