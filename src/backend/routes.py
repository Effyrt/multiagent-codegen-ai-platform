"""
API Routes - Integrating All Team Components
Hemanth's Agents + PeiYing's RAG + Om's Caching/Logging
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict
import uuid
import time
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backend.models import (
    CodeGenerationRequest, CodeGenerationResponse,
    CodeSearchRequest, CodeSearchResponse,
    HealthStatus
)

# Health Router
health_router = APIRouter(tags=["health"])

@health_router.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    return HealthStatus(
        status="healthy",
        version="1.0.0",
        openai_status="ok",
        pinecone_status="ok",
        docker_status="ok"
    )

# Generation Router
generation_router = APIRouter(tags=["generation"])

# Store active generations
active_generations: Dict[str, Dict] = {}

# Lazy-load components
_crew = None
_cache = None
_bq = None

def get_crew():
    """Load Hemanth's multi-agent crew"""
    global _crew
    if _crew is None:
        from src.agents.crew_orchestrator import CodeGenerationCrew
        _crew = CodeGenerationCrew()
        print("✅ Loaded Hemanth's agents")
    return _crew

def get_cache():
    """Load Om's Redis cache"""
    global _cache
    if _cache is None:
        try:
            # Try to load from backend_deployed if exists
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend_deployed"))
            from utils.cache import RedisCache
            _cache = RedisCache()
            print("✅ Loaded Om's cache")
        except:
            _cache = None
            print("⚠️ Cache not available")
    return _cache

def get_bq():
    """Load Om's BigQuery logger"""
    global _bq
    if _bq is None:
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend_deployed"))
            from utils.bigquery_logger import BigQueryLogger
            _bq = BigQueryLogger()
            print("✅ Loaded Om's BigQuery")
        except:
            _bq = None
            print("⚠️ BigQuery not available")
    return _bq

@generation_router.post("/generate/code", response_model=CodeGenerationResponse)
async def generate_code(
    request: CodeGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate code using integrated system
    
    Uses:
    - Hemanth's 5-agent CrewAI system
    - PeiYing's RAG retrieval (if enabled)
    - Om's caching and logging
    """
    gen_id = str(uuid.uuid4())
    
    # Check cache (Om's contribution)
    cache = get_cache()
    if cache and cache.enabled and request.use_rag:
        cache_key = f"{request.description}:{request.language}"
        cached = cache.get(cache_key)
        if cached:
            return CodeGenerationResponse(
                success=True,
                code=str(cached),
                quality_score=9.0,
                confidence=1.0,
                metadata={"from_cache": True}
            )
    
    # Start async generation
    active_generations[gen_id] = {"status": "processing", "started_at": time.time()}
    
    background_tasks.add_task(
        process_generation,
        gen_id,
        request
    )
    
    # Return immediate response
    return CodeGenerationResponse(
        success=True,
        code="",
        metadata={"generation_id": gen_id, "status": "processing"}
    )

async def process_generation(gen_id: str, request: CodeGenerationRequest):
    """Process generation in background"""
    try:
        # Use Hemanth's crew
        crew = get_crew()
        
        result = crew.generate_code(
            user_description=request.description,
            language_hint=request.language,
            framework_hint=request.framework
        )
        
        # Use Om's logging
        bq = get_bq()
        if bq and bq.enabled:
            bq.log_generation({
                "gen_id": gen_id,
                "description": request.description,
                "result": result
            })
        
        active_generations[gen_id] = {
            "status": "completed",
            "result": result,
            "completed_at": time.time()
        }
        
    except Exception as e:
        active_generations[gen_id] = {
            "status": "failed",
            "error": str(e)
        }

@generation_router.get("/generate/status/{gen_id}")
async def get_generation_status(gen_id: str):
    """Get generation status"""
    if gen_id not in active_generations:
        raise HTTPException(404, "Generation not found")
    return active_generations[gen_id]

# Search Router
search_router = APIRouter(tags=["search"])

@search_router.post("/search/code", response_model=CodeSearchResponse)
async def search_code(request: CodeSearchRequest):
    """
    Search for similar code using PeiYing's RAG system
    """
    try:
        from src.rag.retriever import retrieve_similar_code
        
        results = retrieve_similar_code(
            query=request.query,
            top_k=request.top_k,
            language=request.language
        )
        
        return CodeSearchResponse(
            success=True,
            query=request.query,
            results=results,
            total_results=len(results)
        )
    except Exception as e:
        return CodeSearchResponse(
            success=False,
            query=request.query,
            error=str(e)
        )

# Compatibility endpoint for Om's frontend
@generation_router.post("/generate", response_model=CodeGenerationResponse)
async def generate_code_compat(
    description: str,
    language: str = "python",
    complexity: str = "medium",
    background_tasks: BackgroundTasks = None
):
    """Compatibility endpoint for frontend"""
    request = CodeGenerationRequest(
        description=description,
        language=language,
        complexity=complexity
    )
    return await generate_code(request, background_tasks or BackgroundTasks())
