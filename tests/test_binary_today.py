"""Test binary sensor 'is today' functionality for WhenHub integration."""
import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant

@pytest.mark.asyncio
async def test_trip_starts_today(hass: HomeAssistant, trip_config_entry):
    """Test binary sensor on when trip starts today."""
    trip_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-07-12 10:00:00+00:00"):  # Trip start date
        assert await hass.config_entries.async_setup(trip_config_entry.entry_id)
        await hass.async_block_till_done()
        
        # Trip starts today should be on
        starts = hass.states.get("binary_sensor.danemark_2026_trip_starts_today")
        assert starts is not None
        assert starts.state == "on"
        
        # Trip active should also be on
        active = hass.states.get("binary_sensor.danemark_2026_trip_active_today")
        assert active is not None
        assert active.state == "on"
        
        # Trip ends today should be off
        ends = hass.states.get("binary_sensor.danemark_2026_trip_ends_today")
        assert ends is not None
        assert ends.state == "off"

@pytest.mark.asyncio
async def test_trip_ends_today(hass: HomeAssistant, trip_config_entry):
    """Test binary sensor on when trip ends today."""
    trip_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-07-26 10:00:00+00:00"):  # Trip end date
        assert await hass.config_entries.async_setup(trip_config_entry.entry_id)
        await hass.async_block_till_done()
        
        # Trip ends today should be on
        ends = hass.states.get("binary_sensor.danemark_2026_trip_ends_today")
        assert ends is not None
        assert ends.state == "on"
        
        # Trip active should still be on (last day)
        active = hass.states.get("binary_sensor.danemark_2026_trip_active_today")
        assert active is not None
        assert active.state == "on"
        
        # Trip starts today should be off
        starts = hass.states.get("binary_sensor.danemark_2026_trip_starts_today")
        assert starts is not None
        assert starts.state == "off"

@pytest.mark.asyncio
async def test_milestone_is_today_true(hass: HomeAssistant, milestone_config_entry):
    """Test milestone binary sensor on target date."""
    milestone_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-03-15 10:00:00+00:00"):  # Target date
        assert await hass.config_entries.async_setup(milestone_config_entry.entry_id)
        await hass.async_block_till_done()
        
        binary = hass.states.get("binary_sensor.projektabgabe_is_today")
        assert binary is not None
        assert binary.state == "on"

@pytest.mark.asyncio
async def test_milestone_is_today_false(hass: HomeAssistant, milestone_config_entry):
    """Test milestone binary sensor on other dates."""
    milestone_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-03-14 10:00:00+00:00"):  # Day before
        assert await hass.config_entries.async_setup(milestone_config_entry.entry_id)
        await hass.async_block_till_done()
        
        binary = hass.states.get("binary_sensor.projektabgabe_is_today")
        assert binary is not None
        assert binary.state == "off"

@pytest.mark.asyncio
async def test_anniversary_is_today(hass: HomeAssistant, anniversary_config_entry):
    """Test anniversary binary sensor on anniversary date."""
    anniversary_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-05-20 10:00:00+00:00"):  # Anniversary date
        assert await hass.config_entries.async_setup(anniversary_config_entry.entry_id)
        await hass.async_block_till_done()
        
        binary = hass.states.get("binary_sensor.geburtstag_max_is_today")
        assert binary is not None
        assert binary.state == "on"

@pytest.mark.asyncio
async def test_special_christmas_is_today(hass: HomeAssistant, special_config_entry):
    """Test special event binary sensor on Christmas Eve."""
    special_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-12-24 10:00:00+00:00"):  # Christmas Eve
        assert await hass.config_entries.async_setup(special_config_entry.entry_id)
        await hass.async_block_till_done()
        
        binary = hass.states.get("binary_sensor.weihnachts_countdown_is_today")
        assert binary is not None
        assert binary.state == "on"

@pytest.mark.asyncio
async def test_special_christmas_not_today(hass: HomeAssistant, special_config_entry):
    """Test special event binary sensor on other days."""
    special_config_entry.add_to_hass(hass)
    
    with freeze_time("2026-12-23 10:00:00+00:00"):  # Day before Christmas Eve
        assert await hass.config_entries.async_setup(special_config_entry.entry_id)
        await hass.async_block_till_done()
        
        binary = hass.states.get("binary_sensor.weihnachts_countdown_is_today")
        assert binary is not None
        assert binary.state == "off"