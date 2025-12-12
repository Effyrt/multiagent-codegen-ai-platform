#!/usr/bin/env python3
"""
Base Agent Configuration - Shared utilities for all agents
Provides common functionality, logging, and configuration
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BaseAgent:
    """
    Base class providing common functionality for all agents
    """

    def __init__(self, model: str = "gpt-4", temperature: float = 0.2):
        """Initialize base agent with common configuration"""
        self.model = model
        self.temperature = temperature

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging for agent activities"""
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(logs_dir / f"{self.__class__.__name__.lower()}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def log_activity(self, activity: str, details: Dict[str, Any] = None):
        """Log agent activity"""
        message = f"{activity}"
        if details:
            message += f" - {details}"
        self.logger.info(message)

    def validate_environment(self) -> bool:
        """Validate that required environment variables are set"""
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            self.logger.error(f"Missing required environment variables: {missing_vars}")
            return False

        return True

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(text) // 4

    def track_usage(self, prompt_tokens: int, completion_tokens: int, cost_per_1k: float = 0.03):
        """Track API usage and estimated cost"""
        total_tokens = prompt_tokens + completion_tokens
        estimated_cost = (total_tokens / 1000) * cost_per_1k

        self.log_activity("API Usage", {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": f"${estimated_cost:.4f}"
        })

        return {
            "tokens": total_tokens,
            "cost": estimated_cost
        }

# Global configuration
AGENT_CONFIG = {
    "model": os.getenv("AGENT_MODEL", "gpt-4"),
    "temperature": float(os.getenv("AGENT_TEMPERATURE", "0.2")),
    "max_tokens": int(os.getenv("AGENT_MAX_TOKENS", "2000")),
    "timeout": int(os.getenv("AGENT_TIMEOUT", "60"))
}

def create_agent_llm(model: str = None, temperature: float = None) -> ChatOpenAI:
    """Factory function to create LLM instances for agents"""
    return ChatOpenAI(
        model=model or AGENT_CONFIG["model"],
        temperature=temperature or AGENT_CONFIG["temperature"],
        max_tokens=AGENT_CONFIG["max_tokens"],
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

def validate_agent_environment() -> Dict[str, Any]:
    """Validate the environment for all agents"""
    issues = []
    warnings = []

    # Check API keys
    if not os.getenv("OPENAI_API_KEY"):
        issues.append("OPENAI_API_KEY not set")

    if not os.getenv("PINECONE_API_KEY"):
        warnings.append("PINECONE_API_KEY not set (optional for basic functionality)")

    # Check directories
    required_dirs = ["logs", "src/agents/prompts"]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            warnings.append(f"Created missing directory: {dir_path}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }

if __name__ == "__main__":
    # Test base agent setup
    print("Testing base agent configuration...")

    validation = validate_agent_environment()
    if validation["valid"]:
        print("✅ Environment validation passed")
    else:
        print("❌ Environment validation failed:")
        for issue in validation["issues"]:
            print(f"  - {issue}")

    if validation["warnings"]:
        print("⚠️ Warnings:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")

    # Test base agent
    try:
        base_agent = BaseAgent()
        print("✅ Base agent initialized successfully")
    except Exception as e:
        print(f"❌ Base agent initialization failed: {e}")

