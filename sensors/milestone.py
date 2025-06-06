"""Milestone sensor for WhenHub integration.

This module implements sensors for one-time milestone events (e.g., birthdays,
project deadlines, important dates). Milestone sensors track countdown to a
single target date.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from homeassistant.config_entries import ConfigEntry

from ..const import (
    CONF_TARGET_DATE,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    EVENT_TYPE_MILESTONE,
    MILESTONE_SENSOR_TYPES,
    TEXT_ZERO_DAYS,
)
from .base import BaseCountdownSensor, parse_date

_LOGGER = logging.getLogger(__name__)


class MilestoneSensor(BaseCountdownSensor):
    """Sensor for one-time milestone events.
    
    Provides countdown calculations for single-date events that don't repeat:
    - days_until: Integer days until the milestone date
    - countdown_text: Human-readable countdown text with years/months/weeks/days breakdown
    
    Unlike Trip sensors (which have start/end dates) or Anniversary sensors (which repeat),
    Milestone sensors focus on a single target date that occurs once.
    
    Inherits countdown text formatting from BaseCountdownSensor.
    """

    def __init__(self, config_entry: ConfigEntry, event_data: dict, sensor_type: str) -> None:
        """Initialize the milestone sensor.
        
        Args:
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary containing milestone configuration (name, target_date, etc.)
            sensor_type: Type of sensor to create (from MILESTONE_SENSOR_TYPES)
        """
        super().__init__(config_entry, event_data, sensor_type, MILESTONE_SENSOR_TYPES)
        
        # Parse and store the milestone target date
        self._target_date = parse_date(event_data[CONF_TARGET_DATE])

    @property
    def native_value(self) -> str | int | float | None:
        """Return the current sensor value.
        
        Delegates to _calculate_value() with error handling to prevent
        integration failures from date calculation errors.
        
        Returns:
            Sensor value appropriate for the sensor type (int for days, str for countdown text)
        """
        return self._safe_calculate(self._calculate_value)

    def _calculate_value(self) -> str | int | float | None:
        """Calculate the current sensor value based on sensor type.
        
        Returns:
            - days_until: Integer days until milestone (can be negative if date has passed)
            - countdown_text: Formatted countdown string or "0 Tage" if date has passed
        """
        today = date.today()
        
        if self._sensor_type == "days_until":
            # Days until milestone date (negative if date has passed)
            return (self._target_date - today).days
            
        elif self._sensor_type == "countdown_text":
            # Human-readable countdown until milestone date
            if today < self._target_date:
                return self._format_countdown_text(self._target_date)
            else:
                # Milestone date has passed or is today
                return TEXT_ZERO_DAYS
                
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor.
        
        Only countdown_text sensors get attributes - other milestone sensors return empty dict
        to keep the state clean and focused.
        
        Returns:
            Dictionary with event info and countdown breakdown (for countdown_text only)
        """
        # Only countdown_text sensor gets detailed attributes
        if self._sensor_type == "countdown_text":
            attributes = self._get_base_attributes()
            attributes.update({
                "date": self._target_date.isoformat(),
            })
            
            # Add countdown breakdown (years, months, weeks, days)
            attributes.update(self._get_countdown_attributes())
            
            return attributes
        
        # All other milestone sensors have no attributes
        return {}