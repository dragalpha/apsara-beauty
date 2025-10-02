#!/usr/bin/env python3
"""
Deployment-friendly entry point for the Apsara backend.
This script ensures proper Python path setup for imports.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

# Now import and run the app
from main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False,  # Disable reload in production
        log_level="info"
    )
