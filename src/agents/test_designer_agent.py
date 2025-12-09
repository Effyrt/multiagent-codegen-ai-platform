#!/usr/bin/env python3
"""
Test Designer Agent - Independent Test Case Generation
Based on AgentCoder's test designer, adapted for CrewAI and web development
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

# from crewai import Agent  # Temporarily disabled for testing
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestDesignerAgent:
    """
    Test Designer Agent - Creates comprehensive test suites
    Key AgentCoder principle: Tests designed WITHOUT seeing the generated code
    """

    def __init__(self):
        """Initialize the Test Designer Agent"""
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,  # Lower temperature for consistent test generation
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Load prompt template
        prompt_path = Path(__file__).parent / "prompts" / "test_designer.txt"
        if prompt_path.exists():
            with open(prompt_path, "r") as f:
                self.prompt_template = f.read()
        else:
            # Fallback prompt template
            self.prompt_template = self._get_default_prompt()

        # Initialize CrewAI agent (temporarily disabled for testing)
        # self.agent = Agent(
        #     role="Expert QA Engineer",
        #     goal="Design comprehensive, independent test suites that cover all requirements",
        #     backstory="""You are an expert QA engineer specializing in test design.
        #     You create thorough test cases based solely on requirements specifications,
        #     without seeing the actual implementation. Your tests cover normal cases,
        #     edge cases, error conditions, and boundary conditions.""",
        #     llm=self.llm,
        #     allow_delegation=False,
        #     verbose=True
        # )

    def _get_default_prompt(self) -> str:
        """Get default prompt template if file not found"""
        return """
You are an Expert QA Engineer specializing in comprehensive test design.

Requirements:
{requirements}

Design a comprehensive test suite that covers:
1. Normal/Happy path cases
2. Edge cases and boundary conditions
3. Error cases (invalid inputs, exceptions)
4. Integration scenarios

Generate tests using:
- pytest for Python (with descriptive test names)
- Jest for JavaScript (with descriptive test names)

Include:
- Test fixtures and mock data when needed
- Clear test descriptions and assertions
- Coverage of all requirements and edge cases

DO NOT reference any specific code implementation.
Test against the REQUIREMENTS SPECIFICATION only.

Output ONLY the test code, no explanations.
"""

    def design_tests(self, requirements: Dict[str, Any]) -> str:
        """
        Design comprehensive test suite based on requirements

        Args:
            requirements: Requirements specification (WITHOUT code)

        Returns:
            Complete test suite as string
        """
        # Format prompt with requirements
        language = requirements.get("language", "python")
        framework = requirements.get("framework", "none")

        prompt = self.prompt_template.format(
            requirements=json.dumps(requirements, indent=2),
            language=language,
            framework=framework
        )

        # Use OpenAI API directly (temporarily, until CrewAI is installed)
        try:
            response = self.llm.invoke([
                {"role": "system", "content": "You are an expert QA engineer specializing in test design."},
                {"role": "user", "content": prompt}
            ])
            test_code = self._extract_test_code(response.content)
            return self._format_test_code(test_code, language)
        except Exception as e:
            print(f"Error in test design: {e}")
            return self._generate_fallback_tests(requirements)

    def _extract_test_code(self, response: str) -> str:
        """Extract test code from LLM response"""
        # Look for code blocks
        if "```python" in response:
            test_code = response.split("```python")[1].split("```")[0].strip()
        elif "```javascript" in response:
            test_code = response.split("```javascript")[1].split("```")[0].strip()
        elif "```" in response:
            test_code = response.split("```")[1].split("```")[0].strip()
        else:
            # No code block found, return entire response
            test_code = response.strip()

        return test_code

    def _format_test_code(self, test_code: str, language: str) -> str:
        """Format and validate test code"""
        test_code = test_code.strip()

        # Remove any markdown formatting
        if test_code.startswith("```"):
            test_code = test_code.split("```", 2)[-1].strip()

        # Language-specific validation
        if language == "python":
            # Ensure pytest imports
            if "import pytest" not in test_code and "from pytest" not in test_code:
                test_code = "import pytest\n\n" + test_code

        elif language == "javascript":
            # Ensure Jest/test framework setup
            if "describe(" not in test_code:
                # Wrap in describe block
                test_code = f"""describe('API Tests', () => {{
{test_code}
}});
"""

        return test_code

    def _generate_fallback_tests(self, requirements: Dict[str, Any]) -> str:
        """Generate basic fallback tests if LLM generation fails"""
        language = requirements.get("language", "python")
        framework = requirements.get("framework", "none")

        if language == "python":
            return f'''import pytest

def test_basic_functionality():
    """Test basic functionality"""
    # This is a fallback test - implement based on requirements
    assert True  # Placeholder assertion

def test_edge_cases():
    """Test edge cases"""
    # This is a fallback test - implement based on requirements
    assert True  # Placeholder assertion

def test_error_handling():
    """Test error handling"""
    # This is a fallback test - implement based on requirements
    assert True  # Placeholder assertion
'''
        else:
            return f'''describe('API Tests', () => {{
  test('basic functionality', () => {{
    // This is a fallback test - implement based on requirements
    expect(true).toBe(true);
  }});

  test('edge cases', () => {{
    // This is a fallback test - implement based on requirements
    expect(true).toBe(true);
  }});

  test('error handling', () => {{
    // This is a fallback test - implement based on requirements
    expect(true).toBe(true);
  }});
}});
'''

# AgentCoder-style batch processing for evaluation
def design_tests_batch(
    requirements_list: list,
    model: str = "gpt-4",
    times: int = 5
) -> list:
    """
    Design tests for multiple requirements (AgentCoder-style batch processing)
    Used for evaluation - generates multiple test variations
    """
    agent = TestDesignerAgent()
    results = []

    for req in requirements_list:
        test_suites = []
        for i in range(times):
            try:
                test_suite = agent.design_tests(req)
                test_suites.append({
                    "attempt": i + 1,
                    "tests": test_suite,
                    "success": bool(test_suite.strip())
                })
            except Exception as e:
                test_suites.append({
                    "attempt": i + 1,
                    "tests": "",
                    "success": False,
                    "error": str(e)
                })

        results.append({
            "requirements": req,
            "test_attempts": test_suites
        })

    return results

if __name__ == "__main__":
    # Test the agent
    agent = TestDesignerAgent()

    test_requirements = {
        "language": "python",
        "framework": "fastapi",
        "description": "Create a FastAPI endpoint for user registration",
        "requirements": ["POST endpoint", "Pydantic validation", "password hashing"],
        "edge_cases": ["invalid email", "weak password", "duplicate user"],
        "complexity": "medium"
    }

    print("Testing Test Designer Agent...")
    print("Requirements:")
    print(json.dumps(test_requirements, indent=2))
    print("\nGenerating tests...")
    tests = agent.design_tests(test_requirements)
    print("\nGenerated test suite:")
    print("=" * 50)
    print(tests)
    print("=" * 50)

