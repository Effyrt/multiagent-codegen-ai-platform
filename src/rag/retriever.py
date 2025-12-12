"""
Code Retriever

Retrieve similar code examples using RAG with Pinecone and OpenAI embeddings.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
import json



# ============================
# Fix import path (local & Airflow compatible)
# ============================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


import os
from typing import List, Dict, Any, Optional
from embeddings.config import EMBEDDING_CONFIG  


# ============================
# OpenAI SDK compatibility
# ============================
USE_NEW_OPENAI = False

try:
    # New SDK (openai >= 1.0)
    from openai import OpenAI
    _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    USE_NEW_OPENAI = True
except Exception:
    # Old SDK (openai < 1.0)
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")


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


        # Pinecone configuration
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = pinecone_environment or os.getenv(
            "PINECONE_ENVIRONMENT", "us-east-1-aws"
        )
        self.index_name = index_name or os.getenv(
            "PINECONE_INDEX_NAME", "code-snippets-final"
        )
        
        if not self.pinecone_api_key:
            print("⚠️  PINECONE_API_KEY not set! Using mock retrieval.")
            self.pinecone_available = False
            self.index = None
            return


        try:
            from pinecone import Pinecone

            pc = Pinecone(api_key=self.pinecone_api_key)

            self.index = pc.Index(self.index_name)
            self.pinecone_available = True

            print(f"✅ Connected to Pinecone index: {self.index_name}")

            
        except Exception as e:
            print(f"⚠️  Error connecting to Pinecone: {e}")
            self.pinecone_available = False
            self.index = None

    # ============================
    # Embedding (⬅ class)
    # ============================
    def _generate_query_embedding(self, query: str) -> List[float]:
        if USE_NEW_OPENAI:
            response = _openai_client.embeddings.create(
                model=EMBEDDING_CONFIG["model"],
                input=query
            )
            return response.data[0].embedding
        else:
            response = openai.Embedding.create(
                model=EMBEDDING_CONFIG["model"],
                input=query
            )
            return response["data"][0]["embedding"]

    # ============================
    # Retrieval
    # ============================
    def retrieve_similar_code(
        self,
        query: str,
        top_k: int = 3,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        min_quality_score: float = 6.0
    ) -> List[Dict[str, Any]]:

        query_embedding = self._generate_query_embedding(query)
        
        if not self.pinecone_available:
            return self._get_mock_results(query, top_k, language, framework)
        
     
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
#                filter=filter_dict if filter_dict else None,
                include_metadata=True,
#                namespace="__default__"
            )
            
            code_examples = []
            for match in results.matches:
                code_examples.append({
                    "id": match.id,
                    "score": match.score,
#                    "code": match.metadata.get("code", ""),
                    "language": match.metadata.get("language", "unknown"),
                    "framework": match.metadata.get("framework", "none"),
                    "file_path": match.metadata.get("file_path", ""),
                    #"quality_score": match.metadata.get("quality_score", 0),
                })
            
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
        return [
            {
                "id": "mock_example",
                "score": 0.9,
                "language": language or "python",
                "framework": framework or "fastapi",
                "code": "# mock code snippet",
                "file_path": "mock.py",
                "quality_score": 8.5,
            }
        ][:top_k]


def retrieve_similar_code(
    query: str,
    top_k: int = 3,
    language: Optional[str] = None,
    framework: Optional[str] = None
):
    retriever = CodeRetriever()
    return retriever.retrieve_similar_code(query, top_k, language, framework)




def normalize_str(v):
    if not v or not isinstance(v, str):
        return None
    v = v.strip().lower()
    if v in ("none", "null", "unknown", ""):
        return None
    return v



def post_filter_snippets(
    snippets,
    language=None,
    framework=None,
    min_score=None
):
    filtered = []

    user_lang = normalize_str(language)
    user_fw = normalize_str(framework)

    for s in snippets:
        meta_lang = normalize_str(s.get("language"))
        meta_fw = normalize_str(s.get("framework"))
        score = s.get("score", 0)

   
        if user_lang and meta_lang and meta_lang != user_lang:
            continue


        if user_fw and meta_fw and meta_fw != user_fw:
            continue

        if min_score is not None and score < min_score:
            continue

        filtered.append(s)

    return filtered




def save_rag_output(context, out_path="data/rag_outputs/rag_output.json"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)
    print(f"💾 RAG output saved to {out_path}")

if __name__ == "__main__":
    query = "FastAPI endpoint with user authentication"

    results = retrieve_similar_code(
        query,
        top_k=3
    )

    context = {
        "query": query,
        "retrieved": results,
        "metadata": {
            "top_k": 3
        }
    }

    save_rag_output(context)
    print("✅ Done. RAG output generated.")
