"""Binary sensor platform for WhenHub integration - INTERNATIONALIZED VERSION.

This module implements binary sensors that provide boolean (on/off) status
for various event conditions like "trip starts today", "milestone is today",
or "anniversary is today". These are useful for automations and notifications.
All entity names and states are now fully internationalized.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    EVENT_TYPES,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    CONF_START_DATE,
    CONF_END_DATE,
    CONF_TARGET_DATE,
    CONF_IMAGE_PATH,
    CONF_WEBSITE_URL,
    CONF_NOTES,
    TRIP_BINARY_SENSOR_TYPES,
    MILESTONE_BINARY_SENSOR_TYPES,
    ANNIVERSARY_BINARY_SENSOR_TYPES,
    DEFAULT_IMAGE,
)
from .sensors.base import get_device_info, parse_date

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WhenHub binary sensors based on a config entry.
    
    Creates binary sensors based on the event type. Each event type has different
    binary sensor types optimized for that use case.
    
    Args:
        hass: Home Assistant instance
        config_entry: Config entry for this WhenHub integration instance
        async_add_entities: Callback to add entities to Home Assistant
    """
    event_data = hass.data[DOMAIN][config_entry.entry_id]
    event_type = event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_TRIP)
    
    binary_sensors = []
    
    try:
        # Create binary sensors based on event type
        if event_type == EVENT_TYPE_TRIP:
            for sensor_type in TRIP_BINARY_SENSOR_TYPES:
                binary_sensors.append(TripBinarySensor(config_entry, event_data, sensor_type))
        
        elif event_type == EVENT_TYPE_MILESTONE:
            for sensor_type in MILESTONE_BINARY_SENSOR_TYPES:
                binary_sensors.append(MilestoneBinarySensor(config_entry, event_data, sensor_type))
        
        elif event_type == EVENT_TYPE_ANNIVERSARY:
            for sensor_type in ANNIVERSARY_BINARY_SENSOR_TYPES:
                binary_sensors.append(AnniversaryBinarySensor(config_entry, event_data, sensor_type))
        
        if binary_sensors:
            _LOGGER.info("Created %d binary sensors for %s", len(binary_sensors), event_data[CONF_EVENT_NAME])
            async_add_entities(binary_sensors)
    except Exception as err:
        _LOGGER.error("Error setting up binary sensors for %s: %s", event_data.get(CONF_EVENT_NAME), err)
        async_add_entities([])


class BaseBinarySensor(BinarySensorEntity):
    """Base class for all WhenHub binary sensors - INTERNATIONALIZED VERSION.
    
    Provides common functionality for Trip, Milestone, and Anniversary binary sensors
    including device info, error handling, and entity setup with full translation support.
    Child classes implement the specific boolean logic for their sensor types.
    """

    def __init__(self, config_entry: ConfigEntry, event_data: dict, sensor_type: str, sensor_types: dict) -> None:
        """Initialize the binary sensor with translation support.
        
        Args:
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary with event configuration data
            sensor_type: String identifying binary sensor type (e.g. 'trip_starts_today')
            sensor_types: Dictionary mapping sensor types to their metadata
        """
        self._config_entry = config_entry
        self._event_data = event_data
        self._sensor_type = sensor_type
        self._sensor_types = sensor_types
        
        # MIGRATION: Use translation_key instead of hard-coded names
        self._attr_translation_key = sensor_types[sensor_type]["translation_key"]
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{config_entry.entry_id}_binary_{sensor_type}"
        self._attr_icon = sensor_types[sensor_type]["icon"]
        
        # Set Home Assistant device class if specified (e.g., 'occurrence')
        device_class = sensor_types[sensor_type].get("device_class")
        if device_class:
            self._attr_device_class = getattr(BinarySensorDeviceClass, device_class.upper(), None)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity.
        
        Groups all binary sensors from the same WhenHub event under one device.
        """
        return get_device_info(self._config_entry, self._event_data)

    @property
    def translation_placeholders(self) -> dict[str, str]:
        """Return translation placeholders.
        
        CRITICAL: Must return dict, never None to avoid HomeAssistant errors!
        Can include dynamic values for use in translations.
        """
        return {
            "event_name": self._event_data[CONF_EVENT_NAME],
        }

    def _safe_calculate(self, calculation_func, fallback=False):
        """Safely execute boolean calculation with error handling.
        
        Prevents integration failures from calculation errors in binary sensor logic.
        
        Args:
            calculation_func: Function that returns a boolean value
            fallback: Boolean value to return on error (default: False)
            
        Returns:
            Result of calculation_func() or fallback value on error
        """
        try:
            return calculation_func()
        except Exception as err:
            _LOGGER.warning("Binary sensor calculation error in %s: %s", self._sensor_type, err)
            return fallback

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor condition is met.
        
        Delegates to _calculate_value() with error handling.
        """
        return self._safe_calculate(self._calculate_value)

    def _calculate_value(self) -> bool:
        """Calculate the current boolean value.
        
        Abstract method to be implemented by child classes with their specific logic.
        
        Returns:
            Boolean indicating if the sensor condition is currently true
        """
        return False

    async def async_update(self) -> None:
        """Update the binary sensor value.
        
        Called by Home Assistant to refresh the sensor state. Updates the
        internal state attribute with the current calculated value.
        """
        self._attr_is_on = self._calculate_value()


class TripBinarySensor(BaseBinarySensor):
    """Binary sensor for multi-day trip events - INTERNATIONALIZED VERSION.
    
    Provides boolean sensors for trip-related conditions:
    - trip_starts_today: True if today is the trip start date
    - trip_active_today: True if today falls within the trip duration
    - trip_ends_today: True if today is the trip end date
    
    Useful for automations like "turn on vacation mode when trip starts".
    All entity names are now internationalized using translation_key.
    """

    def __init__(self, config_entry: ConfigEntry, event_data: dict, sensor_type: str) -> None:
        """Initialize the trip binary sensor with translation support.
        
        Args:
            config_entry: Home Assistant config entry
            event_data: Trip configuration with start_date and end_date
            sensor_type: Type of trip binary sensor to create
        """
        super().__init__(config_entry, event_data, sensor_type, TRIP_BINARY_SENSOR_TYPES)
        
        # Parse trip date range for calculations
        self._start_date = parse_date(event_data[CONF_START_DATE])
        self._end_date = parse_date(event_data[CONF_END_DATE])

    @property
    def translation_placeholders(self) -> dict[str, str]:
        """Return translation placeholders.
        
        CRITICAL: Must return dict, never None to avoid HomeAssistant errors!
        """
        return {
            "event_name": self._event_data[CONF_EVENT_NAME],
            "start_date": self._start_date.isoformat(),
            "end_date": self._end_date.isoformat(),
        }

    def _calculate_value(self) -> bool:
        """Calculate the current boolean value for this trip condition.
        
        Returns:
            Boolean indicating if the trip condition is currently true
        """
        today = date.today()
        
        if self._sensor_type == "trip_starts_today":
            # Trip starts today
            return today == self._start_date
        elif self._sensor_type == "trip_active_today":
            # Trip is currently active (today is between start and end dates, inclusive)
            return self._start_date <= today <= self._end_date
        elif self._sensor_type == "trip_ends_today":
            # Trip ends today
            return today == self._end_date
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor.
        
        Trip binary sensors don't provide additional attributes to keep them lightweight.
        """
        return {}


class MilestoneBinarySensor(BaseBinarySensor):
    """Binary sensor for one-time milestone events - INTERNATIONALIZED VERSION.
    
    Provides boolean sensors for milestone conditions:
    - is_today: True if today is the milestone date
    
    Useful for automations like "send birthday notification" or "reminder for deadline".
    All entity names are now internationalized using translation_key.
    """

    def __init__(self, config_entry: ConfigEntry, event_data: dict, sensor_type: str) -> None:
        """Initialize the milestone binary sensor with translation support.
        
        Args:
            config_entry: Home Assistant config entry
            event_data: Milestone configuration with target_date
            sensor_type: Type of milestone binary sensor to create
        """
        super().__init__(config_entry, event_data, sensor_type, MILESTONE_BINARY_SENSOR_TYPES)
        
        # Parse and validate milestone target date
        target_date = event_data.get(CONF_TARGET_DATE)
        if not target_date:
            _LOGGER.error("No target_date found for milestone binary sensor: %s", event_data.get(CONF_EVENT_NAME))
            target_date = date.today().isoformat()
        
        self._target_date = parse_date(target_date)

    @property
    def translation_placeholders(self) -> dict[str, str]:
        """Return translation placeholders.
        
        CRITICAL: Must return dict, never None to avoid HomeAssistant errors!
        """
        return {
            "event_name": self._event_data[CONF_EVENT_NAME],
            "target_date": self._target_date.isoformat(),
        }

    def _calculate_value(self) -> bool:
        """Calculate the current boolean value for this milestone condition.
        
        Returns:
            Boolean indicating if the milestone condition is currently true
        """
        if self._sensor_type == "is_today":
            # Milestone date is today
            return date.today() == self._target_date
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor.
        
        Milestone binary sensors include event metadata for automation use.
        
        Returns:
            Dictionary with event details and optional user-provided metadata
        """
        attributes = {
            "event_name": self._event_data[CONF_EVENT_NAME],
            "event_type": self._event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_MILESTONE),
            "target_date": self._target_date.isoformat(),
        }
        
        # Add optional user-provided attributes
        if self._event_data.get(CONF_IMAGE_PATH):
            attributes["image_path"] = self._event_data[CONF_IMAGE_PATH]
        else:
            attributes["image_path"] = DEFAULT_IMAGE
            
        if self._event_data.get(CONF_WEBSITE_URL):
            attributes["website_url"] = self._event_data[CONF_WEBSITE_URL]
            
        if self._event_data.get(CONF_NOTES):
            attributes["notes"] = self._event_data[CONF_NOTES]
        
        return attributes


class AnniversaryBinarySensor(BaseBinarySensor):
    """Binary sensor for recurring anniversary events - INTERNATIONALIZED VERSION.
    
    Provides boolean sensors for anniversary conditions:
    - is_today: True if today is an anniversary occurrence
    
    Handles leap year edge cases (Feb 29 -> Feb 28) and calculates the correct
    anniversary date for the current year.
    
    Useful for automations like "anniversary reminders" or "annual celebrations".
    All entity names are now internationalized using translation_key.
    """

    def __init__(self, config_entry: ConfigEntry, event_data: dict, sensor_type: str) -> None:
        """Initialize the anniversary binary sensor with translation support.
        
        Args:
            config_entry: Home Assistant config entry
            event_data: Anniversary configuration with target_date (original date)
            sensor_type: Type of anniversary binary sensor to create
        """
        super().__init__(config_entry, event_data, sensor_type, ANNIVERSARY_BINARY_SENSOR_TYPES)
        
        # Parse and validate original anniversary date
        target_date = event_data.get(CONF_TARGET_DATE)
        if not target_date:
            _LOGGER.error("No target_date found for anniversary binary sensor: %s", event_data.get(CONF_EVENT_NAME))
            target_date = date.today().isoformat()
        
        self._original_date = parse_date(target_date)

    @property
    def translation_placeholders(self) -> dict[str, str]:
        """Return translation placeholders.
        
        CRITICAL: Must return dict, never None to avoid HomeAssistant errors!
        """
        return {
            "event_name": self._event_data[CONF_EVENT_NAME],
            "original_date": self._original_date.isoformat(),
        }

    def _get_next_anniversary(self) -> date:
        """Calculate the next anniversary date from today.
        
        Determines when the next occurrence of this anniversary will happen,
        handling leap year edge cases for February 29th dates.
        
        Returns:
            Date of the next anniversary occurrence
        """
        today = date.today()
        current_year = today.year
        
        # Try this year's anniversary first
        try:
            this_year_anniversary = self._original_date.replace(year=current_year)
            if this_year_anniversary >= today:
                return this_year_anniversary
        except ValueError:
            # Handle leap year edge case (Feb 29 -> Feb 28 in non-leap years)
            this_year_anniversary = date(current_year, 2, 28)
            if this_year_anniversary >= today:
                return this_year_anniversary
        
        # If this year's anniversary has passed, get next year's
        try:
            next_year_anniversary = self._original_date.replace(year=current_year + 1)
            return next_year_anniversary
        except ValueError:
            # Handle leap year edge case for next year
            return date(current_year + 1, 2, 28)

    def _calculate_value(self) -> bool:
        """Calculate the current boolean value for this anniversary condition.
        
        Returns:
            Boolean indicating if today is an anniversary occurrence
        """
        if self._sensor_type == "is_today":
            # Anniversary is today
            today = date.today()
            next_anniversary = self._get_next_anniversary()
            return today == next_anniversary
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor.
        
        Anniversary binary sensors include comprehensive metadata including
        anniversary progression information for automation use.
        
        Returns:
            Dictionary with event details, anniversary dates, and optional user metadata
        """
        attributes = {
            "event_name": self._event_data[CONF_EVENT_NAME],
            "event_type": self._event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_ANNIVERSARY),
            "original_date": self._original_date.isoformat(),
        }
        
        # Add optional user-provided attributes
        if self._event_data.get(CONF_IMAGE_PATH):
            attributes["image_path"] = self._event_data[CONF_IMAGE_PATH]
        else:
            attributes["image_path"] = DEFAULT_IMAGE
            
        if self._event_data.get(CONF_WEBSITE_URL):
            attributes["website_url"] = self._event_data[CONF_WEBSITE_URL]
            
        if self._event_data.get(CONF_NOTES):
            attributes["notes"] = self._event_data[CONF_NOTES]
        
        # Add anniversary progression metadata
        next_anniversary = self._get_next_anniversary()
        attributes.update({
            "next_anniversary": next_anniversary.isoformat(),
            "years_on_next": next_anniversary.year - self._original_date.year,
        })
        
        return attributes