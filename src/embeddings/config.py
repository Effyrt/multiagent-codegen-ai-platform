"""
Embedding Configuration

Configuration for OpenAI embeddings generation.
"""

import os

# Embedding model configuration
EMBEDDING_CONFIG = {
    "model": "text-embedding-ada-002",  # Using large model for quality
    "dimensions": 1536,                  # Full dimensionality
    "batch_size": 100,                   # Process 100 snippets at a time
    "encoding": "cl100k_base",          # Tokenizer for token counting
    "max_tokens": 8191,                 # Max tokens per input
}


# Cost tracking
EMBEDDING_COSTS = {
    "text-embedding-3-large": 0.13 / 1_000_000,  # $0.13 per 1M tokens
    "text-embedding-3-small": 0.02 / 1_000_000,  # $0.02 per 1M tokens
}

# Snippet preprocessing
SNIPPET_CONFIG = {
    "include_metadata": True,           # Include language, framework in embedding
    "max_code_lines": 50,              # Limit code length
    "include_docstring": True,          # Include function docstrings
    "include_imports": False,           # Don't include import statements
}

def get_embedding_cost(tokens: int, model: str = "text-embedding-3-large") -> float:
    """Calculate embedding generation cost"""
    return tokens * EMBEDDING_COSTS.get(model, 0)

def format_snippet_for_embedding(snippet: dict) -> str:
    """
    Format a code snippet for embedding generation.
    
    Combines code with metadata for better semantic representation.
    """
    parts = []
    
    # Add language and framework context
    if snippet.get("language"):
        parts.append(f"Language: {snippet['language']}")
    
    if snippet.get("framework") and snippet["framework"] != "none":
        parts.append(f"Framework: {snippet['framework']}")
    
    # Add description if available
    if snippet.get("description"):
        parts.append(f"Description: {snippet['description']}")
    
    # Add the actual code
    code = snippet.get("code", "")
    if code:
        # Limit code length
        lines = code.split("\n")
        if len(lines) > SNIPPET_CONFIG["max_code_lines"]:
            code = "\n".join(lines[:SNIPPET_CONFIG["max_code_lines"]])
            code += "\n... (truncated)"
        
        parts.append(f"Code:\n{code}")
    
    return "\n\n".join(parts)
