#!/usr/bin/env python3
"""
CodeGen AI - Multi-Agent System Package
Integrating AgentCoder principles with CrewAI orchestration
"""

from .base_agent import BaseAgent, validate_agent_environment
from .requirements_agent import RequirementsAgent, RequirementsSpec
from .programmer_agent import ProgrammerAgent
from .test_designer_agent import TestDesignerAgent
from .test_executor_agent import TestExecutorAgent
from .docs_agent import DocsAgent
from .crew_orchestrator import CodeGenerationCrew, generate_code_simple, generate_code_advanced

__version__ = "1.0.0"
__author__ = "CodeGen AI Team"

__all__ = [
    # Base classes
    "BaseAgent",
    "validate_agent_environment",

    # Core agents
    "RequirementsAgent",
    "ProgrammerAgent",
    "TestDesignerAgent",
    "TestExecutorAgent",
    "DocsAgent",

    # Data models
    "RequirementsSpec",

    # Orchestration
    "CodeGenerationCrew",
    "generate_code_simple",
    "generate_code_advanced"
]

# Package metadata
PACKAGE_INFO = {
    "name": "codegen-agents",
    "version": __version__,
    "description": "Multi-agent code generation system based on AgentCoder principles",
    "agents": [
        "Requirements Analyzer",
        "Programmer (Code Generator)",
        "Test Designer (Independent)",
        "Test Executor (Sandbox)",
        "Documentation Generator"
    ],
    "key_features": [
        "Independent test design",
        "Iterative code refinement",
        "Docker sandbox testing",
        "RAG-enhanced generation",
        "Comprehensive documentation"
    ]
}

def get_package_info():
    """Get package information"""
    return PACKAGE_INFO

def list_agents():
    """List available agents"""
    return PACKAGE_INFO["agents"]

def test_agents():
    """Test all agents are importable"""
    try:
        # Test imports
        agents = [
            RequirementsAgent(),
            ProgrammerAgent(),
            TestDesignerAgent(),
            TestExecutorAgent(),
            DocsAgent()
        ]

        # Test environment
        env_check = validate_agent_environment()

        return {
            "agents_importable": True,
            "agent_count": len(agents),
            "environment_valid": env_check["valid"],
            "warnings": env_check["warnings"],
            "issues": env_check["issues"]
        }

    except Exception as e:
        return {
            "agents_importable": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Package test
    print("CodeGen AI Agents Package")
    print("=" * 30)

    info = get_package_info()
    print(f"Version: {info['version']}")
    print(f"Agents: {len(info['agents'])}")
    print("\nAgent List:")
    for i, agent in enumerate(info['agents'], 1):
        print(f"{i}. {agent}")

    print("\nTesting agents...")
    test_result = test_agents()

    if test_result["agents_importable"]:
        print("✅ All agents importable")
        print(f"   Agent count: {test_result['agent_count']}")

        if test_result["environment_valid"]:
            print("✅ Environment validation passed")
        else:
            print("⚠️ Environment issues:")
            for issue in test_result["issues"]:
                print(f"   - {issue}")

        if test_result["warnings"]:
            print("ℹ️ Environment warnings:")
            for warning in test_result["warnings"]:
                print(f"   - {warning}")
    else:
        print(f"❌ Agent import failed: {test_result.get('error', 'Unknown error')}")

