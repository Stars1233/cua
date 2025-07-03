"""Gradio UI for Computer-Use Agent."""

import gradio as gr
from typing import Optional

from .app import create_gradio_ui


def registry(name: str = "cua:gpt-4o") -> gr.Blocks:
    """Create and register a Gradio UI for the Computer-Use Agent.

    Args:
        name: The name to use for the Gradio app, in format 'provider:model'

    Returns:
        A Gradio Blocks application
    """
    provider, model = name.split(":", 1) if ":" in name else ("openai", name)

    # Create and return the Gradio UI
    return create_gradio_ui(provider_name=provider, model_name=model)
