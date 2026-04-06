"""URL and Memo sensor classes for WhenHub integration (FR11)."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import CONF_URL, CONF_MEMO
from .base import get_device_info

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..coordinator import WhenHubCoordinator


class WhenHubUrlSensor(CoordinatorEntity["WhenHubCoordinator"], SensorEntity):
    """Sensor exposing the event URL.

    Starts disabled by default; enabled automatically by __init__.py
    when the URL field is populated.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "url"
    _attr_icon = "mdi:link"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._event_data = event_data
        self._attr_unique_id = f"{config_entry.entry_id}_url"

    @property
    def device_info(self) -> DeviceInfo:
        return get_device_info(self._config_entry, self._event_data)

    @property
    def native_value(self) -> str | None:
        value = self._event_data.get(CONF_URL, "")
        return value if value else None


class WhenHubMemoSensor(CoordinatorEntity["WhenHubCoordinator"], SensorEntity):
    """Sensor exposing the event memo / notes.

    Starts disabled by default; enabled automatically by __init__.py
    when the Memo field is populated.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "memo"
    _attr_icon = "mdi:note-text"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: "WhenHubCoordinator",
        config_entry: ConfigEntry,
        event_data: dict,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._event_data = event_data
        self._attr_unique_id = f"{config_entry.entry_id}_memo"

    @property
    def device_info(self) -> DeviceInfo:
        return get_device_info(self._config_entry, self._event_data)

    @property
    def native_value(self) -> str | None:
        value = self._event_data.get(CONF_MEMO, "")
        return value if value else None
