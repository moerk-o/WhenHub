"""WhenHub Integration for Home Assistant.

This is the main integration module that handles setup, configuration updates,
and cleanup for the WhenHub event tracking integration. It manages the lifecycle
of all platforms (sensors, binary sensors, images) for event tracking.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Platforms that this integration provides
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.IMAGE, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WhenHub integration from a config entry.
    
    This function is called when Home Assistant loads the integration. It initializes
    the data storage, sets up all platforms, and registers update listeners.
    
    Args:
        hass: Home Assistant instance
        entry: Configuration entry for this integration instance
        
    Returns:
        True if setup was successful, False otherwise
    """
    # Initialize integration data storage
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Set up all platforms (sensors, binary sensors, images)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register listener for configuration updates (options flow)
    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    
    _LOGGER.info("WhenHub integration loaded: %s", entry.title)
    
    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle configuration updates from the options flow.
    
    This function is called when the user modifies the integration configuration
    through the options flow. It updates the stored data and reloads all platforms
    to reflect the changes.
    
    Args:
        hass: Home Assistant instance
        entry: Updated configuration entry
    """
    # Update stored configuration data
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    # Reload all platforms to apply configuration changes
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
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
    # Attempt to unload all platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove stored configuration data
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Clean up entity registry entries for this config entry
        entity_registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
        
        # Remove all entities created by this integration instance
        for entity in entities:
            entity_registry.async_remove(entity.entity_id)
        
        _LOGGER.info("WhenHub integration unloaded: %s (%d entities removed)", 
                    entry.title, len(entities))
    else:
        _LOGGER.error("Failed to unload WhenHub integration: %s", entry.title)

    return unload_ok