"""
API Routes

All API endpoint routers.
"""

from .generation import router as generation_router
from .search import router as search_router
from .health import router as health_router

__all__ = [
    "generation_router",
    "search_router",
    "health_router",
]
