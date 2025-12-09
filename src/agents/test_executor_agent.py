#!/usr/bin/env python3
"""
Test Executor Agent - Test Execution and Feedback
Based on AgentCoder's test executor, adapted for CrewAI and Docker sandbox
"""

import os
import json
import tempfile
import subprocess
import sys
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import ast

# from crewai import Agent  # Temporarily disabled for testing
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestExecutionError(Exception):
    """Custom exception for test execution errors"""
    pass

class TestExecutorAgent:
    """
    Test Executor Agent - Executes tests in sandbox and provides feedback
    Based on AgentCoder's test executor with Docker security
    """

    def __init__(self):
        """Initialize the Test Executor Agent"""
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,  # Low temperature for consistent analysis
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Initialize CrewAI agent (temporarily disabled for testing)
        # self.agent = Agent(
        #     role="Expert Test Analyst",
        #     goal="Execute tests safely and provide detailed feedback for code improvement",
        #     backstory="""You are an expert test execution engineer. You run tests in secure
        #     sandboxed environments and provide detailed, actionable feedback to developers.
        #     You analyze test failures, identify root causes, and suggest specific fixes.""",
        #     llm=self.llm,
        #     allow_delegation=False,
        #     verbose=True
        # )

    def execute_tests(
        self,
        code: str,
        test_code: str,
        language: str = "python",
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute tests in secure sandbox environment

        Args:
            code: Generated code to test
            test_code: Test suite to execute
            language: Programming language (python/javascript)
            timeout: Execution timeout in seconds

        Returns:
            Test results with detailed feedback
        """
        if language == "python":
            return self._execute_python_tests(code, test_code, timeout)
        elif language == "javascript":
            return self._execute_javascript_tests(code, test_code, timeout)
        else:
            return {
                "success": False,
                "error": f"Unsupported language: {language}",
                "passed": 0,
                "failed": 0,
                "total": 0,
                "pass_rate": 0.0,
                "feedback": f"Language {language} not supported for testing"
            }

    def _execute_python_tests(
        self,
        code: str,
        test_code: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute Python tests using pytest in Docker sandbox
        """
        try:
            # Create temporary directory for test execution
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Write code to file
                code_file = temp_path / "implementation.py"
                with open(code_file, "w") as f:
                    f.write(code)

                # Write tests to file
                test_file = temp_path / "test_implementation.py"
                with open(test_file, "w") as f:
                    f.write(test_code)

                # Create requirements.txt for any dependencies
                req_file = temp_path / "requirements.txt"
                with open(req_file, "w") as f:
                    f.write("pytest>=7.0.0\nfastapi>=0.100.0\nuvicorn>=0.20.0\npydantic>=2.0.0\n")

                # Execute tests using Docker (if available) or direct execution
                if self._is_docker_available():
                    return self._execute_in_docker(temp_path, timeout)
                else:
                    return self._execute_direct(temp_path, timeout)

        except Exception as e:
            return {
                "success": False,
                "error": f"Test execution failed: {str(e)}",
                "passed": 0,
                "failed": 0,
                "total": 0,
                "pass_rate": 0.0,
                "feedback": f"Execution error: {str(e)}"
            }

    def _execute_in_docker(self, temp_path: Path, timeout: int) -> Dict[str, Any]:
        """Execute tests in Docker container for security"""
        try:
            # Build Docker command
            docker_cmd = [
                "docker", "run", "--rm",
                "--network", "none",  # No network access
                "--memory", "512m",   # Memory limit
                "--cpus", "0.5",      # CPU limit
                "--tmpfs", "/tmp",    # Isolated tmp directory
                "-v", f"{temp_path}:/app",
                "-w", "/app",
                "--timeout", str(timeout * 1000),  # Timeout in milliseconds
                "python:3.11-slim",
                "bash", "-c",
                "pip install -q -r requirements.txt && python -m pytest test_implementation.py -v --tb=short --json-report"
            ]

            # Execute Docker command
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return self._parse_pytest_output(result.stdout, result.stderr, result.returncode)

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out",
                "passed": 0,
                "failed": 0,
                "total": 0,
                "pass_rate": 0.0,
                "feedback": f"Tests exceeded {timeout} second timeout limit"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Docker execution failed: {str(e)}",
                "passed": 0,
                "failed": 0,
                "total": 0,
                "pass_rate": 0.0,
                "feedback": f"Docker error: {str(e)}"
            }

    def _execute_direct(self, temp_path: Path, timeout: int) -> Dict[str, Any]:
        """Execute tests directly (fallback when Docker not available)"""
        try:
            # Install requirements
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-q", "-r",
                str(temp_path / "requirements.txt")
            ], capture_output=True, timeout=10)

            # Run pytest
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                str(temp_path / "test_implementation.py"),
                "-v", "--tb=short", "--json-report"
            ], capture_output=True, text=True, timeout=timeout, cwd=temp_path)

            return self._parse_pytest_output(result.stdout, result.stderr, result.returncode)

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out",
                "passed": 0,
                "failed": 0,
                "total": 0,
                "pass_rate": 0.0,
                "feedback": f"Tests exceeded {timeout} second timeout limit"
            }

    def _parse_pytest_output(self, stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
        """Parse pytest output and generate feedback"""
        try:
            # Try to parse JSON output first
            if "--json-report" in stdout:
                # Extract JSON from output (simplified parsing)
                lines = stdout.split('\n')
                json_data = None
                for line in lines:
                    if line.strip().startswith('{'):
                        try:
                            json_data = json.loads(line)
                            break
                        except:
                            continue

                if json_data and 'summary' in json_data:
                    summary = json_data['summary']
                    passed = summary.get('passed', 0)
                    failed = summary.get('failed', 0)
                    total = passed + failed

                    return {
                        "success": returncode == 0,
                        "passed": passed,
                        "failed": failed,
                        "total": total,
                        "pass_rate": passed / total if total > 0 else 0.0,
                        "feedback": self._generate_feedback(stdout, stderr, passed, failed)
                    }

            # Fallback: Parse text output
            passed = stdout.count("PASSED") + stdout.count("passed")
            failed = stdout.count("FAILED") + stdout.count("failed") + stdout.count("ERROR")

            total = passed + failed
            success = returncode == 0 and failed == 0

            return {
                "success": success,
                "passed": passed,
                "failed": failed,
                "total": total,
                "pass_rate": passed / total if total > 0 else 0.0,
                "feedback": self._generate_feedback(stdout, stderr, passed, failed)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Output parsing failed: {str(e)}",
                "passed": 0,
                "failed": 0,
                "total": 0,
                "pass_rate": 0.0,
                "feedback": f"Could not parse test output: {stdout[:200]}..."
            }

    def _generate_feedback(self, stdout: str, stderr: str, passed: int, failed: int) -> str:
        """Generate detailed feedback for the programmer agent"""
        feedback_parts = []

        if failed == 0:
            feedback_parts.append("✅ All tests passed! Great job.")
        else:
            feedback_parts.append(f"❌ {failed} test(s) failed, {passed} passed.")

        # Extract error details from output
        if stderr:
            feedback_parts.append(f"Errors: {stderr[:500]}...")

        if stdout:
            # Look for specific test failures
            lines = stdout.split('\n')
            failure_details = []
            for line in lines:
                if 'FAILED' in line or 'ERROR' in line:
                    failure_details.append(line.strip())

            if failure_details:
                feedback_parts.append("Failed tests:")
                feedback_parts.extend(failure_details[:5])  # Limit to 5 failures

        return "\n".join(feedback_parts)

    def _is_docker_available(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def analyze_test_results(self, test_results: Dict[str, Any]) -> str:
        """
        Use LLM to analyze test results and provide improvement suggestions
        """
        prompt = f"""
Analyze these test execution results and provide specific improvement suggestions:

Test Results:
- Total tests: {test_results.get('total', 0)}
- Passed: {test_results.get('passed', 0)}
- Failed: {test_results.get('failed', 0)}
- Pass rate: {test_results.get('pass_rate', 0.0):.1%}
- Success: {test_results.get('success', False)}

Feedback: {test_results.get('feedback', 'No feedback available')}

Provide specific, actionable suggestions for fixing the failed tests and improving the code.
"""

        try:
            response = self.llm.invoke([
                {"role": "system", "content": "You are an expert test analyst."},
                {"role": "user", "content": prompt}
            ])
            return response.content
        except Exception as e:
            return f"Analysis failed: {str(e)}"

# AgentCoder-style batch processing for evaluation
def execute_tests_batch(
    code_test_pairs: List[Dict[str, Any]],
    language: str = "python",
    timeout: int = 30
) -> List[Dict[str, Any]]:
    """
    Execute tests for multiple code-test pairs (AgentCoder-style batch processing)
    Used for evaluation and benchmarking
    """
    agent = TestExecutorAgent()
    results = []

    for pair in code_test_pairs:
        try:
            result = agent.execute_tests(
                code=pair["code"],
                test_code=pair["tests"],
                language=language,
                timeout=timeout
            )
            results.append({
                "code_test_pair": pair,
                "execution_result": result
            })
        except Exception as e:
            results.append({
                "code_test_pair": pair,
                "execution_result": {
                    "success": False,
                    "error": str(e),
                    "passed": 0,
                    "failed": 0,
                    "total": 0,
                    "pass_rate": 0.0,
                    "feedback": f"Execution setup failed: {str(e)}"
                }
            })

    return results

if __name__ == "__main__":
    # Test the agent
    agent = TestExecutorAgent()

    # Sample code and tests
    sample_code = '''
def add_numbers(a, b):
    """Add two numbers"""
    return a + b
'''

    sample_tests = '''
import pytest
from implementation import add_numbers

def test_add_positive():
    assert add_numbers(2, 3) == 5

def test_add_negative():
    assert add_numbers(-1, -2) == -3

def test_add_zero():
    assert add_numbers(0, 5) == 5
'''

    print("Testing Test Executor Agent...")
    print("Sample code:")
    print(sample_code)
    print("\nSample tests:")
    print(sample_tests)

    print("\nExecuting tests...")
    results = agent.execute_tests(sample_code, sample_tests, language="python")

    print("\nTest Results:")
    print(json.dumps(results, indent=2))

