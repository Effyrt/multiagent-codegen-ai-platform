from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append('.')

from utils.rag import RAGRetriever

print("Testing RAG...")
rag = RAGRetriever()
print("✅ RAG initialized!")
