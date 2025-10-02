from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
# Try to load .env file if it exists, but don't fail if it doesn't
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Add current directory to Python path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import skin_analysis_unified, chatbot
from database.connection import init_db

app = FastAPI(title="Apsara Beauty API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    await init_db()

# Mount uploads directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(skin_analysis_unified.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(chatbot.router, prefix="/api/chat", tags=["chat"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"detail": str(exc.detail)}, exc.status_code


@app.get("/", tags=["Root"])
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the Apsara Beauty API"}