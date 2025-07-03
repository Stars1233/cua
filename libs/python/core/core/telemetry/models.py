"""Models for telemetry data."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    """A telemetry event with properties."""

    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class TelemetryPayload(BaseModel):
    """Telemetry payload sent to the server."""

    version: str
    installation_id: str
    counters: Dict[str, int] = Field(default_factory=dict)
    events: List[TelemetryEvent] = Field(default_factory=list)
    duration: float = 0
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class UserRecord(BaseModel):
    """User record stored in the telemetry database."""

    id: str
    version: Optional[str] = None
    created_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    is_ci: bool = False
