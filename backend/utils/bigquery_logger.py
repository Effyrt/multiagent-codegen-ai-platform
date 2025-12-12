"""
BigQuery Analytics Logger - Production Grade
"""
from google.cloud import bigquery
import os
from datetime import datetime
import json

class BigQueryLogger:
    
    def __init__(self, batch_size: int = 5, flush_interval: int = 10):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.enabled = False
        
        try:
            # Initialize BigQuery client with service account
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not credentials_path or not os.path.exists(credentials_path):
                print(f"⚠️ BigQuery credentials not found at: {credentials_path}")
                return
            
            self.client = bigquery.Client()
            self.project_id = os.getenv("GCP_PROJECT_ID", "codegen-ai-479819")
            self.dataset_id = os.getenv("BQ_DATASET", "codegen_analytics")
            self.table_id = os.getenv("BQ_TABLE", "code_generations")
            
            self.full_table_id = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
            
            # Verify table exists
            self.client.get_table(self.full_table_id)
            
            self.enabled = True
            print(f"✅ BigQuery analytics enabled: {self.full_table_id}")
            
        except Exception as e:
            print(f"⚠️ BigQuery initialization failed: {e}")
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
        error: str = None
    ):
        """Log code generation to BigQuery"""
        
        if not self.enabled:
            return
        
        try:
            row = {
                "generation_id": generation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "description": description[:500],  # Limit length
                "language": language,
                "quality_score": float(quality_score),
                "duration_seconds": float(duration),
                "tokens_used": int(tokens_used),
                "cost_usd": float(cost),
                "cached": bool(cached),
                "rag_examples_used": int(rag_examples),
                "iterations": int(iterations),
                "code_length": int(code_length),
                "test_pass_rate": float(test_pass_rate)
            }
            
            # Insert row
            errors = self.client.insert_rows_json(self.full_table_id, [row])
            
            if errors:
                print(f"⚠️ BigQuery insert errors: {errors}")
            else:
                print(f"📊 Logged generation to BigQuery: {generation_id}")
                
        except Exception as e:
            print(f"⚠️ BigQuery log failed: {e}")
    
    def __del__(self):
        """Cleanup on shutdown"""
        pass
