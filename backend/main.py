from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

load_dotenv()

# Use absolute imports
from api import skin_analysis, recommendations, auth, products
from database.connection import init_db

app = FastAPI(title="Apsara Beauty API")

# Updated CORS setup
origins = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
    "https://your-frontend-domain.vercel.app",  # Add your actual domain
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
async def startup():
    await init_db()

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Create uploads directory
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(skin_analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Apsara Beauty API"}