"""MCP Server for Computer-Use Agent (CUA)."""

import sys
import os

# Add detailed debugging at import time
with open("/tmp/mcp_server_debug.log", "w") as f:
    f.write(f"Python executable: {sys.executable}\n")
    f.write(f"Python version: {sys.version}\n")
    f.write(f"Working directory: {os.getcwd()}\n")
    f.write(f"Python path:\n{chr(10).join(sys.path)}\n")
    f.write(f"Environment variables:\n")
    for key, value in os.environ.items():
        f.write(f"{key}={value}\n")

from .server import server, main

__version__ = "0.1.0"
__all__ = ["server", "main"]
