from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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