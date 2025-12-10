"""Edge case tests for WhenHub integration."""
import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant

from conftest import get_date_from_state


# =============================================================================
# Single Day Trip Tests
# =============================================================================

@pytest.mark.asyncio
async def test_single_day_trip_countdown(hass: HomeAssistant, single_day_trip_config_entry):
    """Test single day trip (start = end) countdown works correctly."""
    single_day_trip_config_entry.add_to_hass(hass)

    with freeze_time("2026-08-10 10:00:00+00:00"):  # 5 days before
        assert await hass.config_entries.async_setup(single_day_trip_config_entry.entry_id)
        await hass.async_block_till_done()

        # Days until start
        sensor = hass.states.get("sensor.tagesausflug_days_until")
        assert sensor is not None
        assert int(sensor.state) == 5

        # Days until end should also be 5 (same day)
        sensor_end = hass.states.get("sensor.tagesausflug_days_until_end")
        assert sensor_end is not None
        assert int(sensor_end.state) == 5


@pytest.mark.asyncio
async def test_single_day_trip_on_the_day(hass: HomeAssistant, single_day_trip_config_entry):
    """Test single day trip sensors on the actual day."""
    single_day_trip_config_entry.add_to_hass(hass)

    with freeze_time("2026-08-15 10:00:00+00:00"):  # The day itself
        assert await hass.config_entries.async_setup(single_day_trip_config_entry.entry_id)
        await hass.async_block_till_done()

        # All binary sensors should be on
        starts = hass.states.get("binary_sensor.tagesausflug_trip_starts_today")
        assert starts is not None
        assert starts.state == "on"

        active = hass.states.get("binary_sensor.tagesausflug_trip_active_today")
        assert active is not None
        assert active.state == "on"

        ends = hass.states.get("binary_sensor.tagesausflug_trip_ends_today")
        assert ends is not None
        assert ends.state == "on"

        # Trip left days should be 1 (today counts)
        left = hass.states.get("sensor.tagesausflug_trip_left_days")
        assert left is not None
        assert int(left.state) == 1


# =============================================================================
# Past Events Tests (Negative Days)
# =============================================================================

@pytest.mark.asyncio
async def test_past_trip_negative_days(hass: HomeAssistant, past_trip_config_entry):
    """Test that past trips show negative days correctly."""
    past_trip_config_entry.add_to_hass(hass)

    with freeze_time("2026-01-15 10:00:00+00:00"):  # Well after the trip
        assert await hass.config_entries.async_setup(past_trip_config_entry.entry_id)
        await hass.async_block_till_done()

        # Days until start should be negative
        sensor = hass.states.get("sensor.vergangener_urlaub_days_until")
        assert sensor is not None
        days = int(sensor.state)
        assert days < 0  # Should be negative (trip was in 2024)

        # Days until end should also be negative
        sensor_end = hass.states.get("sensor.vergangener_urlaub_days_until_end")
        assert sensor_end is not None
        days_end = int(sensor_end.state)
        assert days_end < 0

        # Trip left days should be 0
        left = hass.states.get("sensor.vergangener_urlaub_trip_left_days")
        assert left is not None
        assert int(left.state) == 0

        # Trip left percent should be 0
        percent = hass.states.get("sensor.vergangener_urlaub_trip_left_percent")
        assert percent is not None
        assert float(percent.state) == 0.0


@pytest.mark.asyncio
async def test_past_milestone_days(hass: HomeAssistant, past_milestone_config_entry):
    """Test that past milestones show correct values."""
    past_milestone_config_entry.add_to_hass(hass)

    with freeze_time("2026-01-15 10:00:00+00:00"):  # 2 years after milestone
        assert await hass.config_entries.async_setup(past_milestone_config_entry.entry_id)
        await hass.async_block_till_done()

        # Days until should be negative or 0
        sensor = hass.states.get("sensor.vergangener_milestone_days_until")
        assert sensor is not None
        days = int(sensor.state)
        assert days <= 0  # Past milestone


# =============================================================================
# Long Trip Tests (> 365 days)
# =============================================================================

@pytest.mark.asyncio
async def test_long_trip_countdown(hass: HomeAssistant, long_trip_config_entry):
    """Test very long trip (18 months) works correctly."""
    long_trip_config_entry.add_to_hass(hass)

    with freeze_time("2025-12-01 10:00:00+00:00"):  # 31 days before start
        assert await hass.config_entries.async_setup(long_trip_config_entry.entry_id)
        await hass.async_block_till_done()

        # Days until start
        sensor = hass.states.get("sensor.weltreise_days_until")
        assert sensor is not None
        assert int(sensor.state) == 31

        # Days until end (should be 31 + 546 = 577 days)
        sensor_end = hass.states.get("sensor.weltreise_days_until_end")
        assert sensor_end is not None
        days_until_end = int(sensor_end.state)
        assert days_until_end > 365  # More than a year


@pytest.mark.asyncio
async def test_long_trip_during_trip(hass: HomeAssistant, long_trip_config_entry):
    """Test sensors during a very long trip."""
    long_trip_config_entry.add_to_hass(hass)

    with freeze_time("2026-07-01 10:00:00+00:00"):  # 6 months into the trip
        assert await hass.config_entries.async_setup(long_trip_config_entry.entry_id)
        await hass.async_block_till_done()

        # Trip should be active
        active = hass.states.get("binary_sensor.weltreise_trip_active_today")
        assert active is not None
        assert active.state == "on"

        # Days until start should be negative (already started)
        sensor = hass.states.get("sensor.weltreise_days_until")
        assert sensor is not None
        assert int(sensor.state) < 0

        # Days until end should still be positive
        sensor_end = hass.states.get("sensor.weltreise_days_until_end")
        assert sensor_end is not None
        assert int(sensor_end.state) > 0


# =============================================================================
# Leap Year Tests
# =============================================================================

@pytest.mark.asyncio
async def test_leap_year_anniversary_in_non_leap_year(hass: HomeAssistant, leap_year_anniversary_config_entry):
    """Test Feb 29 anniversary handled correctly in non-leap year."""
    leap_year_anniversary_config_entry.add_to_hass(hass)

    with freeze_time("2025-02-20 10:00:00+00:00"):  # 2025 is NOT a leap year
        assert await hass.config_entries.async_setup(leap_year_anniversary_config_entry.entry_id)
        await hass.async_block_till_done()

        # Next date should be Feb 28 (not Feb 29)
        next_date = hass.states.get("sensor.schaltjahr_geburtstag_next_date")
        assert next_date is not None
        assert get_date_from_state(next_date.state) == "2025-02-28"  # Falls back to Feb 28

        # Days until should be 8 (Feb 20 -> Feb 28)
        days = hass.states.get("sensor.schaltjahr_geburtstag_days_until_next")
        assert days is not None
        assert int(days.state) == 8


@pytest.mark.asyncio
async def test_leap_year_anniversary_in_leap_year(hass: HomeAssistant, leap_year_anniversary_config_entry):
    """Test Feb 29 anniversary in actual leap year."""
    leap_year_anniversary_config_entry.add_to_hass(hass)

    with freeze_time("2028-02-20 10:00:00+00:00"):  # 2028 IS a leap year
        assert await hass.config_entries.async_setup(leap_year_anniversary_config_entry.entry_id)
        await hass.async_block_till_done()

        # Next date should be Feb 29 (leap year!)
        next_date = hass.states.get("sensor.schaltjahr_geburtstag_next_date")
        assert next_date is not None
        assert get_date_from_state(next_date.state) == "2028-02-29"

        # Days until should be 9 (Feb 20 -> Feb 29)
        days = hass.states.get("sensor.schaltjahr_geburtstag_days_until_next")
        assert days is not None
        assert int(days.state) == 9


# =============================================================================
# Easter Calculation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_easter_2026(hass: HomeAssistant, easter_config_entry):
    """Test Easter calculation for 2026 (April 5, 2026)."""
    easter_config_entry.add_to_hass(hass)

    with freeze_time("2026-03-01 10:00:00+00:00"):
        assert await hass.config_entries.async_setup(easter_config_entry.entry_id)
        await hass.async_block_till_done()

        # Easter 2026 is April 5
        next_date = hass.states.get("sensor.ostern_next_date")
        assert next_date is not None
        assert get_date_from_state(next_date.state) == "2026-04-05"

        # Days until (March 1 -> April 5 = 35 days)
        days = hass.states.get("sensor.ostern_days_until")
        assert days is not None
        assert int(days.state) == 35


@pytest.mark.asyncio
async def test_easter_2027(hass: HomeAssistant, easter_config_entry):
    """Test Easter calculation for 2027 (March 28, 2027)."""
    easter_config_entry.add_to_hass(hass)

    with freeze_time("2027-03-01 10:00:00+00:00"):
        assert await hass.config_entries.async_setup(easter_config_entry.entry_id)
        await hass.async_block_till_done()

        # Easter 2027 is March 28
        next_date = hass.states.get("sensor.ostern_next_date")
        assert next_date is not None
        assert get_date_from_state(next_date.state) == "2027-03-28"


# =============================================================================
# Advent Calculation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_advent_2026(hass: HomeAssistant, advent_config_entry):
    """Test 1st Advent calculation for 2026 (November 29, 2026)."""
    advent_config_entry.add_to_hass(hass)

    with freeze_time("2026-11-01 10:00:00+00:00"):
        assert await hass.config_entries.async_setup(advent_config_entry.entry_id)
        await hass.async_block_till_done()

        # 1st Advent 2026 is November 29
        next_date = hass.states.get("sensor.1_advent_next_date")
        assert next_date is not None
        assert get_date_from_state(next_date.state) == "2026-11-29"

        # Days until (Nov 1 -> Nov 29 = 28 days)
        days = hass.states.get("sensor.1_advent_days_until")
        assert days is not None
        assert int(days.state) == 28


@pytest.mark.asyncio
async def test_advent_2025(hass: HomeAssistant, advent_config_entry):
    """Test 1st Advent calculation for 2025 (November 30, 2025)."""
    advent_config_entry.add_to_hass(hass)

    with freeze_time("2025-11-01 10:00:00+00:00"):
        assert await hass.config_entries.async_setup(advent_config_entry.entry_id)
        await hass.async_block_till_done()

        # 1st Advent 2025 is November 30
        next_date = hass.states.get("sensor.1_advent_next_date")
        assert next_date is not None
        assert get_date_from_state(next_date.state) == "2025-11-30"
