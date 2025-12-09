"""
Tool Registry

Central registry for managing and discovering tools.
"""

import logging
from typing import Dict, List, Optional, Type
from functools import lru_cache

from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for managing agent tools
    
    Provides centralized tool discovery, instantiation, and management.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self.logger = logging.getLogger(__name__)
    
    def register(self, tool: BaseTool):
        """
        Register a tool instance
        
        Args:
            tool: Tool instance to register
        """
        if tool.name in self._tools:
            self.logger.warning(f"Tool '{tool.name}' already registered, overwriting")
        
        self._tools[tool.name] = tool
        self._tool_classes[tool.name] = type(tool)
        self.logger.info(f"✅ Registered tool: {tool.name}")
    
    def register_class(self, tool_class: Type[BaseTool]):
        """
        Register a tool class (will be instantiated on first use)
        
        Args:
            tool_class: Tool class to register
        """
        # Instantiate to get metadata
        temp_instance = tool_class()
        tool_name = temp_instance.name
        
        if tool_name in self._tool_classes:
            self.logger.warning(f"Tool class '{tool_name}' already registered, overwriting")
        
        self._tool_classes[tool_name] = tool_class
        self.logger.info(f"✅ Registered tool class: {tool_name}")
    
    def get(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        # Return existing instance if available
        if name in self._tools:
            return self._tools[name]
        
        # Instantiate from class if available
        if name in self._tool_classes:
            tool = self._tool_classes[name]()
            self._tools[name] = tool
            return tool
        
        self.logger.warning(f"Tool '{name}' not found in registry")
        return None
    
    def list_tools(self) -> List[str]:
        """Get list of all registered tool names"""
        return list(set(self._tools.keys()) | set(self._tool_classes.keys()))
    
    def get_all(self) -> Dict[str, BaseTool]:
        """
        Get all registered tools
        
        Returns:
            Dictionary of tool name -> tool instance
        """
        # Ensure all classes are instantiated
        for name, tool_class in self._tool_classes.items():
            if name not in self._tools:
                self._tools[name] = tool_class()
        
        return self._tools.copy()
    
    def get_tools_for_agent(self, agent_type: str = None) -> List[BaseTool]:
        """
        Get tools suitable for a specific agent
        
        Args:
            agent_type: Type of agent (programmer, test_designer, etc.)
            
        Returns:
            List of tools appropriate for that agent
        """
        all_tools = self.get_all().values()
        
        # Could implement agent-specific filtering here
        # For now, return all tools
        return list(all_tools)
    
    def to_openai_functions(self) -> List[dict]:
        """
        Convert all registered tools to OpenAI function format
        
        Returns:
            List of OpenAI function definitions
        """
        tools = self.get_all().values()
        return [tool.to_openai_function() for tool in tools]
    
    def to_anthropic_tools(self) -> List[dict]:
        """
        Convert all registered tools to Anthropic tool format
        
        Returns:
            List of Anthropic tool definitions
        """
        tools = self.get_all().values()
        return [tool.to_anthropic_tool() for tool in tools]
    
    def get_stats(self) -> Dict[str, dict]:
        """Get statistics for all tools"""
        return {
            name: tool.get_stats()
            for name, tool in self._tools.items()
        }
    
    def reset_stats(self):
        """Reset statistics for all tools"""
        for tool in self._tools.values():
            tool.reset_stats()
    
    def clear(self):
        """Clear all registered tools"""
        self._tools.clear()
        self._tool_classes.clear()
        self.logger.info("🗑️  Cleared tool registry")


# Global registry instance
_registry: Optional[ToolRegistry] = None


@lru_cache(maxsize=1)
def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance
    
    Uses singleton pattern to ensure one registry per application.
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        logger.info("📦 Created global tool registry")
    return _registry


def register_default_tools():
    """Register all default tools"""
    from .rag_tools import RAGSearchTool
    from .validation_tools import CodeValidationTool, SecurityScanTool
    from .docs_tools import DocsLookupTool
    
    registry = get_tool_registry()
    
    # Register tool classes
    registry.register_class(RAGSearchTool)
    registry.register_class(CodeValidationTool)
    registry.register_class(SecurityScanTool)
    registry.register_class(DocsLookupTool)
    
    logger.info(f"✅ Registered {len(registry.list_tools())} default tools")
