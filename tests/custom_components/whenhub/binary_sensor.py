"""Binary sensor platform for WhenHub integration.

This module implements binary sensors that provide boolean (on/off) status
for various event conditions like "trip starts today", "milestone is today",
or "anniversary is today". These are useful for automations and notifications.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
    EVENT_TYPE_SPECIAL,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    CONF_SPECIAL_CATEGORY,
    CONF_IMAGE_PATH,
    TRIP_BINARY_SENSOR_TYPES,
    MILESTONE_BINARY_SENSOR_TYPES,
    ANNIVERSARY_BINARY_SENSOR_TYPES,
    SPECIAL_BINARY_SENSOR_TYPES,
    DST_BINARY_SENSOR_TYPES,
    DEFAULT_IMAGE,
    BINARY_UNIQUE_ID_PATTERN,
)
from .sensors.base import get_device_info


# Device class mapping from string to enum for binary sensors
# Note: We intentionally use None for most sensors to show simple "On"/"Off" states
# "occurrence" is not a valid HA device_class, so we map it to None
BINARY_DEVICE_CLASS_MAP = {
    "occurrence": None,  # Shows "On"/"Off" instead of "Running"/"Not running"
}


def create_binary_sensor_description(sensor_key: str, sensor_config: dict) -> BinarySensorEntityDescription:
    """Create a BinarySensorEntityDescription from sensor config dict.

    Args:
        sensor_key: The sensor type key (e.g., 'trip_starts_today')
        sensor_config: Dictionary with icon, device_class

    Returns:
        BinarySensorEntityDescription with translation_key set for localization
    """
    device_class = None
    if "device_class" in sensor_config:
        device_class = BINARY_DEVICE_CLASS_MAP.get(sensor_config["device_class"])

    return BinarySensorEntityDescription(
        key=sensor_key,
        translation_key=sensor_key,  # Uses entity.binary_sensor.<key>.name from translations
        icon=sensor_config.get("icon"),
        device_class=device_class,
    )

if TYPE_CHECKING:
    from .coordinator import WhenHubCoordinator

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
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: "WhenHubCoordinator" = data["coordinator"]
    event_data: dict = data["event_data"]
    event_type = event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_TRIP)

    binary_sensors = []

    try:
        if event_type == EVENT_TYPE_TRIP:
            for sensor_type in TRIP_BINARY_SENSOR_TYPES:
                binary_sensors.append(
                    TripBinarySensor(coordinator, config_entry, event_data, sensor_type)
                )

        elif event_type == EVENT_TYPE_MILESTONE:
            for sensor_type in MILESTONE_BINARY_SENSOR_TYPES:
                binary_sensors.append(
                    MilestoneBinarySensor(coordinator, config_entry, event_data, sensor_type)
                )

        elif event_type == EVENT_TYPE_ANNIVERSARY:
            for sensor_type in ANNIVERSARY_BINARY_SENSOR_TYPES:
                binary_sensors.append(
                    AnniversaryBinarySensor(coordinator, config_entry, event_data, sensor_type)
                )

        elif event_type == EVENT_TYPE_SPECIAL:
            # Check if this is a DST event
            special_category = event_data.get(CONF_SPECIAL_CATEGORY)
            if special_category == "dst":
                for sensor_type in DST_BINARY_SENSOR_TYPES:
                    binary_sensors.append(
                        DSTBinarySensor(coordinator, config_entry, event_data, sensor_type)
                    )
            else:
                for sensor_type in SPECIAL_BINARY_SENSOR_TYPES:
                    binary_sensors.append(
                        SpecialBinarySensor(coordinator, config_entry, event_data, sensor_type)
                    )

        if binary_sensors:
            _LOGGER.info("Created %d binary sensors for %s", len(binary_sensors), event_data[CONF_EVENT_NAME])
            async_add_entities(binary_sensors)
    except Exception as err:
        _LOGGER.error("Error setting up binary sensors for %s: %s", event_data.get(CONF_EVENT_NAME), err)
        async_add_entities([])


class BaseBinarySensor(CoordinatorEntity["WhenHubCoordinator"], BinarySensorEntity):
    """Base class for all WhenHub binary sensors.

    Provides common functionality for Trip, Milestone, and Anniversary binary sensors
    using CoordinatorEntity for efficient updates. Child classes implement
    the specific boolean logic for their sensor types.

    Uses BinarySensorEntityDescription with translation_key for proper entity name
    localization (following the pattern used in solstice_season).
    """

    entity_description: BinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
        sensor_types: dict,
    ) -> None:
        """Initialize the binary sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary with event configuration data
            sensor_type: String identifying binary sensor type (e.g. 'trip_starts_today')
            sensor_types: Dictionary mapping sensor types to their metadata
        """
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._event_data = event_data
        self._sensor_type = sensor_type
        self._sensor_types = sensor_types

        # Create and set entity_description with translation_key for localization
        # This is the official HA pattern for translatable entity names
        self.entity_description = create_binary_sensor_description(
            sensor_type, sensor_types[sensor_type]
        )

        # Set unique_id for entity registry
        self._attr_unique_id = BINARY_UNIQUE_ID_PATTERN.format(
            entry_id=config_entry.entry_id,
            sensor_type=sensor_type
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity.

        Groups all binary sensors from the same WhenHub event under one device.
        """
        return get_device_info(self._config_entry, self._event_data)

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor condition is met.

        Reads boolean value from coordinator data.
        """
        data = self.coordinator.data
        if not data:
            return False
        return self._get_value_from_coordinator(data)

    def _get_value_from_coordinator(self, data: dict[str, Any]) -> bool:
        """Get the boolean value from coordinator data.

        Abstract method to be implemented by child classes.

        Args:
            data: Coordinator data dictionary

        Returns:
            Boolean indicating if the sensor condition is currently true
        """
        return False


class TripBinarySensor(BaseBinarySensor):
    """Binary sensor for multi-day trip events.

    Provides boolean sensors for trip-related conditions:
    - trip_starts_today: True if today is the trip start date
    - trip_active_today: True if today falls within the trip duration
    - trip_ends_today: True if today is the trip end date

    Data is provided by the WhenHubCoordinator for efficient updates.
    """

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
    ) -> None:
        """Initialize the trip binary sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry
            event_data: Trip configuration with start_date and end_date
            sensor_type: Type of trip binary sensor to create
        """
        super().__init__(coordinator, config_entry, event_data, sensor_type, TRIP_BINARY_SENSOR_TYPES)

    def _get_value_from_coordinator(self, data: dict[str, Any]) -> bool:
        """Get the boolean value for this trip condition from coordinator data."""
        if self._sensor_type == "trip_starts_today":
            return data.get("trip_starts_today", False)
        elif self._sensor_type == "trip_active_today":
            return data.get("trip_active_today", False)
        elif self._sensor_type == "trip_ends_today":
            return data.get("trip_ends_today", False)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor."""
        return {}


class MilestoneBinarySensor(BaseBinarySensor):
    """Binary sensor for one-time milestone events.

    Provides boolean sensors for milestone conditions:
    - is_today: True if today is the milestone date

    Data is provided by the WhenHubCoordinator for efficient updates.
    """

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
    ) -> None:
        """Initialize the milestone binary sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry
            event_data: Milestone configuration with target_date
            sensor_type: Type of milestone binary sensor to create
        """
        super().__init__(coordinator, config_entry, event_data, sensor_type, MILESTONE_BINARY_SENSOR_TYPES)

    def _get_value_from_coordinator(self, data: dict[str, Any]) -> bool:
        """Get the boolean value for this milestone condition from coordinator data."""
        if self._sensor_type == "is_today":
            return data.get("is_today", False)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor."""
        data = self.coordinator.data
        attributes = {
            "event_name": self._event_data[CONF_EVENT_NAME],
            "event_type": self._event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_MILESTONE),
            "target_date": data.get("target_date") if data else None,
        }

        if self._event_data.get(CONF_IMAGE_PATH):
            attributes["image_path"] = self._event_data[CONF_IMAGE_PATH]
        else:
            attributes["image_path"] = DEFAULT_IMAGE

        return attributes


class AnniversaryBinarySensor(BaseBinarySensor):
    """Binary sensor for recurring anniversary events.

    Provides boolean sensors for anniversary conditions:
    - is_today: True if today is an anniversary occurrence

    Data is provided by the WhenHubCoordinator for efficient updates.
    """

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
    ) -> None:
        """Initialize the anniversary binary sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry
            event_data: Anniversary configuration with target_date (original date)
            sensor_type: Type of anniversary binary sensor to create
        """
        super().__init__(coordinator, config_entry, event_data, sensor_type, ANNIVERSARY_BINARY_SENSOR_TYPES)

    def _get_value_from_coordinator(self, data: dict[str, Any]) -> bool:
        """Get the boolean value for this anniversary condition from coordinator data."""
        if self._sensor_type == "is_today":
            return data.get("is_today", False)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor."""
        data = self.coordinator.data
        attributes = {
            "event_name": self._event_data[CONF_EVENT_NAME],
            "event_type": self._event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_ANNIVERSARY),
            "original_date": data.get("original_date") if data else None,
        }

        if self._event_data.get(CONF_IMAGE_PATH):
            attributes["image_path"] = self._event_data[CONF_IMAGE_PATH]
        else:
            attributes["image_path"] = DEFAULT_IMAGE

        if data:
            attributes.update({
                "next_anniversary": data.get("next_anniversary"),
                "years_on_next": data.get("years_on_next", 0),
            })

        return attributes


class SpecialBinarySensor(BaseBinarySensor):
    """Binary sensor for special holiday and astronomical events.

    Provides boolean sensors for special event conditions:
    - is_today: True if today is the special event occurrence

    Data is provided by the WhenHubCoordinator for efficient updates.
    """

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
    ) -> None:
        """Initialize the special event binary sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry
            event_data: Special event configuration with special_type
            sensor_type: Type of special event binary sensor to create
        """
        super().__init__(coordinator, config_entry, event_data, sensor_type, SPECIAL_BINARY_SENSOR_TYPES)

    def _get_value_from_coordinator(self, data: dict[str, Any]) -> bool:
        """Get the boolean value for this special event condition from coordinator data."""
        if self._sensor_type == "is_today":
            return data.get("is_today", False)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor."""
        data = self.coordinator.data
        attributes = {
            "event_name": self._event_data[CONF_EVENT_NAME],
            "event_type": self._event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_SPECIAL),
            "special_type": data.get("special_type") if data else None,
            "special_name": data.get("special_name") if data else None,
        }

        if data and data.get("next_date"):
            attributes["next_date"] = data.get("next_date")

        if self._event_data.get(CONF_IMAGE_PATH):
            attributes["image_path"] = self._event_data[CONF_IMAGE_PATH]
        else:
            attributes["image_path"] = DEFAULT_IMAGE

        return attributes


class DSTBinarySensor(BaseBinarySensor):
    """Binary sensor for DST (Daylight Saving Time) events.

    Provides boolean sensors for DST conditions:
    - is_today: True if today is a DST transition day
    - is_dst_active: True if summer time (DST) is currently active

    Data is provided by the WhenHubCoordinator for efficient updates.
    """

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
        sensor_type: str,
    ) -> None:
        """Initialize the DST binary sensor.

        Args:
            coordinator: The data update coordinator for this event
            config_entry: Home Assistant config entry
            event_data: DST event configuration with dst_type and dst_region
            sensor_type: Type of DST binary sensor to create
        """
        super().__init__(coordinator, config_entry, event_data, sensor_type, DST_BINARY_SENSOR_TYPES)

    def _get_value_from_coordinator(self, data: dict[str, Any]) -> bool:
        """Get the boolean value for this DST condition from coordinator data."""
        if self._sensor_type == "is_today":
            return data.get("is_today", False)
        elif self._sensor_type == "is_dst_active":
            return data.get("is_dst_active", False)
        return False

    @property
    def icon(self) -> str:
        """Return dynamic icon based on DST state for is_dst_active sensor."""
        if self._sensor_type == "is_dst_active":
            # Dynamic icon: sun-clock when DST active, sun-clock-outline when not
            if self.is_on:
                return "mdi:sun-clock"
            return "mdi:sun-clock-outline"
        # For other sensor types, use the default icon from entity_description
        return self.entity_description.icon

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor."""
        data = self.coordinator.data
        attributes = {
            "event_name": self._event_data[CONF_EVENT_NAME],
            "event_type": self._event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_SPECIAL),
            "dst_type": data.get("dst_type") if data else None,
            "dst_region": data.get("dst_region") if data else None,
            "region_name": data.get("region_name") if data else None,
        }

        if data and data.get("next_date"):
            attributes["next_date"] = data.get("next_date")

        if data and data.get("last_date"):
            attributes["last_date"] = data.get("last_date")

        if self._event_data.get(CONF_IMAGE_PATH):
            attributes["image_path"] = self._event_data[CONF_IMAGE_PATH]
        else:
            attributes["image_path"] = DEFAULT_IMAGE

        return attributes
