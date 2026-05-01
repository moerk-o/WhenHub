"""Tests for FR9: Entity as date source.

Tests:
- WhenHubCoordinator._parse_entity_date() — unit tests with stubs
- WhenHubCoordinator._resolve_date() — unit tests with stubs
- Config flow routing when entity checkboxes are checked
- Options flow routing when switching to entity source
"""
from __future__ import annotations

import sys
import os
from datetime import date
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from custom_components.whenhub.const import (
    DOMAIN,
    CONF_TARGET_DATE,
    CONF_START_DATE,
    CONF_END_DATE,
    CONF_EVENT_DATE_USE_ENTITY,
    CONF_EVENT_DATE_ENTITY_ID,
    CONF_START_DATE_USE_ENTITY,
    CONF_START_DATE_ENTITY_ID,
    CONF_END_DATE_USE_ENTITY,
    CONF_END_DATE_ENTITY_ID,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
)


# ---------------------------------------------------------------------------
# Stubs for unit tests (no full HA runtime needed)
# ---------------------------------------------------------------------------

class _FakeHass:
    """Minimal hass stub with a controllable state store."""

    def __init__(self):
        self._states: dict = {}

    def set_state(self, entity_id: str, state_value: str, attributes: dict | None = None) -> None:
        mock_state = MagicMock()
        mock_state.state = state_value
        mock_state.attributes = attributes or {}
        self._states[entity_id] = mock_state

    @property
    def states(self):
        store = self._states
        mock = MagicMock()
        mock.get = lambda eid: store.get(eid)
        return mock


class _FakeConfigEntry:
    def __init__(self, entry_id: str = "test_id", title: str = "Test Event"):
        self.entry_id = entry_id
        self.title = title


def _make_coordinator(event_type: str, event_data: dict, hass: _FakeHass | None = None):
    """Create a WhenHubCoordinator bypassing __init__."""
    from custom_components.whenhub.coordinator import WhenHubCoordinator

    coord = object.__new__(WhenHubCoordinator)
    coord.hass = hass or _FakeHass()
    coord.config_entry = _FakeConfigEntry()
    coord.event_type = event_type
    coord.event_data = event_data
    return coord


# ---------------------------------------------------------------------------
# Tests for _parse_entity_date
# ---------------------------------------------------------------------------

class TestParseEntityDate:
    """Unit tests for WhenHubCoordinator._parse_entity_date()."""

    def _make_state(self, state_value: str, device_class: str | None = None) -> MagicMock:
        mock = MagicMock()
        mock.state = state_value
        mock.attributes = {"device_class": device_class} if device_class else {}
        return mock

    def test_date_device_class_returns_correct_date(self):
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, {})
        state = self._make_state("2026-06-15", device_class="date")
        assert coord._parse_entity_date(state) == date(2026, 6, 15)

    def test_date_device_class_invalid_string_returns_none(self):
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, {})
        state = self._make_state("not-a-date", device_class="date")
        assert coord._parse_entity_date(state) is None

    def test_timestamp_device_class_returns_a_date(self):
        """Timestamp entities return a date (exact value is timezone-dependent)."""
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, {})
        state = self._make_state("2026-07-20T10:00:00+00:00", device_class="timestamp")
        result = coord._parse_entity_date(state)
        assert isinstance(result, date)

    def test_timestamp_device_class_unparseable_returns_none(self):
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, {})
        state = self._make_state("not-a-timestamp", device_class="timestamp")
        assert coord._parse_entity_date(state) is None

    def test_no_device_class_falls_back_to_date_parse(self):
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, {})
        state = self._make_state("2026-12-25")  # no device_class attribute
        assert coord._parse_entity_date(state) == date(2026, 12, 25)

    def test_no_device_class_invalid_string_returns_none(self):
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, {})
        state = self._make_state("invalid")
        assert coord._parse_entity_date(state) is None

    def test_different_dates_return_correctly(self):
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, {})
        for date_str, expected in [
            ("2024-02-29", date(2024, 2, 29)),   # leap year
            ("2000-01-01", date(2000, 1, 1)),
            ("2099-12-31", date(2099, 12, 31)),
        ]:
            state = self._make_state(date_str, device_class="date")
            assert coord._parse_entity_date(state) == expected


# ---------------------------------------------------------------------------
# Tests for _resolve_date
# ---------------------------------------------------------------------------

class TestResolveDate:
    """Unit tests for WhenHubCoordinator._resolve_date()."""

    def test_manual_mode_returns_configured_date(self):
        data = {CONF_TARGET_DATE: "2026-09-01"}
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data)
        result = coord._resolve_date(
            CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
        )
        assert result == date(2026, 9, 1)

    def test_manual_mode_empty_date_raises_update_failed(self):
        from homeassistant.helpers.update_coordinator import UpdateFailed
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, {CONF_TARGET_DATE: ""})
        with pytest.raises(UpdateFailed):
            coord._resolve_date(
                CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
            )

    def test_manual_mode_missing_key_raises_update_failed(self):
        from homeassistant.helpers.update_coordinator import UpdateFailed
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, {})
        with pytest.raises(UpdateFailed):
            coord._resolve_date(
                CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
            )

    def test_entity_mode_date_entity_returns_correct_date(self):
        hass = _FakeHass()
        hass.set_state("sensor.my_date", "2026-10-01", {"device_class": "date"})
        data = {
            CONF_EVENT_DATE_USE_ENTITY: True,
            CONF_EVENT_DATE_ENTITY_ID: "sensor.my_date",
        }
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data, hass)
        result = coord._resolve_date(
            CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
        )
        assert result == date(2026, 10, 1)

    def test_entity_mode_timestamp_entity_returns_a_date(self):
        hass = _FakeHass()
        hass.set_state("sensor.ts", "2026-10-15T00:00:00+00:00", {"device_class": "timestamp"})
        data = {
            CONF_EVENT_DATE_USE_ENTITY: True,
            CONF_EVENT_DATE_ENTITY_ID: "sensor.ts",
        }
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data, hass)
        result = coord._resolve_date(
            CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
        )
        assert isinstance(result, date)

    def test_entity_mode_no_entity_id_configured_raises_update_failed(self):
        from homeassistant.helpers.update_coordinator import UpdateFailed
        data = {CONF_EVENT_DATE_USE_ENTITY: True}  # no entity_id key
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data)
        with pytest.raises(UpdateFailed):
            coord._resolve_date(
                CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
            )

    def test_entity_mode_entity_not_in_hass_raises_update_failed(self):
        from homeassistant.helpers.update_coordinator import UpdateFailed
        data = {
            CONF_EVENT_DATE_USE_ENTITY: True,
            CONF_EVENT_DATE_ENTITY_ID: "sensor.does_not_exist",
        }
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data)  # empty hass
        with pytest.raises(UpdateFailed):
            coord._resolve_date(
                CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
            )

    def test_entity_mode_unavailable_state_raises_update_failed(self):
        from homeassistant.helpers.update_coordinator import UpdateFailed
        hass = _FakeHass()
        hass.set_state("sensor.date", "unavailable", {"device_class": "date"})
        data = {
            CONF_EVENT_DATE_USE_ENTITY: True,
            CONF_EVENT_DATE_ENTITY_ID: "sensor.date",
        }
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data, hass)
        with pytest.raises(UpdateFailed):
            coord._resolve_date(
                CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
            )

    def test_entity_mode_unknown_state_raises_update_failed(self):
        from homeassistant.helpers.update_coordinator import UpdateFailed
        hass = _FakeHass()
        hass.set_state("sensor.date", "unknown", {"device_class": "date"})
        data = {
            CONF_EVENT_DATE_USE_ENTITY: True,
            CONF_EVENT_DATE_ENTITY_ID: "sensor.date",
        }
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data, hass)
        with pytest.raises(UpdateFailed):
            coord._resolve_date(
                CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
            )

    def test_entity_mode_unparseable_state_raises_update_failed(self):
        from homeassistant.helpers.update_coordinator import UpdateFailed
        hass = _FakeHass()
        hass.set_state("sensor.date", "not-a-date", {"device_class": "date"})
        data = {
            CONF_EVENT_DATE_USE_ENTITY: True,
            CONF_EVENT_DATE_ENTITY_ID: "sensor.date",
        }
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data, hass)
        with pytest.raises(UpdateFailed):
            coord._resolve_date(
                CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
            )

    def test_trip_start_date_via_entity(self):
        hass = _FakeHass()
        hass.set_state("sensor.start", "2026-08-01", {"device_class": "date"})
        data = {
            CONF_START_DATE_USE_ENTITY: True,
            CONF_START_DATE_ENTITY_ID: "sensor.start",
        }
        coord = _make_coordinator(EVENT_TYPE_TRIP, data, hass)
        result = coord._resolve_date(
            CONF_START_DATE, CONF_START_DATE_USE_ENTITY, CONF_START_DATE_ENTITY_ID
        )
        assert result == date(2026, 8, 1)

    def test_trip_end_date_via_entity(self):
        hass = _FakeHass()
        hass.set_state("sensor.end", "2026-08-15", {"device_class": "date"})
        data = {
            CONF_END_DATE_USE_ENTITY: True,
            CONF_END_DATE_ENTITY_ID: "sensor.end",
        }
        coord = _make_coordinator(EVENT_TYPE_TRIP, data, hass)
        result = coord._resolve_date(
            CONF_END_DATE, CONF_END_DATE_USE_ENTITY, CONF_END_DATE_ENTITY_ID
        )
        assert result == date(2026, 8, 15)

    def test_manual_mode_explicit_false_uses_manual_date(self):
        """Explicit use_entity=False must fall through to manual date, not entity."""
        hass = _FakeHass()
        hass.set_state("sensor.ignored", "2099-01-01", {"device_class": "date"})
        data = {
            CONF_EVENT_DATE_USE_ENTITY: False,
            CONF_EVENT_DATE_ENTITY_ID: "sensor.ignored",
            CONF_TARGET_DATE: "2026-03-15",
        }
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data, hass)
        result = coord._resolve_date(
            CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
        )
        assert result == date(2026, 3, 15)


# ---------------------------------------------------------------------------
# Config flow routing tests (require full HA runtime)
# ---------------------------------------------------------------------------

class TestConfigFlowEntityRouting:
    """Test that entity checkboxes correctly route the config flow."""

    @pytest.mark.asyncio
    async def test_trip_no_entity_creates_entry_directly(self, hass):
        """Trip without entity checkboxes creates entry without extra steps."""
        from homeassistant.data_entry_flow import FlowResultType

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"event_type": "trip"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "start_date": "2026-08-01",
                "end_date": "2026-08-15",
                "start_date_use_entity": False,
                "end_date_use_entity": False,
                "image_path": "",
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["start_date"] == "2026-08-01"
        assert result["data"].get("start_date_use_entity") is False

    @pytest.mark.asyncio
    async def test_trip_start_entity_routes_to_start_entity_step(self, hass):
        """start_date_use_entity=True routes to trip_start_entity step."""
        from homeassistant.data_entry_flow import FlowResultType

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"event_type": "trip"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "start_date": "2026-08-01",
                "end_date": "2026-08-15",
                "start_date_use_entity": True,
                "end_date_use_entity": False,
                "image_path": "",
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "trip_start_entity"

    @pytest.mark.asyncio
    async def test_trip_end_entity_only_routes_to_end_entity_step(self, hass):
        """end_date_use_entity=True (without start) routes to trip_end_entity step."""
        from homeassistant.data_entry_flow import FlowResultType

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"event_type": "trip"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "start_date": "2026-08-01",
                "end_date": "2026-08-15",
                "start_date_use_entity": False,
                "end_date_use_entity": True,
                "image_path": "",
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "trip_end_entity"

    @pytest.mark.asyncio
    async def test_trip_both_entities_start_entity_step_shown_first(self, hass):
        """Both entity checkboxes → trip_start_entity step shown first."""
        from homeassistant.data_entry_flow import FlowResultType

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"event_type": "trip"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "start_date": "2026-08-01",
                "end_date": "2026-08-15",
                "start_date_use_entity": True,
                "end_date_use_entity": True,
                "image_path": "",
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "trip_start_entity"

    @pytest.mark.asyncio
    async def test_trip_both_entities_full_flow_creates_entry(self, hass):
        """Both entity checkboxes → start entity → end entity → entry created."""
        from homeassistant.data_entry_flow import FlowResultType

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"event_type": "trip"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "start_date": "2026-08-01",
                "end_date": "2026-08-15",
                "start_date_use_entity": True,
                "end_date_use_entity": True,
                "image_path": "",
            },
        )
        assert result["step_id"] == "trip_start_entity"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"start_date_entity_id": "sensor.trip_start"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "trip_end_entity"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"end_date_entity_id": "sensor.trip_end"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["start_date_use_entity"] is True
        assert result["data"]["end_date_use_entity"] is True
        assert result["data"]["start_date_entity_id"] == "sensor.trip_start"
        assert result["data"]["end_date_entity_id"] == "sensor.trip_end"

    @pytest.mark.asyncio
    async def test_trip_start_entity_only_full_flow(self, hass):
        """Start entity only → start entity step → entry (no end entity step)."""
        from homeassistant.data_entry_flow import FlowResultType

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"event_type": "trip"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "start_date": "2026-08-01",
                "end_date": "2026-08-15",
                "start_date_use_entity": True,
                "end_date_use_entity": False,
                "image_path": "",
            },
        )
        assert result["step_id"] == "trip_start_entity"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"start_date_entity_id": "sensor.trip_start"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["start_date_use_entity"] is True
        assert result["data"]["start_date_entity_id"] == "sensor.trip_start"
        assert result["data"].get("end_date_use_entity") is False

    @pytest.mark.asyncio
    async def test_milestone_entity_checkbox_routes_to_entity_step(self, hass):
        """Milestone event_date_use_entity routes to milestone_entity step."""
        from homeassistant.data_entry_flow import FlowResultType

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"event_type": "milestone"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "target_date": "2026-12-31",
                "event_date_use_entity": True,
                "image_path": "",
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "milestone_entity"

    @pytest.mark.asyncio
    async def test_milestone_entity_full_flow_creates_entry(self, hass):
        """Milestone entity checkbox → entity step → entry created."""
        from homeassistant.data_entry_flow import FlowResultType

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"event_type": "milestone"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "target_date": "2026-12-31",
                "event_date_use_entity": True,
                "image_path": "",
            },
        )
        assert result["step_id"] == "milestone_entity"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_date_entity_id": "input_datetime.my_milestone"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["event_date_use_entity"] is True
        assert result["data"]["event_date_entity_id"] == "input_datetime.my_milestone"

    @pytest.mark.asyncio
    async def test_milestone_no_entity_creates_entry_directly(self, hass):
        """Milestone without entity checkbox creates entry without extra step."""
        from homeassistant.data_entry_flow import FlowResultType

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"event_type": "milestone"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "target_date": "2026-12-31",
                "event_date_use_entity": False,
                "image_path": "",
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["target_date"] == "2026-12-31"

    @pytest.mark.asyncio
    async def test_anniversary_entity_checkbox_routes_to_entity_step(self, hass):
        """Anniversary event_date_use_entity routes to anniversary_entity step."""
        from homeassistant.data_entry_flow import FlowResultType

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"event_type": "anniversary"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "target_date": "2010-05-20",
                "event_date_use_entity": True,
                "image_path": "",
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "anniversary_entity"

    @pytest.mark.asyncio
    async def test_anniversary_entity_full_flow_creates_entry(self, hass):
        """Anniversary entity checkbox → entity step → entry created."""
        from homeassistant.data_entry_flow import FlowResultType

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"event_type": "anniversary"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "target_date": "2010-05-20",
                "event_date_use_entity": True,
                "image_path": "",
            },
        )
        assert result["step_id"] == "anniversary_entity"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_date_entity_id": "sensor.birthday_date"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["event_date_use_entity"] is True
        assert result["data"]["event_date_entity_id"] == "sensor.birthday_date"


# ---------------------------------------------------------------------------
# Options flow routing tests (require full HA runtime)
# ---------------------------------------------------------------------------

class TestOptionsFlowEntityRouting:
    """Test options flow routing when enabling entity source."""

    @pytest.mark.asyncio
    async def test_trip_options_no_entity_finishes_directly(self, hass):
        """Trip options without entity checkboxes finishes without extra steps."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry
        from homeassistant.data_entry_flow import FlowResultType

        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "event_type": "trip",
                "start_date": "2026-07-01",
                "end_date": "2026-07-15",
                "image_path": "",
            },
            title="Test Trip",
            version=2,
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "start_date": "2026-08-01",
                "end_date": "2026-08-15",
                "start_date_use_entity": False,
                "end_date_use_entity": False,
                "image_path": "",
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_trip_options_start_entity_routes_to_entity_step(self, hass):
        """Trip options: enabling start entity routes to trip_start_entity_options."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry
        from homeassistant.data_entry_flow import FlowResultType

        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "event_type": "trip",
                "start_date": "2026-07-01",
                "end_date": "2026-07-15",
                "image_path": "",
            },
            title="Test Trip",
            version=2,
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["step_id"] == "trip_options"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "start_date": "2026-07-01",
                "end_date": "2026-07-15",
                "start_date_use_entity": True,
                "end_date_use_entity": False,
                "image_path": "",
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "trip_start_entity_options"

    @pytest.mark.asyncio
    async def test_trip_options_both_entities_full_flow(self, hass):
        """Trip options: both entity checkboxes → start entity → end entity → done."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry
        from homeassistant.data_entry_flow import FlowResultType

        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "event_type": "trip",
                "start_date": "2026-07-01",
                "end_date": "2026-07-15",
                "image_path": "",
            },
            title="Test Trip",
            version=2,
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "start_date": "2026-07-01",
                "end_date": "2026-07-15",
                "start_date_use_entity": True,
                "end_date_use_entity": True,
                "image_path": "",
            },
        )
        assert result["step_id"] == "trip_start_entity_options"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"start_date_entity_id": "sensor.trip_start"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "trip_end_entity_options"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"end_date_entity_id": "sensor.trip_end"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_milestone_options_entity_routes_to_entity_step(self, hass):
        """Milestone options: enabling entity checkbox routes to milestone_entity_options."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry
        from homeassistant.data_entry_flow import FlowResultType

        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "event_type": "milestone",
                "target_date": "2026-12-31",
                "image_path": "",
            },
            title="Test Milestone",
            version=2,
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["step_id"] == "milestone_options"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "target_date": "2026-12-31",
                "event_date_use_entity": True,
                "image_path": "",
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "milestone_entity_options"

    @pytest.mark.asyncio
    async def test_milestone_options_entity_full_flow(self, hass):
        """Milestone options: entity step → finalize."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry
        from homeassistant.data_entry_flow import FlowResultType

        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "event_type": "milestone",
                "target_date": "2026-12-31",
                "image_path": "",
            },
            title="Test Milestone",
            version=2,
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "target_date": "2026-12-31",
                "event_date_use_entity": True,
                "image_path": "",
            },
        )
        assert result["step_id"] == "milestone_entity_options"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"event_date_entity_id": "input_datetime.my_date"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_anniversary_options_entity_routes_to_entity_step(self, hass):
        """Anniversary options: enabling entity checkbox routes to anniversary_entity_options."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry
        from homeassistant.data_entry_flow import FlowResultType

        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "event_type": "anniversary",
                "target_date": "2010-05-20",
                "image_path": "",
            },
            title="Test Anniversary",
            version=2,
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["step_id"] == "anniversary_options"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "target_date": "2010-05-20",
                "event_date_use_entity": True,
                "image_path": "",
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "anniversary_entity_options"
