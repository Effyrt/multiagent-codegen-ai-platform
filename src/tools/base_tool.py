"""
Base Tool Class

Foundation for all agent tools.
"""

import time
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ToolParameter(BaseModel):
    """Parameter definition for a tool"""
    
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, integer, boolean, object, array)")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value if not provided")
    enum: Optional[List[str]] = Field(default=None, description="Valid values if enumerated")


class ToolResult(BaseModel):
    """Result from tool execution"""
    
    success: bool = Field(..., description="Whether tool execution succeeded")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Tool execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    latency: float = Field(..., description="Execution time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseTool(ABC):
    """
    Base class for all agent tools
    
    Tools provide dynamic capabilities to agents, allowing them to:
    - Search for information
    - Validate code
    - Execute operations
    - Query external services
    """
    
    # Tool metadata (override in subclasses)
    name: str = "base_tool"
    description: str = "Base tool"
    parameters: List[ToolParameter] = []
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.execution_count = 0
        self.total_latency = 0.0
        self.error_count = 0
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ToolExecutionError: If tool execution fails
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    async def run(self, **kwargs) -> ToolResult:
        """
        Run the tool and return structured result
        
        Wraps execute() with timing, logging, and error handling.
        """
        start_time = time.time()
        self.execution_count += 1
        
        try:
            self.logger.info(f"🔧 Executing {self.name} with params: {list(kwargs.keys())}")
            
            # Validate parameters
            self._validate_parameters(kwargs)
            
            # Execute tool
            result = await self.execute(**kwargs)
            
            latency = time.time() - start_time
            self.total_latency += latency
            
            self.logger.info(f"✅ {self.name} completed in {latency:.3f}s")
            
            return ToolResult(
                success=True,
                result=result,
                error=None,
                latency=latency,
                metadata={
                    "tool_name": self.name,
                    "execution_count": self.execution_count,
                    "parameters": list(kwargs.keys())
                }
            )
            
        except Exception as e:
            latency = time.time() - start_time
            self.error_count += 1
            
            self.logger.error(f"❌ {self.name} failed: {str(e)}")
            
            return ToolResult(
                success=False,
                result=None,
                error=str(e),
                latency=latency,
                metadata={
                    "tool_name": self.name,
                    "execution_count": self.execution_count,
                    "error_type": type(e).__name__
                }
            )
    
    def _validate_parameters(self, kwargs: Dict[str, Any]):
        """Validate that required parameters are present"""
        required_params = {p.name for p in self.parameters if p.required}
        provided_params = set(kwargs.keys())
        missing_params = required_params - provided_params
        
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")
    
    def to_openai_function(self) -> dict:
        """
        Convert tool to OpenAI function calling format
        
        Returns:
            OpenAI function definition
        """
        properties = {}
        required = []
        
        for param in self.parameters:
            prop_def = {
                "type": param.type,
                "description": param.description
            }
            
            if param.enum:
                prop_def["enum"] = param.enum
            
            if param.default is not None:
                prop_def["default"] = param.default
            
            properties[param.name] = prop_def
            
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    def to_anthropic_tool(self) -> dict:
        """
        Convert tool to Anthropic tool format
        
        Returns:
            Anthropic tool definition
        """
        input_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param in self.parameters:
            input_schema["properties"][param.name] = {
                "type": param.type,
                "description": param.description
            }
            
            if param.required:
                input_schema["required"].append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": input_schema
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        avg_latency = self.total_latency / self.execution_count if self.execution_count > 0 else 0
        error_rate = self.error_count / self.execution_count if self.execution_count > 0 else 0
        
        return {
            "tool_name": self.name,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "total_latency": self.total_latency,
            "average_latency": avg_latency
        }
    
    def reset_stats(self):
        """Reset tool statistics"""
        self.execution_count = 0
        self.total_latency = 0.0
        self.error_count = 0


# Utility function to create tool from dict (for dynamic tool loading)
def create_tool_from_spec(spec: dict) -> BaseTool:
    """
    Create a tool instance from specification dictionary
    
    Useful for loading tools dynamically or from configuration.
    """
    # This would be implemented based on specific needs
    # For now, it's a placeholder for future extensibility
    raise NotImplementedError("Dynamic tool creation not yet implemented")
