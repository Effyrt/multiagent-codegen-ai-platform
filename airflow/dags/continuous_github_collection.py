"""
PRODUCTION DAG: Continuous GitHub Code Collection
Runs every hour, collects code, adds to Pinecone
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests
import tempfile
import subprocess
import os
import sys
from pathlib import Path

default_args = {
    'owner': 'om-raut',
    'depends_on_past': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def collect_and_upload(**context):
    """Collect code and upload to Pinecone - runs every hour"""
    
    # This will be imported inside Airflow container
    sys.path.append('/opt/airflow/backend')
    
    from dotenv import load_dotenv
    load_dotenv('/opt/airflow/.env')
    
    import asyncio
    from utils.rag import RAGRetriever
    
    print(f"🚀 Starting collection run at {datetime.now()}")
    
    # GitHub search - rotate through different queries each hour
    queries = [
        "language:python stars:>1000 topic:fastapi",
        "language:python stars:>1000 topic:machine-learning",
        "language:python stars:>1000 topic:data-science",
        "language:python stars:>1000 topic:api",
        "language:python stars:>1000 topic:automation",
    ]
    
    # Use hour to rotate queries
    query_idx = datetime.now().hour % len(queries)
    query = queries[query_idx]
    
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN', '')}"}
    
    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "per_page": 5  # 5 repos per hour
    }
    
    response = requests.get(url, headers=headers, params=params)
    repos = response.json().get("items", [])
    
    print(f"Found {len(repos)} repos for query: {query}")
    
    # Collect code
    all_code = []
    for repo in repos:
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Clone
                subprocess.run(
                    ['git', 'clone', '--depth', '1', repo['clone_url'], tmpdir],
                    capture_output=True,
                    timeout=60
                )
                
                # Extract Python files
                for filepath in Path(tmpdir).rglob('*.py'):
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()
                            
                            if 200 < len(code) < 8000:
                                all_code.append({
                                    "code": code,
                                    "description": f"Code from {repo['full_name']}/{filepath.name}",
                                    "repo": repo["full_name"],
                                    "stars": repo["stargazers_count"],
                                    "language": "python"
                                })
                    except:
                        pass
                
                # Limit per repo
                if len(all_code) > 20:
                    break
                    
            except Exception as e:
                print(f"Failed: {e}")
    
    print(f"Collected {len(all_code)} code files")
    
    # Upload to Pinecone
    async def upload():
        rag = RAGRetriever()
        success = 0
        
        for item in all_code:
            try:
                await rag.add_code(
                    code=item["code"],
                    description=item["description"],
                    language=item["language"],
                    metadata={"repo": item["repo"], "stars": item["stars"], "source": "github-continuous"}
                )
                success += 1
            except Exception as e:
                print(f"Upload failed: {e}")
        
        return success
    
    uploaded = asyncio.run(upload())
    
    print(f"✅ Uploaded {uploaded} files to Pinecone")
    
    return uploaded

# DAG definition
with DAG(
    'codegen_ai_continuous_collection',
    default_args=default_args,
    description='Continuously collect code from GitHub (runs hourly)',
    schedule_interval='@hourly',  # Runs every hour!
    start_date=datetime(2024, 11, 30),
    catchup=False,
    tags=['codegen-ai', 'production', 'continuous'],
) as dag:
    
    collect_task = PythonOperator(
        task_id='collect_and_upload_code',
        python_callable=collect_and_upload,
    )