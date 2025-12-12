"""
Docker Sandbox - Actually execute code in isolated containers
"""

import docker
import tempfile
import os
import time

class DockerExecutor:
    
    def __init__(self):
        self.client = docker.from_env()
        self.timeout = 5  # 5 seconds max per test
        
    async def execute_python(self, code: str, tests: str) -> dict:
        """Execute Python code + tests in Docker container"""
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.write("\n\n")
            f.write(tests)
            temp_file = f.name
        
        try:
            # Run in Docker
            container = self.client.containers.run(
                "python:3.11-slim",
                f"python /code/test.py",
                volumes={os.path.dirname(temp_file): {'bind': '/code', 'mode': 'ro'}},
                working_dir='/code',
                detach=True,
                remove=True,
                mem_limit='256m',
                cpu_period=100000,
                cpu_quota=50000,  # 50% CPU
            )
            
            # Wait for completion
            result = container.wait(timeout=self.timeout)
            logs = container.logs().decode('utf-8')
            
            # Parse results
            if result['StatusCode'] == 0:
                return {
                    "passed": 1.0,
                    "total": self._count_tests(tests),
                    "failed": [],
                    "output": logs
                }
            else:
                return {
                    "passed": 0.0,
                    "total": self._count_tests(tests),
                    "failed": [logs],
                    "output": logs
                }
                
        except docker.errors.ContainerError as e:
            return {
                "passed": 0.0,
                "total": self._count_tests(tests),
                "failed": [str(e)],
                "output": str(e)
            }
        except Exception as e:
            return {
                "passed": 0.0,
                "total": self._count_tests(tests),
                "failed": [str(e)],
                "output": str(e)
            }
        finally:
            # Clean up
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def _count_tests(self, tests: str) -> int:
        """Count number of test assertions"""
        return tests.count('assert')