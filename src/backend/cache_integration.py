"""
Om's Redis Cache Integration
"""
import sys
from pathlib import Path

# Try to import Om's cache
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend_deployed"))
    from utils.cache import RedisCache
    cache = RedisCache()
except:
    cache = None

def get_cache():
    return cache if cache and cache.enabled else None
