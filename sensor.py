"""Sensor platform for WhenHub integration.

This module sets up the sensor platform that creates different types of
sensors based on the event type (Trip, Milestone, Anniversary). It handles
the platform initialization and delegates sensor creation to the appropriate
sensor classes.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    TRIP_SENSOR_TYPES,
    MILESTONE_SENSOR_TYPES,
    ANNIVERSARY_SENSOR_TYPES,
)
from .sensors import TripSensor, MilestoneSensor, AnniversarySensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WhenHub sensors based on a config entry.
    
    Creates sensor entities based on the event type configuration. Each event type
    (Trip, Milestone, Anniversary) has its own set of relevant sensor types that
    provide different calculations and information.
    
    Args:
        hass: Home Assistant instance
        config_entry: Config entry for this WhenHub integration instance
        async_add_entities: Callback to add entities to Home Assistant
    """
    event_data = hass.data[DOMAIN][config_entry.entry_id]
    event_type = event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_TRIP)
    
    sensors = []
    
    try:
        # Create sensors based on event type
        if event_type == EVENT_TYPE_TRIP:
            sensors.extend(_create_trip_sensors(config_entry, event_data))
                
        elif event_type == EVENT_TYPE_MILESTONE:
            sensors.extend(_create_milestone_sensors(config_entry, event_data))
                
        elif event_type == EVENT_TYPE_ANNIVERSARY:
            sensors.extend(_create_anniversary_sensors(config_entry, event_data))
            
        else:
            # Fallback for unknown event types - use trip sensors as default
            _LOGGER.warning("Unknown event_type: %s, falling back to TRIP", event_type)
            sensors.extend(_create_trip_sensors(config_entry, event_data))
    
        _LOGGER.info("Created %d sensors for %s (%s)", 
                    len(sensors), event_data[CONF_EVENT_NAME], event_type)
        async_add_entities(sensors, update_before_add=True)
        
    except Exception as err:
        _LOGGER.error("Error setting up sensors for %s: %s", 
                     event_data.get(CONF_EVENT_NAME, "unknown"), err)
        # Add empty list to prevent platform setup failure
        async_add_entities([])


def _create_trip_sensors(config_entry: ConfigEntry, event_data: dict) -> list[TripSensor]:
    """Create sensor entities for Trip events.
    
    Trip events have start and end dates and provide sensors for:
    - Days until trip starts
    - Days until trip ends
    - Countdown text to trip start
    - Days remaining in active trip
    - Percentage of trip remaining
    
    Args:
        config_entry: Home Assistant config entry
        event_data: Trip event configuration data
        
    Returns:
        List of TripSensor instances
    """
    sensors = []
    for sensor_type in TRIP_SENSOR_TYPES:
        sensors.append(TripSensor(config_entry, event_data, sensor_type))
    return sensors


def _create_milestone_sensors(config_entry: ConfigEntry, event_data: dict) -> list[MilestoneSensor]:
    """Create sensor entities for Milestone events.
    
    Milestone events have a single target date and provide sensors for:
    - Days until milestone date
    - Countdown text to milestone
    
    Args:
        config_entry: Home Assistant config entry
        event_data: Milestone event configuration data
        
    Returns:
        List of MilestoneSensor instances
    """
    sensors = []
    for sensor_type in MILESTONE_SENSOR_TYPES:
        sensors.append(MilestoneSensor(config_entry, event_data, sensor_type))
    return sensors


def _create_anniversary_sensors(config_entry: ConfigEntry, event_data: dict) -> list[AnniversarySensor]:
    """Create sensor entities for Anniversary events.
    
    Anniversary events repeat annually and provide sensors for:
    - Days until next anniversary
    - Days since last anniversary
    - Countdown text to next anniversary
    - Count of total occurrences
    - Next anniversary date
    - Last anniversary date
    
    Args:
        config_entry: Home Assistant config entry
        event_data: Anniversary event configuration data
        
    Returns:
        List of AnniversarySensor instances
    """
    sensors = []
    for sensor_type in ANNIVERSARY_SENSOR_TYPES:
        sensors.append(AnniversarySensor(config_entry, event_data, sensor_type))
    return sensors


class WhenHubSensor(TripSensor):
    """Legacy sensor class for backwards compatibility.
    
    This class exists to support configurations created with older versions
    of the integration. New installations should use the event-type specific
    sensor classes directly.
    
    Inherits from TripSensor as the original WhenHub implementation was
    primarily focused on trip/vacation tracking.
    """
    
    def __init__(self, config_entry: ConfigEntry, event_data: dict, sensor_type: str) -> None:
        """Initialize legacy sensor as trip sensor.
        
        Ensures backwards compatibility by adding missing event type configuration
        and delegating to TripSensor implementation.
        
        Args:
            config_entry: Home Assistant config entry
            event_data: Event configuration data (may be missing event_type)
            sensor_type: Type of sensor to create
        """
        # Add event type if missing for backwards compatibility
        if CONF_EVENT_TYPE not in event_data:
            event_data[CONF_EVENT_TYPE] = EVENT_TYPE_TRIP
        super().__init__(config_entry, event_data, sensor_type)