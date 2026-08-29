"""WhenHub Integration for Home Assistant.

This is the main integration module that handles setup, configuration updates,
and cleanup for the WhenHub event tracking integration. It manages the lifecycle
of all platforms (sensors, binary sensors, images) for event tracking.
"""
from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue, async_delete_issue
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType
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
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# Platforms per entry type
EVENT_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.IMAGE, Platform.BINARY_SENSOR]
CALENDAR_PLATFORMS: list[Platform] = [Platform.CALENDAR]

# Key in hass.data[DOMAIN] for tracking entity restore listeners (per entry_id)
_RESTORE_LISTENER_KEY = "_entity_restore_listeners"

# Key in hass.data[DOMAIN] for entry IDs whose update listener must not reload
# because the caller reloads them itself (see suppress_update_reload)
_SUPPRESSED_RELOAD_KEY = "_suppressed_update_reloads"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WhenHub integration.

    Only registers the event services (FR15). Everything else is per config
    entry; the services are global and must exist exactly once.
    """
    async_setup_services(hass)
    return True


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
        _check_entity_source_availability(hass, entry)
        coordinator = WhenHubCoordinator(hass, entry, dict(entry.data))
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "event_data": dict(entry.data),
        }
        _setup_entity_date_listeners(hass, entry, coordinator)
        _setup_entity_registry_listener(hass, entry)
        await hass.config_entries.async_forward_entry_setups(entry, EVENT_PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    _LOGGER.info("WhenHub integration loaded: %s", entry.title)

    return True


@contextmanager
def suppress_update_reload(hass: HomeAssistant, entry_id: str) -> Iterator[None]:
    """Keep `async_update_listener` from reloading one entry (#29).

    For a caller that has to reload synchronously — `whenhub.update_event` only
    returns once the entities carry the new values — the listener's reload is a
    duplicate. Wrapping both the `async_update_entry` call and the caller's own
    `async_reload` in this context manager reloads the entry exactly once.

    Home Assistant starts the listener task eagerly, so it runs while the block
    is still open; even without eager start it would run at the first suspension
    point, which is the caller's `async_reload` inside the block.

    Args:
        hass: Home Assistant instance
        entry_id: Entry whose listener reload is suppressed
    """
    suppressed: set[str] = hass.data.setdefault(DOMAIN, {}).setdefault(
        _SUPPRESSED_RELOAD_KEY, set()
    )
    suppressed.add(entry_id)
    try:
        yield
    finally:
        suppressed.discard(entry_id)


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle configuration updates of a config entry.

    Called for every `async_update_entry` on this entry — the options flow, the
    entity rename auto-migration and the event services all go through it. The
    entry is reloaded so the coordinator and all platforms pick up the new data.

    Callers that reload the entry themselves suppress this reload via
    `suppress_update_reload`, otherwise the entry would be reloaded twice.

    Args:
        hass: Home Assistant instance
        entry: Updated configuration entry
    """
    if entry.entry_id in hass.data.get(DOMAIN, {}).get(_SUPPRESSED_RELOAD_KEY, ()):
        _LOGGER.debug(
            "WhenHub update listener skipped, caller reloads: %s", entry.title
        )
        return

    await hass.config_entries.async_reload(entry.entry_id)

    _LOGGER.info("WhenHub integration updated: %s", entry.title)


def _get_source_entity_map(data: dict) -> dict[str, str]:
    """Return {config_key: entity_id} for all active entity date sources."""
    result: dict[str, str] = {}
    for use_key, id_key in (
        (CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID),
        (CONF_START_DATE_USE_ENTITY, CONF_START_DATE_ENTITY_ID),
        (CONF_END_DATE_USE_ENTITY, CONF_END_DATE_ENTITY_ID),
    ):
        if data.get(use_key) and data.get(id_key):
            result[id_key] = data[id_key]
    return result


def _setup_entity_registry_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register entity registry listener to track renames and deletions of entity date sources.

    - On rename (action="update", entity_id changed): auto-migrates config entry data.
    - On delete (action="remove"): creates a Repairs issue.
    - On create (action="create"): auto-resolves a previous Repairs issue.

    The listener is automatically removed when the entry is unloaded via entry.async_on_unload().
    """
    if not _get_source_entity_map(entry.data):
        return

    @callback
    def _handle_entity_registry_update(event: Any) -> None:  # noqa: ANN401
        action = event.data.get("action")
        source_map = _get_source_entity_map(entry.data)

        if action == "update":
            changes = event.data.get("changes", {})
            if "entity_id" not in changes:
                return
            old_entity_id = changes["entity_id"]
            new_entity_id = event.data["entity_id"]

            affected_keys = [k for k, v in source_map.items() if v == old_entity_id]
            if not affected_keys:
                return

            new_data = dict(entry.data)
            for key in affected_keys:
                new_data[key] = new_entity_id
            hass.config_entries.async_update_entry(entry, data=new_data)

        elif action == "remove":
            deleted_entity_id = event.data["entity_id"]
            if deleted_entity_id not in source_map.values():
                return

            async_create_issue(
                hass,
                DOMAIN,
                f"entity_deleted_{entry.entry_id}",
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key="entity_source_deleted",
                translation_placeholders={
                    "name": entry.title,
                    "entity_id": deleted_entity_id,
                },
            )

        elif action == "create":
            new_entity_id = event.data["entity_id"]
            if new_entity_id not in source_map.values():
                return

            async_delete_issue(hass, DOMAIN, f"entity_deleted_{entry.entry_id}")
            coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
            hass.async_create_task(coordinator.async_request_refresh())

    entry.async_on_unload(
        hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, _handle_entity_registry_update)
    )


def _check_entity_source_availability(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Check configured entity date sources and update Repairs issue accordingly.

    Called on every entry setup (including HA restarts and retries). When sources are
    missing, also registers a one-shot restore listener so the Repairs issue is cleared
    immediately when the entity comes back — even while the entry is in retry mode
    (where _setup_entity_registry_listener is not yet active).

    The restore listener triggers an immediate reload so the coordinator picks up the
    restored entity without waiting for the next retry cycle.
    """
    # Cancel any restore listener from a previous setup attempt (handles retry cycles)
    restore_listeners: dict = hass.data[DOMAIN].setdefault(_RESTORE_LISTENER_KEY, {})
    if old_unsub := restore_listeners.pop(entry.entry_id, None):
        old_unsub()

    source_map = _get_source_entity_map(entry.data)

    if not source_map:
        async_delete_issue(hass, DOMAIN, f"entity_deleted_{entry.entry_id}")
        return

    entity_reg = er.async_get(hass)
    missing = [eid for eid in source_map.values() if entity_reg.async_get(eid) is None]

    if missing:
        async_create_issue(
            hass,
            DOMAIN,
            f"entity_deleted_{entry.entry_id}",
            is_fixable=False,
            severity=IssueSeverity.WARNING,
            translation_key="entity_source_deleted",
            translation_placeholders={
                "name": entry.title,
                "entity_id": missing[0],
            },
        )

        missing_set = set(missing)

        @callback
        def _on_entity_restored(event: Any) -> None:  # noqa: ANN401
            if event.data.get("action") != "create":
                return
            if event.data.get("entity_id") not in missing_set:
                return
            if unsub := restore_listeners.pop(entry.entry_id, None):
                unsub()
            async_delete_issue(hass, DOMAIN, f"entity_deleted_{entry.entry_id}")
            hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))

        unsub = hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, _on_entity_restored)
        restore_listeners[entry.entry_id] = unsub
    else:
        async_delete_issue(hass, DOMAIN, f"entity_deleted_{entry.entry_id}")


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

        # Cancel entity restore listener if present (registered while in retry mode)
        restore_listeners = hass.data[DOMAIN].get(_RESTORE_LISTENER_KEY, {})
        if unsub := restore_listeners.pop(entry.entry_id, None):
            unsub()

        hass.data[DOMAIN].pop(entry.entry_id, None)

        entity_registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)

        for entity in entities:
            entity_registry.async_remove(entity.entity_id)

        _LOGGER.info("WhenHub integration unloaded: %s (%d entities removed)",
                    entry.title, len(entities))
    else:
        _LOGGER.error("Failed to unload WhenHub integration: %s", entry.title)

    return unload_ok
