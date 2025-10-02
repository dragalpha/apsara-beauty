"""API routers for the Apsara backend."""

"""
Backend package initializer for Apsara.

All imports within backend code should be absolute from the project root,
enabled by setting PYTHONPATH="." in the environment.
"""

from .skin_analysis_unified import router as skin_analysis_unified_router
from .chatbot import router as chatbot_router
from .notifications import router as notifications_router

__all__ = [
    "skin_analysis_unified_router",
    "chatbot_router",
    "notifications_router"
]

