"""Extended edge case tests for WhenHub integration.

Tests for unicode characters, special characters, long names, and other edge cases.
"""
import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant


# =============================================================================
# Unicode Event Names Tests
# =============================================================================

@pytest.mark.asyncio
async def test_event_name_with_umlauts(hass: HomeAssistant, umlaut_milestone_config_entry):
    """Test that event names with German umlauts work correctly."""
    umlaut_milestone_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(umlaut_milestone_config_entry.entry_id)
    await hass.async_block_till_done()

    # Entity ID should be created (umlauts converted)
    states = [s for s in hass.states.async_all() if "fruhjahrsputz" in s.entity_id.lower()]
    assert len(states) > 0, "No entities found for umlaut event name"


@pytest.mark.asyncio
async def test_event_name_with_sharp_s(hass: HomeAssistant, sharp_s_milestone_config_entry):
    """Test that event names with ß (sharp s) work correctly."""
    sharp_s_milestone_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(sharp_s_milestone_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that entities were created
    states = [s for s in hass.states.async_all() if "gro" in s.entity_id.lower()]
    assert len(states) > 0, "No entities found for sharp-s event name"


# =============================================================================
# Special Character Event Names Tests
# =============================================================================

@pytest.mark.asyncio
async def test_event_name_with_ampersand(hass: HomeAssistant, ampersand_milestone_config_entry):
    """Test that event names with & work correctly."""
    ampersand_milestone_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(ampersand_milestone_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that entities were created
    states = [s for s in hass.states.async_all() if "tom" in s.entity_id.lower()]
    assert len(states) > 0, "No entities found for ampersand event name"


@pytest.mark.asyncio
async def test_event_name_with_emoji(hass: HomeAssistant, emoji_trip_config_entry):
    """Test that event names with emojis work correctly."""
    emoji_trip_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(emoji_trip_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that entities were created (emoji likely stripped from entity_id)
    states = [s for s in hass.states.async_all() if "spanien" in s.entity_id.lower()]
    assert len(states) > 0, "No entities found for emoji event name"


# =============================================================================
# Long Event Names Tests
# =============================================================================

@pytest.mark.asyncio
async def test_very_long_event_name(hass: HomeAssistant, long_name_milestone_config_entry):
    """Test that very long event names (100+ chars) work correctly."""
    long_name_milestone_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(long_name_milestone_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that entities were created
    states = [s for s in hass.states.async_all() if "dieser" in s.entity_id.lower() or "extrem" in s.entity_id.lower()]
    assert len(states) > 0, "No entities found for long event name"


# =============================================================================
# Year Boundary Edge Cases Tests
# =============================================================================

@pytest.mark.asyncio
async def test_new_years_eve_countdown(hass: HomeAssistant, silvester_special_config_entry):
    """Test countdown to New Year's Eve on December 30."""
    silvester_special_config_entry.add_to_hass(hass)

    with freeze_time("2026-12-30 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(silvester_special_config_entry.entry_id)
        await hass.async_block_till_done()

        # Should be 1 day until Dec 31
        state = hass.states.get("sensor.silvester_test_days_until_start")
        assert state is not None
        assert int(state.state) == 1


@pytest.mark.asyncio
async def test_new_year_countdown_from_previous_year(hass: HomeAssistant, neujahr_special_config_entry):
    """Test countdown to New Year from December 31."""
    neujahr_special_config_entry.add_to_hass(hass)

    with freeze_time("2025-12-31 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(neujahr_special_config_entry.entry_id)
        await hass.async_block_till_done()

        # Should be 1 day until Jan 1
        state = hass.states.get("sensor.neujahr_test_days_until_start")
        assert state is not None
        assert int(state.state) == 1


# =============================================================================
# Multiple Parallel Events Tests
# =============================================================================

@pytest.mark.asyncio
async def test_multiple_trips_same_time(hass: HomeAssistant, parallel_trip_1_config_entry, parallel_trip_2_config_entry):
    """Test that multiple trip events can coexist."""
    # Setup each entry immediately after adding to avoid auto-load issues
    parallel_trip_1_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(parallel_trip_1_config_entry.entry_id)
    await hass.async_block_till_done()

    parallel_trip_2_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(parallel_trip_2_config_entry.entry_id)
    await hass.async_block_till_done()

    # Both should have their own sensors
    trip1_sensor = hass.states.get("sensor.parallel_trip_1_days_until_start")
    trip2_sensor = hass.states.get("sensor.parallel_trip_2_days_until_start")

    assert trip1_sensor is not None, "Trip 1 sensor not found"
    assert trip2_sensor is not None, "Trip 2 sensor not found"


@pytest.mark.asyncio
async def test_mixed_event_types(hass: HomeAssistant, trip_config_entry, milestone_config_entry, anniversary_config_entry):
    """Test that different event types can coexist."""
    # Setup each entry immediately after adding to avoid auto-load issues
    trip_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(trip_config_entry.entry_id)
    await hass.async_block_till_done()

    milestone_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(milestone_config_entry.entry_id)
    await hass.async_block_till_done()

    anniversary_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(anniversary_config_entry.entry_id)
    await hass.async_block_till_done()

    # All three should have sensors
    assert hass.states.get("sensor.danemark_2026_days_until_start") is not None
    assert hass.states.get("sensor.projektabgabe_days_until_start") is not None
    assert hass.states.get("sensor.geburtstag_max_days_until_next") is not None
