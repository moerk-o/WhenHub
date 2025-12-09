"""Special Event sensor for WhenHub integration.

This module implements sensors for special holidays and astronomical events
(e.g., Christmas, Easter, Solstices). Special event sensors calculate dates
for fixed holidays and compute dates for moveable feasts like Easter.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry

from ..const import (
    CONF_SPECIAL_TYPE,
    SPECIAL_SENSOR_TYPES,
    SPECIAL_EVENTS,
    TEXT_ZERO_DAYS,
)
from ..calculations import (
    days_until,
    next_special_event,
    last_special_event,
)
from .base import BaseCountdownSensor

_LOGGER = logging.getLogger(__name__)


class SpecialEventSensor(BaseCountdownSensor):
    """Sensor for special holidays and astronomical events.
    
    Provides countdown calculations for fixed and calculated special events:
    - days_until: Integer days until the next occurrence
    - countdown_text: Human-readable countdown text
    - next_date: ISO date string of next occurrence
    
    Handles complex date calculations for moveable feasts (Easter-based holidays)
    and astronomical events (solstices, equinoxes).
    """

    def __init__(self, config_entry: ConfigEntry, event_data: dict, sensor_type: str) -> None:
        """Initialize the special event sensor.
        
        Args:
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary containing special event configuration
            sensor_type: Type of sensor to create (from SPECIAL_SENSOR_TYPES)
        """
        super().__init__(config_entry, event_data, sensor_type, SPECIAL_SENSOR_TYPES)
        
        # Get the special event type
        self._special_type = event_data.get(CONF_SPECIAL_TYPE, "christmas_eve")
        self._special_info = SPECIAL_EVENTS.get(self._special_type, SPECIAL_EVENTS["christmas_eve"])
        
        # Use consistent star icon for all special events (matches other event types)

    @property
    def native_value(self) -> str | int | float | None:
        """Return the current sensor value.

        Delegates to _calculate_value() with error handling to prevent
        integration failures from date calculation errors.

        Returns:
            Sensor value appropriate for the sensor type
        """
        return self._safe_calculate(self._calculate_value)

    def _calculate_value(self) -> str | int | float | None:
        """Calculate the current sensor value based on sensor type.

        Returns:
            - days_until: Integer days until next occurrence
            - days_since_last: Integer days since last occurrence
            - countdown_text: Formatted countdown string
            - next_date: ISO date string of next occurrence
            - last_date: ISO date string of last occurrence
        """
        today = date.today()

        if self._sensor_type == "days_until":
            next_date = next_special_event(self._special_info, today)
            return days_until(next_date, today) if next_date else 0

        elif self._sensor_type == "days_since_last":
            last_date = last_special_event(self._special_info, today)
            return (today - last_date).days if last_date else None

        elif self._sensor_type == "countdown_text":
            next_date = next_special_event(self._special_info, today)
            if next_date:
                if days_until(next_date, today) == 0:
                    return TEXT_ZERO_DAYS
                else:
                    return self._format_countdown_text(next_date)
            return TEXT_ZERO_DAYS

        elif self._sensor_type == "next_date":
            next_date = next_special_event(self._special_info, today)
            return next_date.isoformat() if next_date else today.isoformat()

        elif self._sensor_type == "last_date":
            last_date = last_special_event(self._special_info, today)
            return last_date.isoformat() if last_date else None

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor."""
        # Only countdown_text sensor gets detailed attributes
        if self._sensor_type == "countdown_text":
            today = date.today()
            attributes = self._get_base_attributes()
            attributes.update({
                "special_type": self._special_type,
                "special_name": self._special_info.get("name", "Unknown"),
            })

            # Add next event date
            next_date = next_special_event(self._special_info, today)
            if next_date:
                attributes["next_date"] = next_date.isoformat()

            # Add countdown breakdown
            attributes.update(self._get_countdown_attributes())

            return attributes

        # All other special sensors have no attributes
        return {}