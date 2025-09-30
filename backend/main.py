from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use absolute import for deployment compatibility
from api import skin_analysis  # , recommendations, auth, products

app = FastAPI(title="Apsara Beauty API")

# Set up CORS (Cross-Origin Resource Sharing)
origins = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
    "http://localhost:3000",  # For local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure 'uploads' directory exists for user-uploaded images
uploads_dir = "uploads"
os.makedirs(uploads_dir, exist_ok=True)

# Serve static files (uploaded images) at /uploads endpoint
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include routers from the api directory
app.include_router(skin_analysis.router)
# app.include_router(recommendations.router)
# app.include_router(auth.router)
# app.include_router(products.router)

@app.get("/", tags=["Root"])
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the Apsara Beauty API"}