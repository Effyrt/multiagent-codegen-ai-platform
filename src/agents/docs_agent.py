#!/usr/bin/env python3
"""
Documentation Generator Agent - Create comprehensive documentation
Our addition to AgentCoder: Generates README and API docs from code
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

# from crewai import Agent  # Temporarily disabled for testing
from dotenv import load_dotenv

from .base_agent import BaseAgent, create_agent_llm

# Load environment variables
load_dotenv()

class DocsAgent(BaseAgent):
    """
    Documentation Generator Agent - Creates comprehensive documentation
    Our addition to AgentCoder: Generates docs after code+tests are complete
    """

    def __init__(self):
        """Initialize the Documentation Generator Agent"""
        super().__init__(model="gpt-4", temperature=0.1)  # Low temperature for consistent docs

        # Load prompt template
        prompt_path = Path(__file__).parent / "prompts" / "docs_generator.txt"
        if prompt_path.exists():
            with open(prompt_path, "r") as f:
                self.prompt_template = f.read()
        else:
            # Fallback prompt template
            self.prompt_template = self._get_default_prompt()

        # Initialize CrewAI agent (temporarily disabled for testing)
        # self.agent = Agent(
        #     role="Expert Technical Writer",
        #     goal="Create comprehensive, clear documentation for developers and users",
        #     backstory="""You are an expert technical writer specializing in API documentation
        #     and developer guides. You create clear, comprehensive documentation that helps
        #     developers understand and use code effectively. You excel at writing both
        #     technical documentation and user-friendly guides.""",
        #     llm=self.llm,
        #     allow_delegation=False,
        #     verbose=True
        # )

    def _get_default_prompt(self) -> str:
        """Get default prompt template if file not found"""
        return """
You are an Expert Technical Writer creating documentation for a web application.

Generated Code:
{code}

Test Suite:
{tests}

Requirements:
{requirements}

Create comprehensive documentation including:

## README.md Structure:
1. **Project Title and Description**
2. **Features Overview**
3. **Installation Instructions**
4. **Usage Examples**
5. **API Reference** (if applicable)
6. **Configuration**
7. **Testing Instructions**
8. **Deployment Notes**

## Documentation Guidelines:
- Use clear, concise language
- Include code examples with syntax highlighting
- Explain setup and configuration steps
- Document API endpoints with examples
- Include error handling examples
- Add deployment and production notes

Output the complete README.md content in Markdown format.
"""

    def generate_documentation(
        self,
        code: str,
        tests: str,
        requirements: Dict[str, Any],
        language: str = "python"
    ) -> str:
        """
        Generate comprehensive documentation

        Args:
            code: Generated code
            tests: Test suite
            requirements: Requirements specification
            language: Programming language

        Returns:
            Complete documentation in Markdown format
        """
        self.log_activity("Generating documentation", {
            "code_length": len(code),
            "language": language
        })

        # Use OpenAI API directly (temporarily, until CrewAI is installed)
        prompt = self.prompt_template.format(
            code=code,
            tests=tests,
            requirements=json.dumps(requirements, indent=2)
        )

        try:
            response = self.llm.invoke([
                {"role": "system", "content": "You are an expert technical writer."},
                {"role": "user", "content": prompt}
            ])
            documentation = self._format_documentation(response.content, requirements)

            self.log_activity("Documentation generated", {
                "docs_length": len(documentation)
            })

            return documentation

        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            return self._generate_fallback_docs(requirements)

    def _format_documentation(self, raw_docs: str, requirements: Dict[str, Any]) -> str:
        """Format and enhance the generated documentation"""
        # Clean up the response
        docs = raw_docs.strip()

        # Remove any code block markers if present
        if docs.startswith("```"):
            docs = docs.split("```", 2)[-1].strip()

        # Add standard sections if missing
        if "## Installation" not in docs and "# " in docs:
            docs += "\n\n## Installation\n\n```bash\npip install -r requirements.txt\n```"

        if "## Usage" not in docs and "# " in docs:
            docs += "\n\n## Usage\n\nAdd usage examples here."

        # Add footer
        if "# " in docs:
            docs += "\n\n---\n\n*Documentation generated automatically*"

        return docs

    def _generate_fallback_docs(self, requirements: Dict[str, Any]) -> str:
        """Generate basic fallback documentation"""
        language = requirements.get("language", "python")
        framework = requirements.get("framework", "web framework")
        description = requirements.get("description", "Web application")

        return f"""# {framework.title()} Application

{description}

## Features

- Web API endpoints
- Data validation
- Error handling
- Comprehensive testing

## Installation

```bash
# Clone repository
git clone <repository-url>
cd <project-directory>

# Install dependencies
pip install -r requirements.txt

# Run application
uvicorn main:app --reload
```

## Usage

### Basic Usage

```python
# Example usage
from main import app

# Start the application
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /` - Health check
- `POST /items` - Create item
- `GET /items` - List items
- `GET /items/{{item_id}}` - Get item
- `PUT /items/{{item_id}}` - Update item
- `DELETE /items/{{item_id}}` - Delete item

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src
```

## Configuration

Environment variables:
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Application secret key
- `DEBUG` - Debug mode (development only)

## Deployment

### Development
```bash
uvicorn main:app --reload
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Error Handling

The application includes comprehensive error handling for:
- Invalid input data
- Database connection errors
- Authentication failures
- Resource not found errors

---

*Generated documentation*
"""

    def enhance_with_api_docs(self, documentation: str, code: str) -> str:
        """
        Enhance documentation with API details extracted from code

        Args:
            documentation: Existing documentation
            code: Generated code

        Returns:
            Enhanced documentation
        """
        # This could be enhanced to parse code and extract API endpoints
        # For now, return as-is
        return documentation

# Utility functions for batch processing
def generate_docs_batch(code_test_pairs: list) -> list:
    """
    Generate documentation for multiple code-test pairs
    """
    agent = DocsAgent()
    results = []

    for pair in code_test_pairs:
        try:
            docs = agent.generate_documentation(
                code=pair["code"],
                tests=pair.get("tests", ""),
                requirements=pair.get("requirements", {})
            )
            results.append({
                "code_test_pair": pair,
                "documentation": docs,
                "success": True
            })
        except Exception as e:
            results.append({
                "code_test_pair": pair,
                "error": str(e),
                "success": False
            })

    return results

if __name__ == "__main__":
    # Test the agent
    agent = DocsAgent()

    # Sample inputs
    sample_code = '''
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.post("/items/")
def create_item(item: Item):
    return {"item": item, "message": "Item created"}
'''

    sample_tests = '''
def test_create_item():
    response = client.post("/items/", json={"name": "Test", "price": 10.0})
    assert response.status_code == 200
'''

    sample_requirements = {
        "language": "python",
        "framework": "fastapi",
        "description": "Create FastAPI endpoint for managing items",
        "requirements": ["POST endpoint for items", "Pydantic validation"],
        "endpoints": ["POST /items/"]
    }

    print("Testing Documentation Generator Agent...")
    print("Generating documentation...")

    docs = agent.generate_documentation(
        code=sample_code,
        tests=sample_tests,
        requirements=sample_requirements
    )

    print("\nGenerated Documentation:")
    print("=" * 60)
    print(docs)
    print("=" * 60)

