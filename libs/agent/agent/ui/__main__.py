"""
Main entry point for agent.ui module.

This allows running the agent UI with:
    python -m agent.ui

Instead of:
    python -m agent.ui.gradio.app
"""

from .gradio.app import create_gradio_ui

if __name__ == "__main__":
    app = create_gradio_ui()
    app.launch(share=False, inbrowser=True)
