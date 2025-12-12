"""
Enterprise-Grade BigQuery Analytics System
- Batch inserts for efficiency
- Multiple tables (generations, agents, costs)
- Partitioned tables for performance
- Error handling with retries
- Thread-safe operations
"""

from google.cloud import bigquery
from google.api_core import retry
import os
from datetime import datetime
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import threading
import queue
import time

@dataclass
class GenerationLog:
    """Schema for code_generations table"""
    generation_id: str
    user_id: Optional[str]
    description: str
    language: str
    complexity: str
    quality_score: float
    quality_tier: str
    duration_seconds: float
    tokens_used: int
    cost_usd: float
    cached: bool
    rag_examples_used: int
    iterations: int
    test_pass_rate: float
    code_length: int
    error_occurred: bool
    error_message: Optional[str]
    timestamp: str

@dataclass
class AgentLog:
    """Schema for agent_performance table"""
    execution_id: str
    generation_id: str
    agent_name: str
    status: str
    duration_seconds: float
    tokens_used: int
    model_used: str
    success: bool
    error_message: Optional[str]
    timestamp: str

class BigQueryLogger:
    """Production BigQuery logger with batching and retry"""
    
    def __init__(self, batch_size: int = 10, flush_interval: int = 30):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        try:
            self.client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))
            self.project_id = os.getenv("GCP_PROJECT_ID")
            self.dataset_id = "codegen_analytics"
            
            self.generations_table = f"{self.project_id}.{self.dataset_id}.code_generations"
            self.agents_table = f"{self.project_id}.{self.dataset_id}.agent_performance"
            
            # Batch queues
            self.generation_queue = queue.Queue()
            self.agent_queue = queue.Queue()
            
            # Start background flusher
            self._start_background_flusher()
            
            print("✅ BigQuery analytics connected (enterprise mode)")
            self.enabled = True
            
        except Exception as e:
            print(f"⚠️ BigQuery not available: {e}")
            self.enabled = False
    
    def log_generation(
        self,
        generation_id: str,
        description: str,
        language: str,
        quality_score: float,
        duration: float,
        tokens_used: int,
        cost: float,
        cached: bool = False,
        rag_examples: int = 0,
        iterations: int = 0,
        code_length: int = 0,
        test_pass_rate: float = 0.0,
        error: Optional[str] = None
    ):
        """Log code generation with full metrics"""
        
        if not self.enabled:
            return
        
        quality_tier = self._get_quality_tier(quality_score)
        complexity = self._infer_complexity(description)
        
        log = GenerationLog(
            generation_id=generation_id,
            user_id=None,
            description=description,
            language=language,
            complexity=complexity,
            quality_score=quality_score,
            quality_tier=quality_tier,
            duration_seconds=duration,
            tokens_used=tokens_used,
            cost_usd=cost,
            cached=cached,
            rag_examples_used=rag_examples,
            iterations=iterations,
            test_pass_rate=test_pass_rate,
            code_length=code_length,
            error_occurred=error is not None,
            error_message=error,
            timestamp=datetime.utcnow().isoformat()
        )
        
        self.generation_queue.put(asdict(log))
        
        if self.generation_queue.qsize() >= self.batch_size:
            self._flush_generations()
    
    def log_agent_execution(
        self,
        generation_id: str,
        agent_name: str,
        duration: float,
        tokens_used: int,
        model: str,
        success: bool,
        error: Optional[str] = None
    ):
        """Log individual agent performance"""
        
        if not self.enabled:
            return
        
        log = AgentLog(
            execution_id=str(uuid.uuid4()),
            generation_id=generation_id,
            agent_name=agent_name,
            status="success" if success else "failed",
            duration_seconds=duration,
            tokens_used=tokens_used,
            model_used=model,
            success=success,
            error_message=error,
            timestamp=datetime.utcnow().isoformat()
        )
        
        self.agent_queue.put(asdict(log))
        
        if self.agent_queue.qsize() >= self.batch_size:
            self._flush_agents()
    
    @retry.Retry(predicate=retry.if_exception_type(Exception), deadline=30.0)
    def _flush_generations(self):
        """Batch insert to BigQuery"""
        
        if self.generation_queue.empty():
            return
        
        rows = []
        while not self.generation_queue.empty() and len(rows) < self.batch_size:
            try:
                rows.append(self.generation_queue.get_nowait())
            except queue.Empty:
                break
        
        if rows:
            try:
                errors = self.client.insert_rows_json(self.generations_table, rows)
                if not errors:
                    print(f"📊 Logged {len(rows)} generations to BigQuery")
            except Exception as e:
                print(f"BigQuery insert failed: {e}")
    
    @retry.Retry(predicate=retry.if_exception_type(Exception), deadline=30.0)
    def _flush_agents(self):
        """Batch insert agent logs"""
        
        if self.agent_queue.empty():
            return
        
        rows = []
        while not self.agent_queue.empty() and len(rows) < self.batch_size:
            try:
                rows.append(self.agent_queue.get_nowait())
            except queue.Empty:
                break
        
        if rows:
            try:
                errors = self.client.insert_rows_json(self.agents_table, rows)
                if not errors:
                    print(f"📊 Logged {len(rows)} agent executions")
            except Exception as e:
                print(f"Agent log failed: {e}")
    
    def _start_background_flusher(self):
        """Background thread to flush batches"""
        
        def flush_worker():
            while True:
                time.sleep(self.flush_interval)
                self._flush_generations()
                self._flush_agents()
        
        thread = threading.Thread(target=flush_worker, daemon=True)
        thread.start()
    
    def _get_quality_tier(self, score: float) -> str:
        if score >= 9.0:
            return "excellent"
        elif score >= 8.0:
            return "good"
        elif score >= 7.0:
            return "acceptable"
        else:
            return "poor"
    
    def _infer_complexity(self, description: str) -> str:
        desc_lower = description.lower()
        
        if any(kw in desc_lower for kw in ['class', 'system', 'pipeline', 'architecture']):
            return "complex"
        elif any(kw in desc_lower for kw in ['function', 'add', 'reverse']):
            return "simple"
        else:
            return "medium"
    
    def __del__(self):
        """Flush on shutdown"""
        self._flush_generations()
        self._flush_agents()