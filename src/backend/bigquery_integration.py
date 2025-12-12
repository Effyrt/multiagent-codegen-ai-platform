"""
Om's BigQuery Logging Integration
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend_deployed"))
    from utils.bigquery_logger import BigQueryLogger
    bq = BigQueryLogger()
except:
    bq = None

def get_bq_logger():
    return bq if bq and bq.enabled else None
