"""Base sensor classes for WhenHub integration.

This module provides the foundation classes for all WhenHub sensors, including
common functionality like device info creation, error handling, and countdown
text formatting that is shared across Trip, Milestone, and Anniversary sensors.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from ..const import (
    DOMAIN,
    EVENT_TYPES,
    EVENT_TYPE_TRIP,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
)
from ..calculations import (
    parse_date,
    format_countdown_text,
    countdown_breakdown,
    anniversary_for_year,
)

_LOGGER = logging.getLogger(__name__)


def get_device_info(config_entry: ConfigEntry, event_data: dict) -> DeviceInfo:
    """Create standardized device info for all WhenHub entities.

    This function ensures consistent device information across all platforms
    (sensors, binary sensors, images) for the same WhenHub event.

    Args:
        config_entry: The Home Assistant config entry for this integration instance
        event_data: Dictionary containing event configuration data

    Returns:
        DeviceInfo object with standardized identifiers, name, and metadata
    """
    event_type = event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_TRIP)
    event_info = EVENT_TYPES.get(event_type, EVENT_TYPES[EVENT_TYPE_TRIP])

    return DeviceInfo(
        identifiers={(DOMAIN, config_entry.entry_id)},
        name=event_data[CONF_EVENT_NAME],
        manufacturer="WhenHub",
        model=event_info["model"],
        sw_version="1.0.0",
    )


# Re-export parse_date for backward compatibility
__all__ = ["get_device_info", "parse_date", "BaseSensor", "BaseCountdownSensor"]


class BaseSensor(SensorEntity):
    """Base class for all WhenHub sensors.
    
    This abstract base class provides common functionality for Trip, Milestone,
    and Anniversary sensors. It handles entity initialization, device info,
    error handling, and attribute management.
    
    Child classes must implement their own native_value calculation logic.
    """

    def __init__(
        self, 
        config_entry: ConfigEntry, 
        event_data: dict, 
        sensor_type: str, 
        sensor_types: dict
    ) -> None:
        """Initialize the base sensor.
        
        Args:
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary with event configuration (name, dates, etc.)
            sensor_type: String identifying sensor type (e.g. 'days_until', 'countdown_text')
            sensor_types: Dictionary mapping sensor types to their metadata (name, icon, unit)
        """
        self._config_entry = config_entry
        self._event_data = event_data
        self._sensor_type = sensor_type
        self._sensor_types = sensor_types
        
        # Set entity attributes based on sensor type configuration
        self._attr_name = f"{event_data[CONF_EVENT_NAME]} {sensor_types[sensor_type]['name']}"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_icon = sensor_types[sensor_type]["icon"]
        self._attr_native_unit_of_measurement = sensor_types[sensor_type]["unit"]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity.
        
        Groups all entities from the same WhenHub event under one device.
        """
        return get_device_info(self._config_entry, self._event_data)

    def _safe_calculate(self, calculation_func: Callable, fallback: Any = None) -> Any:
        """Safely execute calculation with error handling and logging.
        
        Wraps sensor value calculations to prevent integration failures from
        calculation errors (e.g. invalid dates, arithmetic errors).
        
        Args:
            calculation_func: Function that performs the calculation
            fallback: Value to return if calculation fails (default: None)
            
        Returns:
            Result of calculation_func() or fallback value on error
        """
        try:
            return calculation_func()
        except Exception as err:
            _LOGGER.warning("Calculation error in %s sensor %s: %s", 
                           self._event_data[CONF_EVENT_NAME], self._sensor_type, err)
            return fallback

    def _get_base_attributes(self) -> dict[str, Any]:
        """Get common base attributes for countdown sensors.
        
        Returns:
            Dictionary with event_name and event_type attributes
        """
        return {
            "event_name": self._event_data[CONF_EVENT_NAME],
            "event_type": self._event_data.get(CONF_EVENT_TYPE),
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor.
        
        Base implementation returns empty dict. Child classes can override
        to provide sensor-specific attributes.
        
        Returns:
            Dictionary of attributes to expose in Home Assistant
        """
        return {}

    async def async_update(self) -> None:
        """Update the sensor value.
        
        Called by Home Assistant to refresh sensor state. Base implementation
        does nothing - child classes should implement if needed.
        """
        pass


class BaseCountdownSensor(BaseSensor):
    """Base class for sensors with countdown text functionality.

    Extends BaseSensor with countdown text formatting capabilities. This class
    delegates to functions in calculations.py for the actual computation.

    Used by Trip, Milestone, and Anniversary sensors that need countdown_text sensors.
    """

    def __init__(
        self,
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
        sensor_types: dict
    ) -> None:
        """Initialize the countdown sensor.

        Args:
            config_entry: Home Assistant config entry
            event_data: Event configuration data
            sensor_type: Type of sensor being created
            sensor_types: Sensor type definitions with metadata
        """
        super().__init__(config_entry, event_data, sensor_type, sensor_types)
        # Store breakdown of countdown for use in entity attributes
        self._countdown_breakdown = {"years": 0, "months": 0, "weeks": 0, "days": 0}

    def _format_countdown_text(self, target_date: date) -> str:
        """Format countdown from today to target date into human-readable German text.

        Delegates to calculations.format_countdown_text() and updates the
        internal breakdown for use in attributes.

        Args:
            target_date: The date to count down to

        Returns:
            German countdown string like "2 Jahre, 3 Monate, 1 Woche, 4 Tage"
        """
        today = date.today()
        # Update breakdown for attributes
        self._countdown_breakdown = countdown_breakdown(target_date, today)
        # Return formatted text
        return format_countdown_text(target_date, today)

    def _get_countdown_attributes(self) -> dict[str, int]:
        """Get countdown breakdown as individual attributes.

        Returns:
            Dictionary with text_years, text_months, text_weeks, text_days keys
        """
        return {
            "text_years": self._countdown_breakdown["years"],
            "text_months": self._countdown_breakdown["months"],
            "text_weeks": self._countdown_breakdown["weeks"],
            "text_days": self._countdown_breakdown["days"],
        }

    def _get_anniversary_for_year(self, original_date: date, target_year: int) -> date:
        """Get anniversary date for a specific year, handling leap year edge cases.

        Delegates to calculations.anniversary_for_year().

        Args:
            original_date: The original event date (e.g., birth date)
            target_year: Year to calculate anniversary for

        Returns:
            Anniversary date for the target year
        """
        return anniversary_for_year(original_date, target_year)