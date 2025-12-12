"""
Upstash Redis Cache - HTTP-based (Cloud Run Compatible!)
Works everywhere - local, Cloud Run, serverless
"""
import requests
import json
import hashlib
import os
from typing import Optional

class RedisCache:
    
    def __init__(self):
        """Initialize Upstash Redis with REST API"""
        self.rest_url = os.getenv("UPSTASH_REDIS_REST_URL")
        self.rest_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        
        if not self.rest_url or not self.rest_token:
            print("⚠️ Upstash Redis credentials not found")
            print("   Set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN")
            self.enabled = False
            return
        
        # Test connection
        try:
            response = requests.get(
                f"{self.rest_url}/ping",
                headers={"Authorization": f"Bearer {self.rest_token}"},
                timeout=2
            )
            
            if response.status_code == 200 and response.json().get("result") == "PONG":
                self.enabled = True
                print(f"✅ Upstash Redis connected (serverless)")
            else:
                self.enabled = False
                print("⚠️ Upstash Redis connection failed")
                
        except Exception as e:
            self.enabled = False
            print(f"⚠️ Upstash Redis unavailable: {e}")
        
        self.ttl = 30 * 24 * 60 * 60  # 30 days
        self.hits = 0
        self.misses = 0
    
    def get(self, description: str, language: str) -> Optional[dict]:
        """Get cached result"""
        if not self.enabled:
            return None
        
        key = self._make_key(description, language)
        
        try:
            response = requests.get(
                f"{self.rest_url}/get/{key}",
                headers={"Authorization": f"Bearer {self.rest_token}"},
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json().get("result")
                if data:
                    self.hits += 1
                    print(f"🎯 CACHE HIT ({self.hits} total) - Instant response, $0 cost!")
                    return json.loads(data)
            
            self.misses += 1
            print(f"❌ CACHE MISS ({self.misses} total) - Generating fresh...")
            return None
            
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
            self.misses += 1
            return None
    
    def set(self, description: str, language: str, result: dict):
        """Cache result for 30 days"""
        if not self.enabled:
            return
        
        key = self._make_key(description, language)
        
        try:
            # SETEX with TTL
            response = requests.post(
                f"{self.rest_url}/setex/{key}/{self.ttl}",
                headers={
                    "Authorization": f"Bearer {self.rest_token}",
                    "Content-Type": "application/json"
                },
                json={"value": json.dumps(result)},
                timeout=2
            )
            
            if response.status_code == 200:
                print(f"💾 Cached result - Next request will be instant!")
            else:
                print(f"⚠️ Cache write failed: {response.text}")
                
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled:
            return {
                "enabled": False,
                "reason": "Upstash Redis not configured"
            }
        
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "enabled": True,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "cost_savings": f"{hit_rate * 0.6:.1f}%"
        }
    
    def _make_key(self, description: str, language: str) -> str:
        """Generate unique cache key"""
        combined = f"{description.lower().strip()}:{language}"
        return f"codegen:{hashlib.md5(combined.encode()).hexdigest()}"
