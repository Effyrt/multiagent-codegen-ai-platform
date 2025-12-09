"""
RAG (Retrieval-Augmented Generation)

Semantic code search and retrieval using Pinecone vector database.
"""

__version__ = "0.1.0"

from .retriever import CodeRetriever, retrieve_similar_code

__all__ = [
    "CodeRetriever",
    "retrieve_similar_code",
]
