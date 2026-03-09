from typing import Optional, Any, Dict, List
import logging
from hap.tools.base import Tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Bridge between Agent and Tools.

    Provides tool registration, management, and execution capabilities.
    Acts as a central registry that agents use to discover and invoke tools.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> "ToolRegistry":
        """
        Register a tool.

        Args:
            tool: Tool instance to register

        Returns:
            Self for method chaining
        """
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already exists and will be overwritten.")

        self._tools[tool.name] = tool
        logger.info(f"Tool '{tool.name}' registered.")
        return self

    def register_tools(self, *tools: Tool) -> "ToolRegistry":
        """
        Register multiple tools at once.

        Args:
            *tools: Tool instances to register

        Returns:
            Self for method chaining

        Example:
            registry = ToolRegistry()
            registry.register_tools(WebSearch(), BashTool(), PythonREPL())
        """
        for tool in tools:
            self.register_tool(tool)
        return self

    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool.

        Args:
            name: Tool name to unregister

        Returns:
            True if tool was found and removed, False otherwise
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Tool '{name}' unregistered.")
            return True
        else:
            logger.warning(f"Tool '{name}' does not exist.")
            return False

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """
        Get list of all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """
        Check if a tool is registered.

        Args:
            name: Tool name to check

        Returns:
            True if tool exists, False otherwise
        """
        return name in self._tools

    def get_tools_description(self) -> str:
        """
        Get formatted description of all available tools.

        Returns:
            Tool descriptions string for building prompts
        """
        descriptions = [tool.get_description() for tool in self._tools.values()]
        return "\n\n".join(descriptions) if descriptions else "No tools available"

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters dictionary

        Returns:
            Tool execution result (can be Any type)
        """
        if tool_name not in self._tools:
            return f"Error: Tool '{tool_name}' not found."

        tool = self._tools[tool_name]
        try:
            return tool.run(parameters)
        except Exception as e:
            return f"Error: Exception occurred while executing tool '{tool_name}': {str(e)}"

    def clear(self) -> "ToolRegistry":
        """
        Clear all registered tools.

        Returns:
            Self for method chaining
        """
        self._tools.clear()
        logger.info("All tools cleared.")
        return self

    def __len__(self) -> int:
        """Return number of registered tools."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if tool name is registered."""
        return name in self._tools

    def __iter__(self):
        """Iterate over registered tools."""
        return iter(self._tools.values())
