#!/usr/bin/env python3
"""
CodeGen AI - Setup Verification Script
Tests basic functionality and environment setup
"""

import sys
import os
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.11+")
        return False

def check_project_structure():
    """Verify project directory structure"""
    print("\n📁 Checking project structure...")

    required_dirs = [
        "src/agents",
        "src/backend",
        "src/frontend",
        "src/rag",
        "src/embeddings",
        "src/etl",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "logs",
        "scripts"
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)

    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    else:
        print("✅ All required directories present")
        return True

def check_configuration_files():
    """Check configuration files exist"""
    print("\n⚙️ Checking configuration files...")

    required_files = [
        ".gitignore",
        ".env.example",
        "requirements.txt",
        "README.md",
        "Roadmap.md"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All configuration files present")
        return True

def test_basic_imports():
    """Test basic Python imports work"""
    print("\n📦 Testing basic imports...")

    basic_modules = [
        "os", "sys", "pathlib", "json", "re"
    ]

    failed_imports = []
    for module in basic_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError:
            failed_imports.append(module)
            print(f"❌ {module}")

    if failed_imports:
        print(f"❌ Failed imports: {failed_imports}")
        return False
    else:
        print("✅ All basic imports successful")
        return True

def check_environment_variables():
    """Check if .env.example has required variables"""
    print("\n🔑 Checking environment variables template...")

    env_file = Path(".env.example")
    if not env_file.exists():
        print("❌ .env.example not found")
        return False

    content = env_file.read_text()
    required_vars = [
        "OPENAI_API_KEY",
        "PINECONE_API_KEY",
        "PINECONE_ENVIRONMENT",
        "PINECONE_INDEX_NAME",
        "APP_ENV",
        "FASTAPI_HOST",
        "FASTAPI_PORT"
    ]

    missing_vars = []
    for var in required_vars:
        if var not in content:
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables defined")
        return True

def check_requirements_file():
    """Verify requirements.txt has core dependencies"""
    print("\n📋 Checking requirements.txt...")

    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found")
        return False

    content = req_file.read_text()
    core_packages = [
        "openai",
        "crewai",
        "fastapi",
        "uvicorn",
        "streamlit",
        "pinecone-client",
        "pydantic",
        "pytest"
    ]

    missing_packages = []
    for package in core_packages:
        if package not in content:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing core packages: {missing_packages}")
        return False
    else:
        print("✅ All core packages in requirements.txt")
        return True

def main():
    """Run all setup checks"""
    print("🚀 CodeGen AI - Setup Verification")
    print("=" * 50)

    checks = [
        check_python_version,
        check_project_structure,
        check_configuration_files,
        test_basic_imports,
        check_environment_variables,
        check_requirements_file
    ]

    results = []
    for check in checks:
        results.append(check())

    print("\n" + "=" * 50)
    print("📊 SUMMARY")

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 ALL CHECKS PASSED ({passed}/{total})")
        print("\n✅ Phase 1 setup is complete!")
        print("Next: Proceed to Phase 2 - Data Collection")
        return 0
    else:
        print(f"⚠️ SOME CHECKS FAILED ({passed}/{total})")
        print("\n❌ Please fix the failed checks before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())




