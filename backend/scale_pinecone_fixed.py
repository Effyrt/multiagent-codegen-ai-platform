import os
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI
import time

load_dotenv('../.env')

print("🚀 Starting Pinecone scaling...")

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index('codegen-ai-embeddings')
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

initial_stats = index.describe_index_stats()
initial_count = initial_stats.get('total_vector_count', 0)
print(f"📊 Starting count: {initial_count} vectors\n")

patterns = [
    "python fastapi rest api", "python flask authentication", "python django model",
    "javascript react component", "javascript express middleware", "javascript vue component",
    "binary search algorithm", "merge sort implementation", "quicksort algorithm",
    "breadth first search", "depth first search", "dijkstra algorithm",
    "fibonacci memoization", "hash table implementation", "linked list operations",
    "binary tree traversal", "stack implementation", "queue implementation",
    "sql select join", "mongodb query", "postgresql connection",
    "rest api endpoint", "graphql resolver", "api rate limiting",
    "password hashing", "jwt token", "oauth2 implementation",
    "docker container", "kubernetes deployment", "ci cd pipeline",
    "pandas dataframe", "numpy array", "matplotlib visualization",
]

vectors = []
vector_id = initial_count
success_count = 0

print("🔄 Generating embeddings with text-embedding-3-large...\n")

for i, pattern in enumerate(patterns, 1):
    for complexity in ["simple", "medium", "complex"]:
        for style in ["production", "optimized"]:
            description = f"{pattern} - {complexity} {style} implementation"
            
            try:
                # Use text-embedding-3-large (3072 dimensions)
                response = openai_client.embeddings.create(
                    model="text-embedding-3-large",
                    input=description
                )
                
                embedding = response.data[0].embedding
                language = "python" if "python" in pattern else "javascript" if "javascript" in pattern else "general"
                
                vectors.append({
                    'id': f'code_{vector_id}',
                    'values': embedding,
                    'metadata': {
                        'description': description,
                        'pattern': pattern,
                        'complexity': complexity,
                        'quality_score': 8.5,
                        'language': language,
                    }
                })
                
                vector_id += 1
                success_count += 1
                
                if len(vectors) >= 50:
                    index.upsert(vectors=vectors)
                    print(f"✅ Upserted batch | Total: {vector_id} vectors | Pattern {i}/{len(patterns)}")
                    vectors = []
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Error: {e}")

if vectors:
    index.upsert(vectors=vectors)

time.sleep(2)
final_stats = index.describe_index_stats()
final_count = final_stats.get('total_vector_count', 0)

print("\n" + "="*60)
print("🎉 COMPLETE!")
print(f"📊 Started: {initial_count} | Final: {final_count} | Added: {final_count - initial_count}")
print("="*60)
