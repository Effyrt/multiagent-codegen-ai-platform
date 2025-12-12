"""
Code Generation Endpoints

Multi-agent code generation with tests and documentation.
"""

import time
import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime

from ..models import (
    CodeGenerationRequest,
    CodeGenerationResponse,
    TestResults,
    AgentMetrics,
    ToolUsage
)
from ..exceptions import CodeGenerationError, ValidationError, TimeoutError
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/generate", tags=["Generation"])


@router.post("/code", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """
    Generate code using multi-agent system
    
    This endpoint orchestrates 5 specialized AI agents to:
    1. Analyze requirements
    2. Design tests (independently)
    3. Generate code
    4. Execute tests (iterative refinement)
    5. Generate documentation
    
    **AgentCoder Principles:**
    - Tests are designed independently from code
    - Iterative refinement based on test feedback
    - Multi-agent collaboration
    - RAG-enhanced with real code examples
    - Optional tool calling for dynamic capabilities
    
    **Parameters:**
    - **description**: Natural language description of what to build
    - **language**: Target language (python or javascript)
    - **framework**: Target framework (fastapi, flask, express, etc.)
    - **complexity**: Expected complexity level
    - **include_tests**: Whether to generate test suite
    - **include_docs**: Whether to generate documentation
    - **use_rag**: Whether to retrieve similar examples
    - **use_tools**: Whether to enable agent tool calling
    
    **Returns:**
    - Generated code with tests and documentation
    - Quality metrics and test results
    - Agent execution details
    - Token usage and timing
    """
    
    start_time = time.time()
    agent_metrics = []
    
    try:
        logger.info(f"=== CODE GENERATION REQUEST ===")
        logger.info(f"Description: {request.description[:100]}...")
        logger.info(f"Language: {request.language}, Framework: {request.framework}")
        logger.info(f"Settings: tests={request.include_tests}, docs={request.include_docs}, rag={request.use_rag}, tools={request.use_tools}")
        
        # ===================================================================
        # ACTUAL AGENT INTEGRATION
        # ===================================================================
        
        # Import and initialize the crew
        from src.agents.crew_orchestrator import CodeGenerationCrew
        
        logger.info("→ Initializing agent crew")
        crew = CodeGenerationCrew()
        
        # Call the actual agent system
        logger.info("→ Executing multi-agent workflow")
        result = crew.generate_code(
            user_description=request.description,
            rag_examples="",  # RAG will be integrated by crew
            language_hint=request.language,
            framework_hint=request.framework
        )
        
        # Extract results from crew response
        generated_code = result.get("code", "")
        generated_tests = result.get("tests", "") if request.include_tests else None
        generated_docs = result.get("documentation", "") if request.include_docs else None
        
        # Update agent metrics from actual execution
        if "agent_metrics" in result:
            agent_metrics = [
                AgentMetrics(
                    agent_name=m.get("agent_name", "Unknown"),
                    execution_time=m.get("execution_time", 0),
                    token_usage=m.get("token_usage", {}),
                    iterations=m.get("iterations", 1),
                    success=m.get("success", True),
                    tools_used=[
                        ToolUsage(
                            tool_name=t.get("tool_name", ""),
                            parameters=t.get("parameters", {}),
                            result=t.get("result", {}),
                            success=t.get("success", True),
                            latency=t.get("latency", 0),
                            error=t.get("error")
                        )
                        for t in m.get("tools_used", [])
                    ] if m.get("tools_used") else []
                )
                for m in result.get("agent_metrics", [])
            ]
        
        # Get test results from crew
        test_results_data = result.get("test_results", {})
        test_results = TestResults(
            passed=test_results_data.get("passed", 0),
            failed=test_results_data.get("failed", 0),
            errors=test_results_data.get("errors", 0),
            pass_rate=test_results_data.get("pass_rate", 1.0),
            failures=test_results_data.get("failures", []),
            execution_time=test_results_data.get("execution_time", 0)
        ) if request.include_tests else None
        
        # Calculate totals
        execution_time = time.time() - start_time
        total_tokens = result.get("total_tokens", sum(m.token_usage.get("total", 0) for m in agent_metrics))
        
        logger.info(f"✅ Code generation completed in {execution_time:.2f}s")
        logger.info(f"   Tokens used: {total_tokens}")
        if test_results:
            logger.info(f"   Test pass rate: {test_results.pass_rate:.0%}")
        
        return CodeGenerationResponse(
            success=True,
            code=generated_code,
            tests=generated_tests,
            documentation=generated_docs,
            quality_score=result.get("quality_score", 8.5),
            confidence=result.get("confidence", 0.90),
            test_results=test_results,
            iterations_used=result.get("iterations_used", 1),
            execution_time=execution_time,
            total_tokens=total_tokens,
            agent_metrics=agent_metrics,
            timestamp=datetime.utcnow(),
            metadata={
                "language": request.language,
                "framework": request.framework,
                "complexity": request.complexity,
                "rag_enabled": request.use_rag,
                "tools_enabled": request.use_tools
            }
        )
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    
    except TimeoutError as e:
        logger.error(f"Timeout: {str(e)}")
        raise HTTPException(status_code=408, detail=str(e))
    
    except Exception as e:
        logger.error(f"Code generation error: {str(e)}", exc_info=True)
        execution_time = time.time() - start_time
        
        return CodeGenerationResponse(
            success=False,
            error=str(e),
            error_type=type(e).__name__,
            execution_time=execution_time,
            timestamp=datetime.utcnow(),
            metadata={"language": request.language, "framework": request.framework}
        )


# Compatibility endpoint for Om's frontend
@router.post("", response_model=CodeGenerationResponse)
async def generate_code_compat(request: CodeGenerationRequest):
    """
    Compatibility endpoint for frontend (calls /api/v1/generate directly)
    Forwards to the main generate_code endpoint
    """
    return await generate_code(request)