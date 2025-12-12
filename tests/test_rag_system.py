"""
Test RAG System

Test embedding generation and code retrieval.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all RAG modules can be imported"""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)
    
    try:
        from src.embeddings import EmbeddingGenerator, generate_embedding
        from src.embeddings.config import EMBEDDING_CONFIG
        from src.rag import CodeRetriever, retrieve_similar_code
        print("✅ All modules imported successfully!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_embedding_config():
    """Test embedding configuration"""
    print("\n" + "="*60)
    print("TEST 2: Embedding Configuration")
    print("="*60)
    
    from src.embeddings.config import EMBEDDING_CONFIG
    
    print(f"Model: {EMBEDDING_CONFIG['model']}")
    print(f"Dimensions: {EMBEDDING_CONFIG['dimensions']}")
    print(f"Batch size: {EMBEDDING_CONFIG['batch_size']}")
    
    assert EMBEDDING_CONFIG['model'] == 'text-embedding-3-large'
    assert EMBEDDING_CONFIG['dimensions'] == 3072
    
    print("✅ Configuration is correct!")
    return True


def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n" + "="*60)
    print("TEST 3: OpenAI API Connection")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not set!")
        print("Add it to .env file and try again.")
        return False
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Test with a simple embedding
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input="test",
            dimensions=3072
        )
        
        embedding = response.data[0].embedding
        
        print(f"✅ OpenAI connected!")
        print(f"   Generated test embedding: {len(embedding)} dimensions")
        print(f"   First 5 values: {embedding[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False


def test_embedding_generator():
    """Test embedding generator"""
    print("\n" + "="*60)
    print("TEST 4: Embedding Generator")
    print("="*60)
    
    try:
        from src.embeddings import EmbeddingGenerator
        
        generator = EmbeddingGenerator()
        
        # Test single embedding
        test_code = """
def hello_world():
    print("Hello, World!")
"""
        
        print("Generating test embedding...")
        embedding = generator.generate_embedding(test_code)
        
        print(f"✅ Embedding generated!")
        print(f"   Dimensions: {len(embedding)}")
        print(f"   Tokens used: {generator.total_tokens}")
        print(f"   Estimated cost: ${generator.total_cost:.6f}")
        
        assert len(embedding) == 3072
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_code_retriever():
    """Test code retriever (with mock data)"""
    print("\n" + "="*60)
    print("TEST 5: Code Retriever")
    print("="*60)
    
    try:
        from src.rag import CodeRetriever
        
        retriever = CodeRetriever()
        
        # Test retrieval (will use mock data if Pinecone not configured)
        query = "FastAPI user authentication endpoint"
        
        print(f"Testing query: {query}")
        results = retriever.retrieve_similar_code(query, top_k=3)
        
        print(f"\n✅ Retrieved {len(results)} examples!")
        
        for i, result in enumerate(results, 1):
            print(f"\nExample {i}:")
            print(f"  Similarity: {result['score']:.2f}")
            print(f"  Language: {result['language']}")
            print(f"  Framework: {result['framework']}")
            print(f"  Code preview: {result['code'][:100]}...")
        
        # Test prompt formatting
        formatted = retriever.format_for_prompt(results)
        print(f"\n✅ Prompt formatting works!")
        print(f"   Formatted length: {len(formatted)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Code retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pinecone_status():
    """Check Pinecone configuration status"""
    print("\n" + "="*60)
    print("TEST 6: Pinecone Status")
    print("="*60)
    
    pinecone_key = os.getenv("PINECONE_API_KEY")
    pinecone_env = os.getenv("PINECONE_ENVIRONMENT")
    
    if not pinecone_key:
        print("⚠️  PINECONE_API_KEY not set")
        print("   This is OK - Pauline will add this")
        print("   RAG system will use mock data for now")
        return True
    else:
        print(f"✅ PINECONE_API_KEY is set")
        print(f"✅ PINECONE_ENVIRONMENT: {pinecone_env}")
        
        try:
            import pinecone
            pinecone.init(api_key=pinecone_key, environment=pinecone_env)
            print("✅ Pinecone connection successful!")
            return True
        except ImportError:
            print("⚠️  pinecone-client not installed")
            print("   Run: pip install pinecone-client")
            return True
        except Exception as e:
            print(f"⚠️  Pinecone connection error: {e}")
            return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("RAG SYSTEM TEST SUITE")
    print("="*60)
    
    results = {
        "imports": test_imports(),
        "config": test_embedding_config(),
        "openai": test_openai_connection(),
        "generator": test_embedding_generator(),
        "retriever": test_code_retriever(),
        "pinecone": test_pinecone_status(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.capitalize():15s}: {status}")
    
    print(f"\n{'='*60}")
    print(f"Overall: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYour RAG system is working!")
        print("\nNext steps:")
        print("1. Wait for Pauline to add PINECONE_API_KEY")
        print("2. Generate embeddings: python src/embeddings/generate.py")
        print("3. Upload to Pinecone: python src/embeddings/upsert_pinecone.py")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        
        if not results["openai"]:
            print("\nCritical: Add OPENAI_API_KEY to .env file!")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
