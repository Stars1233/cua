"""SOM - Computer Vision and OCR library for detecting and analyzing UI elements."""

__version__ = "0.1.0"

from .detect import OmniParser
from .models import (
    BoundingBox,
    UIElement,
    IconElement,
    TextElement,
    ParserMetadata,
    ParseResult
)

__all__ = [
    "OmniParser",
    "BoundingBox",
    "UIElement",
    "IconElement",
    "TextElement",
    "ParserMetadata",
    "ParseResult"
] 