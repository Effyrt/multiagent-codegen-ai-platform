"""Minimal CodeGen AI for Cloud Run"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI(title="CodeGen AI - Cloud")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    description: str
    language: str = "python"

@app.get("/")
def root():
    return {"message": "CodeGen AI is LIVE on Cloud Run!", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.0-cloud"}

@app.post("/api/v1/generate")
async def generate(request: GenerateRequest):
    return {
        "generation_id": "test-123",
        "status": "queued",
        "message": "Cloud deployment successful! Full features coming soon."
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
