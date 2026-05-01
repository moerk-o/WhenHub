"""Integration tests for FR09: Custom Pattern.

Tests cover:
- Config flow: all frequency paths and end conditions
- Options flow: changing frequency
- Coordinator data calculation (via MockConfigEntry + sensor entity)
- Binary sensor is_today
- Calendar entity: custom pattern events in async_get_events
- Calendar entity: STATE_ON when pattern fires today
"""
from __future__ import annotations

import pytest
from datetime import date, datetime, timedelta, timezone
from freezegun import freeze_time
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whenhub.const import DOMAIN


# =============================================================================
# Shared config entry data helpers
# =============================================================================

def _cp_yearly_nth(dtstart: str = "2020-01-01") -> dict:
    """Config for yearly 4th Thursday of November (Thanksgiving-style)."""
    return {
        "event_type": "special",
        "special_category": "custom_pattern",
        "cp_freq": "yearly",
        "cp_dtstart": dtstart,
        "cp_interval": 1,
        "cp_bymonth": 11,
        "cp_day_rule": "nth_weekday",
        "cp_byday_pos": 4,
        "cp_byday_weekday": 3,  # Thursday
        "cp_end_type": "none",
    }


def _cp_monthly_fixed(dtstart: str = "2024-01-01") -> dict:
    """Config for monthly on the 15th."""
    return {
        "event_type": "special",
        "special_category": "custom_pattern",
        "cp_freq": "monthly",
        "cp_dtstart": dtstart,
        "cp_interval": 1,
        "cp_day_rule": "fixed_day",
        "cp_bymonthday": 15,
        "cp_end_type": "none",
    }


def _cp_weekly_mon_wed(dtstart: str = "2024-01-01") -> dict:
    """Config for weekly on Monday and Wednesday."""
    return {
        "event_type": "special",
        "special_category": "custom_pattern",
        "cp_freq": "weekly",
        "cp_dtstart": dtstart,
        "cp_interval": 1,
        "cp_byday_list": [0, 2],  # Monday=0, Wednesday=2
        "cp_end_type": "none",
    }


def _cp_daily(dtstart: str = "2024-01-01") -> dict:
    """Config for every day."""
    return {
        "event_type": "special",
        "special_category": "custom_pattern",
        "cp_freq": "daily",
        "cp_dtstart": dtstart,
        "cp_interval": 1,
        "cp_end_type": "none",
    }


# =============================================================================
# Config Flow Tests
# =============================================================================

class TestConfigFlowCustomPattern:
    """Tests for Custom Pattern config flow paths."""

    @pytest.mark.asyncio
    async def test_special_category_routes_to_cp_freq(self, hass: HomeAssistant):
        """Selecting custom_pattern category routes to cp_freq step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "special"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"special_category": "custom_pattern"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "cp_freq"

    @pytest.mark.asyncio
    async def test_yearly_nth_weekday_full_path(self, hass: HomeAssistant):
        """Full config flow: yearly → 4th Thursday of November."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "special"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"special_category": "custom_pattern"}
        )
        # cp_freq step
        assert result["step_id"] == "cp_freq"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"cp_freq": "yearly", "cp_dtstart": "2020-01-01", "cp_interval": 1},
        )
        # cp_yearly step
        assert result["step_id"] == "cp_yearly"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"cp_bymonth": "11", "cp_day_rule": "nth_weekday"},
        )
        # cp_weekday_nth step
        assert result["step_id"] == "cp_weekday_nth"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"cp_byday_pos": "4", "cp_byday_weekday": "3"},
        )
        # cp_end step
        assert result["step_id"] == "cp_end"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"cp_end_type": "none"}
        )
        # cp_image step (image + URL/Memo optional)
        assert result["step_id"] == "cp_image"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {}
        )
        # Entry created
        assert result["type"] == FlowResultType.CREATE_ENTRY
        data = result["data"]
        assert data["cp_freq"] == "yearly"
        assert data["cp_bymonth"] == 11
        assert data["cp_byday_pos"] == 4
        assert data["cp_byday_weekday"] == 3
        assert data["cp_end_type"] == "none"
        assert data["special_category"] == "custom_pattern"

    @pytest.mark.asyncio
    async def test_yearly_last_weekday_path(self, hass: HomeAssistant):
        """Config flow: yearly → last Monday of a month."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        for step_data in [
            {"event_type": "special"},
            {"special_category": "custom_pattern"},
            {"cp_freq": "yearly", "cp_dtstart": "2020-01-01", "cp_interval": 1},
            {"cp_bymonth": "5", "cp_day_rule": "last_weekday"},
        ]:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], step_data
            )
        assert result["step_id"] == "cp_weekday_last"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"cp_byday_weekday": "0"}
        )
        assert result["step_id"] == "cp_end"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"cp_end_type": "none"}
        )
        assert result["step_id"] == "cp_image"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["cp_day_rule"] == "last_weekday"
        assert result["data"]["cp_byday_weekday"] == 0

    @pytest.mark.asyncio
    async def test_monthly_fixed_day_path(self, hass: HomeAssistant):
        """Config flow: monthly → fixed day of month."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        for step_data in [
            {"event_type": "special"},
            {"special_category": "custom_pattern"},
            {"cp_freq": "monthly", "cp_dtstart": "2024-01-01", "cp_interval": 1},
            {"cp_day_rule": "fixed_day"},
        ]:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], step_data
            )
        assert result["step_id"] == "cp_fixed_day"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"cp_bymonthday": 15}
        )
        assert result["step_id"] == "cp_end"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"cp_end_type": "none"}
        )
        assert result["step_id"] == "cp_image"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["cp_bymonthday"] == 15

    @pytest.mark.asyncio
    async def test_weekly_path(self, hass: HomeAssistant):
        """Config flow: weekly → Mon + Wed selection."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        for step_data in [
            {"event_type": "special"},
            {"special_category": "custom_pattern"},
            {"cp_freq": "weekly", "cp_dtstart": "2024-01-01", "cp_interval": 1},
        ]:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], step_data
            )
        assert result["step_id"] == "cp_weekly"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"cp_byday_list": ["0", "2"]}
        )
        assert result["step_id"] == "cp_end"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"cp_end_type": "none"}
        )
        assert result["step_id"] == "cp_image"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["cp_byday_list"] == [0, 2]

    @pytest.mark.asyncio
    async def test_daily_skips_to_end_step(self, hass: HomeAssistant):
        """Config flow: daily → skips detail step → goes directly to cp_end."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        for step_data in [
            {"event_type": "special"},
            {"special_category": "custom_pattern"},
        ]:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], step_data
            )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"cp_freq": "daily", "cp_dtstart": "2024-01-01", "cp_interval": 1},
        )
        # daily skips directly to cp_end
        assert result["step_id"] == "cp_end"

    @pytest.mark.asyncio
    async def test_end_condition_until(self, hass: HomeAssistant):
        """End condition 'until' routes to cp_end_until and saves until date."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        for step_data in [
            {"event_type": "special"},
            {"special_category": "custom_pattern"},
            {"cp_freq": "daily", "cp_dtstart": "2024-01-01", "cp_interval": 1},
            {"cp_end_type": "until"},
        ]:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], step_data
            )
        assert result["step_id"] == "cp_end_until"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"cp_until": "2025-12-31"}
        )
        assert result["step_id"] == "cp_image"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["cp_until"] == "2025-12-31"

    @pytest.mark.asyncio
    async def test_end_condition_count(self, hass: HomeAssistant):
        """End condition 'count' routes to cp_end_count and saves count."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        for step_data in [
            {"event_type": "special"},
            {"special_category": "custom_pattern"},
            {"cp_freq": "daily", "cp_dtstart": "2024-01-01", "cp_interval": 1},
            {"cp_end_type": "count"},
        ]:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], step_data
            )
        assert result["step_id"] == "cp_end_count"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"cp_count": 5}
        )
        assert result["step_id"] == "cp_image"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["cp_count"] == 5

    @pytest.mark.asyncio
    async def test_entry_title_auto_increments(self, hass: HomeAssistant):
        """Second 'Daily Pattern' entry gets auto-incremented title."""
        # Create first entry directly
        entry1 = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_daily(),
            title="Daily Pattern",
        )
        entry1.add_to_hass(hass)

        # Create second via flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        for step_data in [
            {"event_type": "special"},
            {"special_category": "custom_pattern"},
            {"cp_freq": "daily", "cp_dtstart": "2024-06-01", "cp_interval": 1},
            {"cp_end_type": "none"},
        ]:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], step_data
            )
        assert result["step_id"] == "cp_image"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Daily Pattern 2"


# =============================================================================
# Options Flow Tests
# =============================================================================

class TestOptionsFlowCustomPattern:
    """Tests for Custom Pattern options flow."""

    @pytest.mark.asyncio
    async def test_options_flow_shows_cp_freq_step(self, hass: HomeAssistant):
        """Opening options for a CP entry shows the cp_freq form."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_monthly_fixed(),
            title="Monthly 15th",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "cp_freq"

    @pytest.mark.asyncio
    async def test_options_flow_prepopulates_from_entry_data(self, hass: HomeAssistant):
        """Options form pre-fills defaults from current config entry."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_monthly_fixed(dtstart="2024-03-15"),
            title="Monthly 15th",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        # Schema should have default cp_freq = "monthly"
        schema = result["data_schema"].schema
        freq_field = next(
            (v for k, v in schema.items() if str(k) == "cp_freq"), None
        )
        assert freq_field is not None

    @pytest.mark.asyncio
    async def test_options_flow_change_frequency(self, hass: HomeAssistant):
        """Changing frequency from monthly to daily via options flow."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_monthly_fixed(),
            title="Monthly 15th",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        # Submit cp_freq with daily
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {"cp_freq": "daily", "cp_dtstart": "2024-01-01", "cp_interval": 1},
        )
        # daily → cp_end directly
        assert result["step_id"] == "cp_end"
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"cp_end_type": "none"}
        )
        assert result["step_id"] == "cp_image"
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert entry.data["cp_freq"] == "daily"


# =============================================================================
# Coordinator & Sensor Tests
# =============================================================================

class TestCustomPatternSensors:
    """Test coordinator data and sensor values for Custom Pattern."""

    @pytest.mark.asyncio
    @freeze_time("2026-04-06")  # Monday
    async def test_daily_sensors_loaded(self, hass: HomeAssistant):
        """Daily pattern creates all expected sensor entities."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_daily(dtstart="2024-01-01"),
            title="Every Day",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state == ConfigEntryState.LOADED
        # days_until translates to "Days until start" → entity_id ends with days_until
        state = hass.states.get("sensor.every_day_days_until")
        assert state is not None
        # Today IS an occurrence → days_until shows days to NEXT future occurrence = 1
        assert state.state == "1"

    @pytest.mark.asyncio
    @freeze_time("2026-04-06")  # Monday
    async def test_weekly_days_until_next_wednesday(self, hass: HomeAssistant):
        """Weekly Mon+Wed pattern: on Monday, days_until == 2 (next is Wednesday)."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_weekly_mon_wed(dtstart="2024-01-01"),
            title="Mon Wed",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.mon_wed_days_until")
        assert state is not None
        # Monday IS occurrence → next_display = Wed Apr 8 → days_until == 2
        assert state.state == "2"

    @pytest.mark.asyncio
    @freeze_time("2026-04-06")  # Monday
    async def test_occurrence_count_sensor_exists(self, hass: HomeAssistant):
        """occurrence_count sensor is created for custom pattern."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_daily(dtstart="2024-01-01"),
            title="Every Day Count",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.every_day_count_occurrence_count")
        assert state is not None
        # Since dtstart=2024-01-01 and today=2026-04-06, count > 700
        count = int(state.state)
        assert count > 700

    @pytest.mark.asyncio
    @freeze_time("2026-04-06")  # Monday
    async def test_next_date_sensor_daily(self, hass: HomeAssistant):
        """next_date sensor for daily pattern shows tomorrow when today is occurrence."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_daily(dtstart="2024-01-01"),
            title="Daily Next",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.daily_next_next_date")
        assert state is not None
        # Today IS occurrence → next_display = tomorrow
        assert "2026-04-07" in state.state

    @pytest.mark.asyncio
    @freeze_time("2026-11-26")  # 4th Thursday of November 2026 = Thanksgiving
    async def test_yearly_thanksgiving_is_today(self, hass: HomeAssistant):
        """On Thanksgiving day, is_today binary sensor is on; days_until points to next year."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_yearly_nth(dtstart="2020-01-01"),
            title="Thanksgiving",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # is_today must be on
        bs = hass.states.get("binary_sensor.thanksgiving_is_today")
        assert bs is not None
        assert bs.state == "on"
        # days_until shows days to next Thanksgiving (2027-11-25 = 364 days away)
        state = hass.states.get("sensor.thanksgiving_days_until")
        assert state is not None
        assert state.state == "364"

    @pytest.mark.asyncio
    @freeze_time("2026-04-06")  # Monday, not Thanksgiving
    async def test_yearly_thanksgiving_not_today(self, hass: HomeAssistant):
        """On a non-Thanksgiving day, days_until > 0."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_yearly_nth(dtstart="2020-01-01"),
            title="Thanksgiving Future",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.thanksgiving_future_days_until")
        assert state is not None
        assert int(state.state) > 0


# =============================================================================
# Binary Sensor Tests
# =============================================================================

class TestCustomPatternBinarySensor:
    """Test is_today binary sensor for Custom Pattern."""

    @pytest.mark.asyncio
    @freeze_time("2026-04-06")  # Monday
    async def test_is_today_on_daily_pattern(self, hass: HomeAssistant):
        """Binary sensor is_today is ON for daily pattern (every day)."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_daily(dtstart="2024-01-01"),
            title="Daily Binary",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("binary_sensor.daily_binary_is_today")
        assert state is not None
        assert state.state == "on"

    @pytest.mark.asyncio
    @freeze_time("2026-04-07")  # Tuesday — not in Mon+Wed list
    async def test_is_today_off_for_weekly_on_tuesday(self, hass: HomeAssistant):
        """Binary sensor is_today is OFF for Mon+Wed pattern on Tuesday."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_weekly_mon_wed(dtstart="2024-01-01"),
            title="Mon Wed Binary",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("binary_sensor.mon_wed_binary_is_today")
        assert state is not None
        assert state.state == "off"

    @pytest.mark.asyncio
    @freeze_time("2026-04-06")  # Monday — in Mon+Wed list
    async def test_is_today_on_for_weekly_on_monday(self, hass: HomeAssistant):
        """Binary sensor is_today is ON for Mon+Wed pattern on Monday."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=_cp_weekly_mon_wed(dtstart="2024-01-01"),
            title="Mon Wed On",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("binary_sensor.mon_wed_on_is_today")
        assert state is not None
        assert state.state == "on"


# =============================================================================
# Calendar Entity Tests
# =============================================================================

class TestCalendarCustomPattern:
    """Test calendar entity with custom pattern events."""

    @pytest.mark.asyncio
    @freeze_time("2026-04-06")
    async def test_daily_events_in_range(self, hass: HomeAssistant):
        """Daily pattern produces events for every day in the query range."""
        from custom_components.whenhub.calendar import _custom_pattern_events

        data = _cp_daily(dtstart="2024-01-01")
        start = date(2026, 4, 6)
        end = date(2026, 4, 8)
        events = _custom_pattern_events(data, start, end, "Daily")

        # 3 days → 3 events
        assert len(events) == 3
        dates = [e.start for e in events]
        assert date(2026, 4, 6) in dates
        assert date(2026, 4, 7) in dates
        assert date(2026, 4, 8) in dates

    @pytest.mark.asyncio
    async def test_weekly_events_in_range(self):
        """Weekly Mon+Wed pattern returns only matching days in range."""
        from custom_components.whenhub.calendar import _custom_pattern_events

        data = _cp_weekly_mon_wed(dtstart="2024-01-01")
        # Week starting 2026-04-06 (Mon): Mon=6, Tue=7, Wed=8, Thu=9, Fri=10
        start = date(2026, 4, 6)
        end = date(2026, 4, 10)
        events = _custom_pattern_events(data, start, end, "Mon Wed")

        event_dates = {e.start for e in events}
        assert date(2026, 4, 6) in event_dates   # Monday
        assert date(2026, 4, 8) in event_dates   # Wednesday
        assert date(2026, 4, 7) not in event_dates  # Tuesday
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_monthly_fixed_day_events_in_range(self):
        """Monthly 15th pattern returns the 15th of each month in range."""
        from custom_components.whenhub.calendar import _custom_pattern_events

        data = _cp_monthly_fixed(dtstart="2024-01-01")
        start = date(2026, 3, 1)
        end = date(2026, 5, 31)
        events = _custom_pattern_events(data, start, end, "Monthly 15")

        event_dates = {e.start for e in events}
        assert date(2026, 3, 15) in event_dates
        assert date(2026, 4, 15) in event_dates
        assert date(2026, 5, 15) in event_dates
        assert len(events) == 3

    @pytest.mark.asyncio
    async def test_yearly_thanksgiving_appears_in_november(self):
        """Yearly 4th Thu Nov pattern shows Thanksgiving 2026 in November range."""
        from custom_components.whenhub.calendar import _custom_pattern_events

        data = _cp_yearly_nth(dtstart="2020-01-01")
        start = date(2026, 11, 1)
        end = date(2026, 11, 30)
        events = _custom_pattern_events(data, start, end, "Thanksgiving")

        assert len(events) == 1
        # 4th Thursday of November 2026
        assert events[0].start == date(2026, 11, 26)
        assert events[0].summary == "Thanksgiving"

    @pytest.mark.asyncio
    async def test_event_description_is_custom_pattern(self):
        """Calendar events have description 'Custom Pattern'."""
        from custom_components.whenhub.calendar import _custom_pattern_events

        data = _cp_daily(dtstart="2024-01-01")
        events = _custom_pattern_events(data, date(2026, 4, 6), date(2026, 4, 6), "Test")
        assert events[0].description == "Custom Pattern"

    @pytest.mark.asyncio
    async def test_event_end_is_next_day(self):
        """Calendar events for single-day occurrences end the following day."""
        from custom_components.whenhub.calendar import _custom_pattern_events

        data = _cp_daily(dtstart="2024-01-01")
        events = _custom_pattern_events(data, date(2026, 4, 6), date(2026, 4, 6), "Test")
        assert events[0].end == date(2026, 4, 7)

    @pytest.mark.asyncio
    async def test_no_events_before_dtstart(self):
        """Custom pattern returns no events before the anchor date."""
        from custom_components.whenhub.calendar import _custom_pattern_events

        data = _cp_daily(dtstart="2026-05-01")
        events = _custom_pattern_events(data, date(2026, 4, 1), date(2026, 4, 30), "Test")
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_count_exhausted_returns_no_events(self):
        """Pattern with COUNT=1 returns no events after the single occurrence."""
        from custom_components.whenhub.calendar import _custom_pattern_events

        data = {
            "event_type": "special",
            "special_category": "custom_pattern",
            "cp_freq": "daily",
            "cp_dtstart": "2026-01-01",
            "cp_interval": 1,
            "cp_end_type": "count",
            "cp_count": 1,
        }
        # Only 2026-01-01 is the single occurrence
        events = _custom_pattern_events(data, date(2026, 4, 1), date(2026, 4, 30), "Once")
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_get_current_event_monthly_on_occurrence_day(self):
        """_get_current_event returns an event when today matches the pattern."""
        from custom_components.whenhub.calendar import _get_current_event

        data = _cp_monthly_fixed(dtstart="2024-01-01")
        today = date(2026, 4, 15)  # 15th of month
        event = _get_current_event(data, today, "Monthly 15th")
        assert event is not None
        assert event.start == today
        assert event.description == "Custom Pattern"

    @pytest.mark.asyncio
    async def test_get_current_event_monthly_off_non_occurrence_day(self):
        """_get_current_event returns None when today does not match the pattern."""
        from custom_components.whenhub.calendar import _get_current_event

        data = _cp_monthly_fixed(dtstart="2024-01-01")
        today = date(2026, 4, 14)  # 14th — not the 15th
        event = _get_current_event(data, today, "Monthly 15th")
        assert event is None

    @pytest.mark.asyncio
    async def test_get_current_event_daily_always_on(self):
        """_get_current_event returns an event for daily pattern on any day."""
        from custom_components.whenhub.calendar import _get_current_event

        data = _cp_daily(dtstart="2024-01-01")
        for day in [date(2026, 4, 6), date(2026, 4, 7), date(2026, 4, 15)]:
            event = _get_current_event(data, day, "Daily")
            assert event is not None, f"Expected event on {day}"

    @pytest.mark.asyncio
    async def test_get_current_event_thanksgiving_2026(self):
        """_get_current_event returns Thanksgiving on the correct date."""
        from custom_components.whenhub.calendar import _get_current_event

        data = _cp_yearly_nth(dtstart="2020-01-01")
        thanksgiving_2026 = date(2026, 11, 26)  # 4th Thursday of November 2026
        event = _get_current_event(data, thanksgiving_2026, "Thanksgiving")
        assert event is not None
        assert event.start == thanksgiving_2026

    @pytest.mark.asyncio
    async def test_get_current_event_thanksgiving_wrong_day_returns_none(self):
        """_get_current_event returns None the day before Thanksgiving."""
        from custom_components.whenhub.calendar import _get_current_event

        data = _cp_yearly_nth(dtstart="2020-01-01")
        day_before = date(2026, 11, 25)
        event = _get_current_event(data, day_before, "Thanksgiving")
        assert event is None
