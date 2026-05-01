"""Tests for FR19: Entity registry tracking for entity-based date sources.

Tests:
- _get_source_entity_map() helper function
- _setup_entity_registry_listener() registration logic
- Callback: rename (action="update") → auto-migration
- Callback: delete (action="remove") → Repairs issue created
- Callback: create/restore (action="create") → Repairs issue auto-resolved
- Data correctness after auto-migration
"""
from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from custom_components.whenhub.const import (
    DOMAIN,
    CONF_EVENT_DATE_USE_ENTITY,
    CONF_EVENT_DATE_ENTITY_ID,
    CONF_START_DATE_USE_ENTITY,
    CONF_START_DATE_ENTITY_ID,
    CONF_END_DATE_USE_ENTITY,
    CONF_END_DATE_ENTITY_ID,
)
from custom_components.whenhub import _get_source_entity_map, _setup_entity_registry_listener


# ---------------------------------------------------------------------------
# Patch targets (functions imported into custom_components/whenhub/__init__.py)
# ---------------------------------------------------------------------------

PATCH_CREATE = "custom_components.whenhub.async_create_issue"
PATCH_DELETE = "custom_components.whenhub.async_delete_issue"


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class _FakeEntry:
    def __init__(self, entry_id="test_id", title="Test Event", data=None):
        self.entry_id = entry_id
        self.title = title
        self.data = data or {}
        self.async_on_unload = MagicMock()


class _FakeHass:
    def __init__(self, entry_id="test_id"):
        self.bus = MagicMock()
        self.config_entries = MagicMock()
        self.async_create_task = MagicMock()
        self.data = {DOMAIN: {entry_id: {"coordinator": MagicMock()}}}


def _make_event(action: str, entity_id: str, changes: dict | None = None) -> MagicMock:
    """Build a minimal entity-registry event mock."""
    event = MagicMock()
    event.data = {"action": action, "entity_id": entity_id}
    if changes is not None:
        event.data["changes"] = changes
    return event


def _setup_and_get_callback(hass: _FakeHass, entry: _FakeEntry):
    """Register listener and return the captured callback (None when not registered)."""
    captured = [None]

    def _capture(event_name, callback):
        captured[0] = callback
        return MagicMock()

    hass.bus.async_listen.side_effect = _capture
    _setup_entity_registry_listener(hass, entry)
    return captured[0]


# ---------------------------------------------------------------------------
# _get_source_entity_map
# ---------------------------------------------------------------------------

class TestGetSourceEntityMap:
    """Unit tests for the _get_source_entity_map() helper."""

    def test_empty_data_returns_empty(self):
        assert _get_source_entity_map({}) == {}

    def test_milestone_entity_source(self):
        data = {CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.bday"}
        assert _get_source_entity_map(data) == {CONF_EVENT_DATE_ENTITY_ID: "sensor.bday"}

    def test_trip_start_only(self):
        data = {CONF_START_DATE_USE_ENTITY: True, CONF_START_DATE_ENTITY_ID: "sensor.dep"}
        assert _get_source_entity_map(data) == {CONF_START_DATE_ENTITY_ID: "sensor.dep"}

    def test_trip_end_only(self):
        data = {CONF_END_DATE_USE_ENTITY: True, CONF_END_DATE_ENTITY_ID: "sensor.ret"}
        assert _get_source_entity_map(data) == {CONF_END_DATE_ENTITY_ID: "sensor.ret"}

    def test_trip_both_sources(self):
        data = {
            CONF_START_DATE_USE_ENTITY: True, CONF_START_DATE_ENTITY_ID: "sensor.dep",
            CONF_END_DATE_USE_ENTITY: True, CONF_END_DATE_ENTITY_ID: "sensor.ret",
        }
        assert _get_source_entity_map(data) == {
            CONF_START_DATE_ENTITY_ID: "sensor.dep",
            CONF_END_DATE_ENTITY_ID: "sensor.ret",
        }

    def test_use_entity_false_excluded(self):
        data = {CONF_EVENT_DATE_USE_ENTITY: False, CONF_EVENT_DATE_ENTITY_ID: "sensor.bday"}
        assert _get_source_entity_map(data) == {}

    def test_missing_entity_id_excluded(self):
        data = {CONF_EVENT_DATE_USE_ENTITY: True}
        assert _get_source_entity_map(data) == {}


# ---------------------------------------------------------------------------
# Listener registration
# ---------------------------------------------------------------------------

class TestListenerRegistration:
    """_setup_entity_registry_listener() registers only when entity sources exist."""

    def test_registers_listener_when_entity_source_present(self):
        entry = _FakeEntry(data={CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.x"})
        hass = _FakeHass(entry.entry_id)

        _setup_entity_registry_listener(hass, entry)

        hass.bus.async_listen.assert_called_once()
        entry.async_on_unload.assert_called_once()

    def test_no_listener_without_entity_source(self):
        entry = _FakeEntry(data={"event_type": "milestone", "target_date": "2025-01-01"})
        hass = _FakeHass(entry.entry_id)

        _setup_entity_registry_listener(hass, entry)

        hass.bus.async_listen.assert_not_called()
        entry.async_on_unload.assert_not_called()


# ---------------------------------------------------------------------------
# Rename (action="update")
# ---------------------------------------------------------------------------

class TestEntityRename:
    """Auto-migration when entity-id changes in the registry."""

    def test_rename_milestone_entity_updates_config_data(self):
        entry = _FakeEntry(data={CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.old"})
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        cb(_make_event("update", "sensor.new", changes={"entity_id": "sensor.old"}))

        hass.config_entries.async_update_entry.assert_called_once()
        new_data = hass.config_entries.async_update_entry.call_args[1]["data"]
        assert new_data[CONF_EVENT_DATE_ENTITY_ID] == "sensor.new"

    def test_rename_trip_start_entity_updates_config_data(self):
        entry = _FakeEntry(data={
            CONF_START_DATE_USE_ENTITY: True, CONF_START_DATE_ENTITY_ID: "sensor.dep_old",
            CONF_END_DATE_USE_ENTITY: True, CONF_END_DATE_ENTITY_ID: "sensor.ret",
        })
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        cb(_make_event("update", "sensor.dep_new", changes={"entity_id": "sensor.dep_old"}))

        new_data = hass.config_entries.async_update_entry.call_args[1]["data"]
        assert new_data[CONF_START_DATE_ENTITY_ID] == "sensor.dep_new"
        assert new_data[CONF_END_DATE_ENTITY_ID] == "sensor.ret"

    def test_rename_trip_end_entity_updates_config_data(self):
        entry = _FakeEntry(data={
            CONF_START_DATE_USE_ENTITY: True, CONF_START_DATE_ENTITY_ID: "sensor.dep",
            CONF_END_DATE_USE_ENTITY: True, CONF_END_DATE_ENTITY_ID: "sensor.ret_old",
        })
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        cb(_make_event("update", "sensor.ret_new", changes={"entity_id": "sensor.ret_old"}))

        new_data = hass.config_entries.async_update_entry.call_args[1]["data"]
        assert new_data[CONF_END_DATE_ENTITY_ID] == "sensor.ret_new"
        assert new_data[CONF_START_DATE_ENTITY_ID] == "sensor.dep"

    def test_rename_non_source_entity_no_change(self):
        entry = _FakeEntry(data={CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.bday"})
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        cb(_make_event("update", "sensor.other_new", changes={"entity_id": "sensor.other_old"}))

        hass.config_entries.async_update_entry.assert_not_called()

    def test_update_without_entity_id_in_changes_is_ignored(self):
        """Only changes containing 'entity_id' trigger migration (e.g. name changes are skipped)."""
        entry = _FakeEntry(data={CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.bday"})
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        cb(_make_event("update", "sensor.bday", changes={"name": "old name"}))

        hass.config_entries.async_update_entry.assert_not_called()


# ---------------------------------------------------------------------------
# Delete (action="remove")
# ---------------------------------------------------------------------------

class TestEntityDelete:
    """Repairs issue is created when a source entity is removed."""

    def test_delete_milestone_entity_creates_repair(self):
        entry = _FakeEntry(
            entry_id="abc123", title="My Birthday",
            data={CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.bday"},
        )
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        with patch(PATCH_CREATE) as mock_create:
            cb(_make_event("remove", "sensor.bday"))

        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        assert kwargs["translation_key"] == "entity_source_deleted"
        assert kwargs["is_fixable"] is False
        assert kwargs["translation_placeholders"]["name"] == "My Birthday"
        assert kwargs["translation_placeholders"]["entity_id"] == "sensor.bday"

    def test_delete_uses_correct_issue_id(self):
        entry = _FakeEntry(
            entry_id="uniquekey",
            data={CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.bday"},
        )
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        with patch(PATCH_CREATE) as mock_create:
            cb(_make_event("remove", "sensor.bday"))

        positional = mock_create.call_args[0]
        assert positional[2] == "entity_deleted_uniquekey"

    def test_delete_non_source_entity_no_repair(self):
        entry = _FakeEntry(data={CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.bday"})
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        with patch(PATCH_CREATE) as mock_create:
            cb(_make_event("remove", "sensor.unrelated"))

        mock_create.assert_not_called()

    def test_delete_trip_start_entity_creates_repair(self):
        entry = _FakeEntry(
            entry_id="trip1", title="My Trip",
            data={
                CONF_START_DATE_USE_ENTITY: True, CONF_START_DATE_ENTITY_ID: "sensor.dep",
                CONF_END_DATE_USE_ENTITY: True, CONF_END_DATE_ENTITY_ID: "sensor.ret",
            },
        )
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        with patch(PATCH_CREATE) as mock_create:
            cb(_make_event("remove", "sensor.dep"))

        mock_create.assert_called_once()
        assert mock_create.call_args[1]["translation_placeholders"]["entity_id"] == "sensor.dep"


# ---------------------------------------------------------------------------
# Create / restore (action="create")
# ---------------------------------------------------------------------------

class TestEntityCreate:
    """Repairs issue is auto-resolved when source entity comes back."""

    def test_restore_source_entity_deletes_repair(self):
        entry = _FakeEntry(
            entry_id="abc123",
            data={CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.bday"},
        )
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        with patch(PATCH_DELETE) as mock_delete:
            cb(_make_event("create", "sensor.bday"))

        mock_delete.assert_called_once_with(hass, DOMAIN, "entity_deleted_abc123")

    def test_restore_source_entity_triggers_coordinator_refresh(self):
        entry = _FakeEntry(
            entry_id="abc123",
            data={CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.bday"},
        )
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        with patch(PATCH_DELETE):
            cb(_make_event("create", "sensor.bday"))

        hass.async_create_task.assert_called_once()

    def test_create_non_source_entity_no_effect(self):
        entry = _FakeEntry(data={CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.bday"})
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        with patch(PATCH_DELETE) as mock_delete:
            cb(_make_event("create", "sensor.unrelated"))

        mock_delete.assert_not_called()
        hass.async_create_task.assert_not_called()


# ---------------------------------------------------------------------------
# Auto-migration data correctness
# ---------------------------------------------------------------------------

class TestAutoMigrate:
    """Config entry data is correctly updated on rename, preserving all other fields."""

    def test_migrated_data_preserves_other_fields(self):
        entry = _FakeEntry(data={
            CONF_EVENT_DATE_USE_ENTITY: True,
            CONF_EVENT_DATE_ENTITY_ID: "sensor.old",
            "event_type": "milestone",
            "other_field": "preserved",
        })
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        cb(_make_event("update", "sensor.new", changes={"entity_id": "sensor.old"}))

        new_data = hass.config_entries.async_update_entry.call_args[1]["data"]
        assert new_data["event_type"] == "milestone"
        assert new_data["other_field"] == "preserved"
        assert new_data[CONF_EVENT_DATE_ENTITY_ID] == "sensor.new"

    def test_async_update_entry_receives_entry_reference(self):
        """async_update_entry is called with the correct entry object."""
        entry = _FakeEntry(data={CONF_EVENT_DATE_USE_ENTITY: True, CONF_EVENT_DATE_ENTITY_ID: "sensor.old"})
        hass = _FakeHass(entry.entry_id)
        cb = _setup_and_get_callback(hass, entry)

        cb(_make_event("update", "sensor.new", changes={"entity_id": "sensor.old"}))

        call_positional = hass.config_entries.async_update_entry.call_args[0]
        assert call_positional[0] is entry
