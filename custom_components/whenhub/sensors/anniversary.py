"""Anniversary sensor for WhenHub integration.

This module implements sensors for recurring anniversary events (e.g., wedding
anniversaries, company founding dates, annual celebrations). Anniversary sensors
track both upcoming and past occurrences of yearly repeating events.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry

from ..const import (
    CONF_TARGET_DATE,
    CONF_EVENT_NAME,
    ANNIVERSARY_SENSOR_TYPES,
    TEXT_ZERO_DAYS,
    TEXT_CALCULATION_RUNNING,
)
from ..calculations import (
    parse_date,
    days_until,
    next_anniversary,
    last_anniversary,
    anniversary_count,
)
from .base import BaseCountdownSensor

_LOGGER = logging.getLogger(__name__)


class AnniversarySensor(BaseCountdownSensor):
    """Sensor for recurring anniversary events.
    
    Provides comprehensive tracking for events that repeat annually:
    - days_until_next: Days until the next anniversary occurrence
    - days_since_last: Days since the last anniversary occurrence  
    - countdown_text: Human-readable countdown to next anniversary
    - occurrences_count: Total number of times the anniversary has occurred
    - next_date: ISO date of the next anniversary
    - last_date: ISO date of the last anniversary (if any)
    
    Handles complex logic like leap year birthdays (Feb 29 -> Feb 28 in non-leap years)
    and distinguishes between future events (no past occurrences) and established
    anniversaries with historical data.
    
    Inherits countdown text formatting from BaseCountdownSensor.
    """

    def __init__(self, config_entry: ConfigEntry, event_data: dict, sensor_type: str) -> None:
        """Initialize the anniversary sensor.
        
        Args:
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary containing anniversary configuration (name, target_date, etc.)
            sensor_type: Type of sensor to create (from ANNIVERSARY_SENSOR_TYPES)
        """
        super().__init__(config_entry, event_data, sensor_type, ANNIVERSARY_SENSOR_TYPES)
        
        # Parse and validate the original anniversary date
        target_date = event_data.get(CONF_TARGET_DATE)
        if not target_date:
            _LOGGER.error("No target_date found for anniversary sensor: %s", event_data.get(CONF_EVENT_NAME))
            target_date = date.today().isoformat()
        
        self._original_date = parse_date(target_date)

    @property
    def available(self) -> bool:
        """Return if entity is available.
        
        Anniversary sensors are only available if they have a valid original date.
        
        Returns:
            True if the sensor has valid date data and can perform calculations
        """
        return self._original_date is not None

    @property
    def native_value(self) -> str | int | float | None:
        """Return the current sensor value.
        
        Delegates to _calculate_value() with error handling and sensor-specific
        fallback values to prevent integration failures.
        
        Returns:
            Sensor value appropriate for the sensor type with fallbacks on error
        """
        return self._safe_calculate(self._calculate_value, self._get_fallback_value())

    def _calculate_value(self) -> str | int | float | None:
        """Calculate the current sensor value based on sensor type.

        Returns:
            - days_until_next: Integer days until next anniversary
            - days_since_last: Integer days since last anniversary (or None if no past occurrence)
            - countdown_text: Formatted countdown string or "0 Tage" if anniversary is today
            - occurrences_count: Integer count of past + current occurrences
            - next_date: ISO date string of next anniversary
            - last_date: ISO date string of last anniversary (or None)
        """
        today = date.today()

        if self._sensor_type == "days_until_next":
            next_ann = next_anniversary(self._original_date, today)
            return days_until(next_ann, today)

        elif self._sensor_type == "days_since_last":
            last_ann = last_anniversary(self._original_date, today)
            return (today - last_ann).days if last_ann else None

        elif self._sensor_type == "countdown_text":
            next_ann = next_anniversary(self._original_date, today)
            if days_until(next_ann, today) == 0:
                return TEXT_ZERO_DAYS
            else:
                return self._format_countdown_text(next_ann)

        elif self._sensor_type == "occurrences_count":
            return anniversary_count(self._original_date, today)

        elif self._sensor_type == "next_date":
            next_ann = next_anniversary(self._original_date, today)
            return next_ann.isoformat()

        elif self._sensor_type == "last_date":
            last_ann = last_anniversary(self._original_date, today)
            return last_ann.isoformat() if last_ann else None

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
        elif self._sensor_type == "countdown_text":
            return TEXT_CALCULATION_RUNNING
        elif self._sensor_type in ["next_date", "last_date"]:
            return date.today().isoformat()
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor.

        Only countdown_text sensors get attributes - other anniversary sensors return empty dict
        to keep the state clean and focused.

        Returns:
            Dictionary with event info and countdown breakdown (for countdown_text only)
        """
        # Only countdown_text sensor gets detailed attributes
        if self._sensor_type == "countdown_text":
            today = date.today()
            attributes = self._get_base_attributes()
            attributes.update({
                "initial_date": self._original_date.isoformat(),
            })

            # Add countdown breakdown (years, months, weeks, days)
            attributes.update(self._get_countdown_attributes())

            # Add next anniversary metadata for automation use
            next_ann = next_anniversary(self._original_date, today)
            attributes.update({
                "next_anniversary": next_ann.isoformat(),
                "years_on_next": next_ann.year - self._original_date.year,
            })

            return attributes

        # All other anniversary sensors have no attributes
        return {}