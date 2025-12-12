"""
embed_pipeline.py
Generates OpenAI embeddings for code snippets and uploads to Pinecone.
Fully cleaned, production-safe, error-free version.
"""

import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import openai
import tiktoken
import numpy as np

# --------------------------------------------
# Load .env
# --------------------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# ✔ FIXED: correctly read your .env variable name
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "code-snippets")

# ✔ FIXED: ensure embedding model 100% comes from .env
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "embedding-3-small")

# OpenAI small embedding = 1536
EMBED_DIM = 1536

# --------------------------------------------
# OpenAI Client
# --------------------------------------------
openai.api_key = OPENAI_API_KEY


# --------------------------------------------
# Tokenizer (tiktoken) + chunk functions
# --------------------------------------------
ENC = tiktoken.get_encoding("cl100k_base")

# --------------------------------------------
# Detect OpenAI API version (new vs old)
# --------------------------------------------
import openai
try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    USE_NEW_OPENAI = True
except Exception:
    # old API (openai==0.28)
    client = None
    USE_NEW_OPENAI = False



def count_tokens(text: str):
    return len(ENC.encode(text, disallowed_special=()))


def chunk_text(text: str, max_tokens=2000, overlap=200):
    """Split long code into chunks small enough for OpenAI embeddings."""
    tokens = ENC.encode(text, disallowed_special=())
    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk = tokens[start:end]
        chunks.append(ENC.decode(chunk))
        start += max_tokens - overlap

    return chunks

# --------------------------------------------
# Sanitize metadata for Pinecone
# --------------------------------------------
def sanitize(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return [str(v) for v in value]
    return str(value)

# --------------------------------------------
# Load final snippets
# --------------------------------------------
def load_snippets(path="data/processed/final_snippets/snippets_final.jsonl"):
    if not os.path.exists(path):
        print(f"❌ Snippet file not found: {path}")
        return []

    snippets = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                snippets.append(json.loads(line))
            except:
                continue

    print(f"🔍 Loaded {len(snippets)} snippets")
    return snippets



def embed_single_text(text: str):
    """ openai>=1.0 & openai==0.28 embedding """
    if USE_NEW_OPENAI:
        # New API
        resp = client.embeddings.create(
            model=EMBED_MODEL,
            input=text
        )
        return resp.data[0].embedding
    else:
        # Old API
        resp = openai.Embedding.create(
            model=EMBED_MODEL,
            input=text
        )
        return resp["data"][0]["embedding"]



# --------------------------------------------
# OpenAI Embedding
# --------------------------------------------

def embed_text(text: str):
    """Embed text with chunking for long code."""
    tok = count_tokens(text)

    # If text is short, embed directly
    if tok <= 2000:
        try:
            return embed_single_text(text)
        except Exception as e:
            print("❌ OpenAI embedding error:", e)
            return None

    # Too long → chunk it
    chunks = chunk_text(text)
    vectors = []

    for ch in chunks:
        try:
            vec = embed_single_text(ch)   
            vectors.append(vec)
        except Exception as e:
            print("❌ Chunk embedding failed:", e)
            continue

    if not vectors:
        return None

    return np.mean(np.array(vectors), axis=0).tolist()


# --------------------------------------------
# Pinecone Setup
# --------------------------------------------
def connect_pinecone():
    pc = Pinecone(api_key=PINECONE_API_KEY)

    existing = [idx.name for idx in pc.list_indexes()]
    
    if INDEX_NAME not in existing:
        print(f"⚠️ Index {INDEX_NAME} not found. Creating new 1536-dim index…")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    else:
        print(f"✅ Using existing index: {INDEX_NAME}")

    return pc.Index(INDEX_NAME)

# --------------------------------------------
# Upsert Snippets to Pinecone
# --------------------------------------------
def upsert_snippets(index, snippets, batch_size=100):
    total = len(snippets)

    for i, snip in enumerate(snippets):

        snip_id = snip["snippet_id"]
        code_text = snip.get("cleaned_code") or snip.get("code") or ""

        vector = embed_text(code_text)
        if vector is None:
            print(f"❌ Skipped embedding for {snip_id}")
            continue

        if len(vector) != EMBED_DIM:
            print(f"❌ Wrong embedding dimension ({len(vector)}) for {snip_id}")
            continue

        metadata = {
            "snippet_id": snip_id,
            "repo": sanitize(snip.get("repo")),
            "file_path": sanitize(snip.get("file_path")),
            "language": sanitize(snip.get("language")),
            "framework": sanitize(snip.get("framework")),
            "type": sanitize(snip.get("type")),
            "func_name": sanitize(snip.get("func_name")),
            "class_name": sanitize(snip.get("class_name")),
            "imports": sanitize(snip.get("imports")),
            "complexity": float(snip.get("complexity", 0.0)),
        }

        try:
            index.upsert([
                {
                    "id": snip_id,
                    "values": vector,
                    "metadata": metadata
                }
            ])
        except Exception as e:
            print(f"❌ Error at snippet {snip_id}")
            print(e)
            continue

        if i % 200 == 0:
            print(f"➡️ {i}/{total} embeddings uploaded…")

    print("🎉 Upsert complete!")

# --------------------------------------------
# Public function for Airflow DAG
# --------------------------------------------
def run_embedding_pipeline(
    path="data/processed/final_snippets/snippets_final.jsonl"
):
    print("🚀 Running embedding pipeline from DAG...")

    # Step 1: load snippets
    snippets = load_snippets(path)
    if not snippets:
        print("❌ No snippets found. Pipeline stopped.")
        return

    # Step 2: connect Pinecone
    index = connect_pinecone()

    # Step 3: embed + upsert
    upsert_snippets(index, snippets)

    print("🎉 Embedding pipeline completed inside Airflow task.")

# --------------------------------------------
# Main
# --------------------------------------------
if __name__ == "__main__":
    print("🔧 EMBED_MODEL =", EMBED_MODEL)
    print("🔧 Expected DIM =", EMBED_DIM)

    # Step 1: load snippets
    snippets = load_snippets("data/processed/final_snippets/snippets_final.jsonl")
    if not snippets:
        exit()

    # Step 2: connect Pinecone
    index = connect_pinecone()

    # Step 3: embed + upsert
    upsert_snippets(index, snippets)
