"""Telemetry client using PostHog for collecting anonymous usage data."""

from __future__ import annotations

import json
import logging
import os
import random
import time
import uuid
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import posthog
from core import __version__

logger = logging.getLogger("core.telemetry")

# Controls how frequently telemetry will be sent (percentage)
TELEMETRY_SAMPLE_RATE = 100  # 100% sampling rate (was 5%)

# Public PostHog config for anonymous telemetry
# These values are intentionally public and meant for anonymous telemetry only
# https://posthog.com/docs/product-analytics/troubleshooting#is-it-ok-for-my-api-key-to-be-exposed-and-public
PUBLIC_POSTHOG_API_KEY = "phc_eSkLnbLxsnYFaXksif1ksbrNzYlJShr35miFLDppF14"
PUBLIC_POSTHOG_HOST = "https://eu.i.posthog.com"


@dataclass
class TelemetryConfig:
    """Configuration for telemetry collection."""

    enabled: bool = True  # Default to enabled (opt-out)
    sample_rate: float = TELEMETRY_SAMPLE_RATE

    @classmethod
    def from_env(cls) -> TelemetryConfig:
        """Load config from environment variables."""
        # Check for multiple environment variables that can disable telemetry:
        # CUA_TELEMETRY=off to disable telemetry (legacy way)
        # CUA_TELEMETRY_DISABLED=1 to disable telemetry (new, more explicit way)
        telemetry_disabled = os.environ.get("CUA_TELEMETRY", "").lower() == "off" or os.environ.get(
            "CUA_TELEMETRY_DISABLED", ""
        ).lower() in ("1", "true", "yes", "on")

        return cls(
            enabled=not telemetry_disabled,
            sample_rate=float(os.environ.get("CUA_TELEMETRY_SAMPLE_RATE", TELEMETRY_SAMPLE_RATE)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "sample_rate": self.sample_rate,
        }


def get_posthog_config() -> dict:
    """Get PostHog configuration for anonymous telemetry.

    Uses the public API key that's specifically intended for anonymous telemetry collection.
    No private keys are used or required from users.

    Returns:
        Dict with PostHog configuration
    """
    # Return the public config
    logger.debug("Using public PostHog configuration")
    return {"api_key": PUBLIC_POSTHOG_API_KEY, "host": PUBLIC_POSTHOG_HOST}


class PostHogTelemetryClient:
    """Collects and reports telemetry data via PostHog."""

    def __init__(self):
        """Initialize PostHog telemetry client."""
        self.config = TelemetryConfig.from_env()
        self.installation_id = self._get_or_create_installation_id()
        self.initialized = False
        self.queued_events: List[Dict[str, Any]] = []
        self.start_time = time.time()

        # Log telemetry status on startup
        if self.config.enabled:
            logger.info(f"Telemetry enabled (sampling at {self.config.sample_rate}%)")
            # Initialize PostHog client if config is available
            self._initialize_posthog()
        else:
            logger.info("Telemetry disabled")

    def _initialize_posthog(self) -> bool:
        """Initialize the PostHog client with configuration.

        Returns:
            bool: True if initialized successfully, False otherwise
        """
        if self.initialized:
            return True

        posthog_config = get_posthog_config()

        try:
            # Initialize the PostHog client
            posthog.api_key = posthog_config["api_key"]
            posthog.host = posthog_config["host"]

            # Configure the client
            posthog.debug = os.environ.get("CUA_TELEMETRY_DEBUG", "").lower() == "on"
            posthog.disabled = not self.config.enabled

            # Log telemetry status
            if not posthog.disabled:
                logger.info(
                    f"Initializing PostHog telemetry with installation ID: {self.installation_id}"
                )
                if posthog.debug:
                    logger.debug(f"PostHog API Key: {posthog.api_key}")
                    logger.debug(f"PostHog Host: {posthog.host}")
            else:
                logger.info("PostHog telemetry is disabled")

            # Identify this installation
            self._identify()

            # Process any queued events
            for event in self.queued_events:
                posthog.capture(
                    distinct_id=self.installation_id,
                    event=event["event"],
                    properties=event["properties"],
                )
            self.queued_events = []

            self.initialized = True
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize PostHog: {e}")
            return False

    def _identify(self) -> None:
        """Identify the current installation with PostHog."""
        try:
            properties = {
                "version": __version__,
                "is_ci": "CI" in os.environ,
                "os": os.name,
                "python_version": sys.version.split()[0],
            }

            logger.debug(
                f"Identifying PostHog user: {self.installation_id} with properties: {properties}"
            )
            posthog.identify(
                distinct_id=self.installation_id,
                properties=properties,
            )
        except Exception as e:
            logger.warning(f"Failed to identify with PostHog: {e}")

    def _get_or_create_installation_id(self) -> str:
        """Get or create a unique installation ID that persists across runs.

        The ID is always stored within the core library directory itself,
        ensuring it persists regardless of how the library is used.

        This ID is not tied to any personal information.
        """
        # Get the core library directory (where this file is located)
        try:
            # Find the core module directory using this file's location
            core_module_dir = Path(
                __file__
            ).parent.parent  # core/telemetry/posthog_client.py -> core/telemetry -> core
            storage_dir = core_module_dir / ".storage"
            storage_dir.mkdir(exist_ok=True)

            id_file = storage_dir / "installation_id"

            # Try to read existing ID
            if id_file.exists():
                try:
                    stored_id = id_file.read_text().strip()
                    if stored_id:  # Make sure it's not empty
                        logger.debug(f"Using existing installation ID: {stored_id}")
                        return stored_id
                except Exception as e:
                    logger.debug(f"Error reading installation ID file: {e}")

            # Create new ID
            new_id = str(uuid.uuid4())
            try:
                id_file.write_text(new_id)
                logger.debug(f"Created new installation ID: {new_id}")
                return new_id
            except Exception as e:
                logger.warning(f"Could not write installation ID: {e}")
        except Exception as e:
            logger.warning(f"Error accessing core module directory: {e}")

        # Last resort: Create a new in-memory ID
        logger.warning("Using random installation ID (will not persist across runs)")
        return str(uuid.uuid4())

    def increment(self, counter_name: str, value: int = 1) -> None:
        """Increment a named counter.

        Args:
            counter_name: Name of the counter
            value: Amount to increment by (default: 1)
        """
        if not self.config.enabled:
            return

        # Apply sampling to reduce number of events
        if random.random() * 100 > self.config.sample_rate:
            return

        properties = {
            "value": value,
            "counter_name": counter_name,
            "version": __version__,
        }

        if self.initialized:
            try:
                posthog.capture(
                    distinct_id=self.installation_id,
                    event="counter_increment",
                    properties=properties,
                )
            except Exception as e:
                logger.debug(f"Failed to send counter event to PostHog: {e}")
        else:
            # Queue the event for later
            self.queued_events.append({"event": "counter_increment", "properties": properties})
            # Try to initialize now if not already
            self._initialize_posthog()

    def record_event(self, event_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Record an event with optional properties.

        Args:
            event_name: Name of the event
            properties: Event properties (must not contain sensitive data)
        """
        if not self.config.enabled:
            logger.debug(f"Telemetry disabled, skipping event: {event_name}")
            return

        # Apply sampling to reduce number of events
        if random.random() * 100 > self.config.sample_rate:
            logger.debug(
                f"Event sampled out due to sampling rate {self.config.sample_rate}%: {event_name}"
            )
            return

        event_properties = {"version": __version__, **(properties or {})}

        logger.info(f"Recording event: {event_name} with properties: {event_properties}")

        if self.initialized:
            try:
                posthog.capture(
                    distinct_id=self.installation_id, event=event_name, properties=event_properties
                )
                logger.info(f"Sent event to PostHog: {event_name}")
                # Flush immediately to ensure delivery
                posthog.flush()
            except Exception as e:
                logger.warning(f"Failed to send event to PostHog: {e}")
        else:
            # Queue the event for later
            logger.info(f"PostHog not initialized, queuing event for later: {event_name}")
            self.queued_events.append({"event": event_name, "properties": event_properties})
            # Try to initialize now if not already
            initialize_result = self._initialize_posthog()
            logger.info(f"Attempted to initialize PostHog: {initialize_result}")

    def flush(self) -> bool:
        """Flush any pending events to PostHog.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.config.enabled:
            return False

        if not self.initialized and not self._initialize_posthog():
            return False

        try:
            posthog.flush()
            return True
        except Exception as e:
            logger.debug(f"Failed to flush PostHog events: {e}")
            return False

    def enable(self) -> None:
        """Enable telemetry collection."""
        self.config.enabled = True
        if posthog:
            posthog.disabled = False
        logger.info("Telemetry enabled")
        self._initialize_posthog()

    def disable(self) -> None:
        """Disable telemetry collection."""
        self.config.enabled = False
        if posthog:
            posthog.disabled = True
        logger.info("Telemetry disabled")


# Global telemetry client instance
_client: Optional[PostHogTelemetryClient] = None


def get_posthog_telemetry_client() -> PostHogTelemetryClient:
    """Get or initialize the global PostHog telemetry client.

    Returns:
        The global telemetry client instance
    """
    global _client

    if _client is None:
        _client = PostHogTelemetryClient()

    return _client


def disable_telemetry() -> None:
    """Disable telemetry collection globally."""
    if _client is not None:
        _client.disable()
