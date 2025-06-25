"""Universal telemetry module for collecting anonymous usage data.
This module provides a unified interface for telemetry collection,
using PostHog as the backend.
"""

from __future__ import annotations

import logging
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union


# Configure telemetry logging before importing anything else
# By default, set telemetry loggers to WARNING level to hide INFO messages
# This can be overridden with CUA_TELEMETRY_LOG_LEVEL environment variable
def _configure_telemetry_logging() -> None:
    """Set up initial logging configuration for telemetry."""
    # Determine log level from environment variable or use WARNING by default
    env_level = os.environ.get("CUA_TELEMETRY_LOG_LEVEL", "WARNING").upper()
    level = logging.WARNING  # Default to WARNING to hide INFO messages

    if env_level == "DEBUG":
        level = logging.DEBUG
    elif env_level == "INFO":
        level = logging.INFO
    elif env_level == "ERROR":
        level = logging.ERROR

    # Configure the main telemetry logger
    telemetry_logger = logging.getLogger("core.telemetry")
    telemetry_logger.setLevel(level)


# Configure logging immediately
_configure_telemetry_logging()

# Import telemetry backend
try:
    from core.telemetry.posthog_client import (
        PostHogTelemetryClient,
        get_posthog_telemetry_client,
    )

    POSTHOG_AVAILABLE = True
except ImportError:
    logger = logging.getLogger("core.telemetry")
    logger.info("PostHog not available. Install with: pdm add posthog")
    POSTHOG_AVAILABLE = False

logger = logging.getLogger("core.telemetry")


# Check environment variables for global telemetry opt-out
def is_telemetry_globally_disabled() -> bool:
    """Check if telemetry is globally disabled via environment variables.

    Returns:
        bool: True if telemetry is globally disabled, False otherwise
    """
    # Only check for CUA_TELEMETRY_ENABLED - telemetry is enabled only if explicitly set to a truthy value
    telemetry_enabled = os.environ.get("CUA_TELEMETRY_ENABLED", "true").lower()
    return telemetry_enabled not in ("1", "true", "yes", "on")


class TelemetryBackend(str, Enum):
    """Available telemetry backend types."""

    POSTHOG = "posthog"
    NONE = "none"


class UniversalTelemetryClient:
    """Universal telemetry client that delegates to the PostHog backend."""

    def __init__(
        self,
        backend: Optional[str] = None,
    ):
        """Initialize the universal telemetry client.

        Args:
            backend: Backend to use ("posthog" or "none")
                     If not specified, will try PostHog
        """
        # Check for global opt-out first
        if is_telemetry_globally_disabled():
            self.backend_type = TelemetryBackend.NONE
            logger.info("Telemetry globally disabled via environment variable")
        # Determine which backend to use
        elif backend and backend.lower() == "none":
            self.backend_type = TelemetryBackend.NONE
        else:
            # Auto-detect based on environment variables and available backends
            if POSTHOG_AVAILABLE:
                self.backend_type = TelemetryBackend.POSTHOG
            else:
                self.backend_type = TelemetryBackend.NONE
                logger.warning("PostHog is not available, telemetry will be disabled")

        # Initialize the appropriate client
        self._client = self._initialize_client()
        self._enabled = self.backend_type != TelemetryBackend.NONE

    def _initialize_client(self) -> Any:
        """Initialize the appropriate telemetry client based on the selected backend."""
        if self.backend_type == TelemetryBackend.POSTHOG and POSTHOG_AVAILABLE:
            logger.debug("Initializing PostHog telemetry client")
            return get_posthog_telemetry_client()
        else:
            logger.debug("No telemetry client initialized")
            return None

    def increment(self, counter_name: str, value: int = 1) -> None:
        """Increment a named counter.

        Args:
            counter_name: Name of the counter
            value: Amount to increment by (default: 1)
        """
        if self._client and self._enabled:
            self._client.increment(counter_name, value)

    def record_event(self, event_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Record an event with optional properties.

        Args:
            event_name: Name of the event
            properties: Event properties (must not contain sensitive data)
        """
        if self._client and self._enabled:
            self._client.record_event(event_name, properties)

    def flush(self) -> bool:
        """Flush any pending events to the backend.

        Returns:
            bool: True if successful, False otherwise
        """
        if self._client and self._enabled:
            return self._client.flush()
        return False

    def enable(self) -> None:
        """Enable telemetry collection."""
        if self._client and not is_telemetry_globally_disabled():
            self._client.enable()
            self._enabled = True
        else:
            if is_telemetry_globally_disabled():
                logger.info("Cannot enable telemetry: globally disabled via environment variable")
            self._enabled = False

    def disable(self) -> None:
        """Disable telemetry collection."""
        if self._client:
            self._client.disable()
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if telemetry is enabled.

        Returns:
            bool: True if telemetry is enabled, False otherwise
        """
        return self._enabled and not is_telemetry_globally_disabled()


# Global telemetry client instance
_universal_client: Optional[UniversalTelemetryClient] = None


def get_telemetry_client(
    backend: Optional[str] = None,
) -> UniversalTelemetryClient:
    """Get or initialize the global telemetry client.

    Args:
        backend: Backend to use ("posthog" or "none")

    Returns:
        The global telemetry client instance
    """
    global _universal_client

    if _universal_client is None:
        _universal_client = UniversalTelemetryClient(backend)

    return _universal_client


def increment(counter_name: str, value: int = 1) -> None:
    """Increment a named counter using the global telemetry client.

    Args:
        counter_name: Name of the counter
        value: Amount to increment by (default: 1)
    """
    client = get_telemetry_client()
    client.increment(counter_name, value)


def record_event(event_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
    """Record an event with optional properties using the global telemetry client.

    Args:
        event_name: Name of the event
        properties: Event properties (must not contain sensitive data)
    """
    client = get_telemetry_client()
    client.record_event(event_name, properties)


def flush() -> bool:
    """Flush any pending events using the global telemetry client.

    Returns:
        bool: True if successful, False otherwise
    """
    client = get_telemetry_client()
    return client.flush()


def enable_telemetry() -> bool:
    """Enable telemetry collection globally.

    Returns:
        bool: True if successfully enabled, False if globally disabled
    """
    if is_telemetry_globally_disabled():
        logger.info("Cannot enable telemetry: globally disabled via environment variable")
        return False

    client = get_telemetry_client()
    client.enable()
    return True


def disable_telemetry() -> None:
    """Disable telemetry collection globally."""
    client = get_telemetry_client()
    client.disable()


def is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled.

    Returns:
        bool: True if telemetry is enabled, False otherwise
    """
    # First check for global disable
    if is_telemetry_globally_disabled():
        return False

    # Get the global client and check
    client = get_telemetry_client()
    return client.is_enabled()


def set_telemetry_log_level(level: Optional[int] = None) -> None:
    """Set the logging level for telemetry loggers to reduce console output.

    By default, checks the CUA_TELEMETRY_LOG_LEVEL environment variable:
    - If set to "DEBUG", sets level to logging.DEBUG
    - If set to "INFO", sets level to logging.INFO
    - If set to "WARNING", sets level to logging.WARNING
    - If set to "ERROR", sets level to logging.ERROR
    - If not set, defaults to logging.WARNING

    This means telemetry logs will only show up when explicitly requested via
    the environment variable, not during normal operation.

    Args:
        level: The logging level to set (overrides environment variable if provided)
    """
    # Determine the level from environment variable if not explicitly provided
    if level is None:
        env_level = os.environ.get("CUA_TELEMETRY_LOG_LEVEL", "WARNING").upper()
        if env_level == "DEBUG":
            level = logging.DEBUG
        elif env_level == "INFO":
            level = logging.INFO
        elif env_level == "WARNING":
            level = logging.WARNING
        elif env_level == "ERROR":
            level = logging.ERROR
        else:
            # Default to WARNING if environment variable is not recognized
            level = logging.WARNING

    # Set the level for all telemetry-related loggers
    telemetry_loggers = [
        "core.telemetry",
        "agent.telemetry",
        "computer.telemetry",
        "posthog",
    ]

    for logger_name in telemetry_loggers:
        try:
            logging.getLogger(logger_name).setLevel(level)
        except Exception:
            pass


# Set telemetry loggers to appropriate level based on environment variable
# This is called at module import time to ensure proper configuration before any logging happens
set_telemetry_log_level()
