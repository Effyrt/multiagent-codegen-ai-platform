"""
Populate Pinecone with example code snippets
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import sys
sys.path.append('.')

from utils.rag import RAGRetriever

# Example code snippets to add
EXAMPLES = [
    {
        "code": """def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None""",
        "description": "Email validation function using regex",
        "language": "python",
        "metadata": {"framework": "stdlib", "quality_score": 8.5}
    },
    {
        "code": """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)""",
        "description": "Recursive fibonacci number calculator",
        "language": "python",
        "metadata": {"algorithm": "recursion", "quality_score": 7.0}
    },
    {
        "code": """from fastapi import FastAPI, UploadFile

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile):
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}""",
        "description": "FastAPI file upload endpoint",
        "language": "python",
        "metadata": {"framework": "fastapi", "quality_score": 9.0}
    },
    {
        "code": """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1""",
        "description": "Binary search algorithm implementation",
        "language": "python",
        "metadata": {"algorithm": "search", "quality_score": 8.0}
    },
    {
        "code": """def remove_duplicates(lst):
    return list(set(lst))""",
        "description": "Remove duplicates from a list",
        "language": "python",
        "metadata": {"utility": "list-manipulation", "quality_score": 7.5}
    },
    {
        "code": """def is_palindrome(s):
    s = ''.join(c for c in s if c.isalnum()).lower()
    return s == s[::-1]""",
        "description": "Check if string is palindrome",
        "language": "python",
        "metadata": {"string-manipulation": "validation", "quality_score": 8.0}
    }
]

async def populate():
    rag = RAGRetriever()
    
    print("Adding example code to Pinecone...")
    
    for i, example in enumerate(EXAMPLES):
        success = await rag.add_code(
            code=example["code"],
            description=example["description"],
            language=example["language"],
            metadata=example["metadata"]
        )
        
        if success:
            print(f"✅ Added example {i+1}: {example['description']}")
        else:
            print(f"❌ Failed to add example {i+1}")
    
    print(f"\n✅ Done! Added {len(EXAMPLES)} examples to Pinecone")

if __name__ == "__main__":
    asyncio.run(populate())