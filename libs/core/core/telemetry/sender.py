"""Telemetry sender module for sending anonymous usage data."""

import logging
from typing import Any, Dict

logger = logging.getLogger("core.telemetry")


def send_telemetry(payload: Dict[str, Any]) -> bool:
    """Send telemetry data to collection endpoint.

    Args:
        payload: Telemetry data to send

    Returns:
        bool: True if sending was successful, False otherwise
    """
    try:
        # For now, just log the payload and return success
        logger.debug(f"Would send telemetry: {payload}")
        return True
    except Exception as e:
        logger.debug(f"Error sending telemetry: {e}")
        return False
