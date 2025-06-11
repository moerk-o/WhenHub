"""Anniversary sensor for WhenHub integration - INTERNATIONALIZED VERSION.

This module implements sensors for recurring anniversary events (e.g., wedding
anniversaries, company founding dates, annual celebrations). Anniversary sensors
track both upcoming and past occurrences of yearly repeating events with full translation support.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry

from ..const import (
    CONF_TARGET_DATE,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    EVENT_TYPE_ANNIVERSARY,
    ANNIVERSARY_SENSOR_TYPES,
    TEXT_ZERO_DAYS,
    TEXT_CALCULATION_RUNNING,
)
from .base import BaseCountdownSensor, parse_date

_LOGGER = logging.getLogger(__name__)


class AnniversarySensor(BaseCountdownSensor):
    """Sensor for recurring anniversary events - INTERNATIONALIZED VERSION.
    
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
    
    All entity names and states are now fully internationalized using translation_key.
    """

    def __init__(self, config_entry: ConfigEntry, event_data: dict, sensor_type: str) -> None:
        """Initialize the anniversary sensor with translation support.
        
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

    @property
    def translation_placeholders(self) -> dict[str, str]:
        """Return translation placeholders.
        
        CRITICAL: Must return dict, never None to avoid HomeAssistant errors!
        Can include dynamic values for use in translations.
        """
        next_anniversary = self._get_next_anniversary()
        return {
            "event_name": self._event_data[CONF_EVENT_NAME],
            "original_date": self._original_date.isoformat(),
            "next_anniversary": next_anniversary.isoformat(),
            "years_on_next": str(next_anniversary.year - self._original_date.year),
        }

    def _calculate_value(self) -> str | int | float | None:
        """Calculate the current sensor value based on sensor type.
        
        Returns:
            - days_until_next: Integer days until next anniversary
            - days_since_last: Integer days since last anniversary (or None if no past occurrence)
            - countdown_text: Formatted countdown string or translation key for zero
            - occurrences_count: Integer count of past + current occurrences
            - next_date: ISO date string of next anniversary
            - last_date: ISO date string of last anniversary (or None)
        """
        today = date.today()
        
        if self._sensor_type == "days_until_next":
            next_anniversary = self._get_next_anniversary()
            return (next_anniversary - today).days
        
        elif self._sensor_type == "days_since_last":
            last_anniversary = self._get_last_anniversary()
            return (today - last_anniversary).days if last_anniversary else None
            
        elif self._sensor_type == "countdown_text":
            next_anniversary = self._get_next_anniversary()
            days_until = (next_anniversary - today).days
            if days_until == 0:
                return TEXT_ZERO_DAYS  # Translation key instead of "0 Tage"
            else:
                return self._format_countdown_text(next_anniversary)
                
        elif self._sensor_type == "occurrences_count":
            return self._count_occurrences()
                
        elif self._sensor_type == "next_date":
            next_anniversary = self._get_next_anniversary()
            return next_anniversary.isoformat()
            
        elif self._sensor_type == "last_date":
            last_anniversary = self._get_last_anniversary()
            return last_anniversary.isoformat() if last_anniversary else None
        
        return None

    def _get_next_anniversary(self) -> date:
        """Calculate the next anniversary date from today.
        
        Determines when the next occurrence of this anniversary will happen,
        considering the current year and handling leap year edge cases.
        
        Returns:
            Date of the next anniversary occurrence
        """
        today = date.today()
        current_year = today.year
        
        # Try this year's anniversary first
        this_year_anniversary = self._get_anniversary_for_year(self._original_date, current_year)
        if this_year_anniversary >= today:
            return this_year_anniversary
        
        # If this year's anniversary has already passed, get next year's
        return self._get_anniversary_for_year(self._original_date, current_year + 1)

    def _get_last_anniversary(self) -> Optional[date]:
        """Calculate the most recent anniversary date before today.
        
        Determines when the last occurrence of this anniversary happened.
        Returns None if the original date is in the future (no past occurrences).
        
        Returns:
            Date of the last anniversary occurrence, or None if no past occurrence
        """
        today = date.today()
        current_year = today.year
        
        # If original date is in the future, there's no "last" anniversary yet
        if self._original_date > today:
            return None
        
        # Try this year's anniversary
        this_year_anniversary = self._get_anniversary_for_year(self._original_date, current_year)
        if this_year_anniversary <= today:
            return this_year_anniversary
        
        # If this year's anniversary hasn't happened yet, get last year's
        return self._get_anniversary_for_year(self._original_date, current_year - 1)

    def _count_occurrences(self) -> int:
        """Count total number of anniversary occurrences including today if applicable.
        
        Calculates how many times this anniversary has occurred from the original
        date up to and including today. Accounts for the original occurrence plus
        all subsequent yearly repetitions.
        
        Returns:
            Integer count of occurrences (minimum 1 if original date has passed, 0 if future)
        """
        today = date.today()
        
        # If original date is in the future, no occurrences yet
        if self._original_date > today:
            return 0
        
        # Calculate base occurrences (full years that have passed)
        years_passed = today.year - self._original_date.year
        
        # Check if this year's anniversary has already happened
        this_year_anniversary = self._get_anniversary_for_year(self._original_date, today.year)
        if this_year_anniversary > today:
            # This year's anniversary hasn't happened yet, so reduce count
            years_passed -= 1
        
        # Add 1 because we count the original occurrence
        return max(1, years_passed + 1)

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
            return TEXT_CALCULATION_RUNNING  # Translation key instead of "Berechnung läuft..."
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
            attributes = self._get_base_attributes()
            attributes.update({
                "initial_date": self._original_date.isoformat(),
            })
            
            # Add countdown breakdown (years, months, weeks, days)
            attributes.update(self._get_countdown_attributes())
            
            # Add next anniversary metadata for automation use
            next_anniversary = self._get_next_anniversary()
            attributes.update({
                "next_anniversary": next_anniversary.isoformat(),
                "years_on_next": next_anniversary.year - self._original_date.year,
            })
            
            return attributes
        
        # All other anniversary sensors have no attributes
        return {}