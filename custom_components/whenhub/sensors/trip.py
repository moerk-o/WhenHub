"""Trip sensor for WhenHub integration.

This module implements sensors for multi-day trip events (e.g., vacations,
business trips). Trip sensors track time until trip start, trip progress,
and remaining trip duration.
"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

from ..const import (
    TRIP_SENSOR_TYPES,
)
from .base import BaseCountdownSensor

if TYPE_CHECKING:
    from ..coordinator import WhenHubCoordinator

_LOGGER = logging.getLogger(__name__)


class TripSensor(BaseCountdownSensor):
    """Sensor for multi-day trip events.

    Provides various calculations for trip events that have both start and end dates:
    - days_until: Days until trip starts
    - days_until_end: Days until trip ends
    - event_date: Start date of the trip (ISO format)
    - trip_left_days: Days remaining in an active trip
    - trip_left_percent: Percentage of trip remaining

    Data is provided by the WhenHubCoordinator for efficient updates.
    """

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
    ) -> None:
        """Initialize the trip sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary containing trip configuration (name, start_date, end_date, etc.)
            sensor_type: Type of sensor to create (from TRIP_SENSOR_TYPES)
        """
        super().__init__(coordinator, config_entry, event_data, sensor_type, TRIP_SENSOR_TYPES)

    @property
    def native_value(self) -> str | int | float | None:
        """Return the current sensor value from coordinator data.

        Returns:
            Sensor value appropriate for the sensor type (int for days, str for text, etc.)
        """
        data = self.coordinator.data
        if not data:
            return None

        if self._sensor_type == "days_until":
            return data.get("days_until")
        elif self._sensor_type == "days_until_end":
            return data.get("days_until_end")
        elif self._sensor_type == "event_date":
            return data.get("start_date")
        elif self._sensor_type == "trip_left_days":
            return data.get("trip_left_days")
        elif self._sensor_type == "trip_left_percent":
            return data.get("trip_left_percent")

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor.

        Only event_date sensors get attributes - other trip sensors return empty dict
        to keep the state clean and focused.

        Returns:
            Dictionary with event info and countdown breakdown (for event_date only)
        """
        if self._sensor_type == "event_date":
            data = self.coordinator.data
            attributes = self._get_base_attributes()
            attributes.update({
                "end_date": data.get("end_date"),
                "trip_duration_days": data.get("total_days"),
            })
            attributes.update(self._get_countdown_attributes())
            return attributes

        return {}