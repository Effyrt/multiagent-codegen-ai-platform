"""
CodeGen AI - Main API (Cloud Run Optimized with Lazy Loading)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
from typing import Optional, Dict
import os

# Load env early
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="CodeGen AI", version="1.0.0-cloud")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚡ LAZY-LOAD ORCHESTRATOR (don't import on startup)
orchestrator = None

def get_orchestrator():
    """Lazy-load orchestrator on first request"""
    global orchestrator
    if orchestrator is None:
        print("🔄 Loading orchestrator on-demand...")
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from orchestrator.orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator()
        print("✅ Orchestrator loaded on-demand")
    return orchestrator

# In-memory storage
active_generations = {}

# ============================================================================
# Models
# ============================================================================

class GenerateRequest(BaseModel):
    description: str
    language: str = "python"
    complexity: str = "medium"

class GenerateResponse(BaseModel):
    generation_id: str
    status: str

# ============================================================================
# Routes
# ============================================================================

@app.get("/")
async def root():
    return {
        "message": "CodeGen AI - Multi-Agent Code Generation", 
        "status": "running",
        "version": "1.0.0-cloud"
    }

@app.get("/health")
async def health():
    """Health check for Cloud Run"""
    return {"status": "healthy", "service": "codegen-ai"}

@app.post("/api/v1/generate", response_model=GenerateResponse)
async def generate_code(request: GenerateRequest):
    """Start code generation"""
    import uuid
    
    gen_id = str(uuid.uuid4())
    
    active_generations[gen_id] = {
        "status": "queued",
        "request": request.dict()
    }
    
    # Start generation in background (lazy-loads orchestrator)
    asyncio.create_task(
        process_generation(gen_id, request)
    )
    
    return GenerateResponse(
        generation_id=gen_id,
        status="queued"
    )

async def process_generation(gen_id: str, request: GenerateRequest):
    """Process generation in background"""
    
    try:
        active_generations[gen_id]["status"] = "processing"
        
        # ⚡ Lazy-load orchestrator here (not on startup!)
        orch = get_orchestrator()
        
        # Use orchestrator to generate code
        result = await orch.generate_code(
            description=request.description,
            language=request.language
        )
        
        active_generations[gen_id]["status"] = "completed"
        active_generations[gen_id]["result"] = result
        
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"❌ Generation failed: {error_msg}")
        print(f"Full traceback:")
        active_generations[gen_id]["status"] = "failed"
        active_generations[gen_id]["error"] = str(e)

@app.get("/api/v1/status/{generation_id}")
async def get_status(generation_id: str):
    """Get generation status"""
    
    if generation_id not in active_generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    return active_generations[generation_id]

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "start_generation":
                # ⚡ Lazy-load orchestrator
                orch = get_orchestrator()
                
                # Generate code and stream updates
                req = GenerateRequest(**data["data"])
                
                async def send_update(msg):
                    await websocket.send_json(msg)
                
                result = await orch.generate_code(
                    description=req.description,
                    language=req.language,
                    websocket_callback=send_update
                )
                
                # Send final result
                await websocket.send_json({
                    "type": "generation_complete",
                    "data": result
                })
            
    except WebSocketDisconnect:
        print(f"Client disconnected: {client_id}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


@app.get("/api/v1/hitl/pending")
async def get_pending_reviews():
    """Get all pending HITL reviews"""
    orch = get_orchestrator()
    pending = orch.hitl_queue.get_pending()
    return {"count": len(pending), "reviews": [vars(r) for r in pending]}

@app.post("/api/v1/hitl/{generation_id}/approve")
async def approve_generation(generation_id: str):
    """Approve a generation in HITL queue"""
    orch = get_orchestrator()
    if orch.hitl_queue.approve(generation_id):
        return {"message": "Approved", "generation_id": generation_id}
    raise HTTPException(status_code=404, detail="Not found in queue")

@app.post("/api/v1/hitl/{generation_id}/reject")
async def reject_generation(generation_id: str):
    """Reject a generation in HITL queue"""
    orch = get_orchestrator()
    if orch.hitl_queue.reject(generation_id):
        return {"message": "Rejected", "generation_id": generation_id}
    raise HTTPException(status_code=404, detail="Not found in queue")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)