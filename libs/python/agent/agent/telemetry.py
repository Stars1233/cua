"""Telemetry support for Agent class."""

import os
import platform
import sys
import time
from typing import Any, Dict, Optional

from core.telemetry import (
    record_event,
    is_telemetry_enabled,
    flush,
    get_telemetry_client,
    increment,
)

# System information used for telemetry
SYSTEM_INFO = {
    "os": sys.platform,
    "python_version": platform.python_version(),
}
