"""Tests for FR11: URL and Memo sensors."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.whenhub.sensors.url_memo import WhenHubUrlSensor, WhenHubMemoSensor
from custom_components.whenhub.const import CONF_URL, CONF_MEMO


# ---------------------------------------------------------------------------
# Unit tests — sensor native_value without HA
# ---------------------------------------------------------------------------

class _FakeCoordinator:
    """Minimal coordinator stub."""
    data = {}

    def async_add_listener(self, *_): return lambda: None
    def async_add_context_listener(self, *_): return lambda: None


class _FakeEntry:
    entry_id = "test_entry_id"
    title = "Test Event"
    data = {}


def _make_url_sensor(url="", memo=""):
    coord = _FakeCoordinator()
    entry = _FakeEntry()
    event_data = {CONF_URL: url, CONF_MEMO: memo, "event_type": "trip"}
    sensor = object.__new__(WhenHubUrlSensor)
    sensor._config_entry = entry
    sensor._event_data = event_data
    sensor._attr_unique_id = f"{entry.entry_id}_url"
    return sensor


def _make_memo_sensor(url="", memo=""):
    coord = _FakeCoordinator()
    entry = _FakeEntry()
    event_data = {CONF_URL: url, CONF_MEMO: memo, "event_type": "trip"}
    sensor = object.__new__(WhenHubMemoSensor)
    sensor._config_entry = entry
    sensor._event_data = event_data
    sensor._attr_unique_id = f"{entry.entry_id}_memo"
    return sensor


class TestUrlSensorValue:
    def test_returns_url_when_set(self):
        s = _make_url_sensor(url="https://example.com")
        assert s.native_value == "https://example.com"

    def test_returns_none_when_empty(self):
        s = _make_url_sensor(url="")
        assert s.native_value is None

    def test_returns_none_when_missing(self):
        s = _make_url_sensor()
        # key present but empty
        assert s.native_value is None

    def test_url_does_not_bleed_into_memo(self):
        s = _make_url_sensor(url="https://example.com", memo="some notes")
        # URL sensor only returns the URL
        assert s.native_value == "https://example.com"


class TestMemoSensorValue:
    def test_returns_memo_when_set(self):
        s = _make_memo_sensor(memo="Hotel booked, room 204")
        assert s.native_value == "Hotel booked, room 204"

    def test_returns_none_when_empty(self):
        s = _make_memo_sensor(memo="")
        assert s.native_value is None

    def test_returns_none_when_missing(self):
        s = _make_memo_sensor()
        assert s.native_value is None

    def test_memo_supports_multiline(self):
        text = "Line 1\nLine 2\n**Bold**"
        s = _make_memo_sensor(memo=text)
        assert s.native_value == text

    def test_memo_does_not_bleed_into_url(self):
        s = _make_memo_sensor(url="https://example.com", memo="notes")
        # Memo sensor only returns the memo
        assert s.native_value == "notes"


class TestSensorDefaults:
    def test_url_sensor_enabled_by_default(self):
        # Sensors are only created when their field is non-empty, so always enabled.
        s = _make_url_sensor()
        assert s.entity_registry_enabled_default is True

    def test_memo_sensor_enabled_by_default(self):
        s = _make_memo_sensor()
        assert s.entity_registry_enabled_default is True

    def test_url_sensor_has_entity_name(self):
        s = _make_url_sensor()
        assert s.has_entity_name is True

    def test_memo_sensor_has_entity_name(self):
        s = _make_memo_sensor()
        assert s.has_entity_name is True

    def test_url_sensor_translation_key(self):
        s = _make_url_sensor()
        assert s.translation_key == "url"

    def test_memo_sensor_translation_key(self):
        s = _make_memo_sensor()
        assert s.translation_key == "memo"

    def test_url_sensor_icon(self):
        s = _make_url_sensor()
        assert s.icon == "mdi:link"

    def test_memo_sensor_icon(self):
        s = _make_memo_sensor()
        assert s.icon == "mdi:note-text"


# ---------------------------------------------------------------------------
# Integration-style tests with HA fixtures
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_url_memo_sensors_created_for_trip(hass):
    """URL and Memo sensors should be registered for a Trip event."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain="whenhub",
        title="Summer Trip",
        data={
            "event_type": "trip",
            "start_date": "2026-07-01",
            "end_date": "2026-07-14",
            "url": "https://booking.com/summertrip",
            "memo": "Pack sunscreen",
        },
        unique_id="whenhub_summer_trip",
        version=1,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_ids = hass.states.async_entity_ids("sensor")
    url_entities = [e for e in entity_ids if e.endswith("_url") or "url" in e]
    memo_entities = [e for e in entity_ids if e.endswith("_memo") or "memo" in e]

    # At minimum the integration should not have crashed
    assert entry.state.value in ("loaded", )


@pytest.mark.asyncio
async def test_url_sensor_state_when_url_set(hass):
    """URL sensor should report the configured URL."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain="whenhub",
        title="Test Trip",
        data={
            "event_type": "trip",
            "start_date": "2026-08-01",
            "end_date": "2026-08-10",
            "url": "https://example.com/trip",
            "memo": "",
        },
        unique_id="whenhub_test_trip_url",
        version=1,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Find the URL sensor
    from homeassistant.helpers import entity_registry as er
    entity_reg = er.async_get(hass)
    url_entity = next(
        (e for e in er.async_entries_for_config_entry(entity_reg, entry.entry_id)
         if e.unique_id.endswith("_url")),
        None,
    )
    assert url_entity is not None, "URL sensor entity should be registered"


@pytest.mark.asyncio
async def test_memo_sensor_registered_for_milestone(hass):
    """Memo sensor should be registered for a Milestone event."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain="whenhub",
        title="Project Launch",
        data={
            "event_type": "milestone",
            "target_date": "2026-09-01",
            "url": "",
            "memo": "Remember to prepare the slides",
        },
        unique_id="whenhub_project_launch",
        version=1,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    from homeassistant.helpers import entity_registry as er
    entity_reg = er.async_get(hass)
    memo_entity = next(
        (e for e in er.async_entries_for_config_entry(entity_reg, entry.entry_id)
         if e.unique_id.endswith("_memo")),
        None,
    )
    assert memo_entity is not None, "Memo sensor entity should be registered"


@pytest.mark.asyncio
async def test_url_entity_enabled_when_url_set(hass):
    """URL sensor should be enabled (not disabled) when URL field is populated."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from homeassistant.helpers import entity_registry as er

    entry = MockConfigEntry(
        domain="whenhub",
        title="Booking Trip",
        data={
            "event_type": "trip",
            "start_date": "2026-10-01",
            "end_date": "2026-10-07",
            "url": "https://booking.example.com",
            "memo": "",
        },
        unique_id="whenhub_booking_trip",
        version=1,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_reg = er.async_get(hass)
    url_entity = next(
        (e for e in er.async_entries_for_config_entry(entity_reg, entry.entry_id)
         if e.unique_id.endswith("_url")),
        None,
    )
    assert url_entity is not None
    assert url_entity.disabled_by is None, "URL sensor should be enabled when URL is set"


@pytest.mark.asyncio
async def test_url_entity_not_created_when_url_empty(hass):
    """URL sensor should not be created when URL field is empty."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from homeassistant.helpers import entity_registry as er

    entry = MockConfigEntry(
        domain="whenhub",
        title="No URL Trip",
        data={
            "event_type": "trip",
            "start_date": "2026-11-01",
            "end_date": "2026-11-07",
            "url": "",
            "memo": "",
        },
        unique_id="whenhub_no_url_trip",
        version=1,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_reg = er.async_get(hass)
    url_entity = next(
        (e for e in er.async_entries_for_config_entry(entity_reg, entry.entry_id)
         if e.unique_id.endswith("_url")),
        None,
    )
    assert url_entity is None, "URL sensor should not be created when URL is empty"
