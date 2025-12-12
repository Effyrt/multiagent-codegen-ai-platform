"""
Collect REAL code from GitHub and populate Pinecone
This is what will make your RAG actually useful
"""

from dotenv import load_dotenv
load_dotenv()

import requests
import tempfile
import subprocess
import os
import sys
import asyncio
from pathlib import Path

sys.path.append('.')
from utils.rag import RAGRetriever

# GitHub API
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

def collect_popular_repos(num_repos=20):
    """Find popular Python repos"""
    
    print("🔍 Searching for popular Python repositories...")
    
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "language:python stars:>5000 pushed:>2023-01-01",
        "sort": "stars",
        "order": "desc",
        "per_page": num_repos
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    repos = response.json().get("items", [])
    
    print(f"✅ Found {len(repos)} repos")
    
    return [{
        "name": r["full_name"],
        "clone_url": r["clone_url"],
        "stars": r["stargazers_count"],
        "description": r["description"] or "No description"
    } for r in repos]

def clone_and_extract(repo, max_files=20):
    """Clone repo and extract Python files"""
    
    print(f"\n📦 Cloning: {repo['name']} ({repo['stars']} stars)")
    
    code_files = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Shallow clone (faster)
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', repo['clone_url'], tmpdir],
                capture_output=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"  ❌ Clone failed")
                return []
            
            # Find Python files
            py_files = list(Path(tmpdir).rglob('*.py'))
            print(f"  Found {len(py_files)} Python files")
            
            for filepath in py_files[:max_files]:
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                        
                        # Filter: reasonable size
                        if 200 < len(code) < 10000:
                            code_files.append({
                                "code": code,
                                "description": f"Code from {repo['name']}/{filepath.name}",
                                "repo": repo["name"],
                                "file": filepath.name,
                                "stars": repo["stars"],
                                "language": "python"
                            })
                except:
                    pass
            
            print(f"  ✅ Extracted {len(code_files)} usable files")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return code_files

async def upload_to_pinecone(code_files):
    """Upload all collected code to Pinecone"""
    
    print(f"\n📤 Uploading {len(code_files)} files to Pinecone...")
    
    rag = RAGRetriever()
    
    success = 0
    failed = 0
    
    for i, item in enumerate(code_files):
        try:
            await rag.add_code(
                code=item["code"],
                description=item["description"],
                language=item["language"],
                metadata={
                    "repo": item["repo"],
                    "stars": item["stars"],
                    "file": item["file"],
                    "source": "github"
                }
            )
            success += 1
            
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(code_files)} uploaded")
                
        except Exception as e:
            failed += 1
            if failed < 5:  # Only print first few errors
                print(f"  ⚠️ Upload failed: {e}")
    
    print(f"\n✅ Upload complete!")
    print(f"   Success: {success}")
    print(f"   Failed: {failed}")
    
    return success

async def main():
    """Main collection pipeline"""
    
    print("=" * 60)
    print("CodeGen AI - Real Code Collection Pipeline")
    print("=" * 60)
    
    # Step 1: Find repos
    repos = collect_popular_repos(num_repos=10)  # Start with 10 repos
    
    # Step 2: Clone and extract
    all_code = []
    for repo in repos:
        code_files = clone_and_extract(repo, max_files=20)
        all_code.extend(code_files)
        
        # Don't overwhelm - stop if we have enough
        if len(all_code) > 100:
            break
    
    print(f"\n📊 Total code files collected: {len(all_code)}")
    
    # Step 3: Upload to Pinecone
    if all_code:
        uploaded = await upload_to_pinecone(all_code)
        print(f"\n🎉 Done! Pinecone now has {uploaded} real code examples!")
    else:
        print("\n❌ No code collected")

if __name__ == "__main__":
    asyncio.run(main())