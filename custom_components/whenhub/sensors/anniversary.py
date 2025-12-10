"""Anniversary sensor for WhenHub integration.

This module implements sensors for recurring anniversary events (e.g., wedding
anniversaries, company founding dates, annual celebrations). Anniversary sensors
track both upcoming and past occurrences of yearly repeating events.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

from ..const import (
    ANNIVERSARY_SENSOR_TYPES,
    TEXT_CALCULATION_RUNNING,
)
from .base import BaseCountdownSensor

if TYPE_CHECKING:
    from ..coordinator import WhenHubCoordinator

_LOGGER = logging.getLogger(__name__)


class AnniversarySensor(BaseCountdownSensor):
    """Sensor for recurring anniversary events.

    Provides comprehensive tracking for events that repeat annually:
    - days_until_next: Days until the next anniversary occurrence
    - days_since_last: Days since the last anniversary occurrence
    - event_date: Date of the next anniversary (ISO format)
    - occurrences_count: Total number of times the anniversary has occurred
    - next_date: ISO date of the next anniversary
    - last_date: ISO date of the last anniversary (if any)

    Data is provided by the WhenHubCoordinator for efficient updates.
    """

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
    ) -> None:
        """Initialize the anniversary sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary containing anniversary configuration (name, target_date, etc.)
            sensor_type: Type of sensor to create (from ANNIVERSARY_SENSOR_TYPES)
        """
        super().__init__(coordinator, config_entry, event_data, sensor_type, ANNIVERSARY_SENSOR_TYPES)

    @property
    def native_value(self) -> str | int | float | None:
        """Return the current sensor value from coordinator data.

        Returns:
            Sensor value appropriate for the sensor type with fallbacks on error
        """
        data = self.coordinator.data
        if not data:
            return self._get_fallback_value()

        if self._sensor_type == "days_until_next":
            return data.get("days_until_next", 0)
        elif self._sensor_type == "days_since_last":
            return data.get("days_since_last")
        elif self._sensor_type == "event_date":
            return data.get("next_anniversary")
        elif self._sensor_type == "occurrences_count":
            return data.get("occurrences_count", 0)
        elif self._sensor_type == "next_date":
            return data.get("next_anniversary")
        elif self._sensor_type == "last_date":
            return data.get("last_anniversary")

        return None

    def _get_fallback_value(self) -> str | int | None:
        """Get a safe fallback value based on sensor type for error scenarios.

        Provides reasonable default values when calculation errors occur,
        ensuring the integration remains functional even with invalid data.

        Returns:
            Appropriate fallback value based on sensor type
        """
        if self._sensor_type in ["days_until_next", "days_since_last", "occurrences_count"]:
            return 0
        elif self._sensor_type == "event_date":
            return date.today().isoformat()
        elif self._sensor_type in ["next_date", "last_date"]:
            return date.today().isoformat()
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor.

        Only event_date sensors get attributes - other anniversary sensors return empty dict
        to keep the state clean and focused.

        Returns:
            Dictionary with event info and countdown breakdown (for event_date only)
        """
        if self._sensor_type == "event_date":
            data = self.coordinator.data
            attributes = self._get_base_attributes()
            attributes.update({
                "initial_date": data.get("original_date"),
                "years_on_next": data.get("years_on_next", 0),
            })
            attributes.update(self._get_countdown_attributes())
            return attributes

        return {}
