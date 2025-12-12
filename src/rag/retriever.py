"""
Code Retriever

Retrieve similar code examples using RAG with Pinecone and OpenAI embeddings.
"""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from src.embeddings.config import EMBEDDING_CONFIG


class CodeRetriever:
    """
    Retrieve similar code examples using semantic search.
    
    Uses OpenAI embeddings + Pinecone vector database.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        pinecone_environment: Optional[str] = None,
        index_name: Optional[str] = None
    ):
        """
        Initialize code retriever.
        
        Args:
            openai_api_key: OpenAI API key (defaults to env)
            pinecone_api_key: Pinecone API key (defaults to env)
            pinecone_environment: Pinecone environment (defaults to env)
            index_name: Pinecone index name (defaults to env)
        """
        # Initialize OpenAI client
        self.openai_client = OpenAI(
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        
        # Pinecone configuration
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = pinecone_environment or os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
        self.index_name = index_name or os.getenv("PINECONE_INDEX", "codegen-ai-dev")
        
        # Check if Pinecone is available
        if not self.pinecone_api_key:
            print("⚠️  PINECONE_API_KEY not set! Using mock retrieval.")
            self.pinecone_available = False
            self.index = None
        else:
            try:
                import pinecone
                
                pinecone.init(
                    api_key=self.pinecone_api_key,
                    environment=self.pinecone_environment
                )
                
                self.index = pinecone.Index(self.index_name)
                self.pinecone_available = True
                
                print(f"✅ Connected to Pinecone index: {self.index_name}")
                
            except ImportError:
                print("⚠️  pinecone-client not installed! Using mock retrieval.")
                self.pinecone_available = False
                self.index = None
            except Exception as e:
                print(f"⚠️  Error connecting to Pinecone: {e}")
                print("Using mock retrieval.")
                self.pinecone_available = False
                self.index = None
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for search query.
        
        Args:
            query: Natural language search query
            
        Returns:
            Embedding vector
        """
        response = self.openai_client.embeddings.create(
            model=EMBEDDING_CONFIG["model"],
            input=query,
            dimensions=EMBEDDING_CONFIG["dimensions"]
        )
        
        return response.data[0].embedding
    
    def retrieve_similar_code(
        self,
        query: str,
        top_k: int = 3,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        min_quality_score: float = 6.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar code examples based on natural language query.
        
        Args:
            query: Natural language description of what you're looking for
            top_k: Number of results to return
            language: Filter by programming language (optional)
            framework: Filter by framework (optional)
            min_quality_score: Minimum quality score (0-10)
            
        Returns:
            List of code examples with metadata and similarity scores
        """
        # Generate query embedding
        query_embedding = self._generate_query_embedding(query)
        
        if not self.pinecone_available:
            # Return mock results for testing
            return self._get_mock_results(query, top_k, language, framework)
        
        # Build metadata filter
        filter_dict = {}
        if language:
            filter_dict["language"] = language
        if framework and framework != "none":
            filter_dict["framework"] = framework
        if min_quality_score:
            filter_dict["quality_score"] = {"$gte": min_quality_score}
        
        # Query Pinecone
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict if filter_dict else None,
                include_metadata=True
            )
            
            # Format results
            code_examples = []
            for match in results.matches:
                example = {
                    "id": match.id,
                    "score": match.score,
                    "code": match.metadata.get("code", ""),
                    "language": match.metadata.get("language", "unknown"),
                    "framework": match.metadata.get("framework", "none"),
                    "source": match.metadata.get("source", "unknown"),
                    "file_path": match.metadata.get("file_path", ""),
                    "quality_score": match.metadata.get("quality_score", 0),
                }
                code_examples.append(example)
            
            return code_examples
            
        except Exception as e:
            print(f"Error querying Pinecone: {e}")
            return self._get_mock_results(query, top_k, language, framework)
    
    def _get_mock_results(
        self,
        query: str,
        top_k: int,
        language: Optional[str],
        framework: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Return mock results for testing when Pinecone is not available.
        
        NOTE: These are example results for development/testing.
        Once Pauline adds PINECONE_API_KEY, this will use real retrieval.
        """
        mock_examples = [
            {
                "id": "mock_example_1",
                "score": 0.89,
                "code": """from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    username: str
    email: str

@app.post("/users/")
async def create_user(user: User):
    return {"id": 1, "username": user.username}""",
                "language": language or "python",
                "framework": framework or "fastapi",
                "source": "mock",
                "file_path": "examples/user_api.py",
                "quality_score": 8.5,
            },
            {
                "id": "mock_example_2",
                "score": 0.85,
                "code": """@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await fetch_user_from_db(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user""",
                "language": language or "python",
                "framework": framework or "fastapi",
                "source": "mock",
                "file_path": "examples/user_crud.py",
                "quality_score": 8.0,
            },
            {
                "id": "mock_example_3",
                "score": 0.82,
                "code": """from fastapi.security import OAuth2PasswordBearer
from jose import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload""",
                "language": language or "python",
                "framework": framework or "fastapi",
                "source": "mock",
                "file_path": "examples/auth.py",
                "quality_score": 9.0,
            },
        ]
        
        return mock_examples[:top_k]
    
    def format_for_prompt(self, examples: List[Dict[str, Any]]) -> str:
        """
        Format retrieved examples for inclusion in agent prompts.
        
        Args:
            examples: List of code examples from retrieval
            
        Returns:
            Formatted string for prompt inclusion
        """
        if not examples:
            return "No similar examples found."
        
        formatted = "Similar code examples:\n\n"
        
        for i, example in enumerate(examples, 1):
            formatted += f"Example {i} (similarity: {example['score']:.2f}):\n"
            formatted += f"Language: {example['language']}\n"
            formatted += f"Framework: {example['framework']}\n"
            formatted += f"Quality Score: {example['quality_score']}/10\n"
            formatted += f"```{example['language']}\n"
            formatted += example['code']
            formatted += "\n```\n\n"
        
        return formatted


def retrieve_similar_code(
    query: str,
    top_k: int = 3,
    language: Optional[str] = None,
    framework: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to retrieve similar code examples.
    
    Args:
        query: Natural language description
        top_k: Number of results
        language: Filter by language
        framework: Filter by framework
        
    Returns:
        List of code examples
    """
    retriever = CodeRetriever()
    return retriever.retrieve_similar_code(query, top_k, language, framework)


# Example usage
if __name__ == "__main__":
    # Test retrieval
    retriever = CodeRetriever()
    
    test_queries = [
        "FastAPI endpoint with user authentication",
        "Flask database connection with SQLAlchemy",
        "Express.js error handling middleware",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}\n")
        
        results = retriever.retrieve_similar_code(query, top_k=3)
        
        for i, result in enumerate(results, 1):
            print(f"Result {i}:")
            print(f"  Similarity: {result['score']:.2f}")
            print(f"  Language: {result['language']}")
            print(f"  Framework: {result['framework']}")
            print(f"  Code:\n{result['code'][:200]}...")
            print()
