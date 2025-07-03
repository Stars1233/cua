"""Omni provider tools - compatible with multiple LLM providers."""

from ....core.tools import BaseTool, ToolResult, ToolError, ToolFailure, CLIResult
from .base import BaseOmniTool
from .computer import ComputerTool
from .bash import BashTool
from .manager import ToolManager

# Re-export the tools with Omni-specific names for backward compatibility
OmniToolResult = ToolResult
OmniToolError = ToolError
OmniToolFailure = ToolFailure
OmniCLIResult = CLIResult

# We'll export specific tools once implemented
__all__ = [
    "BaseTool",
    "BaseOmniTool",
    "ToolResult",
    "ToolError",
    "ToolFailure",
    "CLIResult",
    "OmniToolResult",
    "OmniToolError",
    "OmniToolFailure",
    "OmniCLIResult",
    "ComputerTool",
    "BashTool",
    "ToolManager",
]
