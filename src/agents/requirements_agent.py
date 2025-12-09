#!/usr/bin/env python3
"""
Requirements Analyzer Agent - Parse and Structure User Requests
Our addition to AgentCoder: Extracts structured requirements from natural language
"""

import os
import json
import re
from typing import Dict, Any, Optional
from pathlib import Path

# from crewai import Agent  # Temporarily disabled for testing
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .base_agent import BaseAgent, create_agent_llm

# Load environment variables
load_dotenv()

class RequirementsSpec(BaseModel):
    """Structured requirements specification"""
    language: str = Field(description="Programming language (python/javascript)")
    framework: Optional[str] = Field(default=None, description="Web framework (fastapi/flask/django/express/nest)")
    description: str = Field(description="Original user description")
    requirements: list[str] = Field(description="List of functional requirements")
    edge_cases: list[str] = Field(description="Edge cases and error conditions to handle")
    complexity: str = Field(description="Complexity level (simple/medium/complex)")
    security_notes: list[str] = Field(description="Security considerations")
    data_models: list[str] = Field(description="Data models/entities needed")
    endpoints: list[str] = Field(description="API endpoints to implement")

class RequirementsAgent(BaseAgent):
    """
    Requirements Analyzer Agent - Parses natural language into structured specifications
    This is our addition to AgentCoder (they assumed structured inputs)
    """

    def __init__(self):
        """Initialize the Requirements Analyzer Agent"""
        super().__init__(model="gpt-4", temperature=0.1)  # Low temperature for consistent parsing

        # Load prompt template
        prompt_path = Path(__file__).parent / "prompts" / "requirements_analyzer.txt"
        if prompt_path.exists():
            with open(prompt_path, "r") as f:
                self.prompt_template = f.read()
        else:
            # Fallback prompt template
            self.prompt_template = self._get_default_prompt()

        # Initialize CrewAI agent (temporarily disabled for testing)
        # self.agent = Agent(
        #     role="Expert Requirements Analyst",
        #     goal="Parse natural language descriptions into structured, actionable requirements",
        #     backstory="""You are an expert business analyst and software architect.
        #     You excel at understanding user needs from natural language descriptions
        #     and translating them into clear, structured technical requirements.
        #     You identify edge cases, security concerns, and implementation details.""",
        #     llm=self.llm,
        #     allow_delegation=False,
        #     verbose=True
        # )

    def _get_default_prompt(self) -> str:
        """Get default prompt template if file not found"""
        return """
You are an Expert Requirements Analyst for web application development.

User Description: {description}

Analyze this description and extract structured requirements:

1. **Programming Language**: Choose python or javascript based on context
2. **Framework**: Identify the most appropriate framework:
   - Python: fastapi, flask, django
   - JavaScript: express, nest, next
3. **Core Requirements**: List of functional requirements
4. **Edge Cases**: Error conditions and edge cases to handle
5. **Complexity Level**: simple/medium/complex based on scope
6. **Security Considerations**: Authentication, validation, security needs
7. **Data Models**: Entities and data structures needed
8. **API Endpoints**: REST endpoints to implement

Output ONLY valid JSON matching this schema:
{
  "language": "python|javascript",
  "framework": "framework_name|null",
  "description": "original_description",
  "requirements": ["req1", "req2", ...],
  "edge_cases": ["case1", "case2", ...],
  "complexity": "simple|medium|complex",
  "security_notes": ["note1", "note2", ...],
  "data_models": ["model1", "model2", ...],
  "endpoints": ["GET /users", "POST /users", ...]
}
"""

    def analyze_requirements(self, description: str) -> RequirementsSpec:
        """
        Analyze natural language description and extract structured requirements

        Args:
            description: User's natural language description

        Returns:
            Structured requirements specification
        """
        self.log_activity("Analyzing requirements", {"description_length": len(description)})

        # Use OpenAI API directly (temporarily, until CrewAI is installed)
        prompt = self.prompt_template.format(description=description)

        try:
            response = self.llm.invoke([
                {"role": "system", "content": "You are an expert requirements analyst."},
                {"role": "user", "content": prompt}
            ])
            json_str = self._extract_json_from_response(response.content)
            parsed_data = json.loads(json_str)

            # Validate with Pydantic
            requirements = RequirementsSpec(**parsed_data)

            self.log_activity("Requirements analysis complete", {
                "language": requirements.language,
                "framework": requirements.framework,
                "complexity": requirements.complexity,
                "requirements_count": len(requirements.requirements)
            })

            return requirements

        except Exception as e:
            self.logger.error(f"Requirements analysis failed: {e}")
            # Return basic fallback
            return self._create_fallback_requirements(description)

    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from LLM response"""
        # Look for JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        # Look for plain JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0).strip()

        # If no JSON found, try to parse the whole response
        try:
            json.loads(response)
            return response
        except:
            raise ValueError(f"No valid JSON found in response: {response[:200]}...")

    def _create_fallback_requirements(self, description: str) -> RequirementsSpec:
        """Create basic fallback requirements if parsing fails"""
        self.logger.warning("Using fallback requirements analysis")

        # Simple keyword-based analysis
        desc_lower = description.lower()

        # Detect language
        if any(word in desc_lower for word in ['python', 'django', 'flask', 'fastapi']):
            language = 'python'
            if 'fastapi' in desc_lower:
                framework = 'fastapi'
            elif 'django' in desc_lower:
                framework = 'django'
            elif 'flask' in desc_lower:
                framework = 'flask'
            else:
                framework = None
        elif any(word in desc_lower for word in ['javascript', 'js', 'node', 'express', 'react', 'next']):
            language = 'javascript'
            if 'express' in desc_lower:
                framework = 'express'
            elif 'next' in desc_lower:
                framework = 'next'
            else:
                framework = None
        else:
            language = 'python'  # Default
            framework = 'fastapi'  # Default

        # Basic complexity assessment
        word_count = len(description.split())
        if word_count < 20:
            complexity = 'simple'
        elif word_count < 50:
            complexity = 'medium'
        else:
            complexity = 'complex'

        return RequirementsSpec(
            language=language,
            framework=framework,
            description=description,
            requirements=["Implement the described functionality"],
            edge_cases=["Handle basic error cases"],
            complexity=complexity,
            security_notes=["Implement basic input validation"],
            data_models=[],
            endpoints=[]
        )

    def refine_requirements(
        self,
        initial_requirements: RequirementsSpec,
        feedback: str
    ) -> RequirementsSpec:
        """
        Refine requirements based on feedback

        Args:
            initial_requirements: Current requirements spec
            feedback: Feedback from other agents or users

        Returns:
            Refined requirements
        """
        prompt = f"""
Original Requirements:
{json.dumps(initial_requirements.dict(), indent=2)}

Feedback: {feedback}

Refine the requirements based on this feedback. Output only the updated JSON.
"""

        try:
            response = self.agent.run(prompt)
            json_str = self._extract_json_from_response(str(response))
            parsed_data = json.loads(json_str)
            return RequirementsSpec(**parsed_data)
        except Exception as e:
            self.logger.error(f"Requirements refinement failed: {e}")
            return initial_requirements

# Utility functions for batch processing
def analyze_requirements_batch(descriptions: list) -> list:
    """
    Analyze multiple requirement descriptions
    """
    agent = RequirementsAgent()
    results = []

    for desc in descriptions:
        try:
            requirements = agent.analyze_requirements(desc)
            results.append({
                "description": desc,
                "requirements": requirements.dict(),
                "success": True
            })
        except Exception as e:
            results.append({
                "description": desc,
                "error": str(e),
                "success": False
            })

    return results

if __name__ == "__main__":
    # Test the agent
    agent = RequirementsAgent()

    test_descriptions = [
        "Create a FastAPI endpoint for user registration with email validation",
        "Build a REST API for managing todo items with CRUD operations",
        "Implement a file upload handler with size validation and type checking",
        "Create an Express.js middleware for JWT authentication"
    ]

    print("Testing Requirements Analyzer Agent...")
    print("=" * 60)

    for i, desc in enumerate(test_descriptions, 1):
        print(f"\nTest {i}: {desc}")
        print("-" * 40)

        try:
            requirements = agent.analyze_requirements(desc)
            print(f"Language: {requirements.language}")
            print(f"Framework: {requirements.framework}")
            print(f"Complexity: {requirements.complexity}")
            print(f"Requirements: {requirements.requirements}")
            print(f"Edge Cases: {requirements.edge_cases}")

        except Exception as e:
            print(f"❌ Analysis failed: {e}")

    print("\n" + "=" * 60)
    print("Requirements analysis testing complete!")

