# FR08: Implementation Plan (Calendar Entity)

Dieses Dokument ist die **finale Umsetzungsreferenz** für FR08. Es enthält alle
abgestimmten Entscheidungen und konkreten Code-Snippets.
Konzept-Hintergrund: [FR08-calendar-entity.md](FR08-calendar-entity.md)
Branch: `feature/fr08-calendar-entity`

---

## Arbeitsweise

- **Unklarheiten und wichtige/größere Entscheidungen** werden vor der Umsetzung mit dem User besprochen.
- **Commits** sind ohne Rückfrage ok.
- **Merge in main** nur nach expliziter Freigabe durch den User.
- **Statusupdates** werden regelmäßig ausgegeben (nach jedem abgeschlossenen Schritt).

---

## Abgestimmte Entscheidungen

| Frage | Entscheidung |
|-------|-------------|
| Config Flow erster Schritt | Kalender als **5. Option** im bestehenden Event-Typ-Schritt (kein neuer Schritt) |
| Calendar `STATE_ON` | `on` wenn irgendein Event gerade aktiv ist (Trip läuft, Milestone/Anniversary/Special ist heute) |
| Schaltjahr Feb 29 | `anniversary_for_year()` aus `calculations.py` verwenden (gibt Feb 28 zurück) |
| Kalender Einzigartigkeit | Nur ein Kalender-Entry erlaubt, Duplikat → `async_abort` |
| Anniversary Titel-Format | `"Geburtstag Jon (40.)"` — year_number = occurrence_year - original_year |

---

## Schritt 1: const.py

Neue Konstanten anhängen:

```python
# Entry type marker
CONF_ENTRY_TYPE = "entry_type"
ENTRY_TYPE_EVENT = "event"        # alle bestehenden Entries (implizit, kein Marker nötig)
ENTRY_TYPE_CALENDAR = "calendar"  # neuer Kalender-Entry

# Calendar scope configuration
CONF_CALENDAR_SCOPE = "calendar_scope"   # "all" | "by_type" | "specific"
CONF_CALENDAR_TYPES = "calendar_types"   # list[str] bei scope "by_type"
CONF_CALENDAR_EVENT_IDS = "calendar_event_ids"  # list[str] bei scope "specific"
```

---

## Schritt 2: \_\_init\_\_.py

Zwei Platform-Listen, Routing nach Entry-Typ:

```python
EVENT_PLATFORMS = [Platform.SENSOR, Platform.IMAGE, Platform.BINARY_SENSOR]
CALENDAR_PLATFORMS = [Platform.CALENDAR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
        # Kalender-Entry: kein Coordinator, nur Calendar-Platform
        hass.data[DOMAIN][entry.entry_id] = {}
        await hass.config_entries.async_forward_entry_setups(entry, CALENDAR_PLATFORMS)
    else:
        # Event-Entry: bisheriges Verhalten unverändert
        coordinator = WhenHubCoordinator(hass, entry, dict(entry.data))
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "event_data": dict(entry.data),
        }
        await hass.config_entries.async_forward_entry_setups(entry, EVENT_PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    _LOGGER.info("WhenHub integration loaded: %s", entry.title)
    return True
```

`async_unload_entry` bleibt unverändert — funktioniert für beide Entry-Typen korrekt.

---

## Schritt 3: config_flow.py

### 3a: Kalender als 5. Option im Event-Typ-Schritt

**WICHTIG:** Kein neuer erster Schritt. Kalender wird direkt als zusätzliche Option
in den bestehenden `async_step_user` (Event-Typ-Auswahl) eingebaut.

```python
# Im Schema für async_step_user (event type selection):
vol.Required(CONF_EVENT_TYPE): SelectSelector(SelectSelectorConfig(
    options=[
        SelectOptionDict(value=EVENT_TYPE_TRIP, label="trip"),
        SelectOptionDict(value=EVENT_TYPE_MILESTONE, label="milestone"),
        SelectOptionDict(value=EVENT_TYPE_ANNIVERSARY, label="anniversary"),
        SelectOptionDict(value=EVENT_TYPE_SPECIAL, label="special"),
        SelectOptionDict(value=ENTRY_TYPE_CALENDAR, label="calendar"),  # NEU
    ],
    translation_key="event_type",
))

# Im Handler:
async def async_step_user(self, user_input=None):
    if user_input is not None:
        if user_input[CONF_EVENT_TYPE] == ENTRY_TYPE_CALENDAR:
            return await self.async_step_calendar()
        # ... bisheriger Event-Flow
```

### 3b: Kalender-Config Flow

```python
async def async_step_calendar(self, user_input=None):
    """Schritt 1: Scope wählen. Prüft auch ob Kalender bereits existiert."""
    # Duplikat-Check
    existing = [
        e for e in self.hass.config_entries.async_entries(DOMAIN)
        if e.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR
    ]
    if existing:
        return self.async_abort(reason="calendar_already_configured")

    if user_input is None:
        return self.async_show_form(
            step_id="calendar",
            data_schema=vol.Schema({
                vol.Required(CONF_CALENDAR_SCOPE, default="all"): SelectSelector(
                    SelectSelectorConfig(
                        options=["all", "by_type", "specific"],
                        translation_key="calendar_scope",
                    )
                )
            }),
        )
    scope = user_input[CONF_CALENDAR_SCOPE]
    self._calendar_data = {
        CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
        CONF_CALENDAR_SCOPE: scope,
    }
    if scope == "by_type":
        return await self.async_step_calendar_by_type()
    if scope == "specific":
        return await self.async_step_calendar_specific()
    # scope == "all"
    return self.async_create_entry(title="WhenHub Calendar", data=self._calendar_data)


async def async_step_calendar_by_type(self, user_input=None):
    """Schritt 2a: Welche Event-Typen sollen erscheinen?"""
    if user_input is None:
        return self.async_show_form(
            step_id="calendar_by_type",
            data_schema=vol.Schema({
                vol.Required(CONF_CALENDAR_TYPES, default=[
                    EVENT_TYPE_TRIP, EVENT_TYPE_MILESTONE,
                    EVENT_TYPE_ANNIVERSARY, EVENT_TYPE_SPECIAL,
                ]): SelectSelector(SelectSelectorConfig(
                    options=[
                        EVENT_TYPE_TRIP, EVENT_TYPE_MILESTONE,
                        EVENT_TYPE_ANNIVERSARY, EVENT_TYPE_SPECIAL,
                    ],
                    multiple=True,
                    translation_key="event_type",
                ))
            }),
        )
    self._calendar_data[CONF_CALENDAR_TYPES] = user_input[CONF_CALENDAR_TYPES]
    return self.async_create_entry(title="WhenHub Calendar", data=self._calendar_data)


async def async_step_calendar_specific(self, user_input=None):
    """Schritt 2b: Konkrete Events auswählen."""
    # Alle Event-Entries dynamisch laden (keine Kalender-Entries)
    event_entries = [
        e for e in self.hass.config_entries.async_entries(DOMAIN)
        if e.data.get(CONF_ENTRY_TYPE) != ENTRY_TYPE_CALENDAR
    ]
    options = [
        SelectOptionDict(value=e.entry_id, label=e.title)
        for e in event_entries
    ]

    if user_input is None:
        return self.async_show_form(
            step_id="calendar_specific",
            data_schema=vol.Schema({
                vol.Required(CONF_CALENDAR_EVENT_IDS): SelectSelector(
                    SelectSelectorConfig(options=options, multiple=True)
                )
            }),
        )
    self._calendar_data[CONF_CALENDAR_EVENT_IDS] = user_input[CONF_CALENDAR_EVENT_IDS]
    return self.async_create_entry(title="WhenHub Calendar", data=self._calendar_data)
```

### 3c: Options Flow für Kalender-Entry

```python
async def async_step_init(self, user_input=None):
    if self.config_entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
        return await self.async_step_calendar()
    # bisheriger Event-Options-Flow...

# Danach: async_step_calendar, async_step_calendar_by_type, async_step_calendar_specific
# analog zum Config Flow (ohne Duplikat-Check)
```

---

## Schritt 4: calendar.py (neue Datei)

```python
"""Calendar platform for WhenHub integration."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .calculations import (
    parse_date,
    anniversary_for_year,
    next_special_event,
    last_special_event,
    is_trip_active,
    is_date_today,
)
from .const import (
    DOMAIN,
    CONF_ENTRY_TYPE,
    ENTRY_TYPE_CALENDAR,
    CONF_CALENDAR_SCOPE,
    CONF_CALENDAR_TYPES,
    CONF_CALENDAR_EVENT_IDS,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
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
    """Calendar entity aggregating all WhenHub events."""

    _attr_has_entity_name = True
    _attr_name = None  # Uses device name

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_name = "WhenHub"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current active event (determines STATE_ON/OFF).

        STATE_ON wenn irgendein Event gerade aktiv ist:
        - Trip: heute zwischen Start und Ende
        - Milestone/Anniversary/Special: heute ist der Event-Tag
        """
        today = date.today()
        for entry in self._hass.config_entries.async_entries(DOMAIN):
            if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
                continue
            if not self._entry_in_scope(entry):
                continue
            current = _get_current_event(entry.data, today)
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
            if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
                continue
            if not self._entry_in_scope(entry):
                continue
            events.extend(_get_calendar_events(entry.data, start, end))

        return events

    def _entry_in_scope(self, entry: ConfigEntry) -> bool:
        """Check if an event entry is included in this calendar's scope."""
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
```

### Event-Berechnungsfunktionen (untere Hälfte von calendar.py)

```python
def _get_calendar_events(event_data: dict, start: date, end: date) -> list[CalendarEvent]:
    """Route event calculation by event type."""
    event_type = event_data.get(CONF_EVENT_TYPE)
    if event_type == EVENT_TYPE_TRIP:
        return _trip_events(event_data, start, end)
    if event_type == EVENT_TYPE_MILESTONE:
        return _milestone_events(event_data, start, end)
    if event_type == EVENT_TYPE_ANNIVERSARY:
        return _anniversary_events(event_data, start, end)
    if event_type == EVENT_TYPE_SPECIAL:
        return _special_events(event_data, start, end)
    return []


def _get_current_event(event_data: dict, today: date) -> CalendarEvent | None:
    """Return a CalendarEvent if this event is active today (for STATE_ON)."""
    event_type = event_data.get(CONF_EVENT_TYPE)
    name = event_data.get(CONF_EVENT_NAME, "")

    if event_type == EVENT_TYPE_TRIP:
        start = parse_date(event_data[CONF_START_DATE])
        end = parse_date(event_data[CONF_END_DATE])
        if start <= today <= end:
            return CalendarEvent(summary=name, start=start, end=end, description="Trip")

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
        # Special/DST: prüfe ob next_special_event == today
        # (DST-Events analog, next_dst_event verwenden)
        pass  # TODO: implementieren

    return None


def _trip_events(data: dict, start: date, end: date) -> list[CalendarEvent]:
    trip_start = parse_date(data[CONF_START_DATE])
    trip_end = parse_date(data[CONF_END_DATE])
    # Überschneidung: Trip-Start vor Zeitraum-Ende UND Trip-Ende nach Zeitraum-Start
    if trip_start <= end and trip_end >= start:
        return [CalendarEvent(
            summary=data[CONF_EVENT_NAME],
            start=trip_start,
            end=trip_end,
            description="Trip",
        )]
    return []


def _milestone_events(data: dict, start: date, end: date) -> list[CalendarEvent]:
    target = parse_date(data[CONF_TARGET_DATE])
    if start <= target <= end:
        return [CalendarEvent(
            summary=data[CONF_EVENT_NAME],
            start=target,
            end=target + timedelta(days=1),
            description="Milestone",
        )]
    return []


def _anniversary_events(data: dict, start: date, end: date) -> list[CalendarEvent]:
    """Return all anniversary occurrences in [start, end].

    WICHTIG: anniversary_for_year() aus calculations.py verwenden,
    NICHT original.replace(year=year) — sonst ValueError bei Feb 29!
    """
    original = parse_date(data[CONF_TARGET_DATE])
    name = data[CONF_EVENT_NAME]
    events = []

    for year in range(max(original.year, start.year), end.year + 1):
        occ = anniversary_for_year(original, year)  # Schaltjahr-sicher!
        if start <= occ <= end:
            year_number = year - original.year
            events.append(CalendarEvent(
                summary=f"{name} ({year_number}.)",
                start=occ,
                end=occ + timedelta(days=1),
                description="Anniversary",
            ))
    return events


def _special_events(data: dict, start: date, end: date) -> list[CalendarEvent]:
    """Return all special event occurrences in [start, end].

    Iteriert über alle Jahre im Zeitraum und ruft next_special_event() auf.
    Funktioniert für Fixed-Events (Weihnachten) und Calculated-Events (Ostern).
    DST-Events werden über next_dst_event() berechnet.
    """
    special_category = data.get(CONF_SPECIAL_CATEGORY)
    name = data.get(CONF_EVENT_NAME, "")
    events = []

    if special_category == "dst":
        # DST Events
        from .calculations import next_dst_event
        dst_type = data.get(CONF_DST_TYPE, "next_change")
        dst_region = data.get(CONF_DST_REGION, "eu")
        region_info = DST_REGIONS.get(dst_region, DST_REGIONS["eu"])

        for year in range(start.year, end.year + 1):
            # Berechne DST-Datum für dieses Jahr
            probe_date = date(year, 1, 1)
            occ = next_dst_event(region_info, dst_type, probe_date)
            if occ and start <= occ <= end:
                events.append(CalendarEvent(
                    summary=name,
                    start=occ,
                    end=occ + timedelta(days=1),
                    description="DST",
                ))
    else:
        # Reguläre Special Events
        special_type = data.get(CONF_SPECIAL_TYPE, "christmas_eve")
        special_info = SPECIAL_EVENTS.get(special_type, SPECIAL_EVENTS["christmas_eve"])

        for year in range(start.year, end.year + 1):
            probe_date = date(year, 1, 1)
            occ = next_special_event(special_info, probe_date)
            if occ and start <= occ <= end:
                events.append(CalendarEvent(
                    summary=name,
                    start=occ,
                    end=occ + timedelta(days=1),
                    description="Special",
                ))

    return events
```

---

## Schritt 5: Übersetzungen

### translations/en.json — neue Schlüssel

```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "event_type": "Type"
        },
        "data_description": {
          "event_type": "Select the type of event or choose WhenHub Calendar to add all events to your HA calendar."
        }
      },
      "calendar": {
        "title": "WhenHub Calendar",
        "description": "Choose which events should appear in the calendar.",
        "data": {
          "calendar_scope": "Scope"
        }
      },
      "calendar_by_type": {
        "title": "Filter by Type",
        "data": {
          "calendar_types": "Event types"
        }
      },
      "calendar_specific": {
        "title": "Select Events",
        "data": {
          "calendar_event_ids": "Events"
        }
      }
    },
    "abort": {
      "calendar_already_configured": "WhenHub Calendar is already set up. Only one calendar per instance is supported."
    }
  },
  "selector": {
    "event_type": {
      "options": {
        "trip": "Trip — Multi-day events like vacations or trips",
        "milestone": "Milestone — One-time important dates",
        "anniversary": "Anniversary — Yearly recurring events",
        "special": "Special Event — Holidays and calendar events",
        "calendar": "WhenHub Calendar — Show all events in HA calendar view"
      }
    },
    "calendar_scope": {
      "options": {
        "all": "All events",
        "by_type": "Filter by type",
        "specific": "Select specific events"
      }
    }
  }
}
```

### translations/de.json — entsprechend auf Deutsch

---

## Schritt 6: manifest.json

Version erhöhen: `2.2.2` → `2.3.0` (neues Feature, Minor-Version).

---

## Schritt 7: Tests

Testdatei: `tests/test_calendar_entity.py` (bereits erstellt, ~1600 Zeilen).

Nach Implementierung:
1. Testdatei nach `tests/custom_components/whenhub/` synchronisieren
2. Tests ausführen: `pytest tests/custom_components/whenhub/test_calendar_entity.py -v`
3. Imports in der Testdatei anpassen (lokale Konstanten → Import aus const.py)

---

## Status-Checkliste

- [ ] `const.py`: Neue Konstanten
- [ ] `__init__.py`: Entry-Typ-Routing, zwei Platform-Listen
- [ ] `config_flow.py`: Kalender als 5. Option im Event-Typ-Schritt
- [ ] `config_flow.py`: `async_step_calendar` + `async_step_calendar_by_type` + `async_step_calendar_specific`
- [ ] `config_flow.py`: Options Flow Kalender-Branch
- [ ] `calendar.py`: Neue Datei — `WhenHubCalendar` + alle `_*_events` Funktionen
- [ ] `calendar.py`: `_get_current_event` für Special/DST vervollständigen
- [ ] `translations/en.json`: Neue Schlüssel
- [ ] `translations/de.json`: Neue Schlüssel
- [ ] `manifest.json`: Version → 2.3.0
- [ ] Tests synchronisieren und ausführen
