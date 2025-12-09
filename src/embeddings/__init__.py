"""
Embeddings Generation

Generate vector embeddings from code snippets using OpenAI.
"""

__version__ = "0.1.0"

from .generate import EmbeddingGenerator, generate_embedding, generate_batch_embeddings
from .config import EMBEDDING_CONFIG

__all__ = [
    "EmbeddingGenerator",
    "generate_embedding",
    "generate_batch_embeddings",
    "EMBEDDING_CONFIG",
]
