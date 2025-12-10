"""Test countdown sensor calculations for WhenHub integration."""
import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant

@pytest.mark.asyncio
async def test_trip_countdown_future_18_days(hass: HomeAssistant, trip_config_entry):
    """Test trip countdown shows 18 days when 18 days before start."""
    trip_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-06-24 08:00:00+00:00"):  # 18 days before 2026-07-12
        assert await hass.config_entries.async_setup(trip_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check days until start sensor
        sensor = hass.states.get("sensor.danemark_2026_days_until_start")
        assert sensor is not None
        assert int(sensor.state) == 18
        
        # Check event_date sensor shows start date
        event_date = hass.states.get("sensor.danemark_2026_event_date")
        assert event_date is not None
        assert event_date.state == "2026-07-12"

@pytest.mark.asyncio
async def test_trip_active_during_trip(hass: HomeAssistant, trip_config_entry):
    """Test trip sensors during active trip."""
    trip_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-07-15 10:00:00+00:00"):  # During trip
        assert await hass.config_entries.async_setup(trip_config_entry.entry_id)
        await hass.async_block_till_done()

        # Trip should be active
        binary = hass.states.get("binary_sensor.danemark_2026_trip_active_today")
        assert binary is not None
        assert binary.state == "on"
        
        # Check remaining days (12 days left from 15th to 26th, inclusive)
        remaining = hass.states.get("sensor.danemark_2026_trip_left_days")
        assert remaining is not None
        assert int(remaining.state) == 12

@pytest.mark.asyncio
async def test_milestone_countdown_future(hass: HomeAssistant, milestone_config_entry):
    """Test milestone countdown for future date."""
    milestone_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-03-01 08:00:00+00:00"):  # 14 days before 2026-03-15
        assert await hass.config_entries.async_setup(milestone_config_entry.entry_id)
        await hass.async_block_till_done()

        sensor = hass.states.get("sensor.projektabgabe_days_until")
        assert sensor is not None
        assert int(sensor.state) == 14

@pytest.mark.asyncio
async def test_milestone_is_today(hass: HomeAssistant, milestone_config_entry):
    """Test milestone binary sensor on target date."""
    milestone_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-03-15 10:00:00+00:00"):  # On target date
        assert await hass.config_entries.async_setup(milestone_config_entry.entry_id)
        await hass.async_block_till_done()

        # Binary sensor should be on
        binary = hass.states.get("binary_sensor.projektabgabe_is_today")
        assert binary is not None
        assert binary.state == "on"
        
        # Days until should be 0
        sensor = hass.states.get("sensor.projektabgabe_days_until")
        assert sensor is not None
        assert int(sensor.state) == 0

@pytest.mark.asyncio
async def test_anniversary_next_occurrence(hass: HomeAssistant, anniversary_config_entry):
    """Test anniversary calculates next occurrence correctly."""
    anniversary_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-05-01 08:00:00+00:00"):  # 19 days before anniversary
        assert await hass.config_entries.async_setup(anniversary_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check days until next
        sensor = hass.states.get("sensor.geburtstag_max_days_until_next")
        assert sensor is not None
        assert int(sensor.state) == 19
        
        # Check occurrences count (16 occurrences from 2010-2025, including birth year)
        count = hass.states.get("sensor.geburtstag_max_occurrences_count")
        assert count is not None
        assert int(count.state) == 16  # 16 occurrences (2010-2025)
        
        # Check next date
        next_date = hass.states.get("sensor.geburtstag_max_next_date")
        assert next_date is not None
        assert next_date.state == "2026-05-20"

@pytest.mark.asyncio
async def test_special_christmas_countdown(hass: HomeAssistant, special_config_entry):
    """Test special event Christmas countdown."""
    special_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-12-01 08:00:00+00:00"):  # 23 days before Christmas Eve
        assert await hass.config_entries.async_setup(special_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check days until
        sensor = hass.states.get("sensor.weihnachts_countdown_days_until")
        assert sensor is not None
        assert int(sensor.state) == 23
        
        # Check next date
        next_date = hass.states.get("sensor.weihnachts_countdown_next_date")
        assert next_date is not None
        assert next_date.state == "2026-12-24"