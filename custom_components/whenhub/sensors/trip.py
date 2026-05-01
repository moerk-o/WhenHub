"""Trip sensor for WhenHub integration.

This module implements sensors for multi-day trip events (e.g., vacations,
business trips). Trip sensors track time until trip start, trip progress,
and remaining trip duration.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

from ..const import (
    TRIP_SENSOR_TYPES,
    CONF_START_DATE_USE_ENTITY,
    CONF_START_DATE_ENTITY_ID,
    CONF_END_DATE_USE_ENTITY,
    CONF_END_DATE_ENTITY_ID,
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
    def icon(self) -> str | None:
        """Return calendar-sync icon when any date comes from an entity."""
        if self._sensor_type == "event_date" and (
            self._event_data.get(CONF_START_DATE_USE_ENTITY)
            or self._event_data.get(CONF_END_DATE_USE_ENTITY)
        ):
            return "mdi:calendar-sync"
        return self.entity_description.icon

    @property
    def native_value(self) -> datetime | int | float | None:
        """Return the current sensor value from coordinator data.

        Returns:
            Sensor value appropriate for the sensor type (datetime, int for days, float for percent)
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
            end_datetime = data.get("end_date")
            attributes = self._get_base_attributes()
            attributes.update({
                "end_date": end_datetime.date().isoformat() if end_datetime else None,
                "trip_duration_days": data.get("total_days"),
            })
            attributes.update(self._get_countdown_attributes())
            if self._event_data.get(CONF_START_DATE_USE_ENTITY):
                attributes["start_date_source_entity"] = self._event_data.get(CONF_START_DATE_ENTITY_ID)
            if self._event_data.get(CONF_END_DATE_USE_ENTITY):
                attributes["end_date_source_entity"] = self._event_data.get(CONF_END_DATE_ENTITY_ID)
            return attributes

        return {}