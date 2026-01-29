"""Tests for Special Events in WhenHub integration."""
import pytest
from datetime import date
from homeassistant.core import HomeAssistant


class TestFixedSpecialEvents:
    """Tests for fixed-date special events (Christmas, Halloween, etc.)."""

    @pytest.mark.asyncio
    async def test_christmas_eve_setup(self, hass: HomeAssistant, special_config_entry):
        """Test that christmas_eve special event creates all expected sensors."""
        special_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(special_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check that all 5 sensors are created
        base = "sensor.weihnachts_countdown"
        assert hass.states.get(f"{base}_days_until_start") is not None
        assert hass.states.get(f"{base}_days_since_last") is not None
        assert hass.states.get(f"{base}_event_date") is not None
        assert hass.states.get(f"{base}_next_date") is not None
        assert hass.states.get(f"{base}_last_date") is not None

    @pytest.mark.asyncio
    async def test_christmas_eve_days_until_positive(self, hass: HomeAssistant, special_config_entry):
        """Test that days_until for Christmas Eve is a positive number (or 0 on the day)."""
        special_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(special_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.weihnachts_countdown_days_until_start")
        assert state is not None
        days = int(state.state)
        # Should be between 0 and 365
        assert 0 <= days <= 365

    @pytest.mark.asyncio
    async def test_christmas_eve_next_date_is_dec_24(self, hass: HomeAssistant, special_config_entry):
        """Test that next_date for Christmas Eve is always December 24."""
        special_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(special_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.weihnachts_countdown_next_date")
        assert state is not None
        # next_date should be a timestamp ending with December 24
        assert "-12-24" in state.state


class TestCalculatedSpecialEvents:
    """Tests for calculated special events (Easter, Pentecost, Advent)."""

    @pytest.mark.asyncio
    async def test_easter_setup(self, hass: HomeAssistant, easter_config_entry):
        """Test that Easter special event creates all expected sensors."""
        easter_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(easter_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check that sensors are created
        base = "sensor.ostern"
        assert hass.states.get(f"{base}_days_until_start") is not None
        assert hass.states.get(f"{base}_next_date") is not None

    @pytest.mark.asyncio
    async def test_easter_date_is_sunday(self, hass: HomeAssistant, easter_config_entry):
        """Test that Easter date is always a Sunday."""
        from datetime import datetime
        easter_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(easter_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.ostern_next_date")
        assert state is not None
        # Parse the date and check it's a Sunday (weekday 6)
        date_str = state.state.split("T")[0]  # Get YYYY-MM-DD
        easter_date = datetime.strptime(date_str, "%Y-%m-%d")
        assert easter_date.weekday() == 6, f"Easter {date_str} is not a Sunday"

    @pytest.mark.asyncio
    async def test_advent_1_setup(self, hass: HomeAssistant, advent_config_entry):
        """Test that 1st Advent special event creates all expected sensors."""
        advent_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(advent_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check that sensors are created
        base = "sensor.1_advent"
        assert hass.states.get(f"{base}_days_until_start") is not None
        assert hass.states.get(f"{base}_next_date") is not None

    @pytest.mark.asyncio
    async def test_advent_1_is_sunday(self, hass: HomeAssistant, advent_config_entry):
        """Test that 1st Advent is always a Sunday."""
        from datetime import datetime
        advent_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(advent_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.1_advent_next_date")
        assert state is not None
        date_str = state.state.split("T")[0]
        advent_date = datetime.strptime(date_str, "%Y-%m-%d")
        assert advent_date.weekday() == 6, f"1st Advent {date_str} is not a Sunday"


class TestDSTEvents:
    """Tests for Daylight Saving Time events."""

    @pytest.mark.asyncio
    async def test_dst_eu_setup(self, hass: HomeAssistant, dst_eu_config_entry):
        """Test that EU DST event creates all expected sensors."""
        dst_eu_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(dst_eu_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check that sensors are created
        base = "sensor.zeitumstellung_eu"
        assert hass.states.get(f"{base}_days_until_start") is not None
        assert hass.states.get(f"{base}_next_date") is not None

        # Check binary sensor
        assert hass.states.get("binary_sensor.zeitumstellung_eu_daylight_saving_time_active") is not None

    @pytest.mark.asyncio
    async def test_dst_eu_next_date_is_sunday(self, hass: HomeAssistant, dst_eu_config_entry):
        """Test that EU DST transition is always on a Sunday."""
        from datetime import datetime
        dst_eu_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(dst_eu_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.zeitumstellung_eu_next_date")
        assert state is not None
        date_str = state.state.split("T")[0]
        dst_date = datetime.strptime(date_str, "%Y-%m-%d")
        assert dst_date.weekday() == 6, f"EU DST {date_str} is not a Sunday"

    @pytest.mark.asyncio
    async def test_dst_usa_setup(self, hass: HomeAssistant, dst_usa_config_entry):
        """Test that USA DST event creates all expected sensors."""
        dst_usa_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(dst_usa_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check that sensors are created
        base = "sensor.dst_usa"
        assert hass.states.get(f"{base}_days_until_start") is not None
        assert hass.states.get(f"{base}_next_date") is not None

    @pytest.mark.asyncio
    async def test_dst_is_dst_active_binary(self, hass: HomeAssistant, dst_eu_config_entry):
        """Test that is_dst_active binary sensor has valid state."""
        dst_eu_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(dst_eu_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("binary_sensor.zeitumstellung_eu_daylight_saving_time_active")
        assert state is not None
        # Should be either "on" or "off"
        assert state.state in ("on", "off")
