"""Load sample code examples into Pinecone"""
import os
import sys
from dotenv import load_dotenv
load_dotenv('../.env')

from pinecone import Pinecone
from openai import OpenAI
import time

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "codegen-ai-embeddings"))

examples = [
    {
        "id": "fastapi-upload-1",
        "code": '''from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
import shutil
from pathlib import Path

app = FastAPI()
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")
    
    allowed = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed:
        raise HTTPException(400, "Invalid file type")
    
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": file.filename, "size": file.size}''',
        "description": "FastAPI file upload endpoint with validation",
        "language": "python",
        "framework": "fastapi"
    },
    {
        "id": "fibonacci-memo-1",
        "code": '''def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("Negative input not allowed")
    cache = {}
    def fib(n: int) -> int:
        if n in cache:
            return cache[n]
        if n <= 1:
            return n
        cache[n] = fib(n-1) + fib(n-2)
        return cache[n]
    return fib(n)''',
        "description": "Fibonacci with dynamic programming memoization",
        "language": "python",
        "framework": "python-stdlib"
    },
    {
        "id": "rest-api-auth-1",
        "code": '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import bcrypt

app = FastAPI()

class User(BaseModel):
    email: EmailStr
    name: str
    password: str

users_db = {}

@app.post("/users/")
async def create_user(user: User):
    if user.email in users_db:
        raise HTTPException(400, "Email exists")
    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    users_db[user.email] = {"email": user.email, "name": user.name, "password": hashed}
    return {"message": "User created", "email": user.email}''',
        "description": "REST API user registration with bcrypt password hashing",
        "language": "python",
        "framework": "fastapi"
    },
    {
        "id": "pydantic-validation-1",
        "code": '''from pydantic import BaseModel, validator, EmailStr

class UserInput(BaseModel):
    email: EmailStr
    age: int
    username: str
    
    @validator('age')
    def validate_age(cls, v):
        if v < 18 or v > 120:
            raise ValueError('Invalid age')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or not v.isalnum():
            raise ValueError('Invalid username')
        return v''',
        "description": "Pydantic data validation with custom validators",
        "language": "python",
        "framework": "pydantic"
    },
    {
        "id": "async-http-1",
        "code": '''import asyncio
import aiohttp
from typing import List, Dict

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.json()

async def fetch_multiple(urls: List[str]) -> List[Dict]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)''',
        "description": "Async HTTP requests with aiohttp and gather",
        "language": "python",
        "framework": "aiohttp"
    }
]

print("🔄 Uploading examples to Pinecone...")

for ex in examples:
    print(f"  Processing: {ex['id']}")
    text = f"{ex['description']}\n\n{ex['code']}"
    
    response = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    embedding = response.data[0].embedding
    
    index.upsert(vectors=[{
        "id": ex['id'],
        "values": embedding,
        "metadata": {
            "code": ex['code'][:4000],
            "description": ex['description'],
            "language": ex['language'],
            "framework": ex['framework']
        }
    }])
    
    print(f"  ✅ Uploaded: {ex['id']}")
    time.sleep(0.3)

print("\n🎉 SUCCESS! Loaded 5 examples into Pinecone")
print(f"📊 Index stats: {index.describe_index_stats()}")
