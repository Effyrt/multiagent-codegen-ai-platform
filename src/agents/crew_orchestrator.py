#!/usr/bin/env python3
"""
CrewAI Orchestrator - Coordinates the 5-Agent System
Based on AgentCoder workflow, enhanced with our Requirements & Documentation agents
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

# from crewai import Crew, Task  # Temporarily disabled for testing
from dotenv import load_dotenv

from .requirements_agent import RequirementsAgent, RequirementsSpec
from .programmer_agent import ProgrammerAgent
from .test_designer_agent import TestDesignerAgent
from .test_executor_agent import TestExecutorAgent
from .docs_agent import DocsAgent
from .base_agent import validate_agent_environment

# Load environment variables
load_dotenv()

class CodeGenerationCrew:
    """
    CrewAI orchestrator implementing the AgentCoder-inspired 5-agent workflow:
    1. Requirements Analyzer → 2. Test Designer → 3. Programmer → 4. Test Executor → 5. Documentation Generator

    Key AgentCoder principles:
    - Independent test design (tests created before code)
    - Iterative refinement based on test feedback
    - Multi-agent collaboration
    """

    def __init__(self, max_iterations: int = 3):
        """Initialize the code generation crew"""
        self.max_iterations = max_iterations

        # Validate environment
        env_check = validate_agent_environment()
        if not env_check["valid"]:
            raise EnvironmentError(f"Environment validation failed: {env_check['issues']}")

        # Initialize agents
        self.requirements_agent = RequirementsAgent()
        self.programmer_agent = ProgrammerAgent()
        self.test_designer_agent = TestDesignerAgent()
        self.test_executor_agent = TestExecutorAgent()
        self.docs_agent = DocsAgent()

        # Track execution metrics
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "iterations": 0,
            "agent_execution_times": {},
            "token_usage": {},
            "costs": {}
        }

    def generate_code(
        self,
        user_description: str,
        rag_examples: str = "",
        language_hint: str = None,
        framework_hint: str = None
    ) -> Dict[str, Any]:
        """
        Execute the complete 5-agent code generation workflow

        Args:
            user_description: Natural language description of desired functionality
            rag_examples: Similar code examples from RAG system
            language_hint: Preferred programming language
            framework_hint: Preferred web framework

        Returns:
            Complete generation result with code, tests, docs, and metrics
        """
        self.metrics["start_time"] = time.time()
        self._log_workflow("Starting code generation workflow")

        try:
            # Phase 1: Requirements Analysis
            requirements = self._execute_requirements_analysis(user_description, language_hint, framework_hint)
            self._log_workflow(f"Requirements analyzed: {requirements.language}/{requirements.framework}")

            # Phase 2: Test Design (Independent - before coding!)
            test_suite = self._execute_test_design(requirements)
            self._log_workflow(f"Test suite designed: {len(test_suite)} tests")

            # Phase 3-4: Iterative Code Generation & Testing
            code, test_results = self._execute_iterative_refinement(requirements, test_suite, rag_examples)
            self._log_workflow(f"Code refined through {self.metrics['iterations']} iterations")

            # Phase 5: Documentation Generation
            documentation = self._execute_documentation_generation(code, test_suite, requirements)
            self._log_workflow("Documentation generated")

            # Calculate final metrics
            self.metrics["end_time"] = time.time()
            final_metrics = self._calculate_final_metrics(code, test_results, requirements)

            result = {
                "success": True,
                "code": code,
                "tests": test_suite,
                "documentation": documentation,
                "requirements": requirements.dict(),
                "test_results": test_results,
                "metrics": final_metrics,
                "language": requirements.language,
                "framework": requirements.framework
            }

            self._log_workflow("Workflow completed successfully")
            return result

        except Exception as e:
            self._log_workflow(f"Workflow failed: {str(e)}", level="ERROR")
            return {
                "success": False,
                "error": str(e),
                "metrics": self.metrics
            }

    def _execute_requirements_analysis(
        self,
        description: str,
        language_hint: str = None,
        framework_hint: str = None
    ) -> RequirementsSpec:
        """Phase 1: Analyze and structure requirements"""
        start_time = time.time()

        # Apply hints if provided
        if language_hint or framework_hint:
            enhanced_description = f"{description} (Prefer {language_hint or 'any language'}"
            if framework_hint:
                enhanced_description += f" with {framework_hint}"
            enhanced_description += ")"
        else:
            enhanced_description = description

        requirements = self.requirements_agent.analyze_requirements(enhanced_description)

        self.metrics["agent_execution_times"]["requirements"] = time.time() - start_time
        return requirements

    def _execute_test_design(self, requirements: RequirementsSpec) -> str:
        """Phase 2: Design tests independently (AgentCoder key principle)"""
        start_time = time.time()

        test_suite = self.test_designer_agent.design_tests(requirements.dict())

        self.metrics["agent_execution_times"]["test_design"] = time.time() - start_time
        return test_suite

    def _execute_iterative_refinement(
        self,
        requirements: RequirementsSpec,
        test_suite: str,
        rag_examples: str
    ) -> tuple[str, Dict[str, Any]]:
        """
        Phase 3-4: Iterative code generation and testing
        AgentCoder's core refinement loop
        """
        code = ""
        test_results = None

        for iteration in range(self.max_iterations):
            self.metrics["iterations"] = iteration + 1
            self._log_workflow(f"Starting iteration {iteration + 1}")

            # Generate/refine code
            start_time = time.time()
            code = self.programmer_agent.generate_code(
                requirements=requirements.dict(),
                rag_examples=rag_examples,
                previous_code=code,
                test_feedback=self._format_test_feedback(test_results) if test_results else ""
            )
            self.metrics["agent_execution_times"][f"programming_{iteration}"] = time.time() - start_time

            # Execute tests
            start_time = time.time()
            test_results = self.test_executor_agent.execute_tests(
                code=code,
                test_code=test_suite,
                language=requirements.language
            )
            self.metrics["agent_execution_times"][f"testing_{iteration}"] = time.time() - start_time

            self._log_workflow(f"Iteration {iteration + 1}: Pass rate {test_results.get('pass_rate', 0):.1%}")

            # Check if tests pass sufficiently
            if test_results.get("pass_rate", 0) >= 0.8:  # 80% pass rate
                self._log_workflow("Tests passed! Stopping refinement.")
                break

        return code, test_results

    def _execute_documentation_generation(
        self,
        code: str,
        test_suite: str,
        requirements: RequirementsSpec
    ) -> str:
        """Phase 5: Generate comprehensive documentation"""
        start_time = time.time()

        documentation = self.docs_agent.generate_documentation(
            code=code,
            tests=test_suite,
            requirements=requirements.dict(),
            language=requirements.language
        )

        self.metrics["agent_execution_times"]["documentation"] = time.time() - start_time
        return documentation

    def _format_test_feedback(self, test_results: Dict[str, Any]) -> str:
        """Format test results for programmer feedback"""
        if not test_results:
            return ""

        feedback = f"Test Results: {test_results.get('passed', 0)}/{test_results.get('total', 0)} passed"
        if test_results.get("feedback"):
            feedback += f"\n\nIssues:\n{test_results['feedback']}"

        return feedback

    def _calculate_final_metrics(
        self,
        code: str,
        test_results: Dict[str, Any],
        requirements: RequirementsSpec
    ) -> Dict[str, Any]:
        """Calculate comprehensive final metrics"""
        total_time = self.metrics["end_time"] - self.metrics["start_time"]

        # Code quality metrics
        quality_score = self._estimate_quality_score(code, test_results, requirements)

        # Confidence score (based on test results and iterations)
        confidence_score = self._calculate_confidence_score(test_results, self.metrics["iterations"])

        return {
            "total_time": round(total_time, 2),
            "iterations_used": self.metrics["iterations"],
            "quality_score": quality_score,
            "confidence_score": confidence_score,
            "test_pass_rate": test_results.get("pass_rate", 0),
            "code_lines": len(code.split('\n')),
            "test_lines": len(test_results.get("tests", "").split('\n')),
            "agent_times": self.metrics["agent_execution_times"],
            "language": requirements.language,
            "framework": requirements.framework,
            "complexity": requirements.complexity
        }

    def _estimate_quality_score(self, code: str, test_results: Dict[str, Any], requirements: RequirementsSpec) -> float:
        """Estimate code quality score (0-10)"""
        score = 5.0  # Base score

        # Test performance (40% weight)
        pass_rate = test_results.get("pass_rate", 0)
        score += pass_rate * 4

        # Code structure (20% weight)
        if "def " in code or "function" in code:  # Has functions
            score += 1
        if "class " in code:  # Has classes
            score += 1

        # Error handling (20% weight)
        if "try:" in code or "except" in code or "catch" in code:
            score += 2

        # Documentation (10% weight)
        if '"""' in code or "'''" in code or "/**" in code:
            score += 1

        # Framework usage (10% weight)
        framework = requirements.framework
        if framework and framework.lower() in code.lower():
            score += 1

        return round(min(score, 10.0), 1)

    def _calculate_confidence_score(self, test_results: Dict[str, Any], iterations: int) -> float:
        """Calculate confidence score based on test results and refinement needed"""
        base_confidence = test_results.get("pass_rate", 0) * 100

        # Penalty for multiple iterations (uncertainty)
        iteration_penalty = (iterations - 1) * 10
        confidence = max(base_confidence - iteration_penalty, 0)

        return round(confidence, 1)

    def _log_workflow(self, message: str, level: str = "INFO"):
        """Log workflow progress"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

# Convenience functions for easy usage
def generate_code_simple(description: str) -> Dict[str, Any]:
    """
    Simple interface for code generation
    """
    crew = CodeGenerationCrew()
    return crew.generate_code(description)

def generate_code_advanced(
    description: str,
    language_hint: str = None,
    framework_hint: str = None,
    max_iterations: int = 3
) -> Dict[str, Any]:
    """
    Advanced interface with customization options
    """
    crew = CodeGenerationCrew(max_iterations=max_iterations)
    return crew.generate_code(
        user_description=description,
        language_hint=language_hint,
        framework_hint=framework_hint
    )

if __name__ == "__main__":
    # Test the orchestrator
    print("Testing Code Generation Crew...")
    print("=" * 50)

    # Simple test case
    test_description = "Create a FastAPI endpoint for user registration with email validation"

    try:
        result = generate_code_simple(test_description)

        if result["success"]:
            print("✅ Code generation successful!")
            print(f"Language: {result['language']}")
            print(f"Framework: {result['framework']}")
            print(f"Test Pass Rate: {result['metrics']['test_pass_rate']:.1%}")
            print(f"Quality Score: {result['metrics']['quality_score']}/10")
            print(f"Iterations: {result['metrics']['iterations_used']}")
            print(f"Total Time: {result['metrics']['total_time']}s")

            print("\n" + "=" * 30 + " GENERATED CODE " + "=" * 30)
            print(result["code"][:500] + "..." if len(result["code"]) > 500 else result["code"])
            print("=" * 70)

        else:
            print(f"❌ Code generation failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

