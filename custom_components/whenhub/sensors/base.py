"""Base sensor classes for WhenHub integration.

This module provides the foundation classes for all WhenHub sensors, including
common functionality like device info creation, error handling, and countdown
text formatting that is shared across Trip, Milestone, and Anniversary sensors.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Callable, Optional

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


def parse_date(date_str: str | date) -> date:
    """Parse date string in ISO format or return existing date object.
    
    Args:
        date_str: Either an ISO date string (YYYY-MM-DD) or a date object
        
    Returns:
        A date object
        
    Raises:
        ValueError: If date_str is a malformed string
    """
    if isinstance(date_str, str):
        return date.fromisoformat(date_str)
    return date_str


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
    handles the complex logic of converting date differences into human-readable
    countdown strings like "2 Jahre, 3 Monate, 1 Woche, 4 Tage".
    
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

        Converts the time difference into a breakdown of years, months, weeks, and days
        using approximations (365 days/year, 30 days/month) for simplicity and reliability.
        Zero values are omitted from the output.

        Note: German output is intentional - see prompt.md for rationale (sensor state
        values cannot be translated by Home Assistant's translation system).

        Args:
            target_date: The date to count down to

        Returns:
            German countdown string like "2 Jahre, 3 Monate, 1 Woche, 4 Tage"
            or "0 Tage" if target date has passed
        """
        today = date.today()

        # If target date has passed or is today, return zero
        if target_date <= today:
            self._countdown_breakdown = {"years": 0, "months": 0, "weeks": 0, "days": 0}
            return "0 Tage"

        delta = target_date - today
        total_days = delta.days

        # Use simple approximations for consistent behavior across edge cases
        # 365 days per year, 30 days per month, 7 days per week
        years = total_days // 365
        remaining_days = total_days - (years * 365)

        months = remaining_days // 30
        remaining_days = remaining_days - (months * 30)

        weeks = remaining_days // 7
        days = remaining_days % 7

        # Store breakdown for use in entity attributes
        self._countdown_breakdown = {
            "years": years,
            "months": months,
            "weeks": weeks,
            "days": days
        }

        # Build human-readable German string, omitting zero values
        parts = []
        if years > 0:
            parts.append(f"{years} Jahr{'e' if years > 1 else ''}")
        if months > 0:
            parts.append(f"{months} Monat{'e' if months > 1 else ''}")
        if weeks > 0:
            parts.append(f"{weeks} Woche{'n' if weeks > 1 else ''}")
        if days > 0:
            parts.append(f"{days} Tag{'e' if days > 1 else ''}")

        return ", ".join(parts) if parts else "0 Tage"

    def _get_countdown_attributes(self) -> dict[str, int]:
        """Get countdown breakdown as individual attributes.
        
        Provides the numerical breakdown of the countdown for use in automations
        and templates. These attributes are populated by _format_countdown_text().
        
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
        
        Calculates what date an anniversary falls on in a given year, with special
        handling for February 29th birthdays in non-leap years (converts to Feb 28).
        
        Args:
            original_date: The original event date (e.g., birth date)
            target_year: Year to calculate anniversary for
            
        Returns:
            Anniversary date for the target year
            
        Example:
            original_date = 2020-02-29 (leap year)
            target_year = 2021 (non-leap year)
            returns = 2021-02-28
        """
        try:
            return original_date.replace(year=target_year)
        except ValueError:
            # Handle Feb 29 in non-leap year by using Feb 28
            return date(target_year, 2, 28)