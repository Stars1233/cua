"""Telemetry client for collecting anonymous usage data."""

from __future__ import annotations

import json
import logging
import os
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core import __version__
from core.telemetry.sender import send_telemetry

logger = logging.getLogger("core.telemetry")

# Controls how frequently telemetry will be sent (percentage)
TELEMETRY_SAMPLE_RATE = 5  # 5% sampling rate


@dataclass
class TelemetryConfig:
    """Configuration for telemetry collection."""

    enabled: bool = False  # Default to opt-in
    sample_rate: float = TELEMETRY_SAMPLE_RATE
    project_root: Optional[Path] = None

    @classmethod
    def from_env(cls, project_root: Optional[Path] = None) -> TelemetryConfig:
        """Load config from environment variables."""
        # CUA_TELEMETRY should be set to "on" to enable telemetry (opt-in)
        return cls(
            enabled=os.environ.get("CUA_TELEMETRY", "").lower() == "on",
            sample_rate=float(os.environ.get("CUA_TELEMETRY_SAMPLE_RATE", TELEMETRY_SAMPLE_RATE)),
            project_root=project_root,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "sample_rate": self.sample_rate,
        }


class TelemetryClient:
    """Collects and reports telemetry data with transparency and sampling."""

    def __init__(
        self, project_root: Optional[Path] = None, config: Optional[TelemetryConfig] = None
    ):
        """Initialize telemetry client.

        Args:
            project_root: Root directory of the project
            config: Telemetry configuration, or None to load from environment
        """
        self.config = config or TelemetryConfig.from_env(project_root)
        self.installation_id = self._get_or_create_installation_id()
        self.counters: Dict[str, int] = {}
        self.events: List[Dict[str, Any]] = []
        self.start_time = time.time()

        # Log telemetry status on startup
        if self.config.enabled:
            logger.info(f"Telemetry enabled (sampling at {self.config.sample_rate}%)")
        else:
            logger.info("Telemetry disabled")

        # Create .cua directory if it doesn't exist and config is provided
        if self.config.project_root:
            self._setup_local_storage()

    def _get_or_create_installation_id(self) -> str:
        """Get or create a random installation ID.

        This ID is not tied to any personal information.
        """
        if self.config.project_root:
            id_file = self.config.project_root / ".cua" / "installation_id"
            if id_file.exists():
                try:
                    return id_file.read_text().strip()
                except Exception:
                    pass

            # Create new ID if not exists
            new_id = str(uuid.uuid4())
            try:
                id_file.parent.mkdir(parents=True, exist_ok=True)
                id_file.write_text(new_id)
                return new_id
            except Exception:
                pass

        # Fallback to in-memory ID if file operations fail
        return str(uuid.uuid4())

    def _setup_local_storage(self) -> None:
        """Create local storage directories and files."""
        if not self.config.project_root:
            return

        cua_dir = self.config.project_root / ".cua"
        cua_dir.mkdir(parents=True, exist_ok=True)

        # Store telemetry config
        config_path = cua_dir / "telemetry_config.json"
        with open(config_path, "w") as f:
            json.dump(self.config.to_dict(), f)

    def increment(self, counter_name: str, value: int = 1) -> None:
        """Increment a named counter.

        Args:
            counter_name: Name of the counter
            value: Amount to increment by (default: 1)
        """
        if not self.config.enabled:
            return

        if counter_name not in self.counters:
            self.counters[counter_name] = 0
        self.counters[counter_name] += value

    def record_event(self, event_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Record an event with optional properties.

        Args:
            event_name: Name of the event
            properties: Event properties (must not contain sensitive data)
        """
        if not self.config.enabled:
            return

        # Increment counter for this event type
        counter_key = f"event:{event_name}"
        self.increment(counter_key)

        # Record event details for deeper analysis (if sampled)
        if properties and random.random() * 100 <= self.config.sample_rate:
            self.events.append(
                {"name": event_name, "properties": properties, "timestamp": time.time()}
            )

    def flush(self) -> bool:
        """Send collected telemetry if sampling criteria is met.

        Returns:
            bool: True if telemetry was sent, False otherwise
        """
        if not self.config.enabled or (not self.counters and not self.events):
            return False

        # Apply sampling - only send data for a percentage of installations
        if random.random() * 100 > self.config.sample_rate:
            logger.debug("Telemetry sampled out")
            self.counters.clear()
            self.events.clear()
            return False

        # Prepare telemetry payload
        payload = {
            "version": __version__,
            "installation_id": self.installation_id,
            "counters": self.counters.copy(),
            "events": self.events.copy(),
            "duration": time.time() - self.start_time,
            "timestamp": time.time(),
        }

        try:
            # Send telemetry data
            success = send_telemetry(payload)
            if success:
                logger.debug(
                    f"Telemetry sent: {len(self.counters)} counters, {len(self.events)} events"
                )
            else:
                logger.debug("Failed to send telemetry")
            return success
        except Exception as e:
            logger.debug(f"Failed to send telemetry: {e}")
            return False
        finally:
            # Clear data after sending
            self.counters.clear()
            self.events.clear()

    def enable(self) -> None:
        """Enable telemetry collection."""
        self.config.enabled = True
        logger.info("Telemetry enabled")
        if self.config.project_root:
            self._setup_local_storage()

    def disable(self) -> None:
        """Disable telemetry collection."""
        self.config.enabled = False
        logger.info("Telemetry disabled")
        if self.config.project_root:
            self._setup_local_storage()


# Global telemetry client instance
_client: Optional[TelemetryClient] = None


def get_telemetry_client(project_root: Optional[Path] = None) -> TelemetryClient:
    """Get or initialize the global telemetry client.

    Args:
        project_root: Root directory of the project

    Returns:
        The global telemetry client instance
    """
    global _client

    if _client is None:
        _client = TelemetryClient(project_root)

    return _client


def disable_telemetry() -> None:
    """Disable telemetry collection globally."""
    if _client is not None:
        _client.disable()
