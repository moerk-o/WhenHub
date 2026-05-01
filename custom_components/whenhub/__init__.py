"""WhenHub Integration for Home Assistant.

This is the main integration module that handles setup, configuration updates,
and cleanup for the WhenHub event tracking integration. It manages the lifecycle
of all platforms (sensors, binary sensors, images) for event tracking.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.helpers.issue_registry import async_delete_issue
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    CONF_ENTRY_TYPE,
    ENTRY_TYPE_CALENDAR,
    CONF_EVENT_DATE_USE_ENTITY,
    CONF_EVENT_DATE_ENTITY_ID,
    CONF_START_DATE_USE_ENTITY,
    CONF_START_DATE_ENTITY_ID,
    CONF_END_DATE_USE_ENTITY,
    CONF_END_DATE_ENTITY_ID,
)
from .coordinator import WhenHubCoordinator

_LOGGER = logging.getLogger(__name__)

# Platforms per entry type
EVENT_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.IMAGE, Platform.BINARY_SENSOR]
CALENDAR_PLATFORMS: list[Platform] = [Platform.CALENDAR]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entry to the current version.

    Version 1 → 2 (v3.0.0): Standardize entity IDs to English type-key suffixes.

    Entity IDs were previously generated from the translated entity name (language-
    dependent). This migration renames them to always use the English sensor type key
    (e.g. 'event_date' instead of 'ereignisdatum' on German HA).
    Also affects English installs where the translated name differed from the type
    key (e.g. 'days_until_start' → 'days_until', 'trip_days_remaining' → 'trip_left_days').
    """
    _LOGGER.info("Migrating WhenHub entry '%s' from version %s to 2", entry.title, entry.version)

    if entry.version == 1:
        # Calendar entries have no sensor entities with language-dependent IDs.
        if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
            hass.config_entries.async_update_entry(entry, version=2)
            return True

        entity_registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
        device_slug = slugify(entry.title)
        entry_id = entry.entry_id
        binary_prefix = f"{entry_id}_binary_"
        entry_prefix = f"{entry_id}_"
        renamed = 0

        for entity_entry in entities:
            uid = entity_entry.unique_id
            platform = entity_entry.domain  # "sensor", "binary_sensor", or "image"

            # Determine the canonical English suffix from the unique_id
            if uid == f"{entry_id}_image":
                english_suffix = "event_image"
            elif uid == f"{entry_id}_calendar":
                continue  # Should not occur for event entries, skip to be safe
            elif uid.startswith(binary_prefix):
                english_suffix = uid[len(binary_prefix):]
            elif uid.startswith(entry_prefix):
                english_suffix = uid[len(entry_prefix):]
            else:
                _LOGGER.warning("Unexpected unique_id during migration: %s — skipping", uid)
                continue

            expected_entity_id = f"{platform}.{device_slug}_{english_suffix}"

            if entity_entry.entity_id == expected_entity_id:
                continue  # Already correct (no rename needed)

            # Skip if the target entity_id is already taken by another entity
            if entity_registry.async_get(expected_entity_id) is not None:
                _LOGGER.warning(
                    "Cannot rename %s → %s: target already exists. "
                    "Please rename manually.",
                    entity_entry.entity_id,
                    expected_entity_id,
                )
                continue

            entity_registry.async_update_entity(
                entity_entry.entity_id,
                new_entity_id=expected_entity_id,
            )
            _LOGGER.debug("Renamed entity: %s → %s", entity_entry.entity_id, expected_entity_id)
            renamed += 1

        hass.config_entries.async_update_entry(entry, version=2)
        _LOGGER.info(
            "Migration complete for '%s': %d of %d entities renamed",
            entry.title,
            renamed,
            len(entities),
        )

    return True


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
        _setup_entity_date_listeners(hass, entry, coordinator)
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


def _setup_entity_date_listeners(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: WhenHubCoordinator,
) -> None:
    """Register state-change listeners for entity date sources.

    For each date field configured to use an entity as source, a listener is
    registered so the coordinator refreshes immediately when that entity changes
    (including transitions to/from unavailable or unknown).

    Listeners are automatically removed when the entry is unloaded via
    entry.async_on_unload().
    """
    data = entry.data
    entity_ids: list[str] = []

    for use_key, id_key in (
        (CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID),
        (CONF_START_DATE_USE_ENTITY, CONF_START_DATE_ENTITY_ID),
        (CONF_END_DATE_USE_ENTITY, CONF_END_DATE_ENTITY_ID),
    ):
        if data.get(use_key) and data.get(id_key):
            entity_ids.append(data[id_key])

    if not entity_ids:
        return

    @callback
    def _handle_entity_date_change(event: Any) -> None:  # noqa: ANN401
        hass.async_create_task(coordinator.async_request_refresh())

    for entity_id in entity_ids:
        entry.async_on_unload(
            async_track_state_change_event(hass, entity_id, _handle_entity_date_change)
        )


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
        # Clean up any open Repairs issues for this entry
        async_delete_issue(hass, DOMAIN, f"expired_{entry.entry_id}")
        async_delete_issue(hass, DOMAIN, f"date_order_{entry.entry_id}")

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
