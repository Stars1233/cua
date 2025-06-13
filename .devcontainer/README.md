# Dev Container Setup

This repository includes a Dev Container configuration that simplifies the development setup to just 3 steps:

## Quick Start

![Clipboard-20250611-180809-459](https://github.com/user-attachments/assets/447eaeeb-0eec-4354-9a82-44446e202e06)

1. **Install Dev Containers extension** in VS Code
2. **Clone and open in container**: 
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Dev Containers: Clone Repository in Container Volume..."
   - Paste the repository URL: `https://github.com/trycua/cua.git`
3. **Hit play**: Once the container builds, you're ready to develop!

## What's Included

The dev container automatically:

- ✅ Sets up Python 3.11 environment
- ✅ Installs all system dependencies (build tools, OpenGL, etc.)
- ✅ Configures Python paths for all packages
- ✅ Installs Python extensions (Black, Ruff, Pylance)
- ✅ Forwards port 7860 for the Gradio web UI
- ✅ Mounts your source code for live editing
- ✅ Creates the required `.env.local` file

## Running Examples

After the container is built, you can run examples directly:

```bash
# Run the agent UI (Gradio web interface)
python examples/agent_ui_examples.py

# Run computer examples
python examples/computer_examples.py

# Run computer UI examples
python examples/computer_ui_examples.py
```

The Gradio UI will be available at `http://localhost:7860` and will automatically forward to your host machine.

## Environment Variables

You'll need to add your API keys to `.env.local`:

```bash
# Required for Anthropic provider
ANTHROPIC_API_KEY=your_anthropic_key_here

# Required for OpenAI provider
OPENAI_API_KEY=your_openai_key_here
```

## Notes

- The container connects to `host.docker.internal:7777` for Lume server communication
- All Python packages are pre-installed and configured
- Source code changes are reflected immediately (no rebuild needed)
- The container uses the same Dockerfile as the regular Docker development environment
