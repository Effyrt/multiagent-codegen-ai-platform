"""
Backend Configuration - Complete
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App Info
    APP_NAME: str = "CodeGen AI"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Multi-Agent Code Generation Platform"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.2
    OPENAI_MAX_TOKENS: int = 4000
    
    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")
    PINECONE_INDEX_NAME: str = "codegen-ai-embeddings"
    
    # Agent
    MAX_ITERATIONS: int = 3
    AGENT_TIMEOUT: int = 30
    
    # Features
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 10
    CACHE_ENABLED: bool = True
    CACHE_TTL_HOURS: int = 24
    DOCKER_ENABLED: bool = True
    DOCKER_TIMEOUT: int = 10
    TOOL_CALLING_ENABLED: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/backend.log"
    
    model_config = {"extra": "allow", "env_file": ".env"}

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

def validate_required_settings():
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY required")
    return True
