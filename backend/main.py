from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- FIX IS ON THE LINE BELOW ---
# We change "from api" to "from .api" to make it an explicit relative import.
# This tells Python to look for the 'api' folder in the same directory as this file.
# Absolute imports from project root
from backend.api import skin_analysis #, recommendations, auth, products
from backend.api import chatbot, notifications


app = FastAPI(title="Apsara Beauty API")

# Set up CORS (Cross-Origin Resource Sharing)
# This allows your frontend (on Vercel) to make requests to this backend (on Render)
origins_env = os.getenv("FRONTEND_URL", "http://localhost:3000")
origins = [o.strip().rstrip('/') for o in origins_env.split(",") if o.strip()] + ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https:\/\/([a-z0-9-]+)\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the 'uploads' directory if it doesn't exist
# This is where user-uploaded images will be stored
uploads_dir = os.getenv("UPLOAD_DIR", "uploads")
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

# Serve static files (the uploaded images) from the /uploads endpoint
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# Include the routers from the api directory
app.include_router(skin_analysis.router)
app.include_router(chatbot.router, tags=["Chatbot"])
app.include_router(notifications.router, tags=["Notifications"])
# app.include_router(recommendations.router)
# app.include_router(auth.router)
# app.include_router(products.router)


@app.get("/", tags=["Root"])
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the Apsara Beauty API"}