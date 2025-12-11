"""
rag_pipeline.py

Author: PeiYing

Purpose:
- Embed user query using OpenAI
- Perform similarity search on Pinecone
- Return RAG context following rag_schema.py

Used by:
- Multi-Agent system 
- Backend API 
"""


import os
import json
import openai
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "code-snippets")

EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

openai.api_key = OPENAI_API_KEY
pc = Pinecone(api_key=PINECONE_API_KEY)


# -------------------------------------------------------------------
# GET INDEX
# -------------------------------------------------------------------
def get_index():
    try:
        return pc.Index(INDEX_NAME)
    except Exception as e:
        print(f"❌ Cannot load Pinecone index `{INDEX_NAME}`:", e)
        return None


# -------------------------------------------------------------------
# EMBED QUERY
# -------------------------------------------------------------------
def embed_query(query: str):
    """Embed query text with full safety."""
    try:
        resp = openai.Embedding.create(
            model=EMBED_MODEL,
            input=query
        )
        return resp["data"][0]["embedding"]

    except Exception as e:
        print("❌ Query embedding failed:", e)
        return None


# -------------------------------------------------------------------
# CONVERT PINECONE MATCH → SNIPPET SCHEMA
# -------------------------------------------------------------------
def convert_match_to_snippet(match):
    """
    Convert Pinecone match into RAG snippet schema.
    Includes full fallback logic.
    """
    meta = match.get("metadata", {}) or {}

    # -----------------------------
    # imports must be list
    # -----------------------------
    imports = meta.get("imports", [])
    if isinstance(imports, str):
        # fallback from older metadata (string)
        imports = [x.strip() for x in imports.split(",") if x.strip()]
    if imports is None:
        imports = []

    # -----------------------------
    # construct unified snippet dict
    # -----------------------------
    return {
        "snippet_id": match.get("id"),

        "repo": meta.get("repo", "unknown"),
        "file_path": meta.get("file_path", ""),

        "type": meta.get("type", "file"),

        "func_name": meta.get("func_name"),
        "class_name": meta.get("class_name"),

        "language": meta.get("language", "unknown"),
        "framework": meta.get("framework", "none"),

        "imports": imports,

        "complexity": float(meta.get("complexity", 0.0)),

        # Pinecone similarity score
        "score": float(match.get("score", 0.0)),
    }


# -------------------------------------------------------------------
# SAVE RAG RESULTS
# -------------------------------------------------------------------
def save_rag_output(context, out_path="data/rag_outputs/rag_output.json"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(context, f, ensure_ascii=False, indent=2)
        print(f"💾 RAG output saved to {out_path}")
    except Exception as e:
        print("⚠️ Failed to save RAG output:", e)


# -------------------------------------------------------------------
# MAIN RAG QUERY FUNCTION
# -------------------------------------------------------------------
def get_rag_context(query: str, top_k: int = 3):
    """
    Main RAG search function.
    1. Embed query
    2. Query Pinecone
    3. Convert matches
    4. Save + return result
    """
    index = get_index()
    if index is None:
        return {
            "query": query,
            "retrieved": [],
            "metadata": {"top_k": top_k, "error": "index_not_loaded"}
        }

    # 1. embed query
    query_vec = embed_query(query)
    if query_vec is None:
        return {
            "query": query,
            "retrieved": [],
            "metadata": {"top_k": top_k, "error": "embedding_failed"}
        }

    # 2. Pinecone search
    try:
        resp = index.query(
            vector=query_vec,
            top_k=top_k,
            include_metadata=True
        )
    except Exception as e:
        print("❌ Pinecone query failed:", e)
        return {
            "query": query,
            "retrieved": [],
            "metadata": {"top_k": top_k, "error": "pinecone_error"}
        }

    # 3. convert result
    retrieved = []
    for match in resp.get("matches", []):
        try:
            retrieved.append(convert_match_to_snippet(match))
        except Exception as e:
            print("⚠️ Failed to convert snippet:", e)

    # 4. final context object
    rag_context = {
        "query": query,
        "retrieved": retrieved,
        "metadata": {
            "top_k": top_k,
            "model": EMBED_MODEL
        }
    }

    save_rag_output(rag_context)
    return rag_context

# ----------------------------------------------------------
# Public function for Airflow DAG
# ----------------------------------------------------------
def run_rag_test(
    query="How to create a dataset?",
    output_path="data/rag_outputs/rag_output.json"
):
    print("🚀 Running RAG test from Airflow...")

    from rag_pipeline import run_rag_pipeline  

    result = run_rag_pipeline(
        query=query,
        output_path=output_path
    )

    print("🎉 RAG test completed inside Airflow task.")
    return result

# -------------------------------------------------------------------
# For CLI Testing
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("⚙️ Running RAG pipeline test...")
    out = get_rag_context("How to create a dataset?")
    print(json.dumps(out, indent=2))
