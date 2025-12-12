#!/usr/bin/env python3
"""
Programmer Agent - Code Generation Agent
Based on AgentCoder's programmer implementation, adapted for CrewAI and web development
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

# from crewai import Agent  # Temporarily disabled for testing
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ProgrammerAgent:
    """
    Programmer Agent - Generates production-ready code
    Based on AgentCoder's programmer with CrewAI integration
    """

    def __init__(self):
        """Initialize the Programmer Agent"""
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.2,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Load prompt template
        prompt_path = Path(__file__).parent / "prompts" / "programmer.txt"
        if prompt_path.exists():
            with open(prompt_path, "r") as f:
                self.prompt_template = f.read()
        else:
            # Fallback prompt template
            self.prompt_template = self._get_default_prompt()

        # Initialize CrewAI agent (temporarily disabled for testing)
        # self.agent = Agent(
        #     role="Expert Software Engineer",
        #     goal="Generate production-ready, high-quality code that meets all requirements",
        #     backstory="""You are an expert software engineer with years of experience in web development.
        #     You specialize in writing clean, maintainable, and efficient code. You always include proper
        #     error handling, type hints, and comprehensive docstrings. You follow best practices and
        #     security guidelines.""",
        #     llm=self.llm,
        #     allow_delegation=False,
        #     verbose=True
        # )

    def _get_default_prompt(self) -> str:
        """Get default prompt template if file not found"""
        return """
You are an Expert Software Engineer specializing in {language} and {framework}.

Requirements:
{requirements}

Similar Code Examples (for reference):
{rag_examples}

Previous Attempt (if refinement):
{previous_code}

Test Failures (if refinement):
{test_feedback}

Generate production-ready code that:
- Follows best practices and coding standards
- Includes type hints (Python) / JSDoc (JavaScript)
- Has comprehensive error handling
- Includes docstrings and comments
- Is secure (no SQL injection, validated inputs)
- Handles all edge cases mentioned in requirements

Output ONLY the code, no explanations.
"""

    def generate_code(
        self,
        requirements: Dict[str, Any],
        rag_examples: str = "",
        previous_code: str = "",
        test_feedback: str = ""
    ) -> str:
        """
        Generate code based on requirements

        Args:
            requirements: Parsed requirements specification
            rag_examples: Similar code examples from RAG
            previous_code: Previous code attempt (for refinement)
            test_feedback: Test execution feedback (for refinement)

        Returns:
            Generated code as string
        """
        # Format prompt with requirements
        language = requirements.get("language", "python")
        framework = requirements.get("framework", "none")

        prompt = self.prompt_template.format(
            language=language,
            framework=framework,
            requirements=json.dumps(requirements, indent=2),
            rag_examples=rag_examples,
            previous_code=previous_code,
            test_feedback=test_feedback
        )

        # Use OpenAI API directly (temporarily, until CrewAI is installed)
        try:
            response = self.llm.invoke([
                {"role": "system", "content": "You are an expert software engineer."},
                {"role": "user", "content": prompt}
            ])
            code = self._extract_code_from_response(response.content)
            return self._format_code(code, language)
        except Exception as e:
            print(f"Error in code generation: {e}")
            return ""

    def _extract_code_from_response(self, response: str) -> str:
        """Extract code from LLM response"""
        # Look for code blocks
        if "```python" in response:
            code = response.split("```python")[1].split("```")[0].strip()
        elif "```javascript" in response:
            code = response.split("```javascript")[1].split("```")[0].strip()
        elif "```" in response:
            code = response.split("```")[1].split("```")[0].strip()
        else:
            # No code block found, return entire response
            code = response.strip()

        return code

    def _format_code(self, code: str, language: str) -> str:
        """Format and clean generated code"""
        # Basic formatting
        code = code.strip()

        # Remove any markdown formatting
        if code.startswith("```"):
            code = code.split("```", 2)[-1].strip()

        # Language-specific formatting
        if language == "python":
            # Ensure proper indentation
            lines = code.split('\n')
            formatted_lines = []

            for line in lines:
                # Skip empty lines at start
                if not formatted_lines and not line.strip():
                    continue
                formatted_lines.append(line)

            code = '\n'.join(formatted_lines)

        return code

    def refine_code(
        self,
        requirements: Dict[str, Any],
        current_code: str,
        test_feedback: str,
        rag_examples: str = ""
    ) -> str:
        """
        Refine existing code based on test feedback

        Args:
            requirements: Original requirements
            current_code: Current code that failed tests
            test_feedback: Feedback from test execution
            rag_examples: RAG examples for guidance

        Returns:
            Refined code
        """
        return self.generate_code(
            requirements=requirements,
            rag_examples=rag_examples,
            previous_code=current_code,
            test_feedback=test_feedback
        )

# AgentCoder-style batch processing (for evaluation)
def generate_code_batch(
    requirements_list: list,
    model: str = "gpt-4",
    times: int = 3
) -> list:
    """
    Generate code for multiple requirements (AgentCoder-style batch processing)
    Used for evaluation and testing
    """
    agent = ProgrammerAgent()
    results = []

    for req in requirements_list:
        codes = []
        for i in range(times):
            try:
                code = agent.generate_code(req)
                codes.append({
                    "attempt": i + 1,
                    "code": code,
                    "success": bool(code.strip())
                })
            except Exception as e:
                codes.append({
                    "attempt": i + 1,
                    "code": "",
                    "success": False,
                    "error": str(e)
                })

        results.append({
            "requirements": req,
            "code_attempts": codes
        })

    return results

if __name__ == "__main__":
    # Test the agent
    agent = ProgrammerAgent()

    test_requirements = {
        "language": "python",
        "framework": "fastapi",
        "description": "Create a FastAPI endpoint for user registration",
        "requirements": ["POST endpoint", "Pydantic validation", "password hashing"],
        "edge_cases": ["invalid email", "weak password"]
    }

    print("Testing Programmer Agent...")
    code = agent.generate_code(test_requirements)
    print("Generated code:")
    print("=" * 50)
    print(code)
    print("=" * 50)

