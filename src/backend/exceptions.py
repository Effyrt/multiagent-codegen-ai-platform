"""
Custom Exceptions

Custom exception classes for the backend API.
"""


class CodeGenException(Exception):
    """Base exception for all CodeGen errors"""
    
    def __init__(self, message: str, error_type: str = "CodeGenError"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class ValidationError(CodeGenException):
    """Validation error"""
    
    def __init__(self, message: str):
        super().__init__(message, "ValidationError")


class CodeGenerationError(CodeGenException):
    """Error during code generation"""
    
    def __init__(self, message: str, agent: str = None):
        self.agent = agent
        super().__init__(message, "CodeGenerationError")


class RAGRetrievalError(CodeGenException):
    """Error during RAG retrieval"""
    
    def __init__(self, message: str):
        super().__init__(message, "RAGRetrievalError")


class TestExecutionError(CodeGenException):
    """Error during test execution"""
    
    def __init__(self, message: str):
        super().__init__(message, "TestExecutionError")


class APIKeyError(CodeGenException):
    """Error with API keys or authentication"""
    
    def __init__(self, message: str):
        super().__init__(message, "APIKeyError")


class TimeoutError(CodeGenException):
    """Operation timeout"""
    
    def __init__(self, message: str, timeout_seconds: int = None):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, "TimeoutError")


class ToolExecutionError(CodeGenException):
    """Error during tool execution"""
    
    def __init__(self, message: str, tool_name: str = None):
        self.tool_name = tool_name
        super().__init__(message, "ToolExecutionError")


class ConfigurationError(CodeGenException):
    """Configuration error"""
    
    def __init__(self, message: str):
        super().__init__(message, "ConfigurationError")
