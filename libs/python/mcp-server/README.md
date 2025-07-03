<div align="center">
<h1>
  <div class="image-wrapper" style="display: inline-block;">
    <picture>
      <source media="(prefers-color-scheme: dark)" alt="logo" height="150" srcset="../../img/logo_white.png" style="display: block; margin: auto;">
      <source media="(prefers-color-scheme: light)" alt="logo" height="150" srcset="../../img/logo_black.png" style="display: block; margin: auto;">
      <img alt="Shows my svg">
    </picture>
  </div>

  [![Python](https://img.shields.io/badge/Python-333333?logo=python&logoColor=white&labelColor=333333)](#)
  [![macOS](https://img.shields.io/badge/macOS-000000?logo=apple&logoColor=F0F0F0)](#)
  [![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?&logo=discord&logoColor=white)](https://discord.com/invite/mVnXXpdE85)
  [![PyPI](https://img.shields.io/pypi/v/cua-computer?color=333333)](https://pypi.org/project/cua-computer/)
</h1>
</div>

**cua-mcp-server** is a MCP server for the Computer-Use Agent (CUA), allowing you to run CUA through Claude Desktop or other MCP clients.
### Get started with Agent

## Prerequisites

Before installing the MCP server, you'll need to set up the full Computer-Use Agent capabilities as described in [Option 2 of the main README](../../README.md#option-2-full-computer-use-agent-capabilities). This includes:

1. Installing the Lume CLI
2. Pulling the latest macOS CUA image
3. Starting the Lume daemon service
4. Installing the required Python libraries (Optional: only needed if you want to verify the agent is working before installing MCP server)

Make sure these steps are completed and working before proceeding with the MCP server installation.

## Installation

Install the package from PyPI:

```bash
pip install cua-mcp-server
```

This will install:
- The MCP server
- CUA agent and computer dependencies 
- An executable `cua-mcp-server` script in your PATH

## Easy Setup Script

If you want to simplify installation, you can use this one-liner to download and run the installation script:

```bash
curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/python/mcp-server/scripts/install_mcp_server.sh | bash
```

This script will:
- Create the ~/.cua directory if it doesn't exist
- Generate a startup script at ~/.cua/start_mcp_server.sh
- Make the script executable
- The startup script automatically manages Python virtual environments and installs/updates the cua-mcp-server package

You can then use the script in your MCP configuration like this:

```json
{ 
  "mcpServers": {
    "cua-agent": {
      "command": "/bin/bash",
      "args": ["~/.cua/start_mcp_server.sh"],
      "env": {
        "CUA_AGENT_LOOP": "OMNI",
        "CUA_MODEL_PROVIDER": "ANTHROPIC",
        "CUA_MODEL_NAME": "claude-3-7-sonnet-20250219",
        "CUA_PROVIDER_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Development Guide

If you want to develop with the cua-mcp-server directly without installation, you can use this configuration:

```json
{
  "mcpServers": {
    "cua-agent": {
      "command": "/bin/bash",
      "args": ["~/cua/libs/python/mcp-server/scripts/start_mcp_server.sh"],
      "env": {
        "CUA_AGENT_LOOP": "UITARS",
        "CUA_MODEL_PROVIDER": "OAICOMPAT",
        "CUA_MODEL_NAME": "ByteDance-Seed/UI-TARS-1.5-7B",
        "CUA_PROVIDER_BASE_URL": "https://****************.us-east-1.aws.endpoints.huggingface.cloud/v1",
        "CUA_PROVIDER_API_KEY": "your-api-key"
      }
    }
  }
}
```

This configuration:
- Uses the start_mcp_server.sh script which automatically sets up the Python path and runs the server module
- Works with Claude Desktop, Cursor, or any other MCP client
- Automatically uses your development code without requiring installation

Just add this to your MCP client's configuration and it will use your local development version of the server.

### Troubleshooting

If you get a `/bin/bash: ~/cua/libs/python/mcp-server/scripts/start_mcp_server.sh: No such file or directory` error, try changing the path to the script to be absolute instead of relative.

To see the logs:
```
tail -n 20 -f ~/Library/Logs/Claude/mcp*.log
```

## Claude Desktop Integration

To use with Claude Desktop, add an entry to your Claude Desktop configuration (`claude_desktop_config.json`, typically found in `~/.config/claude-desktop/`):

For more information on MCP with Claude Desktop, see the [official MCP User Guide](https://modelcontextprotocol.io/quickstart/user).

## Cursor Integration

To use with Cursor, add an MCP configuration file in one of these locations:

- **Project-specific**: Create `.cursor/mcp.json` in your project directory
- **Global**: Create `~/.cursor/mcp.json` in your home directory

After configuration, you can simply tell Cursor's Agent to perform computer tasks by explicitly mentioning the CUA agent, such as "Use the computer control tools to open Safari."

For more information on MCP with Cursor, see the [official Cursor MCP documentation](https://docs.cursor.com/context/model-context-protocol).

### First-time Usage Notes

**API Keys**: Ensure you have valid API keys:
   - Add your Anthropic API key, or other model provider API key in the Claude Desktop config (as shown above)
   - Or set it as an environment variable in your shell profile

## Configuration

The server is configured using environment variables (can be set in the Claude Desktop config):

| Variable | Description | Default |
|----------|-------------|---------|
| `CUA_AGENT_LOOP` | Agent loop to use (OPENAI, ANTHROPIC, UITARS, OMNI) | OMNI |
| `CUA_MODEL_PROVIDER` | Model provider (ANTHROPIC, OPENAI, OLLAMA, OAICOMPAT) | ANTHROPIC |
| `CUA_MODEL_NAME` | Model name to use | None (provider default) |
| `CUA_PROVIDER_BASE_URL` | Base URL for provider API | None |
| `CUA_MAX_IMAGES` | Maximum number of images to keep in context | 3 |

## Available Tools

The MCP server exposes the following tools to Claude:

1. `run_cua_task` - Run a single Computer-Use Agent task with the given instruction
2. `run_multi_cua_tasks` - Run multiple tasks in sequence

## Usage

Once configured, you can simply ask Claude to perform computer tasks:

- "Open Chrome and go to github.com"
- "Create a folder called 'Projects' on my desktop"
- "Find all PDFs in my Downloads folder"
- "Take a screenshot and highlight the error message"

Claude will automatically use your CUA agent to perform these tasks.