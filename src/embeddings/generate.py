"""
Embedding Generation

Generate vector embeddings from code snippets using OpenAI text-embedding-3-large.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from openai import OpenAI
import tiktoken
from tqdm import tqdm

from .config import EMBEDDING_CONFIG, format_snippet_for_embedding, get_embedding_cost


class EmbeddingGenerator:
    """
    Generate embeddings for code snippets using OpenAI's text-embedding-3-large model.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        """
        Initialize embedding generator.
        
        Args:
            api_key: OpenAI API key (defaults to env variable)
            model: Embedding model name (defaults to config)
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model or EMBEDDING_CONFIG["model"]
        self.dimensions = EMBEDDING_CONFIG["dimensions"]
        self.batch_size = EMBEDDING_CONFIG["batch_size"]
        
        # Initialize tokenizer for cost estimation
        self.encoding = tiktoken.get_encoding(EMBEDDING_CONFIG["encoding"])
        
        # Track statistics
        self.total_tokens = 0
        self.total_cost = 0.0
        self.embeddings_generated = 0
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions
            )
            
            embedding = response.data[0].embedding
            
            # Update statistics
            tokens = response.usage.total_tokens
            self.total_tokens += tokens
            self.total_cost += get_embedding_cost(tokens, self.model)
            self.embeddings_generated += 1
            
            return embedding
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions
            )
            
            # Extract embeddings in order
            embeddings = [item.embedding for item in response.data]
            
            # Update statistics
            tokens = response.usage.total_tokens
            self.total_tokens += tokens
            self.total_cost += get_embedding_cost(tokens, self.model)
            self.embeddings_generated += len(texts)
            
            return embeddings
            
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            raise
    
    def generate_from_snippets(
        self, 
        snippets: List[Dict[str, Any]], 
        output_file: Path
    ) -> Dict[str, Any]:
        """
        Generate embeddings for all code snippets and save to file.
        
        Args:
            snippets: List of code snippet dictionaries
            output_file: Path to save embeddings
            
        Returns:
            Statistics dictionary
        """
        print(f"Generating embeddings for {len(snippets)} snippets...")
        print(f"Model: {self.model} ({self.dimensions} dimensions)")
        print(f"Batch size: {self.batch_size}")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Process in batches
        embeddings_data = []
        
        with tqdm(total=len(snippets), desc="Generating embeddings") as pbar:
            for i in range(0, len(snippets), self.batch_size):
                batch = snippets[i:i + self.batch_size]
                
                # Format snippets for embedding
                texts = [format_snippet_for_embedding(snippet) for snippet in batch]
                
                # Generate embeddings
                try:
                    embeddings = self.generate_batch(texts)
                    
                    # Combine with metadata
                    for snippet, embedding in zip(batch, embeddings):
                        embedding_entry = {
                            "id": snippet.get("id", f"snippet_{i}"),
                            "embedding": embedding,
                            "metadata": {
                                "language": snippet.get("language", "unknown"),
                                "framework": snippet.get("framework", "none"),
                                "source": snippet.get("source", "unknown"),
                                "file_path": snippet.get("file_path", ""),
                                "code": snippet.get("code", "")[:500],  # First 500 chars
                                "quality_score": snippet.get("quality_score", 0),
                            }
                        }
                        embeddings_data.append(embedding_entry)
                    
                    pbar.update(len(batch))
                    
                    # Rate limiting: small delay between batches
                    if i + self.batch_size < len(snippets):
                        time.sleep(0.1)
                    
                except Exception as e:
                    print(f"\nError processing batch {i}-{i+len(batch)}: {e}")
                    continue
        
        # Save embeddings to file (JSONL format)
        print(f"\nSaving embeddings to {output_file}...")
        with open(output_file, 'w') as f:
            for entry in embeddings_data:
                f.write(json.dumps(entry) + '\n')
        
        # Generate statistics
        stats = {
            "total_snippets": len(snippets),
            "embeddings_generated": self.embeddings_generated,
            "total_tokens": self.total_tokens,
            "estimated_cost": f"${self.total_cost:.4f}",
            "model": self.model,
            "dimensions": self.dimensions,
            "output_file": str(output_file)
        }
        
        print(f"\n{'='*60}")
        print("Embedding Generation Complete!")
        print(f"{'='*60}")
        print(f"Embeddings generated: {stats['embeddings_generated']}")
        print(f"Total tokens: {stats['total_tokens']:,}")
        print(f"Estimated cost: {stats['estimated_cost']}")
        print(f"Model: {stats['model']}")
        print(f"Saved to: {stats['output_file']}")
        print(f"{'='*60}")
        
        return stats


def generate_embedding(text: str, model: str = None) -> List[float]:
    """
    Convenience function to generate a single embedding.
    
    Args:
        text: Text to embed
        model: Model name (defaults to config)
        
    Returns:
        Embedding vector
    """
    generator = EmbeddingGenerator(model=model)
    return generator.generate_embedding(text)


def generate_batch_embeddings(texts: List[str], model: str = None) -> List[List[float]]:
    """
    Convenience function to generate embeddings for multiple texts.
    
    Args:
        texts: List of texts to embed
        model: Model name (defaults to config)
        
    Returns:
        List of embedding vectors
    """
    generator = EmbeddingGenerator(model=model)
    return generator.generate_batch(texts)


def main():
    """
    Main function to generate embeddings from processed snippets.
    """
    # Load clean snippets
    snippets_file = Path("data/processed/clean_snippets.jsonl")
    
    if not snippets_file.exists():
        print(f"Error: {snippets_file} not found!")
        print("Run data processing first.")
        return
    
    # Load snippets
    print(f"Loading snippets from {snippets_file}...")
    snippets = []
    with open(snippets_file) as f:
        for line in f:
            snippets.append(json.loads(line))
    
    print(f"Loaded {len(snippets)} snippets")
    
    # Generate embeddings
    generator = EmbeddingGenerator()
    output_file = Path("data/processed/embeddings.jsonl")
    
    stats = generator.generate_from_snippets(snippets, output_file)
    
    # Save statistics
    stats_file = Path("data/processed/embedding_stats.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\nStatistics saved to {stats_file}")


if __name__ == "__main__":
    main()
