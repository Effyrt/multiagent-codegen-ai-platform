"""
Human-in-the-Loop (HITL) Queue System
"""
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os

@dataclass
class HITLRequest:
    """Request waiting for human review"""
    generation_id: str
    description: str
    language: str
    code: str
    tests: str
    quality_score: float
    confidence: float
    reason: str  # Why it needs review
    security_flags: List[str]
    timestamp: str
    status: str = "pending"  # pending, approved, rejected

class HITLQueue:
    """Manages human review queue"""
    
    def __init__(self):
        self.queue: Dict[str, HITLRequest] = {}
        self.queue_file = "hitl_queue.json"
        self._load_queue()
    
    def add_to_queue(
        self,
        generation_id: str,
        description: str,
        language: str,
        code: str,
        tests: str,
        quality_score: float,
        confidence: float,
        reason: str,
        security_flags: List[str] = None
    ) -> HITLRequest:
        """Add generation to HITL queue"""
        
        request = HITLRequest(
            generation_id=generation_id,
            description=description,
            language=language,
            code=code,
            tests=tests,
            quality_score=quality_score,
            confidence=confidence,
            reason=reason,
            security_flags=security_flags or [],
            timestamp=datetime.utcnow().isoformat(),
            status="pending"
        )
        
        self.queue[generation_id] = request
        self._save_queue()
        
        print(f"📋 Added to HITL queue: {generation_id} (Reason: {reason})")
        
        return request
    
    def get_pending(self) -> List[HITLRequest]:
        """Get all pending reviews"""
        return [r for r in self.queue.values() if r.status == "pending"]
    
    def approve(self, generation_id: str) -> bool:
        """Approve a generation"""
        if generation_id in self.queue:
            self.queue[generation_id].status = "approved"
            self._save_queue()
            print(f"✅ Approved: {generation_id}")
            return True
        return False
    
    def reject(self, generation_id: str) -> bool:
        """Reject a generation"""
        if generation_id in self.queue:
            self.queue[generation_id].status = "rejected"
            self._save_queue()
            print(f"❌ Rejected: {generation_id}")
            return True
        return False
    
    def _save_queue(self):
        """Persist queue to disk"""
        try:
            with open(self.queue_file, 'w') as f:
                data = {k: asdict(v) for k, v in self.queue.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save HITL queue: {e}")
    
    def _load_queue(self):
        """Load queue from disk"""
        try:
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.queue[k] = HITLRequest(**v)
                print(f"📋 Loaded {len(self.queue)} items from HITL queue")
        except Exception as e:
            print(f"⚠️ Failed to load HITL queue: {e}")
