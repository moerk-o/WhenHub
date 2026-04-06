"""Custom Pattern sensor for WhenHub integration (FR09).

Provides countdown and occurrence sensors for user-defined repeating patterns
(e.g. "4th Thursday of November", "first Monday of every month", "every 3 days").
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

from ..const import CUSTOM_PATTERN_SENSOR_TYPES
from .base import BaseCountdownSensor

if TYPE_CHECKING:
    from ..coordinator import WhenHubCoordinator

_LOGGER = logging.getLogger(__name__)


class CustomPatternSensor(BaseCountdownSensor):
    """Sensor for custom repeating patterns.

    Provides:
    - days_until: Integer days until the next occurrence
    - days_since_last: Integer days since the last occurrence
    - event_date / next_date: Timestamp of the next occurrence
    - last_date: Timestamp of the last occurrence
    - occurrence_count: How many times this pattern has fired since dtstart

    Data is provided by WhenHubCoordinator.
    """

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
    ) -> None:
        """Initialize the custom pattern sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary containing custom pattern configuration
            sensor_type: Type of sensor to create (from CUSTOM_PATTERN_SENSOR_TYPES)
        """
        super().__init__(
            coordinator, config_entry, event_data, sensor_type, CUSTOM_PATTERN_SENSOR_TYPES
        )

    @property
    def native_value(self) -> datetime | int | None:
        """Return the current sensor value from coordinator data."""
        data = self.coordinator.data
        if not data:
            return None

        if self._sensor_type == "days_until":
            return data.get("days_until", 0)
        elif self._sensor_type == "days_since_last":
            return data.get("days_since_last")
        elif self._sensor_type in ("event_date", "next_date"):
            return data.get("next_date")
        elif self._sensor_type == "last_date":
            return data.get("last_date")
        elif self._sensor_type == "occurrence_count":
            return data.get("occurrence_count", 0)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for the event_date sensor."""
        if self._sensor_type == "event_date":
            data = self.coordinator.data
            attributes = self._get_base_attributes()
            attributes.update({
                "cp_freq": data.get("cp_freq"),
                "occurrence_count": data.get("occurrence_count"),
            })
            attributes.update(self._get_countdown_attributes())
            return attributes

        return {}
