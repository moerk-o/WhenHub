"""Tests for async_migrate_entry (config entry version 1 → 2).

Verifies that entity IDs are renamed to English type-key suffixes on upgrade,
that installations with already-correct IDs are left untouched, and that
calendar entries are migrated without touching the entity registry.
"""
from __future__ import annotations

import sys
import os
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from custom_components.whenhub import async_migrate_entry
from custom_components.whenhub.const import CONF_ENTRY_TYPE, ENTRY_TYPE_CALENDAR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(entry_id="abc123", title="Johns Birthday", version=1, entry_type=None):
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.title = title
    entry.version = version
    data = {}
    if entry_type is not None:
        data[CONF_ENTRY_TYPE] = entry_type
    entry.data = data
    return entry


def _make_entity(entity_id, unique_id, domain):
    e = MagicMock()
    e.entity_id = entity_id
    e.unique_id = unique_id
    e.domain = domain
    return e


@contextmanager
def _patch_registry(entities, registry_lookup=None):
    """Patch er.async_get and er.async_entries_for_config_entry."""
    registry = MagicMock()
    registry.async_get.side_effect = lambda eid: (registry_lookup or {}).get(eid)

    with patch("custom_components.whenhub.er.async_get", return_value=registry), \
         patch("custom_components.whenhub.er.async_entries_for_config_entry", return_value=entities):
        yield registry


# ---------------------------------------------------------------------------
# Version 1 → 2: German installation
# ---------------------------------------------------------------------------

class TestMigrationV1ToV2German:

    @pytest.mark.asyncio
    async def test_event_date_renamed(self):
        entry = _make_entry(entry_id="abc123", title="Johns Geburtstag")
        entities = [_make_entity("sensor.johns_geburtstag_ereignisdatum", "abc123_event_date", "sensor")]
        hass = MagicMock()

        with _patch_registry(entities) as reg:
            result = await async_migrate_entry(hass, entry)

        assert result is True
        reg.async_update_entity.assert_called_once_with(
            "sensor.johns_geburtstag_ereignisdatum",
            new_entity_id="sensor.johns_geburtstag_event_date",
        )
        hass.config_entries.async_update_entry.assert_called_once_with(entry, version=2)

    @pytest.mark.asyncio
    async def test_binary_sensor_renamed(self):
        entry = _make_entry(entry_id="abc123", title="Johns Geburtstag")
        entities = [_make_entity("binary_sensor.johns_geburtstag_ist_heute", "abc123_binary_is_today", "binary_sensor")]
        hass = MagicMock()

        with _patch_registry(entities) as reg:
            result = await async_migrate_entry(hass, entry)

        assert result is True
        reg.async_update_entity.assert_called_once_with(
            "binary_sensor.johns_geburtstag_ist_heute",
            new_entity_id="binary_sensor.johns_geburtstag_is_today",
        )

    @pytest.mark.asyncio
    async def test_image_entity_renamed(self):
        entry = _make_entry(entry_id="abc123", title="Johns Geburtstag")
        entities = [_make_entity("image.johns_geburtstag_ereignisbild", "abc123_image", "image")]
        hass = MagicMock()

        with _patch_registry(entities) as reg:
            result = await async_migrate_entry(hass, entry)

        assert result is True
        reg.async_update_entity.assert_called_once_with(
            "image.johns_geburtstag_ereignisbild",
            new_entity_id="image.johns_geburtstag_event_image",
        )

    @pytest.mark.asyncio
    async def test_multiple_entities_all_renamed(self):
        entry = _make_entry(entry_id="abc123", title="Johns Geburtstag")
        entities = [
            _make_entity("sensor.johns_geburtstag_tage_bis_nachster", "abc123_days_until_next", "sensor"),
            _make_entity("sensor.johns_geburtstag_tage_seit_letzter", "abc123_days_since_last", "sensor"),
            _make_entity("binary_sensor.johns_geburtstag_ist_heute", "abc123_binary_is_today", "binary_sensor"),
            _make_entity("image.johns_geburtstag_ereignisbild", "abc123_image", "image"),
        ]
        hass = MagicMock()

        with _patch_registry(entities) as reg:
            await async_migrate_entry(hass, entry)

        assert reg.async_update_entity.call_count == 4


# ---------------------------------------------------------------------------
# Version 1 → 2: English installation
# ---------------------------------------------------------------------------

class TestMigrationV1ToV2English:

    @pytest.mark.asyncio
    async def test_event_date_already_correct_not_renamed(self):
        entry = _make_entry(entry_id="abc123", title="Johns Birthday")
        entities = [_make_entity("sensor.johns_birthday_event_date", "abc123_event_date", "sensor")]
        hass = MagicMock()

        with _patch_registry(entities) as reg:
            await async_migrate_entry(hass, entry)

        reg.async_update_entity.assert_not_called()

    @pytest.mark.asyncio
    async def test_days_until_start_renamed_to_days_until(self):
        entry = _make_entry(entry_id="abc123", title="Denmark Vacation")
        entities = [_make_entity("sensor.denmark_vacation_days_until_start", "abc123_days_until", "sensor")]
        hass = MagicMock()

        with _patch_registry(entities) as reg:
            await async_migrate_entry(hass, entry)

        reg.async_update_entity.assert_called_once_with(
            "sensor.denmark_vacation_days_until_start",
            new_entity_id="sensor.denmark_vacation_days_until",
        )

    @pytest.mark.asyncio
    async def test_trip_days_remaining_renamed(self):
        entry = _make_entry(entry_id="abc123", title="Denmark Vacation")
        entities = [_make_entity("sensor.denmark_vacation_trip_days_remaining", "abc123_trip_left_days", "sensor")]
        hass = MagicMock()

        with _patch_registry(entities) as reg:
            await async_migrate_entry(hass, entry)

        reg.async_update_entity.assert_called_once_with(
            "sensor.denmark_vacation_trip_days_remaining",
            new_entity_id="sensor.denmark_vacation_trip_left_days",
        )

    @pytest.mark.asyncio
    async def test_trip_percent_remaining_renamed(self):
        entry = _make_entry(entry_id="abc123", title="Denmark Vacation")
        entities = [_make_entity("sensor.denmark_vacation_trip_percent_remaining", "abc123_trip_left_percent", "sensor")]
        hass = MagicMock()

        with _patch_registry(entities) as reg:
            await async_migrate_entry(hass, entry)

        reg.async_update_entity.assert_called_once_with(
            "sensor.denmark_vacation_trip_percent_remaining",
            new_entity_id="sensor.denmark_vacation_trip_left_percent",
        )

    @pytest.mark.asyncio
    async def test_dst_active_renamed(self):
        entry = _make_entry(entry_id="abc123", title="EU DST")
        entities = [
            _make_entity(
                "binary_sensor.eu_dst_daylight_saving_time_active",
                "abc123_binary_is_dst_active",
                "binary_sensor",
            )
        ]
        hass = MagicMock()

        with _patch_registry(entities) as reg:
            await async_migrate_entry(hass, entry)

        reg.async_update_entity.assert_called_once_with(
            "binary_sensor.eu_dst_daylight_saving_time_active",
            new_entity_id="binary_sensor.eu_dst_is_dst_active",
        )

    @pytest.mark.asyncio
    async def test_url_memo_already_correct(self):
        """URL and Memo suffixes are language-neutral — no rename needed."""
        entry = _make_entry(entry_id="abc123", title="Johns Birthday")
        entities = [
            _make_entity("sensor.johns_birthday_url", "abc123_url", "sensor"),
            _make_entity("sensor.johns_birthday_memo", "abc123_memo", "sensor"),
        ]
        hass = MagicMock()

        with _patch_registry(entities) as reg:
            await async_migrate_entry(hass, entry)

        reg.async_update_entity.assert_not_called()


# ---------------------------------------------------------------------------
# Calendar entries
# ---------------------------------------------------------------------------

class TestMigrationCalendarEntry:

    @pytest.mark.asyncio
    async def test_calendar_entry_version_bumped(self):
        entry = _make_entry(entry_id="cal1", title="WhenHub Calendar", entry_type=ENTRY_TYPE_CALENDAR)
        hass = MagicMock()

        result = await async_migrate_entry(hass, entry)

        assert result is True
        hass.config_entries.async_update_entry.assert_called_once_with(entry, version=2)

    @pytest.mark.asyncio
    async def test_calendar_entry_no_entity_registry_access(self):
        entry = _make_entry(entry_id="cal1", title="WhenHub Calendar", entry_type=ENTRY_TYPE_CALENDAR)
        hass = MagicMock()

        with patch("custom_components.whenhub.er.async_get") as mock_get, \
             patch("custom_components.whenhub.er.async_entries_for_config_entry") as mock_entries:
            await async_migrate_entry(hass, entry)
            mock_get.assert_not_called()
            mock_entries.assert_not_called()


# ---------------------------------------------------------------------------
# Conflict: target entity_id already occupied
# ---------------------------------------------------------------------------

class TestMigrationConflict:

    @pytest.mark.asyncio
    async def test_conflict_skips_rename(self):
        entry = _make_entry(entry_id="abc123", title="Johns Birthday")
        entities = [_make_entity("sensor.johns_birthday_ereignisdatum", "abc123_event_date", "sensor")]
        existing = MagicMock()
        hass = MagicMock()

        with _patch_registry(entities, registry_lookup={"sensor.johns_birthday_event_date": existing}) as reg:
            result = await async_migrate_entry(hass, entry)

        assert result is True
        reg.async_update_entity.assert_not_called()
        hass.config_entries.async_update_entry.assert_called_once_with(entry, version=2)


# ---------------------------------------------------------------------------
# Already migrated: version >= 2
# ---------------------------------------------------------------------------

class TestMigrationAlreadyMigrated:

    @pytest.mark.asyncio
    async def test_version_2_no_op(self):
        entry = _make_entry(version=2)
        hass = MagicMock()

        with patch("custom_components.whenhub.er.async_get") as mock_get, \
             patch("custom_components.whenhub.er.async_entries_for_config_entry") as mock_entries:
            result = await async_migrate_entry(hass, entry)

        assert result is True
        mock_get.assert_not_called()
        mock_entries.assert_not_called()
        hass.config_entries.async_update_entry.assert_not_called()
