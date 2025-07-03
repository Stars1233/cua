"""This module provides the core telemetry functionality for CUA libraries.

It provides a low-overhead way to collect anonymous usage data.
"""

from core.telemetry.telemetry import (
    UniversalTelemetryClient,
    enable_telemetry,
    disable_telemetry,
    flush,
    get_telemetry_client,
    increment,
    record_event,
    is_telemetry_enabled,
    is_telemetry_globally_disabled,
)


__all__ = [
    "UniversalTelemetryClient",
    "enable_telemetry",
    "disable_telemetry",
    "flush",
    "get_telemetry_client",
    "increment",
    "record_event",
    "is_telemetry_enabled",
    "is_telemetry_globally_disabled",
]
