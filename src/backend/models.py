"""
API Request/Response Models

Pydantic models for API validation.
"""

from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# ============================================================================
# Request Models
# ============================================================================

class CodeGenerationRequest(BaseModel):
    """Request model for code generation endpoint"""
    
    description: str = Field(
        min_length=10,
        max_length=2000,
        description="Natural language description of code to generate"
    )
    language: Literal["python", "javascript"] = Field(
        default="python",
        description="Target programming language"
    )
    framework: Optional[str] = Field(
        default=None,
        description="Target framework (fastapi, flask, django, express, etc.)"
    )
    complexity: Literal["simple", "medium", "complex"] = Field(
        default="medium",
        description="Expected complexity level"
    )
    include_tests: bool = Field(
        default=True,
        description="Whether to generate tests"
    )
    include_docs: bool = Field(
        default=True,
        description="Whether to generate documentation"
    )
    use_rag: bool = Field(
        default=True,
        description="Whether to use RAG for code examples"
    )
    use_tools: bool = Field(
        default=True,
        description="Whether to enable tool calling for agents"
    )
    
    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description content"""
        # Check for suspicious patterns
        suspicious_patterns = ["exec(", "eval(", "import os", "__import__"]
        for pattern in suspicious_patterns:
            if pattern in v.lower():
                raise ValueError(f"Suspicious pattern detected: {pattern}")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "description": "Create a FastAPI endpoint for user registration with email validation and password hashing",
                    "language": "python",
                    "framework": "fastapi",
                    "complexity": "medium",
                    "include_tests": True,
                    "include_docs": True,
                    "use_rag": True,
                    "use_tools": True
                }
            ]
        }
    }


class CodeSearchRequest(BaseModel):
    """Request model for code search endpoint"""
    
    query: str = Field(
        min_length=3,
        max_length=500,
        description="Search query"
    )
    language: Optional[str] = Field(
        default=None,
        description="Filter by language"
    )
    framework: Optional[str] = Field(
        default=None,
        description="Filter by framework"
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of results to return"
    )


# ============================================================================
# Response Models
# ============================================================================

class CodeExample(BaseModel):
    """Model for a code example"""
    
    code: str
    language: str
    framework: Optional[str] = None
    source: str
    complexity: Optional[str] = None
    similarity_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestResults(BaseModel):
    """Model for test execution results"""
    
    passed: int = 0
    failed: int = 0
    errors: int = 0
    pass_rate: float = 0.0
    failures: List[Dict[str, str]] = Field(default_factory=list)
    execution_time: float = 0.0


class ToolUsage(BaseModel):
    """Model for tool usage tracking"""
    
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    success: bool = True
    latency: float = 0.0
    error: Optional[str] = None


class AgentMetrics(BaseModel):
    """Model for agent execution metrics"""
    
    agent_name: str
    execution_time: float
    token_usage: Dict[str, int] = Field(default_factory=dict)
    iterations: int = 1
    success: bool = True
    tools_used: List[ToolUsage] = Field(default_factory=list)


class CodeGenerationResponse(BaseModel):
    """Response model for code generation endpoint"""
    
    success: bool
    code: Optional[str] = None
    tests: Optional[str] = None
    documentation: Optional[str] = None
    
    # Quality Metrics
    quality_score: Optional[float] = None
    confidence: Optional[float] = None
    test_results: Optional[TestResults] = None
    
    # Execution Metrics
    iterations_used: int = 1
    execution_time: float = 0.0
    total_tokens: int = 0
    
    # Agent Details
    agent_metrics: List[AgentMetrics] = Field(default_factory=list)
    
    # Error Info (if failed)
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "code": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\nasync def root():\n    return {'message': 'Hello World'}",
                    "tests": "import pytest\n\ndef test_root():\n    assert True",
                    "documentation": "# FastAPI Hello World\n\n## Installation\n...",
                    "quality_score": 8.5,
                    "confidence": 0.92,
                    "test_results": {
                        "passed": 5,
                        "failed": 0,
                        "errors": 0,
                        "pass_rate": 1.0,
                        "execution_time": 1.2
                    },
                    "iterations_used": 2,
                    "execution_time": 15.3,
                    "total_tokens": 2450
                }
            ]
        }
    }


class CodeSearchResponse(BaseModel):
    """Response model for code search endpoint"""
    
    success: bool
    query: str
    results: List[CodeExample] = Field(default_factory=list)
    total_results: int = 0
    search_time: float = 0.0
    error: Optional[str] = None


class HealthStatus(BaseModel):
    """Model for health check status"""
    
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Service Status
    openai_status: Literal["ok", "error", "not_configured"]
    pinecone_status: Literal["ok", "error", "not_configured"]
    docker_status: Literal["ok", "error", "not_available"]
    
    # System Info
    uptime: float = 0.0
    total_requests: int = 0
    cache_hit_rate: Optional[float] = None
    
    # Errors
    errors: List[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error response"""
    
    success: bool = False
    error: str
    error_type: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
