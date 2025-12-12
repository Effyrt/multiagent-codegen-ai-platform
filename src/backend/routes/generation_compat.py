"""
Compatibility endpoints for Om's frontend
"""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import uuid
import asyncio
from typing import Dict

router_compat = APIRouter(tags=["Compatibility"])

# Store generations
active_gens: Dict[str, dict] = {}

class SimpleGenRequest(BaseModel):
    description: str
    language: str = "python"

@router_compat.post("/generate")
async def generate_compat(request: SimpleGenRequest, background_tasks: BackgroundTasks):
    """Om's frontend compatibility - returns generation_id"""
    gen_id = str(uuid.uuid4())
    active_gens[gen_id] = {"status": "queued", "request": request.dict()}
    
    # Process in background
    background_tasks.add_task(process_gen, gen_id, request)
    
    return {"generation_id": gen_id, "status": "queued"}

async def process_gen(gen_id: str, request: SimpleGenRequest):
    """Process generation"""
    try:
        active_gens[gen_id]["status"] = "processing"
        
        from ..models import CodeGenerationRequest
        from .generation import generate_code
        
        full_request = CodeGenerationRequest(
            description=request.description,
            language=request.language
        )
        
        result = await generate_code(full_request)
        active_gens[gen_id]["status"] = "completed"
        active_gens[gen_id]["result"] = result.dict()
        
    except Exception as e:
        active_gens[gen_id]["status"] = "failed"
        active_gens[gen_id]["error"] = str(e)

@router_compat.get("/status/{gen_id}")
async def get_status_compat(gen_id: str):
    """Get generation status"""
    if gen_id not in active_gens:
        return {"status": "not_found"}
    return active_gens[gen_id]
