"""
RAG Retriever - Pinecone integration for retrieving similar code examples
"""

import os
from pinecone import Pinecone
from openai import OpenAI
import asyncio
import time

class RAGRetriever:
    
    def __init__(self):
        # Initialize Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "codegen-ai-embeddings"))
        
        # OpenAI for embeddings
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print(f"RAG initialized with index: {os.getenv('PINECONE_INDEX_NAME', 'codegen-ai-embeddings')}")
        
    async def retrieve_similar(self, query: str, language: str, top_k: int = 3):
        """Retrieve similar code examples from Pinecone"""
        
        try:
            # Generate embedding for query
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                model="text-embedding-3-large",
                input=query
            )
            
            query_embedding = response.data[0].embedding
            
            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter={"language": language},
                include_metadata=True
            )
            
            # Format examples
            examples = []
            for match in results.matches:
                examples.append({
                    "code": match.metadata.get("code", ""),
                    "description": match.metadata.get("description", ""),
                    "score": match.score,
                    "language": match.metadata.get("language", language)
                })
            
            print(f"Retrieved {len(examples)} similar examples for: {query[:50]}...")
            return examples
            
        except Exception as e:
            print(f"RAG retrieval failed: {e}")
            return []
    
    async def add_code(self, code: str, description: str, language: str, metadata: dict = {}):
        """Add generated code to Pinecone for future retrieval"""
        
        try:
            # Generate embedding
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                model="text-embedding-3-large",
                input=f"{description}\n\n{code}"
            )
            
            embedding = response.data[0].embedding
            
            # Generate unique ID
            import hashlib
            code_id = hashlib.md5(code.encode()).hexdigest()
            
            # Upsert to Pinecone
            self.index.upsert(vectors=[{
                "id": code_id,
                "values": embedding,
                "metadata": {
                    "code": code[:5000],  # Limit to 5000 chars
                    "description": description,
                    "language": language,
                    "quality_score": metadata.get("quality_score", 0),
                    "created_at": time.time(),
                    **metadata
                }
            }])
            
            print(f"Added code to Pinecone: {code_id}")
            return True
            
        except Exception as e:
            print(f"Failed to add code to Pinecone: {e}")
            return False