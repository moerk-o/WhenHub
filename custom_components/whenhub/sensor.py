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
    EVENT_TYPE_SPECIAL,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    TRIP_SENSOR_TYPES,
    MILESTONE_SENSOR_TYPES,
    ANNIVERSARY_SENSOR_TYPES,
    SPECIAL_SENSOR_TYPES,
)
from .coordinator import WhenHubCoordinator
from .sensors import TripSensor, MilestoneSensor, AnniversarySensor, SpecialEventSensor

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
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: WhenHubCoordinator = data["coordinator"]
    event_data: dict = data["event_data"]
    event_type = event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_TRIP)

    sensors = []

    try:
        # Create sensors based on event type
        if event_type == EVENT_TYPE_TRIP:
            sensors.extend(_create_trip_sensors(coordinator, config_entry, event_data))

        elif event_type == EVENT_TYPE_MILESTONE:
            sensors.extend(_create_milestone_sensors(coordinator, config_entry, event_data))

        elif event_type == EVENT_TYPE_ANNIVERSARY:
            sensors.extend(_create_anniversary_sensors(coordinator, config_entry, event_data))

        elif event_type == EVENT_TYPE_SPECIAL:
            sensors.extend(_create_special_sensors(coordinator, config_entry, event_data))

        else:
            # Fallback for unknown event types - use trip sensors as default
            _LOGGER.warning("Unknown event_type: %s, falling back to TRIP", event_type)
            sensors.extend(_create_trip_sensors(coordinator, config_entry, event_data))

        _LOGGER.info("Created %d sensors for %s (%s)",
                    len(sensors), event_data[CONF_EVENT_NAME], event_type)
        async_add_entities(sensors)

    except Exception as err:
        _LOGGER.error("Error setting up sensors for %s: %s",
                     event_data.get(CONF_EVENT_NAME, "unknown"), err)
        async_add_entities([])


def _create_trip_sensors(
    coordinator: WhenHubCoordinator,
    config_entry: ConfigEntry,
    event_data: dict,
) -> list[TripSensor]:
    """Create sensor entities for Trip events.

    Trip events have start and end dates and provide sensors for:
    - Days until trip starts
    - Days until trip ends
    - Countdown text to trip start
    - Days remaining in active trip
    - Percentage of trip remaining

    Args:
        coordinator: The data update coordinator
        config_entry: Home Assistant config entry
        event_data: Trip event configuration data

    Returns:
        List of TripSensor instances
    """
    return [
        TripSensor(coordinator, config_entry, event_data, sensor_type)
        for sensor_type in TRIP_SENSOR_TYPES
    ]


def _create_milestone_sensors(
    coordinator: WhenHubCoordinator,
    config_entry: ConfigEntry,
    event_data: dict,
) -> list[MilestoneSensor]:
    """Create sensor entities for Milestone events.

    Milestone events have a single target date and provide sensors for:
    - Days until milestone date
    - Countdown text to milestone

    Args:
        coordinator: The data update coordinator
        config_entry: Home Assistant config entry
        event_data: Milestone event configuration data

    Returns:
        List of MilestoneSensor instances
    """
    return [
        MilestoneSensor(coordinator, config_entry, event_data, sensor_type)
        for sensor_type in MILESTONE_SENSOR_TYPES
    ]


def _create_anniversary_sensors(
    coordinator: WhenHubCoordinator,
    config_entry: ConfigEntry,
    event_data: dict,
) -> list[AnniversarySensor]:
    """Create sensor entities for Anniversary events.

    Anniversary events repeat annually and provide sensors for:
    - Days until next anniversary
    - Days since last anniversary
    - Countdown text to next anniversary
    - Count of total occurrences
    - Next anniversary date
    - Last anniversary date

    Args:
        coordinator: The data update coordinator
        config_entry: Home Assistant config entry
        event_data: Anniversary event configuration data

    Returns:
        List of AnniversarySensor instances
    """
    return [
        AnniversarySensor(coordinator, config_entry, event_data, sensor_type)
        for sensor_type in ANNIVERSARY_SENSOR_TYPES
    ]


def _create_special_sensors(
    coordinator: WhenHubCoordinator,
    config_entry: ConfigEntry,
    event_data: dict,
) -> list[SpecialEventSensor]:
    """Create sensor entities for Special events.

    Special events are holidays and astronomical events that provide sensors for:
    - Days until next occurrence
    - Days since last occurrence
    - Countdown text to next occurrence
    - Next occurrence date
    - Last occurrence date

    Args:
        coordinator: The data update coordinator
        config_entry: Home Assistant config entry
        event_data: Special event configuration data

    Returns:
        List of SpecialEventSensor instances
    """
    return [
        SpecialEventSensor(coordinator, config_entry, event_data, sensor_type)
        for sensor_type in SPECIAL_SENSOR_TYPES
    ]
