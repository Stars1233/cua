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

**Som** (Set-of-Mark) is a visual grounding component for the Computer-Use Agent (CUA) framework powering Cua, for detecting and analyzing UI elements in screenshots. Optimized for macOS Silicon with Metal Performance Shaders (MPS), it combines YOLO-based icon detection with EasyOCR text recognition to provide comprehensive UI element analysis.

## Features

- Optimized for Apple Silicon with MPS acceleration
- Icon detection using YOLO with multi-scale processing
- Text recognition using EasyOCR (GPU-accelerated)
- Automatic hardware detection (MPS → CUDA → CPU)
- Smart detection parameters tuned for UI elements
- Detailed visualization with numbered annotations
- Performance benchmarking tools

## System Requirements

- **Recommended**: macOS with Apple Silicon
  - Uses Metal Performance Shaders (MPS)
  - Multi-scale detection enabled
  - ~0.4s average detection time
  
- **Supported**: Any Python 3.11+ environment
  - Falls back to CPU if no GPU available
  - Single-scale detection on CPU
  - ~1.3s average detection time

## Installation

```bash
# Using PDM (recommended)
pdm install

# Using pip
pip install -e .
```

## Quick Start

```python
from som import OmniParser
from PIL import Image

# Initialize parser
parser = OmniParser()

# Process an image
image = Image.open("screenshot.png")
result = parser.parse(
    image,
    box_threshold=0.3,    # Confidence threshold
    iou_threshold=0.1,    # Overlap threshold
    use_ocr=True         # Enable text detection
)

# Access results
for elem in result.elements:
    if elem.type == "icon":
        print(f"Icon: confidence={elem.confidence:.3f}, bbox={elem.bbox.coordinates}")
    else:  # text
        print(f"Text: '{elem.content}', confidence={elem.confidence:.3f}")
```

## Configuration

### Detection Parameters

#### Box Threshold (0.3)
Controls the confidence threshold for accepting detections:
```
High Threshold (0.3):     Low Threshold (0.01):
+----------------+        +----------------+
|                |        |  +--------+    |
|   Confident    |        |  |Unsure?|    |
|   Detection    |        |  +--------+    |
|   (✓ Accept)   |        |  (? Reject)   |
|                |        |                |
+----------------+        +----------------+
conf = 0.85             conf = 0.02
```
- Higher values (0.3) yield more precise but fewer detections
- Lower values (0.01) catch more potential icons but increase false positives
- Default is 0.3 for optimal precision/recall balance

#### IOU Threshold (0.1)
Controls how overlapping detections are merged:
```
IOU = Intersection Area / Union Area

Low Overlap (Keep Both):   High Overlap (Merge):
+----------+              +----------+
|     Box1 |              |  Box1   |
|          |     vs.      |+-----+  |
+----------+              ||Box2 |  |
    +----------+          |+-----+  |
    |   Box2   |          +----------+
    |          |
    +----------+
IOU ≈ 0.05 (Keep Both)    IOU ≈ 0.7 (Merge)
```
- Lower values (0.1) more aggressively remove overlapping boxes
- Higher values (0.5) allow more overlapping detections
- Default is 0.1 to handle densely packed UI elements

### OCR Configuration

- **Engine**: EasyOCR
  - Primary choice for all platforms
  - Fast initialization and processing
  - Built-in English language support
  - GPU acceleration when available

- **Settings**:
  - Timeout: 5 seconds
  - Confidence threshold: 0.5
  - Paragraph mode: Disabled
  - Language: English only

## Performance

### Hardware Acceleration

#### MPS (Metal Performance Shaders)
- Multi-scale detection (640px, 1280px, 1920px)
- Test-time augmentation enabled
- Half-precision (FP16)
- Average detection time: ~0.4s
- Best for production use when available

#### CPU
- Single-scale detection (1280px)
- Full-precision (FP32)
- Average detection time: ~1.3s
- Reliable fallback option

### Example Output Structure

```
examples/output/
├── {timestamp}_no_ocr/
│   ├── annotated_images/
│   │   └── screenshot_analyzed.png
│   ├── screen_details.txt
│   └── summary.json
└── {timestamp}_ocr/
    ├── annotated_images/
    │   └── screenshot_analyzed.png
    ├── screen_details.txt
    └── summary.json
```

## Development

### Test Data
- Place test screenshots in `examples/test_data/`
- Not tracked in git to keep repository size manageable
- Default test image: `test_screen.png` (1920x1080)

### Running Tests
```bash
# Run benchmark with no OCR
python examples/omniparser_examples.py examples/test_data/test_screen.png --runs 5 --ocr none

# Run benchmark with OCR
python examples/omniparser_examples.py examples/test_data/test_screen.png --runs 5 --ocr easyocr
```

## License

MIT License - See LICENSE file for details.
