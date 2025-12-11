"""
rag_schema.py

Defines the JSON schema for RAG snippet and context output.
Both Multi-Agent System and Backend API import this file 
to ensure data consistency across the entire pipeline.
"""

# -----------------------------
# Snippet Schema
# -----------------------------
RAG_SNIPPET_SCHEMA = {
    "snippet_id": "string (uuid4)",
    "repo": "string",
    "file_path": "string",

    "language": "string",
    "framework": "string",

    "type": "string",
    "func_name": "string or null",
    "class_name": "string or null",

    "code": "string",
    "imports": ["list of strings"],

    "complexity": "float"
}

# -----------------------------
# RAG Context Schema
# -----------------------------
RAG_CONTEXT_SCHEMA = {
    "query": "string",
    "retrieved": [RAG_SNIPPET_SCHEMA],
    "metadata": {
        "top_k": "int"
    }
}

# -----------------------------
# Validator Function
# -----------------------------
def validate_rag_context(obj: dict) -> bool:

    required_keys = ["query", "retrieved", "metadata"]
    for key in required_keys:
        if key not in obj:
            return False

    retrieved = obj.get("retrieved")
    if not isinstance(retrieved, list):
        return False

    for snip in retrieved:
        for field in RAG_SNIPPET_SCHEMA.keys():
            if field not in snip:
                return False

    metadata = obj["metadata"]
    if "top_k" not in metadata:
        return False

    return True
