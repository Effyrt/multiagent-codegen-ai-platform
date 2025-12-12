"""
FastAPI Middleware

Logging, CORS, rate limiting, and other middleware.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta

from .config import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log requests and responses"""
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(f"→ {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"← {request.method} {request.url.path} "
                f"[{response.status_code}] ({duration:.3f}s)"
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(duration)
            response.headers["X-Request-ID"] = str(id(request))
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"✗ {request.method} {request.url.path} "
                f"ERROR: {str(e)} ({duration:.3f}s)"
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_history = {}  # {ip: [timestamps]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Rate limit by IP address"""
        
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        
        # Clean old entries
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(minutes=1)
        
        if client_ip in self.request_history:
            self.request_history[client_ip] = [
                ts for ts in self.request_history[client_ip]
                if ts > cutoff_time
            ]
        else:
            self.request_history[client_ip] = []
        
        # Check rate limit
        if len(self.request_history[client_ip]) >= self.requests_per_minute:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "error_type": "RateLimitError",
                    "detail": f"Maximum {self.requests_per_minute} requests per minute"
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((cutoff_time + timedelta(minutes=1)).timestamp()))
                }
            )
        
        # Add current request
        self.request_history[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.requests_per_minute - len(self.request_history[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


def setup_cors(app):
    """Configure CORS middleware"""
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_middleware(app):
    """Set up all middleware"""
    
    # CORS (must be first)
    setup_cors(app)
    
    # Logging
    app.add_middleware(LoggingMiddleware)
    
    # Rate limiting
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=settings.RATE_LIMIT_PER_MINUTE
        )
    
    logger.info("✅ Middleware configured")
