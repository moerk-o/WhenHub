"""Base sensor classes for WhenHub integration.

This module provides the foundation classes for all WhenHub sensors, including
common functionality like device info creation, error handling, and countdown
text formatting that is shared across Trip, Milestone, and Anniversary sensors.
"""
from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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


# Device class mapping from string to enum
DEVICE_CLASS_MAP = {
    "duration": SensorDeviceClass.DURATION,
    "timestamp": SensorDeviceClass.TIMESTAMP,
}


def create_sensor_description(sensor_key: str, sensor_config: dict) -> SensorEntityDescription:
    """Create a SensorEntityDescription from sensor config dict.

    Args:
        sensor_key: The sensor type key (e.g., 'days_until')
        sensor_config: Dictionary with icon, unit, device_class

    Returns:
        SensorEntityDescription with translation_key set for localization
    """
    device_class = None
    if "device_class" in sensor_config:
        device_class = DEVICE_CLASS_MAP.get(sensor_config["device_class"])

    return SensorEntityDescription(
        key=sensor_key,
        translation_key=sensor_key,  # Uses entity.sensor.<key>.name from translations
        icon=sensor_config.get("icon"),
        native_unit_of_measurement=sensor_config.get("unit"),
        device_class=device_class,
    )

if TYPE_CHECKING:
    from ..coordinator import WhenHubCoordinator

_LOGGER = logging.getLogger(__name__)

# Load version from manifest_test.json (copy of main manifest for tests)
MANIFEST = json.loads((Path(__file__).parent.parent / "manifest_test.json").read_text())
VERSION = MANIFEST["version"]


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
        sw_version=VERSION,
    )


# Re-export parse_date for backward compatibility
__all__ = ["get_device_info", "parse_date", "BaseSensor", "BaseCountdownSensor", "create_sensor_description"]


class BaseSensor(CoordinatorEntity["WhenHubCoordinator"], SensorEntity):
    """Base class for all WhenHub sensors.

    This abstract base class provides common functionality for Trip, Milestone,
    and Anniversary sensors. It uses CoordinatorEntity for efficient updates
    and handles entity initialization, device info, and attribute management.

    Uses SensorEntityDescription with translation_key for proper entity name
    localization (following the pattern used in solstice_season).

    Child classes must implement their own native_value calculation logic,
    typically by reading from self.coordinator.data.
    """

    entity_description: SensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
        sensor_types: dict,
    ) -> None:
        """Initialize the base sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary with event configuration (name, dates, etc.)
            sensor_type: String identifying sensor type (e.g. 'days_until', 'countdown_text')
            sensor_types: Dictionary mapping sensor types to their metadata (name, icon, unit)
        """
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._event_data = event_data
        self._sensor_type = sensor_type
        self._sensor_types = sensor_types

        # Create and set entity_description with translation_key for localization
        # This is the official HA pattern for translatable entity names
        self.entity_description = create_sensor_description(
            sensor_type, sensor_types[sensor_type]
        )

        # Set unique_id for entity registry
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"

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


class BaseCountdownSensor(BaseSensor):
    """Base class for sensors with countdown text functionality.

    Extends BaseSensor with countdown text formatting capabilities. This class
    can read from coordinator.data or fall back to direct calculation.

    Used by Trip, Milestone, and Anniversary sensors that need countdown_text sensors.
    """

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
        sensor_types: dict,
    ) -> None:
        """Initialize the countdown sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry
            event_data: Event configuration data
            sensor_type: Type of sensor being created
            sensor_types: Sensor type definitions with metadata
        """
        super().__init__(coordinator, config_entry, event_data, sensor_type, sensor_types)

    def _get_countdown_attributes(self) -> dict[str, int]:
        """Get countdown breakdown as individual attributes from coordinator data.

        Returns:
            Dictionary with breakdown_years, breakdown_months, breakdown_weeks, breakdown_days keys
        """
        breakdown = self.coordinator.data.get("countdown_breakdown", {})
        return {
            "breakdown_years": breakdown.get("years", 0),
            "breakdown_months": breakdown.get("months", 0),
            "breakdown_weeks": breakdown.get("weeks", 0),
            "breakdown_days": breakdown.get("days", 0),
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