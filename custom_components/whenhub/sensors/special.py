"""Special Event sensor for WhenHub integration.

This module implements sensors for special holidays and astronomical events
(e.g., Christmas, Easter, Solstices). Special event sensors calculate dates
for fixed holidays and compute dates for moveable feasts like Easter.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

from ..const import (
    SPECIAL_SENSOR_TYPES,
)
from .base import BaseCountdownSensor

if TYPE_CHECKING:
    from ..coordinator import WhenHubCoordinator

_LOGGER = logging.getLogger(__name__)


class SpecialEventSensor(BaseCountdownSensor):
    """Sensor for special holidays and astronomical events.

    Provides countdown calculations for fixed and calculated special events:
    - days_until: Integer days until the next occurrence
    - days_since_last: Integer days since the last occurrence
    - event_date: Date of next occurrence (ISO format)
    - next_date: ISO date string of next occurrence
    - last_date: ISO date string of last occurrence

    Data is provided by the WhenHubCoordinator for efficient updates.
    """

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
    ) -> None:
        """Initialize the special event sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary containing special event configuration
            sensor_type: Type of sensor to create (from SPECIAL_SENSOR_TYPES)
        """
        super().__init__(coordinator, config_entry, event_data, sensor_type, SPECIAL_SENSOR_TYPES)

    @property
    def native_value(self) -> date | int | float | None:
        """Return the current sensor value from coordinator data.

        Returns:
            Sensor value appropriate for the sensor type (date, or int for days)
        """
        data = self.coordinator.data
        if not data:
            return None

        if self._sensor_type == "days_until":
            return data.get("days_until", 0)
        elif self._sensor_type == "days_since_last":
            return data.get("days_since_last")
        elif self._sensor_type == "event_date":
            return data.get("next_date")
        elif self._sensor_type == "next_date":
            return data.get("next_date")
        elif self._sensor_type == "last_date":
            return data.get("last_date")

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor."""
        if self._sensor_type == "event_date":
            data = self.coordinator.data
            attributes = self._get_base_attributes()
            attributes.update({
                "special_type": data.get("special_type"),
                "special_name": data.get("special_name"),
            })
            attributes.update(self._get_countdown_attributes())
            return attributes

        return {}
