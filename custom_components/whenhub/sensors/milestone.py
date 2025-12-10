"""Milestone sensor for WhenHub integration.

This module implements sensors for one-time milestone events (e.g., birthdays,
project deadlines, important dates). Milestone sensors track countdown to a
single target date.
"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

from ..const import (
    MILESTONE_SENSOR_TYPES,
)
from .base import BaseCountdownSensor

if TYPE_CHECKING:
    from ..coordinator import WhenHubCoordinator

_LOGGER = logging.getLogger(__name__)


class MilestoneSensor(BaseCountdownSensor):
    """Sensor for one-time milestone events.

    Provides countdown calculations for single-date events that don't repeat:
    - days_until: Integer days until the milestone date
    - event_date: Target date of the milestone (ISO format)

    Unlike Trip sensors (which have start/end dates) or Anniversary sensors (which repeat),
    Milestone sensors focus on a single target date that occurs once.

    Data is provided by the WhenHubCoordinator for efficient updates.
    """

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
    ) -> None:
        """Initialize the milestone sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary containing milestone configuration (name, target_date, etc.)
            sensor_type: Type of sensor to create (from MILESTONE_SENSOR_TYPES)
        """
        super().__init__(coordinator, config_entry, event_data, sensor_type, MILESTONE_SENSOR_TYPES)

    @property
    def native_value(self) -> str | int | float | None:
        """Return the current sensor value from coordinator data.

        Returns:
            Sensor value appropriate for the sensor type (int for days, str for countdown text)
        """
        data = self.coordinator.data
        if not data:
            return None

        if self._sensor_type == "days_until":
            return data.get("days_until")
        elif self._sensor_type == "event_date":
            return data.get("target_date")

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor.

        Only event_date sensors get attributes - other milestone sensors return empty dict
        to keep the state clean and focused.

        Returns:
            Dictionary with event info and countdown breakdown (for event_date only)
        """
        if self._sensor_type == "event_date":
            data = self.coordinator.data
            attributes = self._get_base_attributes()
            attributes.update(self._get_countdown_attributes())
            return attributes

        return {}
