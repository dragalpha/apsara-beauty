"""API routers for the Apsara backend."""

"""
Backend package initializer for Apsara.

All imports within backend code should be absolute from the project root,
enabled by setting PYTHONPATH="." in the environment.
"""

from .skin_analysis import router as skin_analysis_router
from .skin_analysis_v2 import router as skin_analysis_v2_router
from .notifications import router as notifications_router

__all__ = [
    "skin_analysis_router",
    "skin_analysis_v2_router",
    "notifications_router"
]

