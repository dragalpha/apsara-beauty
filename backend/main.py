# backend/main.py
# ---
# This is the entry point for the FastAPI backend.
# Key changes for deployment:
# 1. Added CORS Middleware to allow requests from our deployed frontend.
# 2. Added StaticFiles to serve the images stored in the 'uploads' directory.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import your API routers
from api import skin_analysis #, recommendations, auth, products

# --- App Initialization ---
app = FastAPI(
    title="Apsara API",
    description="API for the Apsara AI Skincare Recommendation Platform",
    version="1.0.0"
)

# --- CORS (Cross-Origin Resource Sharing) ---
# This is crucial for security. It tells the backend to only accept
# requests from your specific frontend URL in production.

# Get the frontend URL from environment variables.
# For development, we can default to localhost.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

origins = [
    FRONTEND_URL,
    # You can add more origins here if needed, e.g., a staging environment
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],
)


# --- Static File Serving ---
# This line makes the 'uploads' directory publicly accessible.
# So, a file at 'uploads/image.jpg' can be accessed from
# http://your-backend-url.com/uploads/image.jpg
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# --- API Routers ---
# Include the routers from your api directory
app.include_router(skin_analysis.router, prefix="/api/skin", tags=["Skin Analysis"])
# app.include_router(recommendations.router, prefix="/api/recs", tags=["Recommendations"])
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(products.router, prefix="/api/products", tags=["Products"])


# --- Root Endpoint ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Apsara API! 🌸"}
