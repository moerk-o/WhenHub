"""Test that entity IDs are always language-independent (English type keys).

Since v3.0.0, suggested_object_id ensures entity IDs always use the English
sensor type key as suffix, regardless of the HA system language.
"""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry


def create_trip_entry(suffix: str = ""):
    """Create a trip config entry for testing."""
    return MockConfigEntry(
        domain="whenhub",
        title=f"Sprachtest{suffix}",
        data={
            "event_type": "trip",
            "event_name": f"Sprachtest{suffix}",
            "start_date": "2026-07-12",
            "end_date": "2026-07-26",
            "image_path": "",
        },
        unique_id=f"whenhub_sprachtest{suffix}",
        version=2,
    )


@pytest.mark.asyncio
async def test_entity_id_english_system_uses_english_keys(hass: HomeAssistant):
    """English system: entity IDs use English type keys."""
    hass.config.language = "en"

    assert await async_setup_component(hass, "whenhub", {})
    await hass.async_block_till_done()

    entry = create_trip_entry("_en")
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    sensor_ids = [s.entity_id for s in hass.states.async_all() if s.entity_id.startswith("sensor.")]

    assert any("days_until" in eid for eid in sensor_ids), \
        f"Expected 'days_until' in entity IDs, got: {sensor_ids}"
    assert not any("days_until_start" in eid for eid in sensor_ids), \
        f"Should not have old 'days_until_start' suffix: {sensor_ids}"
    assert not any("tage_bis" in eid for eid in sensor_ids), \
        f"Should not have German suffixes: {sensor_ids}"


@pytest.mark.asyncio
async def test_entity_id_german_system_uses_english_keys(hass: HomeAssistant):
    """German system: entity IDs must still use English type keys (not German)."""
    hass.config.language = "de"

    assert await async_setup_component(hass, "whenhub", {})
    await hass.async_block_till_done()

    entry = create_trip_entry("_de")
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    sensor_ids = [s.entity_id for s in hass.states.async_all() if s.entity_id.startswith("sensor.")]

    assert any("days_until" in eid for eid in sensor_ids), \
        f"Expected English 'days_until' even on German HA, got: {sensor_ids}"
    assert not any("tage_bis" in eid for eid in sensor_ids), \
        f"German HA must not produce German entity IDs: {sensor_ids}"
    assert not any("tage_seit" in eid for eid in sensor_ids), \
        f"German HA must not produce German entity IDs: {sensor_ids}"
