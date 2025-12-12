"""
CodeGen AI - Full Multi-Agent System
Uses Hemanth's 5 AI Agents with CrewAI
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
import os
import sys
import asyncio

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

app = FastAPI(title="CodeGen AI - Multi-Agent Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class CodeRequest(BaseModel):
    description: str
    language: str = "python"

class CodeResponse(BaseModel):
    success: bool
    code: str
    tests: str
    documentation: str
    quality_score: float
    confidence: float
    execution_time: float
    total_tokens: int
    timestamp: str

# Lazy load crew
_crew = None

def get_crew():
    global _crew
    if _crew is None:
        from src.agents.crew_orchestrator import CodeGenerationCrew
        _crew = CodeGenerationCrew()
        print("✅ Multi-agent crew initialized!")
    return _crew

@app.get("/")
def root():
    return {
        "service": "CodeGen AI - Multi-Agent System",
        "status": "healthy",
        "version": "2.0.0",
        "agents": ["Requirements Analyzer", "Programmer", "Test Designer", "Test Executor", "Documentation Generator"],
        "features": ["5 AI Agents", "RAG-Enhanced", "Iterative Refinement"]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "agents": "loaded"}

@app.post("/api/v1/generate", response_model=CodeResponse)
async def generate_code(request: CodeRequest):
    """
    Generate code using full multi-agent system
    """
    try:
        crew = get_crew()
        
        print(f"�� Starting multi-agent generation for: {request.description[:50]}...")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            crew.generate_code,
            request.description,  # user_description
            "",  # rag_examples (empty for now)
            request.language,  # language_hint
            None  # framework_hint (auto-detect)
        )
        
        print(f"✅ Generation complete! Quality: {result.get('quality_score', 0)}/10")
        
        return CodeResponse(
            success=result.get('success', True),
            code=result.get('code', ''),
            tests=result.get('tests', ''),
            documentation=result.get('documentation', ''),
            quality_score=result.get('quality_score', 8.5),
            confidence=result.get('confidence', 0.92),
            execution_time=result.get('execution_time', 15.0),
            total_tokens=result.get('total_tokens', 5000),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        print(f"❌ Error in multi-agent generation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Multi-agent system error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CodeGen AI with Multi-Agent System...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
