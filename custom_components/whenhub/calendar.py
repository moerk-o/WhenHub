"""Calendar platform for WhenHub integration.

Provides a single CalendarEntity that aggregates all (or a filtered subset of)
WhenHub events into the Home Assistant calendar view.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .calculations import (
    parse_date,
    anniversary_for_year,
    next_special_event,
    next_dst_event,
    is_date_today,
    is_trip_active,
    custom_pattern_occurrences,
)
from .const import (
    DOMAIN,
    CONF_ENTRY_TYPE,
    ENTRY_TYPE_CALENDAR,
    CONF_CALENDAR_SCOPE,
    CONF_CALENDAR_TYPES,
    CONF_CALENDAR_EVENT_IDS,
    CONF_EVENT_TYPE,
    CONF_START_DATE,
    CONF_END_DATE,
    CONF_TARGET_DATE,
    CONF_SPECIAL_TYPE,
    CONF_SPECIAL_CATEGORY,
    CONF_DST_TYPE,
    CONF_DST_REGION,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
    EVENT_TYPE_SPECIAL,
    SPECIAL_EVENTS,
    DST_REGIONS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WhenHub Calendar entity."""
    async_add_entities([WhenHubCalendar(hass, entry)])


class WhenHubCalendar(CalendarEntity):
    """Calendar entity aggregating all WhenHub events.

    STATE_ON when any event is currently active:
    - Trip: today is between start and end (inclusive)
    - Milestone / Anniversary / Special: today is the event day
    """

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_name = None  # Entity is the main feature of the device; name = device name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info with scope-based model description."""
        scope = self._entry.data.get(CONF_CALENDAR_SCOPE, "all")
        if scope == "by_type":
            types = self._entry.data.get(CONF_CALENDAR_TYPES, [])
            model = ", ".join(t.capitalize() for t in types) if types else "All Types"
        elif scope == "specific":
            ids = self._entry.data.get(CONF_CALENDAR_EVENT_IDS, [])
            titles = [
                e.title
                for entry_id in ids
                if (e := self._hass.config_entries.async_get_entry(entry_id))
            ]
            model = ", ".join(titles) if titles else "Specific Events"
        else:
            model = "All Events"
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="WhenHub",
            model=model,
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current active event (determines STATE_ON/OFF)."""
        today = date.today()
        for entry in self._hass.config_entries.async_entries(DOMAIN):
            if entry.state != ConfigEntryState.LOADED:
                continue
            if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
                continue
            if not self._entry_in_scope(entry):
                continue
            current = _get_current_event(entry.data, today, entry.title)
            if current is not None:
                return current
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> list[CalendarEvent]:
        """Return all events in the requested time range."""
        start = start_datetime.date()
        end = end_datetime.date()
        events: list[CalendarEvent] = []

        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state != ConfigEntryState.LOADED:
                continue
            if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
                continue
            if not self._entry_in_scope(entry):
                continue
            events.extend(_get_calendar_events(entry.data, start, end, entry.title))

        return events

    def _entry_in_scope(self, entry: ConfigEntry) -> bool:
        """Check if an event entry matches this calendar's scope."""
        scope = self._entry.data.get(CONF_CALENDAR_SCOPE, "all")
        if scope == "all":
            return True
        if scope == "by_type":
            types = self._entry.data.get(CONF_CALENDAR_TYPES, [])
            return entry.data.get(CONF_EVENT_TYPE) in types
        if scope == "specific":
            ids = self._entry.data.get(CONF_CALENDAR_EVENT_IDS, [])
            return entry.entry_id in ids
        return True


# =============================================================================
# Event calculation helpers (module-level, no HA dependencies)
# =============================================================================

def _get_calendar_events(event_data: dict, start: date, end: date, name: str) -> list[CalendarEvent]:
    """Route event calculation to the correct type handler."""
    event_type = event_data.get(CONF_EVENT_TYPE)
    if event_type == EVENT_TYPE_TRIP:
        return _trip_events(event_data, start, end, name)
    if event_type == EVENT_TYPE_MILESTONE:
        return _milestone_events(event_data, start, end, name)
    if event_type == EVENT_TYPE_ANNIVERSARY:
        return _anniversary_events(event_data, start, end, name)
    if event_type == EVENT_TYPE_SPECIAL:
        special_category = event_data.get(CONF_SPECIAL_CATEGORY)
        if special_category == "custom_pattern":
            return _custom_pattern_events(event_data, start, end, name)
        return _special_events(event_data, start, end, name)
    return []


def _get_current_event(event_data: dict, today: date, name: str) -> CalendarEvent | None:
    """Return a CalendarEvent if this event is active today (used for STATE_ON)."""
    event_type = event_data.get(CONF_EVENT_TYPE)

    if event_type == EVENT_TYPE_TRIP:
        trip_start = parse_date(event_data[CONF_START_DATE])
        trip_end = parse_date(event_data[CONF_END_DATE])
        if trip_start <= today <= trip_end:
            return CalendarEvent(
                summary=name,
                start=trip_start,
                end=trip_end,
                description="Trip",
            )

    elif event_type == EVENT_TYPE_MILESTONE:
        target = parse_date(event_data[CONF_TARGET_DATE])
        if target == today:
            return CalendarEvent(
                summary=name,
                start=today,
                end=today + timedelta(days=1),
                description="Milestone",
            )

    elif event_type == EVENT_TYPE_ANNIVERSARY:
        original = parse_date(event_data[CONF_TARGET_DATE])
        occ = anniversary_for_year(original, today.year)
        if occ == today:
            year_number = today.year - original.year
            return CalendarEvent(
                summary=f"{name} ({year_number}.)",
                start=today,
                end=today + timedelta(days=1),
                description="Anniversary",
            )

    elif event_type == EVENT_TYPE_SPECIAL:
        special_category = event_data.get(CONF_SPECIAL_CATEGORY)
        if special_category == "dst":
            dst_type = event_data.get(CONF_DST_TYPE, "next_change")
            dst_region = event_data.get(CONF_DST_REGION, "eu")
            region_info = DST_REGIONS.get(dst_region, DST_REGIONS["eu"])
            occ = next_dst_event(region_info, dst_type, today)
            if occ and occ == today:
                return CalendarEvent(
                    summary=name,
                    start=today,
                    end=today + timedelta(days=1),
                    description="DST",
                )
        elif special_category == "custom_pattern":
            if custom_pattern_occurrences(event_data, today, today):
                return CalendarEvent(
                    summary=name,
                    start=today,
                    end=today + timedelta(days=1),
                    description="Custom Pattern",
                )
        else:
            special_type = event_data.get(CONF_SPECIAL_TYPE, "christmas_eve")
            special_info = SPECIAL_EVENTS.get(special_type, SPECIAL_EVENTS["christmas_eve"])
            occ = next_special_event(special_info, today)
            if occ and occ == today:
                return CalendarEvent(
                    summary=name,
                    start=today,
                    end=today + timedelta(days=1),
                    description="Special",
                )

    return None


def _trip_events(data: dict, start: date, end: date, name: str) -> list[CalendarEvent]:
    """Return trip event if it overlaps with [start, end]."""
    trip_start = parse_date(data[CONF_START_DATE])
    trip_end = parse_date(data[CONF_END_DATE])
    if trip_start <= end and trip_end >= start:
        return [CalendarEvent(
            summary=name,
            start=trip_start,
            end=trip_end,
            description="Trip",
        )]
    return []


def _milestone_events(data: dict, start: date, end: date, name: str) -> list[CalendarEvent]:
    """Return milestone event if its date falls within [start, end]."""
    target = parse_date(data[CONF_TARGET_DATE])
    if start <= target <= end:
        return [CalendarEvent(
            summary=name,
            start=target,
            end=target + timedelta(days=1),
            description="Milestone",
        )]
    return []


def _anniversary_events(data: dict, start: date, end: date, name: str) -> list[CalendarEvent]:
    """Return all anniversary occurrences within [start, end].

    Uses anniversary_for_year() for leap-year-safe date calculation.
    Title format: "Name (N.)" where N is the number of years since the original date.
    """
    original = parse_date(data[CONF_TARGET_DATE])
    events = []

    for year in range(max(original.year, start.year), end.year + 1):
        occ = anniversary_for_year(original, year)
        if start <= occ <= end:
            year_number = year - original.year
            events.append(CalendarEvent(
                summary=f"{name} ({year_number}.)",
                start=occ,
                end=occ + timedelta(days=1),
                description="Anniversary",
            ))
    return events


def _custom_pattern_events(data: dict, start: date, end: date, name: str) -> list[CalendarEvent]:
    """Return all custom pattern occurrences within [start, end]."""
    return [
        CalendarEvent(
            summary=name,
            start=occ,
            end=occ + timedelta(days=1),
            description="Custom Pattern",
        )
        for occ in custom_pattern_occurrences(data, start, end)
    ]


def _special_events(data: dict, start: date, end: date, name: str) -> list[CalendarEvent]:
    """Return all special event occurrences within [start, end].

    Iterates over each year in the range and calls the appropriate calculation
    function (next_special_event or next_dst_event) once per year.
    Custom Pattern is handled separately by _custom_pattern_events.
    """
    special_category = data.get(CONF_SPECIAL_CATEGORY)
    events = []

    if special_category == "dst":
        dst_type = data.get(CONF_DST_TYPE, "next_change")
        dst_region = data.get(CONF_DST_REGION, "eu")
        region_info = DST_REGIONS.get(dst_region, DST_REGIONS["eu"])

        for year in range(start.year, end.year + 1):
            occ = next_dst_event(region_info, dst_type, date(year, 1, 1))
            if occ and start <= occ <= end:
                events.append(CalendarEvent(
                    summary=name,
                    start=occ,
                    end=occ + timedelta(days=1),
                    description="DST",
                ))
    else:
        special_type = data.get(CONF_SPECIAL_TYPE, "christmas_eve")
        special_info = SPECIAL_EVENTS.get(special_type, SPECIAL_EVENTS["christmas_eve"])

        for year in range(start.year, end.year + 1):
            occ = next_special_event(special_info, date(year, 1, 1))
            if occ and start <= occ <= end:
                events.append(CalendarEvent(
                    summary=name,
                    start=occ,
                    end=occ + timedelta(days=1),
                    description="Special",
                ))

    return events
