"""
Pinecone Upsert

Upload embeddings to Pinecone vector database.

NOTE: Requires PINECONE_API_KEY to be set by teammate (Pauline).
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm


class PineconeUploader:
    """
    Upload embeddings to Pinecone vector database.
    
    NOTE: This requires pinecone-client to be installed and configured.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: Optional[str] = None
    ):
        """
        Initialize Pinecone uploader.
        
        Args:
            api_key: Pinecone API key (defaults to env variable)
            environment: Pinecone environment (defaults to env variable)
            index_name: Index name (defaults to env variable)
        """
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
        self.index_name = index_name or os.getenv("PINECONE_INDEX", "codegen-ai-dev")
        
        if not self.api_key:
            print("⚠️  PINECONE_API_KEY not set!")
            print("Waiting for teammate (Pauline) to configure Pinecone.")
            self.pinecone_available = False
            return
        
        try:
            # Import and initialize Pinecone
            import pinecone
            
            pinecone.init(
                api_key=self.api_key,
                environment=self.environment
            )
            
            self.pinecone = pinecone
            self.pinecone_available = True
            
            # Check if index exists, create if not
            self._ensure_index_exists()
            
            # Connect to index
            self.index = pinecone.Index(self.index_name)
            
            print(f"✅ Connected to Pinecone index: {self.index_name}")
            
        except ImportError:
            print("⚠️  pinecone-client not installed!")
            print("Run: pip install pinecone-client")
            self.pinecone_available = False
        except Exception as e:
            print(f"⚠️  Error initializing Pinecone: {e}")
            self.pinecone_available = False
    
    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        existing_indexes = self.pinecone.list_indexes()
        
        if self.index_name not in existing_indexes:
            print(f"Creating index: {self.index_name}...")
            self.pinecone.create_index(
                name=self.index_name,
                dimension=3072,  # text-embedding-3-large dimensions
                metric="cosine",
                pod_type="p1.x1"  # Free tier
            )
            # Wait for index to be ready
            time.sleep(10)
            print(f"✅ Index created: {self.index_name}")
    
    def upsert_embeddings(
        self, 
        embeddings_file: Path,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Upload embeddings from file to Pinecone.
        
        Args:
            embeddings_file: Path to embeddings JSONL file
            batch_size: Number of vectors to upload per batch
            
        Returns:
            Statistics dictionary
        """
        if not self.pinecone_available:
            print("\n❌ Pinecone not available!")
            print("This requires Pauline to add PINECONE_API_KEY to .env")
            return {
                "status": "skipped",
                "message": "Pinecone not configured"
            }
        
        print(f"Uploading embeddings from {embeddings_file}...")
        
        # Load embeddings
        embeddings = []
        with open(embeddings_file) as f:
            for line in f:
                embeddings.append(json.loads(line))
        
        print(f"Loaded {len(embeddings)} embeddings")
        
        # Upload in batches
        total_uploaded = 0
        
        with tqdm(total=len(embeddings), desc="Uploading to Pinecone") as pbar:
            for i in range(0, len(embeddings), batch_size):
                batch = embeddings[i:i + batch_size]
                
                # Format for Pinecone
                vectors = []
                for item in batch:
                    vectors.append({
                        "id": item["id"],
                        "values": item["embedding"],
                        "metadata": item["metadata"]
                    })
                
                try:
                    # Upsert to Pinecone
                    self.index.upsert(vectors=vectors)
                    total_uploaded += len(vectors)
                    pbar.update(len(batch))
                    
                    # Small delay to avoid rate limits
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"\nError uploading batch {i}: {e}")
                    continue
        
        # Get index stats
        stats = self.index.describe_index_stats()
        
        result = {
            "status": "success",
            "vectors_uploaded": total_uploaded,
            "index_name": self.index_name,
            "total_vectors_in_index": stats.get("total_vector_count", 0),
            "dimensions": 3072,
        }
        
        print(f"\n{'='*60}")
        print("Upload Complete!")
        print(f"{'='*60}")
        print(f"Vectors uploaded: {result['vectors_uploaded']}")
        print(f"Index: {result['index_name']}")
        print(f"Total in index: {result['total_vectors_in_index']}")
        print(f"{'='*60}")
        
        return result


def main():
    """
    Main function to upload embeddings to Pinecone.
    """
    embeddings_file = Path("data/processed/embeddings.jsonl")
    
    if not embeddings_file.exists():
        print(f"Error: {embeddings_file} not found!")
        print("Run embedding generation first: python src/embeddings/generate.py")
        return
    
    # Initialize uploader
    uploader = PineconeUploader()
    
    if not uploader.pinecone_available:
        print("\n" + "="*60)
        print("⚠️  PINECONE SETUP REQUIRED")
        print("="*60)
        print("\nAction needed by Pauline:")
        print("1. Go to: https://app.pinecone.io/")
        print("2. Create free account")
        print("3. Copy API key")
        print("4. Add to .env file:")
        print("   PINECONE_API_KEY=your_key_here")
        print("   PINECONE_ENVIRONMENT=us-east-1-aws")
        print("\nThen run this script again!")
        print("="*60)
        return
    
    # Upload embeddings
    result = uploader.upsert_embeddings(embeddings_file)
    
    # Save stats
    if result["status"] == "success":
        stats_file = Path("data/processed/pinecone_upload_stats.json")
        with open(stats_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nStatistics saved to {stats_file}")


if __name__ == "__main__":
    main()
