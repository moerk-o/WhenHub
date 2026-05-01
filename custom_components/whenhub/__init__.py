"""WhenHub Integration for Home Assistant.

This is the main integration module that handles setup, configuration updates,
and cleanup for the WhenHub event tracking integration. It manages the lifecycle
of all platforms (sensors, binary sensors, images) for event tracking.
"""
from __future__ import annotations

import logging

from homeassistant.helpers.issue_registry import async_delete_issue
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, CONF_ENTRY_TYPE, ENTRY_TYPE_CALENDAR
from .coordinator import WhenHubCoordinator

_LOGGER = logging.getLogger(__name__)

# Platforms per entry type
EVENT_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.IMAGE, Platform.BINARY_SENSOR]
CALENDAR_PLATFORMS: list[Platform] = [Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WhenHub integration from a config entry.

    This function is called when Home Assistant loads the integration. It initializes
    the data coordinator, sets up all platforms, and registers update listeners.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry for this integration instance

    Returns:
        True if setup was successful, False otherwise
    """
    hass.data.setdefault(DOMAIN, {})

    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
        # Calendar entry: no coordinator, only calendar platform
        hass.data[DOMAIN][entry.entry_id] = {}
        await hass.config_entries.async_forward_entry_setups(entry, CALENDAR_PLATFORMS)
    else:
        # Event entry: existing behavior unchanged
        coordinator = WhenHubCoordinator(hass, entry, dict(entry.data))
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "event_data": dict(entry.data),
        }
        await hass.config_entries.async_forward_entry_setups(entry, EVENT_PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    _LOGGER.info("WhenHub integration loaded: %s", entry.title)

    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle configuration updates from the options flow.

    This function is called when the user modifies the integration configuration
    through the options flow. It recreates the coordinator and reloads all platforms
    to reflect the changes.

    Args:
        hass: Home Assistant instance
        entry: Updated configuration entry
    """
    await hass.config_entries.async_reload(entry.entry_id)

    _LOGGER.info("WhenHub integration updated: %s", entry.title)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload WhenHub integration config entry.

    This function is called when the integration is being removed or reloaded.
    It cleanly unloads all platforms, removes entities from the registry, and
    cleans up stored data.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry being unloaded

    Returns:
        True if unload was successful, False otherwise
    """
    platforms = (
        CALENDAR_PLATFORMS
        if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR
        else EVENT_PLATFORMS
    )

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, platforms):
        # Clean up any open Repairs issue for this entry
        async_delete_issue(hass, DOMAIN, f"expired_{entry.entry_id}")

        hass.data[DOMAIN].pop(entry.entry_id)

        entity_registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)

        for entity in entities:
            entity_registry.async_remove(entity.entity_id)

        _LOGGER.info("WhenHub integration unloaded: %s (%d entities removed)",
                    entry.title, len(entities))
    else:
        _LOGGER.error("Failed to unload WhenHub integration: %s", entry.title)

    return unload_ok
