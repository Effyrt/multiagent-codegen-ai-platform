"""
CodeGen AI - FastAPI Backend

Main application entry point.
"""

import logging
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backend.config import settings, validate_required_settings
from src.backend.middleware import setup_middleware
from src.backend.routes import generation_router, search_router, health_router
from src.backend.models import ErrorResponse
from src.backend.exceptions import CodeGenException

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.LOG_FILE) if Path(settings.LOG_FILE).parent.exists() else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    
    Handles startup and shutdown logic.
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    
    # Validate configuration (warn but don't fail)
    try:
        validate_required_settings()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.warning(f"⚠️  Configuration warning: {e}")
        logger.warning("   Some features may not work without API keys")
    
    # Log configuration
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"OpenAI Model: {settings.OPENAI_MODEL}")
    logger.info(f"Max Iterations: {settings.MAX_ITERATIONS}")
    logger.info(f"Rate Limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    logger.info(f"Caching: {'Enabled' if settings.CACHE_ENABLED else 'Disabled'}")
    logger.info(f"Tool Calling: {'Enabled' if settings.TOOL_CALLING_ENABLED else 'Disabled'}")
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info(f"🛑 Shutting down {settings.APP_NAME}")
    logger.info("=" * 60)


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(CodeGenException)
async def codegen_exception_handler(request: Request, exc: CodeGenException):
    """Handle custom CodeGen exceptions"""
    logger.error(f"CodeGenException: {exc.error_type} - {exc.message}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error=exc.message,
            error_type=exc.error_type
        ).dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            success=False,
            error="Validation failed",
            error_type="ValidationError",
            detail=str(exc.errors())
        ).dict()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(f"Uncaught exception: {type(exc).__name__} - {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error="Internal server error",
            error_type=type(exc).__name__,
            detail=str(exc) if settings.DEBUG else None
        ).dict()
    )


# ============================================================================
# Middleware Setup
# ============================================================================

setup_middleware(app)


# ============================================================================
# Routes
# ============================================================================

# Root endpoint
@app.get("/")
async def root():
    """
    API Root
    
    Welcome endpoint with basic information.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}!",
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
        "generate_code": f"{settings.API_V1_PREFIX}/generate/code",
        "search_code": f"{settings.API_V1_PREFIX}/search/code",
    }


# Include routers
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(generation_router, prefix=settings.API_V1_PREFIX)
app.include_router(search_router, prefix=settings.API_V1_PREFIX)


# ============================================================================
# Run Server (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("🔧 Running in DEVELOPMENT mode")
    logger.info("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
