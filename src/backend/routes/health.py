"""
Health Check Endpoints

System health and status monitoring.
"""

import time
import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime

from ..models import HealthStatus
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])

# Track app start time
app_start_time = time.time()
total_requests = 0


@router.get("", response_model=HealthStatus)
async def health_check():
    """
    Check system health and service status
    
    Returns overall health status and individual service checks.
    """
    global total_requests
    total_requests += 1
    
    errors = []
    
    # Check OpenAI
    openai_status = "not_configured"
    if settings.OPENAI_API_KEY:
        try:
            # Simple check - if key is set, assume OK
            # Could add actual API call here
            openai_status = "ok"
        except Exception as e:
            openai_status = "error"
            errors.append(f"OpenAI: {str(e)}")
    else:
        errors.append("OpenAI API key not configured")
    
    # Check Pinecone
    pinecone_status = "not_configured"
    if settings.PINECONE_API_KEY and settings.PINECONE_ENVIRONMENT:
        try:
            # Simple check - if keys are set, assume OK
            # Could add actual API call here
            pinecone_status = "ok"
        except Exception as e:
            pinecone_status = "error"
            errors.append(f"Pinecone: {str(e)}")
    else:
        errors.append("Pinecone configuration incomplete")
    
    # Check Docker
    docker_status = "not_available"
    if settings.DOCKER_ENABLED:
        try:
            import docker
            client = docker.from_env()
            client.ping()
            docker_status = "ok"
        except Exception as e:
            docker_status = "error"
            errors.append(f"Docker: {str(e)}")
    
    # Determine overall status
    if openai_status == "ok" and pinecone_status == "ok":
        status = "healthy"
    elif openai_status in ["ok", "not_configured"] or pinecone_status in ["ok", "not_configured"]:
        status = "degraded"
    else:
        status = "unhealthy"
    
    uptime = time.time() - app_start_time
    
    return HealthStatus(
        status=status,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        openai_status=openai_status,
        pinecone_status=pinecone_status,
        docker_status=docker_status,
        uptime=uptime,
        total_requests=total_requests,
        errors=errors
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"status": "ok", "message": "pong", "timestamp": datetime.utcnow()}


@router.get("/version")
async def version():
    """Get API version information"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
    }
