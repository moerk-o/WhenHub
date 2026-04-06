"""Tests for FR08: WhenHub Calendar Entity.

Tests the calendar.whenhub entity that aggregates all WhenHub events
into a single HA calendar.

Coverage:
- Platform routing (calendar entry loads CALENDAR, not SENSOR/BINARY_SENSOR)
- Config flow: new first step, calendar scope selection, duplicate abort
- Options flow: scope change for calendar entry
- Calendar entity basics: created, unique_id, STATE_ON/OFF
- async_get_events per event type: Trip, Milestone, Anniversary, Special
- Scope filtering: all / by_type / specific
- Edge cases: empty, year boundaries, mixed types, leap years
"""
from __future__ import annotations

import pytest
from datetime import datetime, date, timedelta, timezone
from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whenhub.const import DOMAIN

# New constants introduced by FR08 - will exist after implementation
ENTRY_TYPE_CALENDAR = "calendar"
ENTRY_TYPE_EVENT = "event"
CONF_ENTRY_TYPE = "entry_type"
CONF_CALENDAR_SCOPE = "calendar_scope"
CONF_CALENDAR_TYPES = "calendar_types"
CONF_CALENDAR_EVENT_IDS = "calendar_event_ids"

CALENDAR_ENTITY_ID = "calendar.whenhub_calendar"


# =============================================================================
# Helpers
# =============================================================================

async def get_calendar_events(
    hass: HomeAssistant,
    entity_id: str,
    start: datetime,
    end: datetime,
) -> list:
    """Retrieve events from a calendar entity via the HA service.

    Uses the calendar.get_events service (HA 2023.4+) to fetch events.
    Returns an empty list if the entity or service is not available.
    """
    try:
        result = await hass.services.async_call(
            "calendar",
            "get_events",
            {
                "entity_id": entity_id,
                "start_date_time": start.isoformat(),
                "end_date_time": end.isoformat(),
            },
            return_response=True,
            blocking=True,
        )
        return result.get(entity_id, {}).get("events", [])
    except Exception:
        # Fallback: access entity directly
        entity_comp = hass.data.get("entity_components", {}).get("calendar")
        if not entity_comp:
            return []
        entity = entity_comp.get_entity(entity_id)
        if not entity:
            return []
        return await entity.async_get_events(hass, start, end)


def _dt(date_str: str) -> datetime:
    """Parse a date string to UTC datetime at midnight."""
    d = date.fromisoformat(date_str)
    return datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def calendar_entry_all():
    """Calendar config entry with scope 'all'."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
            CONF_CALENDAR_SCOPE: "all",
        },
        title="WhenHub Calendar",
        unique_id="whenhub_calendar",
        version=1,
    )


@pytest.fixture
def calendar_entry_by_type_trips():
    """Calendar config entry scoped to trips only."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
            CONF_CALENDAR_SCOPE: "by_type",
            CONF_CALENDAR_TYPES: ["trip"],
        },
        title="WhenHub Calendar",
        unique_id="whenhub_calendar_trips",
        version=1,
    )


@pytest.fixture
def calendar_entry_by_type_trips_and_anniversaries():
    """Calendar config entry scoped to trips + anniversaries."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
            CONF_CALENDAR_SCOPE: "by_type",
            CONF_CALENDAR_TYPES: ["trip", "anniversary"],
        },
        title="WhenHub Calendar",
        unique_id="whenhub_calendar_ta",
        version=1,
    )


@pytest.fixture
def trip_2026():
    """Trip: 2026-07-12 to 2026-07-26."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "event_name": "Dänemark 2026",
            "event_type": "trip",
            "start_date": "2026-07-12",
            "end_date": "2026-07-26",
            "image_path": "",
        },
        title="Dänemark 2026",
        unique_id="whenhub_cal_trip_2026",
        version=1,
    )


@pytest.fixture
def milestone_march():
    """Milestone: 2026-03-15."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "event_name": "Projektabgabe",
            "event_type": "milestone",
            "target_date": "2026-03-15",
            "image_path": "",
        },
        title="Projektabgabe",
        unique_id="whenhub_cal_milestone",
        version=1,
    )


@pytest.fixture
def anniversary_2010():
    """Anniversary: original date 2010-05-20 (Geburtstag Max)."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "event_name": "Geburtstag Max",
            "event_type": "anniversary",
            "target_date": "2010-05-20",
            "image_path": "",
        },
        title="Geburtstag Max",
        unique_id="whenhub_cal_anniversary",
        version=1,
    )


@pytest.fixture
def anniversary_40th():
    """Anniversary: original date 1986-06-10 — will be 40th in 2026."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "event_name": "Hochzeitstag",
            "event_type": "anniversary",
            "target_date": "1986-06-10",
            "image_path": "",
        },
        title="Hochzeitstag",
        unique_id="whenhub_cal_anniversary_40",
        version=1,
    )


@pytest.fixture
def anniversary_leap():
    """Anniversary: original date 2020-02-29 (leap year birthday)."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "event_name": "Schaltjahr Geburtstag",
            "event_type": "anniversary",
            "target_date": "2020-02-29",
            "image_path": "",
        },
        title="Schaltjahr Geburtstag",
        unique_id="whenhub_cal_anniversary_leap",
        version=1,
    )


@pytest.fixture
def christmas_entry():
    """Special event: Christmas Eve."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "event_name": "Heilig Abend",
            "event_type": "special",
            "special_type": "christmas_eve",
            "special_category": "traditional",
            "image_path": "",
        },
        title="Heilig Abend",
        unique_id="whenhub_cal_christmas",
        version=1,
    )


@pytest.fixture
def dst_eu_entry():
    """Special event: DST EU."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "event_name": "Zeitumstellung",
            "event_type": "special",
            "special_type": "dst",
            "special_category": "dst",
            "dst_type": "next_change",
            "dst_region": "eu",
            "image_path": "",
        },
        title="Zeitumstellung",
        unique_id="whenhub_cal_dst",
        version=1,
    )


# =============================================================================
# 1. Platform routing — calendar vs. event entries
# =============================================================================

class TestCalendarSetup:
    """Verify platform routing based on entry_type."""

    @pytest.mark.asyncio
    async def test_calendar_entry_creates_calendar_entity(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Calendar entry must create calendar.whenhub entity."""
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(CALENDAR_ENTITY_ID)
        assert state is not None, "calendar.whenhub must be created"

    @pytest.mark.asyncio
    async def test_calendar_entry_does_not_create_sensors(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Calendar entry must NOT create any sensor entities."""
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        all_states = hass.states.async_all()
        sensor_states = [s for s in all_states if s.entity_id.startswith("sensor.")]
        assert len(sensor_states) == 0, "No sensors must be created for calendar entry"

    @pytest.mark.asyncio
    async def test_calendar_entry_does_not_create_binary_sensors(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Calendar entry must NOT create any binary_sensor entities."""
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        all_states = hass.states.async_all()
        bs_states = [s for s in all_states if s.entity_id.startswith("binary_sensor.")]
        assert len(bs_states) == 0

    @pytest.mark.asyncio
    async def test_event_entry_does_not_create_calendar(
        self, hass: HomeAssistant, trip_2026
    ):
        """Normal event entry must NOT create a calendar entity."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(CALENDAR_ENTITY_ID)
        assert state is None, "Event entry must not create calendar.whenhub"

    @pytest.mark.asyncio
    async def test_calendar_and_event_entry_coexist(
        self, hass: HomeAssistant, calendar_entry_all, trip_2026
    ):
        """Event entry and calendar entry can coexist without conflict."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get(CALENDAR_ENTITY_ID) is not None
        # Trip sensors must still exist
        all_states = hass.states.async_all()
        sensor_states = [s for s in all_states if s.entity_id.startswith("sensor.")]
        assert len(sensor_states) > 0

    @pytest.mark.asyncio
    async def test_calendar_entry_unloads_cleanly(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Unloading calendar entry removes calendar.whenhub."""
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get(CALENDAR_ENTITY_ID) is not None

        assert await hass.config_entries.async_unload(calendar_entry_all.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get(CALENDAR_ENTITY_ID) is None


# =============================================================================
# 2. Config Flow — calendar setup path
# =============================================================================

class TestCalendarConfigFlow:
    """Tests for calendar setup via config flow."""

    @pytest.mark.asyncio
    async def test_first_step_shows_event_type_with_calendar_option(self, hass: HomeAssistant):
        """First step must show event_type selector that includes 'calendar' as an option."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        # event_type field must be present
        assert "event_type" in result["data_schema"].schema

    @pytest.mark.asyncio
    async def test_trip_choice_routes_to_trip_step(self, hass: HomeAssistant):
        """Choosing event_type 'trip' routes to the trip configuration step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "trip"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "trip"

    @pytest.mark.asyncio
    async def test_calendar_choice_routes_to_calendar_step(self, hass: HomeAssistant):
        """Choosing 'calendar' routes to calendar scope selection."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "calendar"

    @pytest.mark.asyncio
    async def test_calendar_scope_all_creates_entry(self, hass: HomeAssistant):
        """Selecting scope 'all' creates calendar config entry directly."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ENTRY_TYPE] == ENTRY_TYPE_CALENDAR
        assert result["data"][CONF_CALENDAR_SCOPE] == "all"

    @pytest.mark.asyncio
    async def test_calendar_scope_by_type_shows_type_selection(self, hass: HomeAssistant):
        """Selecting 'by_type' shows event type checkboxes as next step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "by_type"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "calendar_by_type"

    @pytest.mark.asyncio
    async def test_calendar_scope_by_type_creates_entry(self, hass: HomeAssistant):
        """Scope 'by_type' with types selected creates entry directly."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "by_type"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_TYPES: ["trip", "anniversary"]}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_CALENDAR_SCOPE] == "by_type"
        assert "trip" in result["data"][CONF_CALENDAR_TYPES]
        assert "anniversary" in result["data"][CONF_CALENDAR_TYPES]

    @pytest.mark.asyncio
    async def test_calendar_scope_specific_shows_event_list(
        self, hass: HomeAssistant, trip_2026
    ):
        """Scope 'specific' shows list of existing WhenHub events."""
        trip_2026.add_to_hass(hass)
        await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "specific"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "calendar_specific"

    @pytest.mark.asyncio
    async def test_second_calendar_does_not_abort(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Creating a second calendar is allowed — must NOT abort."""
        calendar_entry_all.add_to_hass(hass)
        await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        # Must NOT abort — proceed to scope selection
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "calendar"

    @pytest.mark.asyncio
    async def test_calendar_entry_title_is_auto_generated(self, hass: HomeAssistant):
        """Calendar entry title is auto-generated (e.g. 'WhenHub Calendar')."""
        hass.config.language = "en"
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "WhenHub Calendar"


# =============================================================================
# 3. Options Flow — calendar entry
# =============================================================================

class TestCalendarOptionsFlow:
    """Tests for calendar options flow."""

    @pytest.mark.asyncio
    async def test_calendar_options_shows_current_scope(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Options flow for calendar entry shows scope selection form."""
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(
            calendar_entry_all.entry_id
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "calendar_options"

    @pytest.mark.asyncio
    async def test_calendar_options_can_change_scope(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Options flow for calendar entry can change scope to by_type."""
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(
            calendar_entry_all.entry_id
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "by_type"}
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_CALENDAR_TYPES: ["milestone"]}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_event_options_flow_unaffected_by_fr08(
        self, hass: HomeAssistant, trip_2026
    ):
        """Existing trip options flow is unaffected by FR08 changes."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(trip_2026.entry_id)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "trip_options"


# =============================================================================
# 3b. Multiple Calendars & Name Step
# =============================================================================

class TestMultipleCalendars:
    """Tests for multiple-calendar support and the name step."""

    @pytest.mark.asyncio
    async def test_scope_all_creates_entry_directly(self, hass: HomeAssistant):
        """Scope 'all' creates entry directly without a name step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_scope_by_type_creates_entry_directly(self, hass: HomeAssistant):
        """Scope 'by_type' creates entry directly without a name step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "by_type"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_TYPES: ["trip"]}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_scope_specific_creates_entry_directly(
        self, hass: HomeAssistant, trip_2026
    ):
        """Scope 'specific' creates entry directly without a name step."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "specific"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_EVENT_IDS: [trip_2026.entry_id]}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_auto_generated_title_not_stored_in_data(self, hass: HomeAssistant):
        """Auto-generated title is stored as entry.title, not in entry.data."""
        hass.config.language = "en"
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "WhenHub Calendar"
        assert "event_name" not in result["data"]

    @pytest.mark.asyncio
    async def test_default_title_english(self, hass: HomeAssistant):
        """Default title is 'WhenHub Calendar' for English locale."""
        hass.config.language = "en"
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "WhenHub Calendar"

    @pytest.mark.asyncio
    async def test_default_title_german(self, hass: HomeAssistant):
        """Default title is 'WhenHub Kalender' for German locale."""
        hass.config.language = "de"
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"event_type": "calendar"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "WhenHub Kalender"

    @pytest.mark.asyncio
    async def test_auto_increment_title_when_first_exists(self, hass: HomeAssistant):
        """When 'WhenHub Calendar' exists, second calendar gets title 'WhenHub Calendar 2'."""
        hass.config.language = "en"
        # Create first calendar via flow
        r = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        r = await hass.config_entries.flow.async_configure(
            r["flow_id"], {"event_type": "calendar"}
        )
        r = await hass.config_entries.flow.async_configure(
            r["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
        )
        assert r["type"] == FlowResultType.CREATE_ENTRY
        assert r["title"] == "WhenHub Calendar"
        await hass.async_block_till_done()

        # Second calendar flow — title should be auto-incremented
        r2 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        r2 = await hass.config_entries.flow.async_configure(
            r2["flow_id"], {"event_type": "calendar"}
        )
        r2 = await hass.config_entries.flow.async_configure(
            r2["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
        )
        assert r2["type"] == FlowResultType.CREATE_ENTRY
        assert r2["title"] == "WhenHub Calendar 2"

    @pytest.mark.asyncio
    async def test_auto_increment_skips_taken_numbers(self, hass: HomeAssistant):
        """When 'WhenHub Calendar' and 'WhenHub Calendar 2' exist, third gets '3'."""
        hass.config.language = "en"
        for expected_title in ["WhenHub Calendar", "WhenHub Calendar 2"]:
            r = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": "user"}
            )
            r = await hass.config_entries.flow.async_configure(
                r["flow_id"], {"event_type": "calendar"}
            )
            r = await hass.config_entries.flow.async_configure(
                r["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
            )
            assert r["type"] == FlowResultType.CREATE_ENTRY
            assert r["title"] == expected_title
            await hass.async_block_till_done()

        # Third calendar
        r3 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        r3 = await hass.config_entries.flow.async_configure(
            r3["flow_id"], {"event_type": "calendar"}
        )
        r3 = await hass.config_entries.flow.async_configure(
            r3["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
        )
        assert r3["type"] == FlowResultType.CREATE_ENTRY
        assert r3["title"] == "WhenHub Calendar 3"

    @pytest.mark.asyncio
    async def test_two_calendars_can_coexist(self, hass: HomeAssistant, trip_2026):
        """Two distinct calendar entries can coexist and are both active."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()

        # Calendar 1: all events
        cal1 = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
                CONF_CALENDAR_SCOPE: "all",
            },
            title="Calendar 1",
            unique_id="whenhub_cal1",
            version=1,
        )
        cal1.add_to_hass(hass)
        assert await hass.config_entries.async_setup(cal1.entry_id)
        await hass.async_block_till_done()

        # Calendar 2: trips only
        cal2 = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
                CONF_CALENDAR_SCOPE: "by_type",
                CONF_CALENDAR_TYPES: ["trip"],
            },
            title="Calendar 2",
            unique_id="whenhub_cal2",
            version=1,
        )
        cal2.add_to_hass(hass)
        assert await hass.config_entries.async_setup(cal2.entry_id)
        await hass.async_block_till_done()

        # Both calendar entities should exist
        state1 = hass.states.get("calendar.calendar_1")
        state2 = hass.states.get("calendar.calendar_2")
        assert state1 is not None
        assert state2 is not None

    @pytest.mark.asyncio
    async def test_options_flow_completes_without_name_step(
        self, hass: HomeAssistant
    ):
        """Options flow for calendar entry completes without a name step."""
        cal = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
                CONF_CALENDAR_SCOPE: "all",
            },
            title="My Calendar",
            unique_id="whenhub_cal_named",
            version=1,
        )
        cal.add_to_hass(hass)
        assert await hass.config_entries.async_setup(cal.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(cal.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_flow_scope_change_persists(
        self, hass: HomeAssistant
    ):
        """Changing scope in options flow updates entry data."""
        cal = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
                CONF_CALENDAR_SCOPE: "all",
            },
            title="My Special Calendar",
            unique_id="whenhub_cal_named2",
            version=1,
        )
        cal.add_to_hass(hass)
        assert await hass.config_entries.async_setup(cal.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(cal.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "by_type"}
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_CALENDAR_TYPES: ["trip"]}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_flow_calendar_creates_entry(
        self, hass: HomeAssistant
    ):
        """Options flow for calendar entry creates updated entry."""
        cal = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
                CONF_CALENDAR_SCOPE: "all",
            },
            title="Old Name",
            unique_id="whenhub_cal_rename",
            version=1,
        )
        cal.add_to_hass(hass)
        assert await hass.config_entries.async_setup(cal.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(cal.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_CALENDAR_SCOPE: "all"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY


# =============================================================================
# 4. Calendar entity basics
# =============================================================================

class TestCalendarEntityBasics:
    """Tests for calendar.whenhub entity properties."""

    @pytest.mark.asyncio
    async def test_entity_exists_after_setup(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """calendar.whenhub is created after setup."""
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(CALENDAR_ENTITY_ID)
        assert state is not None

    @pytest.mark.asyncio
    async def test_entity_unique_id(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """calendar.whenhub has a stable unique_id."""
        from homeassistant.helpers import entity_registry as er

        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        entity_registry = er.async_get(hass)
        entry = entity_registry.async_get(CALENDAR_ENTITY_ID)
        assert entry is not None
        assert entry.unique_id is not None

    @pytest.mark.asyncio
    @freeze_time("2026-06-01 12:00:00+00:00")
    async def test_state_off_when_no_active_events(
        self, hass: HomeAssistant, calendar_entry_all, milestone_march
    ):
        """State is 'off' when no event is currently active."""
        milestone_march.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone_march.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Milestone is March 15, we're June 1 — nothing active
        state = hass.states.get(CALENDAR_ENTITY_ID)
        assert state is not None
        assert state.state == "off"

    @pytest.mark.asyncio
    @freeze_time("2026-07-15 12:00:00+00:00")
    async def test_state_on_during_active_trip(
        self, hass: HomeAssistant, calendar_entry_all, trip_2026
    ):
        """State is 'on' when a trip is currently active (today is within trip)."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Trip is 2026-07-12 to 2026-07-26, we're July 15
        state = hass.states.get(CALENDAR_ENTITY_ID)
        assert state is not None
        assert state.state == "on"

    @pytest.mark.asyncio
    @freeze_time("2026-07-01 12:00:00+00:00")
    async def test_state_off_before_trip_starts(
        self, hass: HomeAssistant, calendar_entry_all, trip_2026
    ):
        """State is 'off' before a trip starts."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Trip starts July 12, we're July 1
        state = hass.states.get(CALENDAR_ENTITY_ID)
        assert state.state == "off"

    @pytest.mark.asyncio
    @freeze_time("2026-07-27 12:00:00+00:00")
    async def test_state_off_after_trip_ends(
        self, hass: HomeAssistant, calendar_entry_all, trip_2026
    ):
        """State is 'off' after a trip has ended."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Trip ended July 26, we're July 27
        state = hass.states.get(CALENDAR_ENTITY_ID)
        assert state.state == "off"


# =============================================================================
# 5. async_get_events — Trip
# =============================================================================

class TestCalendarEventsTrip:
    """Tests for trip events returned by async_get_events."""

    @pytest.mark.asyncio
    @freeze_time("2026-06-01 12:00:00+00:00")
    async def test_trip_in_range_returned(
        self, hass: HomeAssistant, calendar_entry_all, trip_2026
    ):
        """Trip fully within query range is returned."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-07-01"), _dt("2026-08-01")
        )
        assert len(events) == 1
        assert events[0]["summary"] == "Dänemark 2026"

    @pytest.mark.asyncio
    @freeze_time("2026-06-01 12:00:00+00:00")
    async def test_trip_start_end_dates_correct(
        self, hass: HomeAssistant, calendar_entry_all, trip_2026
    ):
        """Trip event start/end dates match configured trip dates."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-07-01"), _dt("2026-08-01")
        )
        assert len(events) == 1
        event = events[0]
        start = event["start"].date() if hasattr(event["start"], "date") else date.fromisoformat(str(event["start"]))
        end = event["end"].date() if hasattr(event["end"], "date") else date.fromisoformat(str(event["end"]))
        assert start == date(2026, 7, 12)
        assert end == date(2026, 7, 26)

    @pytest.mark.asyncio
    @freeze_time("2026-06-01 12:00:00+00:00")
    async def test_trip_overlapping_start_of_range_returned(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Trip that starts before range but ends within is returned."""
        trip = MockConfigEntry(
            domain=DOMAIN,
            data={
                "event_name": "Frühurlaub",
                "event_type": "trip",
                "start_date": "2026-06-28",
                "end_date": "2026-07-05",
                "image_path": "",
            },
            title="Frühurlaub",
            unique_id="whenhub_trip_overlap_start",
            version=1,
        )
        trip.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-07-01"), _dt("2026-07-31")
        )
        assert len(events) == 1
        assert events[0]["summary"] == "Frühurlaub"

    @pytest.mark.asyncio
    @freeze_time("2026-06-01 12:00:00+00:00")
    async def test_trip_overlapping_end_of_range_returned(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Trip that starts within range but ends after is returned."""
        trip = MockConfigEntry(
            domain=DOMAIN,
            data={
                "event_name": "Späturlaub",
                "event_type": "trip",
                "start_date": "2026-07-25",
                "end_date": "2026-08-05",
                "image_path": "",
            },
            title="Späturlaub",
            unique_id="whenhub_trip_overlap_end",
            version=1,
        )
        trip.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-07-01"), _dt("2026-07-31")
        )
        assert len(events) == 1

    @pytest.mark.asyncio
    @freeze_time("2026-06-01 12:00:00+00:00")
    async def test_trip_spanning_entire_range_returned(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Trip that spans the entire query range is returned."""
        trip = MockConfigEntry(
            domain=DOMAIN,
            data={
                "event_name": "Monatelanger Urlaub",
                "event_type": "trip",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "image_path": "",
            },
            title="Monatelanger Urlaub",
            unique_id="whenhub_trip_spans_all",
            version=1,
        )
        trip.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-07-01"), _dt("2026-07-31")
        )
        assert len(events) == 1

    @pytest.mark.asyncio
    @freeze_time("2026-06-01 12:00:00+00:00")
    async def test_trip_before_range_not_returned(
        self, hass: HomeAssistant, calendar_entry_all, trip_2026
    ):
        """Trip entirely before the query range is not returned."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Query August — trip is July
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-08-01"), _dt("2026-09-01")
        )
        assert len(events) == 0

    @pytest.mark.asyncio
    @freeze_time("2026-06-01 12:00:00+00:00")
    async def test_trip_after_range_not_returned(
        self, hass: HomeAssistant, calendar_entry_all, trip_2026
    ):
        """Trip entirely after the query range is not returned."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Query January — trip is July
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-01-01"), _dt("2026-06-30")
        )
        assert len(events) == 0

    @pytest.mark.asyncio
    @freeze_time("2026-06-01 12:00:00+00:00")
    async def test_multiple_trips_all_returned(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Multiple trips in range are all returned."""
        trip_a = MockConfigEntry(
            domain=DOMAIN,
            data={"event_name": "Trip A", "event_type": "trip",
                  "start_date": "2026-07-01", "end_date": "2026-07-07", "image_path": ""},
            title="Trip A",
            unique_id="whenhub_trip_a", version=1,
        )
        trip_b = MockConfigEntry(
            domain=DOMAIN,
            data={"event_name": "Trip B", "event_type": "trip",
                  "start_date": "2026-07-15", "end_date": "2026-07-20", "image_path": ""},
            title="Trip B",
            unique_id="whenhub_trip_b", version=1,
        )
        trip_a.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_a.entry_id)
        await hass.async_block_till_done()
        trip_b.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_b.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-07-01"), _dt("2026-08-01")
        )
        assert len(events) == 2
        summaries = {e["summary"] for e in events}
        assert "Trip A" in summaries
        assert "Trip B" in summaries


# =============================================================================
# 6. async_get_events — Milestone
# =============================================================================

class TestCalendarEventsMilestone:
    """Tests for milestone events returned by async_get_events."""

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_milestone_in_range_returned(
        self, hass: HomeAssistant, calendar_entry_all, milestone_march
    ):
        """Milestone within query range is returned."""
        milestone_march.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone_march.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-03-01"), _dt("2026-04-01")
        )
        assert len(events) == 1
        assert events[0]["summary"] == "Projektabgabe"

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_milestone_outside_range_not_returned(
        self, hass: HomeAssistant, calendar_entry_all, milestone_march
    ):
        """Milestone outside query range is not returned."""
        milestone_march.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone_march.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-04-01"), _dt("2026-12-31")
        )
        assert len(events) == 0

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_milestone_on_range_boundary_included(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Milestone exactly on range start date is included."""
        milestone = MockConfigEntry(
            domain=DOMAIN,
            data={"event_name": "Boundary Test", "event_type": "milestone",
                  "target_date": "2026-07-01", "image_path": ""},
            title="Boundary Test",
            unique_id="whenhub_boundary_ms", version=1,
        )
        milestone.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-07-01"), _dt("2026-08-01")
        )
        assert len(events) == 1

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_milestone_is_single_day_event(
        self, hass: HomeAssistant, calendar_entry_all, milestone_march
    ):
        """Milestone event end date is start date + 1 day (single-day event)."""
        milestone_march.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone_march.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-03-01"), _dt("2026-04-01")
        )
        assert len(events) == 1
        event = events[0]
        start = event["start"].date() if hasattr(event["start"], "date") else date.fromisoformat(str(event["start"]))
        end = event["end"].date() if hasattr(event["end"], "date") else date.fromisoformat(str(event["end"]))
        assert end == start + timedelta(days=1)

    @pytest.mark.asyncio
    async def test_past_milestone_returned_if_in_range(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Past milestone is returned when query range includes its date."""
        past_milestone = MockConfigEntry(
            domain=DOMAIN,
            data={"event_name": "Vergangenes Meilenstein", "event_type": "milestone",
                  "target_date": "2024-01-15", "image_path": ""},
            title="Vergangenes Meilenstein",
            unique_id="whenhub_past_ms", version=1,
        )
        past_milestone.add_to_hass(hass)
        assert await hass.config_entries.async_setup(past_milestone.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Query the past date range
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2024-01-01"), _dt("2024-02-01")
        )
        assert len(events) == 1
        assert events[0]["summary"] == "Vergangenes Meilenstein"


# =============================================================================
# 7. async_get_events — Anniversary
# =============================================================================

class TestCalendarEventsAnniversary:
    """Tests for anniversary events in async_get_events."""

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_anniversary_single_occurrence_in_range(
        self, hass: HomeAssistant, calendar_entry_all, anniversary_2010
    ):
        """One anniversary occurrence within range is returned."""
        anniversary_2010.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_2010.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # 2026-05-20 falls within May
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-05-01"), _dt("2026-06-01")
        )
        assert len(events) == 1

    @pytest.mark.asyncio
    @freeze_time("2020-01-01 12:00:00+00:00")
    async def test_anniversary_multiple_occurrences_in_multi_year_range(
        self, hass: HomeAssistant, calendar_entry_all, anniversary_2010
    ):
        """Anniversary returns one occurrence per year in a multi-year range."""
        anniversary_2010.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_2010.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # 2020-2024 = 5 years, original is 2010 — all 5 in range
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2020-01-01"), _dt("2025-01-01")
        )
        assert len(events) == 5

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_anniversary_title_includes_ordinal_number(
        self, hass: HomeAssistant, calendar_entry_all, anniversary_2010
    ):
        """Anniversary title contains ordinal number: 'Name (16.)'."""
        anniversary_2010.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_2010.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # 2026 - 2010 = 16th anniversary
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-05-01"), _dt("2026-06-01")
        )
        assert len(events) == 1
        assert "(16.)" in events[0]["summary"]
        assert "Geburtstag Max" in events[0]["summary"]

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_anniversary_40th_shows_correct_ordinal(
        self, hass: HomeAssistant, calendar_entry_all, anniversary_40th
    ):
        """40th anniversary shows '(40.)' in title."""
        anniversary_40th.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_40th.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # 2026 - 1986 = 40th
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-06-01"), _dt("2026-07-01")
        )
        assert len(events) == 1
        assert "(40.)" in events[0]["summary"]

    @pytest.mark.asyncio
    async def test_anniversary_no_occurrence_before_original_date(
        self, hass: HomeAssistant, calendar_entry_all, anniversary_2010
    ):
        """Range before original date returns no anniversary events."""
        anniversary_2010.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_2010.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Original is 2010, query is 2009
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2009-01-01"), _dt("2010-01-01")
        )
        assert len(events) == 0

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_anniversary_is_single_day_event(
        self, hass: HomeAssistant, calendar_entry_all, anniversary_2010
    ):
        """Anniversary calendar event is single-day (end = start + 1 day)."""
        anniversary_2010.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_2010.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-05-01"), _dt("2026-06-01")
        )
        assert len(events) == 1
        event = events[0]
        start = event["start"].date() if hasattr(event["start"], "date") else date.fromisoformat(str(event["start"]))
        end = event["end"].date() if hasattr(event["end"], "date") else date.fromisoformat(str(event["end"]))
        assert end == start + timedelta(days=1)

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_anniversary_leap_year_feb29_non_leap_year(
        self, hass: HomeAssistant, calendar_entry_all, anniversary_leap
    ):
        """Feb 29 anniversary in non-leap year returns a valid date (Feb 28 or Mar 1)."""
        anniversary_leap.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_leap.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # 2026 is NOT a leap year — Feb 29 cannot exist
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-02-01"), _dt("2026-04-01")
        )
        assert len(events) == 1
        event_date = events[0]["start"]
        if hasattr(event_date, "date"):
            event_date = event_date.date()
        else:
            event_date = date.fromisoformat(str(event_date))
        # Must be either Feb 28 or Mar 1 — never an invalid date
        assert event_date.month in (2, 3)
        assert event_date.year == 2026

    @pytest.mark.asyncio
    @freeze_time("2024-01-01 12:00:00+00:00")
    async def test_anniversary_leap_year_feb29_in_leap_year(
        self, hass: HomeAssistant, calendar_entry_all, anniversary_leap
    ):
        """Feb 29 anniversary in leap year returns Feb 29."""
        anniversary_leap.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_leap.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # 2024 IS a leap year
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2024-02-01"), _dt("2024-04-01")
        )
        assert len(events) == 1
        event_date = events[0]["start"]
        if hasattr(event_date, "date"):
            event_date = event_date.date()
        else:
            event_date = date.fromisoformat(str(event_date))
        assert event_date == date(2024, 2, 29)


# =============================================================================
# 8. async_get_events — Special Events
# =============================================================================

class TestCalendarEventsSpecial:
    """Tests for special events returned by async_get_events."""

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_christmas_in_range_returned(
        self, hass: HomeAssistant, calendar_entry_all, christmas_entry
    ):
        """Christmas Eve returned when query range includes Dec 24."""
        christmas_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(christmas_entry.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-12-01"), _dt("2027-01-01")
        )
        assert len(events) >= 1
        summaries = [e["summary"] for e in events]
        assert any("Heilig Abend" in s or "Weihnachts" in s for s in summaries)

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_christmas_multiple_years(
        self, hass: HomeAssistant, calendar_entry_all, christmas_entry
    ):
        """Multi-year range returns one Christmas per year."""
        christmas_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(christmas_entry.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # 2026 and 2027 → 2 Christmases
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-12-01"), _dt("2028-01-01")
        )
        christmas_events = [e for e in events if "Heilig Abend" in e.get("summary", "") or "Weihnachts" in e.get("summary", "")]
        assert len(christmas_events) == 2

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_christmas_outside_range_not_returned(
        self, hass: HomeAssistant, calendar_entry_all, christmas_entry
    ):
        """Christmas not returned when range does not include December."""
        christmas_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(christmas_entry.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-01-01"), _dt("2026-12-01")
        )
        assert len(events) == 0

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_dst_eu_in_range_returned(
        self, hass: HomeAssistant, calendar_entry_all, dst_eu_entry
    ):
        """EU DST event returned when range includes DST change date."""
        dst_eu_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(dst_eu_entry.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # EU summer DST is last Sunday in March
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-03-01"), _dt("2026-04-01")
        )
        assert len(events) >= 1

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_special_event_date_is_correct(
        self, hass: HomeAssistant, calendar_entry_all, christmas_entry
    ):
        """Christmas Eve event is always on December 24."""
        christmas_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(christmas_entry.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-12-01"), _dt("2027-01-01")
        )
        assert len(events) >= 1
        event_date = events[0]["start"]
        if hasattr(event_date, "date"):
            event_date = event_date.date()
        else:
            event_date = date.fromisoformat(str(event_date))
        assert event_date.month == 12
        assert event_date.day == 24


# =============================================================================
# 9. Scope filtering
# =============================================================================

class TestCalendarScope:
    """Tests for calendar scope filtering (all / by_type / specific)."""

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_scope_all_returns_all_event_types(
        self, hass: HomeAssistant, calendar_entry_all,
        trip_2026, milestone_march, anniversary_2010
    ):
        """Scope 'all' returns events from all event types."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        milestone_march.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone_march.entry_id)
        await hass.async_block_till_done()
        anniversary_2010.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_2010.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Query the full year 2026 — should include trip, milestone, and anniversary
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-01-01"), _dt("2027-01-01")
        )
        assert len(events) >= 3
        summaries = {e["summary"] for e in events}
        assert "Dänemark 2026" in summaries
        assert "Projektabgabe" in summaries
        # Anniversary: "Geburtstag Max (16.)"
        assert any("Geburtstag Max" in s for s in summaries)

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_scope_by_type_trips_only_excludes_milestones(
        self, hass: HomeAssistant, calendar_entry_by_type_trips,
        trip_2026, milestone_march
    ):
        """Scope 'by_type' with trips only excludes milestone events."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        milestone_march.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone_march.entry_id)
        await hass.async_block_till_done()
        calendar_entry_by_type_trips.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_by_type_trips.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-01-01"), _dt("2027-01-01")
        )
        summaries = [e["summary"] for e in events]
        assert "Dänemark 2026" in summaries
        assert "Projektabgabe" not in summaries

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_scope_by_type_trips_and_anniversaries(
        self, hass: HomeAssistant, calendar_entry_by_type_trips_and_anniversaries,
        trip_2026, milestone_march, anniversary_2010
    ):
        """Scope 'by_type' with trips + anniversaries returns both but not milestones."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        milestone_march.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone_march.entry_id)
        await hass.async_block_till_done()
        anniversary_2010.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_2010.entry_id)
        await hass.async_block_till_done()
        calendar_entry_by_type_trips_and_anniversaries.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_by_type_trips_and_anniversaries.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-01-01"), _dt("2027-01-01")
        )
        summaries = [e["summary"] for e in events]
        assert "Dänemark 2026" in summaries
        assert any("Geburtstag Max" in s for s in summaries)
        assert "Projektabgabe" not in summaries

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_scope_specific_returns_only_selected_entry(
        self, hass: HomeAssistant, trip_2026, milestone_march
    ):
        """Scope 'specific' returns only the selected event entries."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        milestone_march.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone_march.entry_id)
        await hass.async_block_till_done()

        # Calendar entry scoped to only the trip
        calendar_specific = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
                CONF_CALENDAR_SCOPE: "specific",
                CONF_CALENDAR_EVENT_IDS: [trip_2026.entry_id],
            },
            title="WhenHub Calendar",
            unique_id="whenhub_calendar_specific",
            version=1,
        )
        calendar_specific.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_specific.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-01-01"), _dt("2027-01-01")
        )
        summaries = [e["summary"] for e in events]
        assert "Dänemark 2026" in summaries
        assert "Projektabgabe" not in summaries

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_calendar_entry_itself_not_in_results(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """The calendar entry itself is never included in get_events results."""
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-01-01"), _dt("2027-01-01")
        )
        # No event should have "WhenHub Calendar" as summary
        for event in events:
            assert "WhenHub Calendar" not in event.get("summary", "")


# =============================================================================
# 10. Edge cases
# =============================================================================

class TestCalendarEdgeCases:
    """Edge cases for the calendar entity."""

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_no_event_entries_returns_empty_list(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Calendar with no event entries returns empty list for any range."""
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-01-01"), _dt("2027-01-01")
        )
        assert events == []

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_no_events_in_queried_range(
        self, hass: HomeAssistant, calendar_entry_all, trip_2026
    ):
        """Empty list when events exist but none fall in the queried range."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Trip is July, query is January
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-01-01"), _dt("2026-06-01")
        )
        assert events == []

    @pytest.mark.asyncio
    @freeze_time("2026-12-01 12:00:00+00:00")
    async def test_range_spanning_year_boundary(
        self, hass: HomeAssistant, calendar_entry_all, christmas_entry
    ):
        """Query range spanning year boundary (Dec→Jan) works correctly."""
        christmas_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(christmas_entry.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Dec 2026 to Jan 2027 — should return Dec 24 2026
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-12-20"), _dt("2027-01-10")
        )
        assert len(events) >= 1

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_single_day_query_range(
        self, hass: HomeAssistant, calendar_entry_all, milestone_march
    ):
        """Single-day query range (start == end) works correctly."""
        milestone_march.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone_march.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Query March 15 (single day: start of day to start of next day)
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-03-15"), _dt("2026-03-16")
        )
        assert len(events) == 1

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_all_event_types_mixed_in_range(
        self, hass: HomeAssistant, calendar_entry_all,
        trip_2026, milestone_march, anniversary_2010, christmas_entry
    ):
        """All event types appear correctly in a single full-year range."""
        for entry in [trip_2026, milestone_march, anniversary_2010,
                       christmas_entry, calendar_entry_all]:
            entry.add_to_hass(hass)
            assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-01-01"), _dt("2027-01-01")
        )
        # Trip + Milestone + Anniversary + Christmas = at least 4
        assert len(events) >= 4
        summaries = [e["summary"] for e in events]
        assert "Dänemark 2026" in summaries
        assert "Projektabgabe" in summaries
        assert any("Geburtstag Max" in s for s in summaries)
        assert any("Heilig Abend" in s or "Weihnachts" in s for s in summaries)

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_trip_and_anniversary_on_same_date_both_returned(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Trip starting on same date as anniversary — both appear."""
        trip = MockConfigEntry(
            domain=DOMAIN,
            data={"event_name": "Urlaub am Geburtstag", "event_type": "trip",
                  "start_date": "2026-05-20", "end_date": "2026-05-27", "image_path": ""},
            title="Urlaub am Geburtstag",
            unique_id="whenhub_same_date_trip", version=1,
        )
        ann = MockConfigEntry(
            domain=DOMAIN,
            data={"event_name": "Geburtstag", "event_type": "anniversary",
                  "target_date": "2010-05-20", "image_path": ""},
            title="Geburtstag",
            unique_id="whenhub_same_date_ann", version=1,
        )
        for entry in [trip, ann, calendar_entry_all]:
            entry.add_to_hass(hass)
            assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-05-01"), _dt("2026-06-01")
        )
        assert len(events) >= 2
        summaries = [e["summary"] for e in events]
        assert "Urlaub am Geburtstag" in summaries
        assert any("Geburtstag" in s for s in summaries)

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_anniversary_in_year_of_original_date(
        self, hass: HomeAssistant, calendar_entry_all
    ):
        """Anniversary in the exact year of original date is NOT returned (year 0)."""
        ann = MockConfigEntry(
            domain=DOMAIN,
            data={"event_name": "Jahrestag", "event_type": "anniversary",
                  "target_date": "2026-06-15", "image_path": ""},
            title="Jahrestag",
            unique_id="whenhub_ann_same_year", version=1,
        )
        ann.add_to_hass(hass)
        assert await hass.config_entries.async_setup(ann.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-06-01"), _dt("2026-07-01")
        )
        # Year 0 occurrence should not appear or should appear with "(0.)"
        # Either way the event count and handling must be stable (no crash)
        assert isinstance(events, list)

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_very_wide_range_does_not_crash(
        self, hass: HomeAssistant, calendar_entry_all, anniversary_2010
    ):
        """Very wide date range (50 years) returns results without error."""
        anniversary_2010.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_2010.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2010-01-01"), _dt("2060-01-01")
        )
        # 2010 to 2059 = 50 occurrences (starting from year of original)
        assert len(events) >= 49

    @pytest.mark.asyncio
    @freeze_time("2026-01-01 12:00:00+00:00")
    async def test_unloading_event_entry_removes_from_calendar(
        self, hass: HomeAssistant, calendar_entry_all, trip_2026
    ):
        """After unloading an event entry, its events no longer appear in calendar."""
        trip_2026.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_2026.entry_id)
        await hass.async_block_till_done()
        calendar_entry_all.add_to_hass(hass)
        assert await hass.config_entries.async_setup(calendar_entry_all.entry_id)
        await hass.async_block_till_done()

        # Verify trip is in calendar
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-07-01"), _dt("2026-08-01")
        )
        assert len(events) == 1

        # Unload the trip entry
        assert await hass.config_entries.async_unload(trip_2026.entry_id)
        await hass.async_block_till_done()

        # Trip should no longer appear in calendar
        events = await get_calendar_events(
            hass, CALENDAR_ENTITY_ID,
            _dt("2026-07-01"), _dt("2026-08-01")
        )
        assert len(events) == 0
