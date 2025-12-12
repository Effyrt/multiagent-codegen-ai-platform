#!/usr/bin/env python3
"""
CodeGen AI - Account Setup Helper Script
Helps set up and test OpenAI and Pinecone accounts
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def test_openai_api():
    """Test OpenAI API connection"""
    print("🔑 Testing OpenAI API connection...")

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    if not api_key.startswith('sk-'):
        print("❌ OPENAI_API_KEY doesn't look like a valid OpenAI key (should start with 'sk-')")
        return False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, test message"}],
            max_tokens=10
        )

        print("✅ OpenAI API connection successful")
        print(f"   Response: {response.choices[0].message.content.strip()}")
        return True

    except Exception as e:
        print(f"❌ OpenAI API test failed: {str(e)}")
        return False

def test_pinecone_connection():
    """Test Pinecone connection"""
    print("🌲 Testing Pinecone connection...")

    api_key = os.getenv('PINECONE_API_KEY')
    environment = os.getenv('PINECONE_ENVIRONMENT')

    if not api_key:
        print("❌ PINECONE_API_KEY not found in environment")
        return False

    if not environment:
        print("❌ PINECONE_ENVIRONMENT not found in environment")
        return False

    try:
        import pinecone
        pinecone.init(api_key=api_key, environment=environment)

        # List indexes
        indexes = pinecone.list_indexes()
        print("✅ Pinecone connection successful")
        print(f"   Available indexes: {indexes}")

        return True

    except Exception as e:
        print(f"❌ Pinecone connection failed: {str(e)}")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("📄 Checking environment configuration...")

    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found. Copy .env.example to .env and add your API keys")
        return False

    # Load environment variables
    load_dotenv()

    required_vars = [
        'OPENAI_API_KEY',
        'PINECONE_API_KEY',
        'PINECONE_ENVIRONMENT',
        'PINECONE_INDEX_NAME'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("   Please add these to your .env file")
        return False

    print("✅ All required environment variables found")
    return True

def create_pinecone_index():
    """Create Pinecone index if it doesn't exist"""
    print("🏗️ Checking Pinecone index...")

    index_name = os.getenv('PINECONE_INDEX_NAME')
    if not index_name:
        print("❌ PINECONE_INDEX_NAME not set")
        return False

    try:
        import pinecone
        pinecone.init(
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT')
        )

        # Check if index exists
        indexes = pinecone.list_indexes()
        if index_name in indexes:
            print(f"✅ Index '{index_name}' already exists")
            # Check index stats
            index = pinecone.Index(index_name)
            stats = index.describe_index_stats()
            print(f"   Vectors: {stats.total_vector_count}")
            return True

        # Create index
        print(f"📝 Creating index '{index_name}'...")
        pinecone.create_index(
            name=index_name,
            dimension=3072,  # text-embedding-3-large
            metric="cosine"
        )
        print(f"✅ Index '{index_name}' created successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to create/check Pinecone index: {str(e)}")
        return False

def main():
    """Run account setup checks"""
    print("🚀 CodeGen AI - Account Setup Verification")
    print("=" * 50)

    # Check environment file
    if not check_env_file():
        print("\n❌ Environment setup incomplete. Please:")
        print("1. Copy .env.example to .env")
        print("2. Add your API keys to .env")
        print("3. Run this script again")
        return 1

    print()

    # Test connections
    openai_ok = test_openai_api()
    pinecone_ok = test_pinecone_connection()

    print()

    # Create Pinecone index if needed
    if pinecone_ok:
        index_ok = create_pinecone_index()
    else:
        index_ok = False

    print("\n" + "=" * 50)
    print("📊 ACCOUNT SETUP SUMMARY")

    all_good = openai_ok and pinecone_ok and index_ok

    if all_good:
        print("🎉 ALL ACCOUNTS CONFIGURED SUCCESSFULLY!")
        print("\n✅ Ready to proceed with Phase 2 - Data Collection")
        print("✅ OpenAI API: Connected and tested")
        print("✅ Pinecone: Connected and index ready")
        return 0
    else:
        print("⚠️ SOME ACCOUNTS NEED ATTENTION")
        print(f"✅ OpenAI API: {'Ready' if openai_ok else 'Needs setup'}")
        print(f"✅ Pinecone: {'Ready' if pinecone_ok else 'Needs setup'}")
        print(f"✅ Index: {'Ready' if index_ok else 'Needs creation'}")

        print("\n🔧 SETUP INSTRUCTIONS:")
        if not openai_ok:
            print("• OpenAI: Get API key at https://platform.openai.com/api-keys")
        if not pinecone_ok:
            print("• Pinecone: Create account at https://app.pinecone.io/")
        if not index_ok:
            print("• Index will be created automatically once Pinecone is connected")

        return 1

if __name__ == "__main__":
    sys.exit(main())




