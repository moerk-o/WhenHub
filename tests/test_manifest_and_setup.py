"""Test WhenHub integration setup and entity creation."""
import pytest
from homeassistant.core import HomeAssistant

@pytest.mark.asyncio
async def test_trip_setup_creates_entities(hass: HomeAssistant, trip_config_entry):
    """Test that trip setup creates all expected entities."""
    trip_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(trip_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check sensor entities
    assert hass.states.get("sensor.danemark_2026_days_until_start") is not None
    assert hass.states.get("sensor.danemark_2026_days_until_end") is not None
    assert hass.states.get("sensor.danemark_2026_countdown_text") is not None
    assert hass.states.get("sensor.danemark_2026_trip_left_days") is not None
    assert hass.states.get("sensor.danemark_2026_trip_left_percent") is not None
    
    # Check binary sensor entities
    assert hass.states.get("binary_sensor.danemark_2026_trip_starts_today") is not None
    assert hass.states.get("binary_sensor.danemark_2026_trip_active_today") is not None
    assert hass.states.get("binary_sensor.danemark_2026_trip_ends_today") is not None
    
    # Check image entity
    assert hass.states.get("image.danemark_2026_image") is not None

@pytest.mark.asyncio
async def test_milestone_setup_creates_entities(hass: HomeAssistant, milestone_config_entry):
    """Test that milestone setup creates all expected entities."""
    milestone_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(milestone_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check sensor entities
    assert hass.states.get("sensor.projektabgabe_days_until") is not None
    assert hass.states.get("sensor.projektabgabe_countdown_text") is not None
    
    # Check binary sensor entity
    assert hass.states.get("binary_sensor.projektabgabe_is_today") is not None
    
    # Check image entity
    assert hass.states.get("image.projektabgabe_image") is not None

@pytest.mark.asyncio
async def test_anniversary_setup_creates_entities(hass: HomeAssistant, anniversary_config_entry):
    """Test that anniversary setup creates all expected entities."""
    anniversary_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(anniversary_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check sensor entities
    assert hass.states.get("sensor.geburtstag_max_days_until_next") is not None
    assert hass.states.get("sensor.geburtstag_max_days_since_last") is not None
    assert hass.states.get("sensor.geburtstag_max_countdown_text") is not None
    assert hass.states.get("sensor.geburtstag_max_occurrences_count") is not None
    assert hass.states.get("sensor.geburtstag_max_next_date") is not None
    assert hass.states.get("sensor.geburtstag_max_last_date") is not None
    
    # Check binary sensor entity
    assert hass.states.get("binary_sensor.geburtstag_max_is_today") is not None
    
    # Check image entity
    assert hass.states.get("image.geburtstag_max_image") is not None

@pytest.mark.asyncio
async def test_special_setup_creates_entities(hass: HomeAssistant, special_config_entry):
    """Test that special event setup creates all expected entities."""
    special_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(special_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check sensor entities
    assert hass.states.get("sensor.weihnachts_countdown_days_until") is not None
    assert hass.states.get("sensor.weihnachts_countdown_days_since_last") is not None
    assert hass.states.get("sensor.weihnachts_countdown_countdown_text") is not None
    assert hass.states.get("sensor.weihnachts_countdown_next_date") is not None
    assert hass.states.get("sensor.weihnachts_countdown_last_date") is not None
    
    # Check binary sensor entity
    assert hass.states.get("binary_sensor.weihnachts_countdown_is_today") is not None
    
    # Check image entity
    assert hass.states.get("image.weihnachts_countdown_image") is not None