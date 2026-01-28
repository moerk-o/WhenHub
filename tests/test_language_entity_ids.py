"""Test entity ID generation with different system languages."""
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
        version=1,
    )


@pytest.mark.asyncio
async def test_entity_id_with_english_language(hass: HomeAssistant):
    """Test that English system creates English entity IDs."""
    # Set system language to English
    hass.config.language = "en"

    # First load the component
    assert await async_setup_component(hass, "whenhub", {})
    await hass.async_block_till_done()

    entry = create_trip_entry("_en")
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Get all sensor entity IDs
    entity_ids = [state.entity_id for state in hass.states.async_all()]
    sensor_ids = [eid for eid in entity_ids if eid.startswith("sensor.")]

    print(f"\n{'='*60}")
    print(f"ENGLISH SYSTEM (hass.config.language = 'en')")
    print(f"{'='*60}")
    print(f"Sensor entity IDs:")
    for eid in sorted(sensor_ids):
        print(f"  - {eid}")

    # Check for English patterns based on translations/en.json
    # "days_until" -> "Days until start" -> "days_until_start"
    has_english = any("days_until_start" in eid for eid in sensor_ids)
    has_german = any("tage_bis_start" in eid for eid in sensor_ids)

    print(f"\nPattern check:")
    print(f"  Has English 'days_until_start': {has_english}")
    print(f"  Has German 'tage_bis_start': {has_german}")

    assert has_english, f"Expected English entity IDs, got: {sensor_ids}"
    assert not has_german, f"Should not have German entity IDs with English language"


@pytest.mark.asyncio
async def test_entity_id_with_german_language(hass: HomeAssistant):
    """Test that German system creates German entity IDs."""
    # Set system language to German
    hass.config.language = "de"

    # First load the component
    assert await async_setup_component(hass, "whenhub", {})
    await hass.async_block_till_done()

    entry = create_trip_entry("_de")
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Get all sensor entity IDs
    entity_ids = [state.entity_id for state in hass.states.async_all()]
    sensor_ids = [eid for eid in entity_ids if eid.startswith("sensor.")]

    print(f"\n{'='*60}")
    print(f"GERMAN SYSTEM (hass.config.language = 'de')")
    print(f"{'='*60}")
    print(f"Sensor entity IDs:")
    for eid in sorted(sensor_ids):
        print(f"  - {eid}")

    # Check for German patterns based on translations/de.json
    # "days_until" -> "Tage bis Start" -> "tage_bis_start"
    has_english = any("days_until_start" in eid for eid in sensor_ids)
    has_german = any("tage_bis_start" in eid for eid in sensor_ids)

    print(f"\nPattern check:")
    print(f"  Has English 'days_until_start': {has_english}")
    print(f"  Has German 'tage_bis_start': {has_german}")

    assert has_german, f"Expected German entity IDs, got: {sensor_ids}"
    assert not has_english, f"Should not have English entity IDs with German language"
