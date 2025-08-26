"""Trip sensor for WhenHub integration.

This module implements sensors for multi-day trip events (e.g., vacations, 
business trips). Trip sensors track time until trip start, trip progress,
and remaining trip duration.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from homeassistant.config_entries import ConfigEntry

from ..const import (
    CONF_START_DATE,
    CONF_END_DATE,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    EVENT_TYPE_TRIP,
    TRIP_SENSOR_TYPES,
    TEXT_ZERO_DAYS,
)
from .base import BaseCountdownSensor, parse_date

_LOGGER = logging.getLogger(__name__)


class TripSensor(BaseCountdownSensor):
    """Sensor for multi-day trip events.
    
    Provides various calculations for trip events that have both start and end dates:
    - days_until: Days until trip starts
    - days_until_end: Days until trip ends
    - countdown_text: Human-readable countdown to trip start
    - trip_left_days: Days remaining in an active trip
    - trip_left_percent: Percentage of trip remaining
    
    Inherits countdown text formatting from BaseCountdownSensor.
    """

    def __init__(self, config_entry: ConfigEntry, event_data: dict, sensor_type: str) -> None:
        """Initialize the trip sensor.
        
        Args:
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary containing trip configuration (name, start_date, end_date, etc.)
            sensor_type: Type of sensor to create (from TRIP_SENSOR_TYPES)
        """
        super().__init__(config_entry, event_data, sensor_type, TRIP_SENSOR_TYPES)
        
        # Parse and store trip dates for calculations
        self._start_date = parse_date(event_data[CONF_START_DATE])
        self._end_date = parse_date(event_data[CONF_END_DATE])

    @property
    def native_value(self) -> str | int | float | None:
        """Return the current sensor value.
        
        Delegates to _calculate_value() with error handling to prevent
        integration failures from date calculation errors.
        
        Returns:
            Sensor value appropriate for the sensor type (int for days, str for text, etc.)
        """
        return self._safe_calculate(self._calculate_value)

    def _calculate_value(self) -> str | int | float | None:
        """Calculate the current sensor value based on sensor type.
        
        Returns:
            - days_until: Integer days until trip start (can be negative if started)
            - days_until_end: Integer days until trip end (can be negative if ended)
            - countdown_text: Formatted countdown string or "0 Tage" if trip started
            - trip_left_days: Days remaining in active trip (0 if not active)
            - trip_left_percent: Percentage of trip remaining (0-100)
        """
        today = date.today()
        
        if self._sensor_type == "days_until":
            # Days until trip starts (negative if already started)
            return (self._start_date - today).days
            
        elif self._sensor_type == "days_until_end":
            # Days until trip ends (negative if already ended)
            return (self._end_date - today).days
            
        elif self._sensor_type == "countdown_text":
            # Human-readable countdown until trip starts
            if today <= self._start_date:
                return self._format_countdown_text(self._start_date)
            else:
                return TEXT_ZERO_DAYS
                
        elif self._sensor_type == "trip_left_days":
            # Days remaining in an active trip (inclusive of today)
            if today <= self._end_date and today >= self._start_date:
                return (self._end_date - today).days + 1
            return 0
            
        elif self._sensor_type == "trip_left_percent":
            # Percentage of trip remaining
            total_days = (self._end_date - self._start_date).days
            if today < self._start_date:
                return 100.0  # Trip hasn't started yet
            elif today > self._end_date:
                return 0.0    # Trip has ended
            else:
                # Calculate how much of the trip has passed
                passed_days = (today - self._start_date).days
                remaining_percent = 100.0 - ((passed_days / total_days) * 100.0)
                return round(remaining_percent, 1)
                
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor.
        
        Only countdown_text sensors get attributes - other trip sensors return empty dict
        to keep the state clean and focused.
        
        Returns:
            Dictionary with event info and countdown breakdown (for countdown_text only)
        """
        # Only countdown_text sensor gets detailed attributes
        if self._sensor_type == "countdown_text":
            attributes = self._get_base_attributes()
            attributes.update({
                "start_date": self._start_date.isoformat(),
                "end_date": self._end_date.isoformat(),
                "total_days": (self._end_date - self._start_date).days + 1,
            })
            
            # Add countdown breakdown (years, months, weeks, days)
            attributes.update(self._get_countdown_attributes())
            
            return attributes
        
        # All other trip sensors have no attributes
        return {}