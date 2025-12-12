"""
CodeGen AI - GitHub Collection (Self-Contained)
No external imports - everything in one file
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests
import tempfile
import subprocess
import os
from pathlib import Path

default_args = {
    'owner': 'om-raut',
    'retries': 2,
}

def collect_github_code():
    """Collect and upload - all in one function"""
    
    from dotenv import load_dotenv
    load_dotenv('/opt/airflow/.env')
    
    import asyncio
    from pinecone import Pinecone
    from openai import OpenAI
    import hashlib
    import time
    
    print("🔍 Starting GitHub collection...")
    
    # Initialize clients
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "codegen-ai-embeddings"))
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # GitHub API
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN', '')}"}
    
    # Search repos
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "language:python stars:>2000",
        "sort": "stars",
        "per_page": 3  # Just 3 repos per run
    }
    
    response = requests.get(url, headers=headers, params=params)
    repos = response.json().get("items", [])
    
    print(f"✅ Found {len(repos)} repos")
    
    # Collect code
    all_code = []
    
    for repo in repos:
        print(f"📦 Cloning: {repo['full_name']}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                subprocess.run(
                    ['git', 'clone', '--depth', '1', repo['clone_url'], tmpdir],
                    capture_output=True,
                    timeout=60
                )
                
                for filepath in list(Path(tmpdir).rglob('*.py'))[:10]:
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()
                            
                            if 200 < len(code) < 8000:
                                all_code.append({
                                    "code": code,
                                    "description": f"Code from {repo['full_name']}/{filepath.name}",
                                    "repo": repo["full_name"],
                                    "stars": repo["stargazers_count"]
                                })
                    except:
                        pass
                        
            except Exception as e:
                print(f"Failed: {e}")
    
    print(f"Collected {len(all_code)} code files")
    
    # Upload to Pinecone
    async def upload():
        success = 0
        for item in all_code[:15]:  # Limit to 15 per run
            try:
                # Generate embedding
                response = await asyncio.to_thread(
                    openai_client.embeddings.create,
                    model="text-embedding-3-large",
                    input=f"{item['description']}\n\n{item['code']}"
                )
                
                embedding = response.data[0].embedding
                code_id = hashlib.md5(item['code'].encode()).hexdigest()
                
                # Upload to Pinecone
                index.upsert(vectors=[{
                    "id": code_id,
                    "values": embedding,
                    "metadata": {
                        "code": item["code"][:5000],
                        "description": item["description"],
                        "language": "python",
                        "repo": item["repo"],
                        "stars": item["stars"],
                        "source": "github-airflow"
                    }
                }])
                
                success += 1
                
            except Exception as e:
                print(f"Upload failed: {e}")
        
        return success
    
    uploaded = asyncio.run(upload())
    
    print(f"✅ Uploaded {uploaded} files to Pinecone")
    
    return f"Success: {uploaded} files"

with DAG(
    'codegen_github_collection',
    default_args=default_args,
    schedule_interval='0 */6 * * *',
    start_date=datetime(2024, 12, 3),
    catchup=False,
    tags=['codegen-ai'],
) as dag:
    
    collect = PythonOperator(
        task_id='collect_github',
        python_callable=collect_github_code,
    )