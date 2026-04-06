# FR08: Calendar Entity Support

## Referenz

- **GitHub Issue:** [#3 - Feature request: Expose WhenHub events as Home Assistant calendar entities](https://github.com/moerk-o/WhenHub/issues/3)
- **Status:** Konzept / Planung

---

## Problem

WhenHub-Events sind aktuell nur als Sensor-Werte auf dem Dashboard sichtbar. Sie erscheinen nicht in der eingebauten HA-Kalenderansicht und sind nicht mit Standard-Kalender-Karten nutzbar.

---

## Ziel

Eine optionale `calendar.whenhub`-Entity, die alle (oder ausgewählte) WhenHub-Events in der HA-Kalenderansicht anzeigt.

---

## Lösungsansatz

### Architektur: Separater Config Entry

Der Kalender wird als **eigener Config Entry** realisiert - unabhängig von den einzelnen Event-Entries. Der User legt ihn explizit an über:

*Settings → Devices & Services → Add Integration → WhenHub → WhenHub Calendar*

So bleibt die bestehende Architektur unberührt. Wer keinen Kalender will, legt ihn einfach nicht an. Wer ihn wieder loswerden will, löscht nur diesen Entry - ohne ein einziges Event zu verlieren.

### Eine globale Calendar-Entity

Es gibt genau **eine** Calendar-Entity: `calendar.whenhub`.

Sie aggregiert über alle vorhandenen WhenHub-Config-Entries via `hass.config_entries.async_entries(DOMAIN)` und gibt die Events des angefragten Zeitraums zurück.

---

## Config Flow

**Schritt 1 - Scope wählen:**

```
WhenHub Calendar

Welche Events sollen im Kalender erscheinen?

○ Alle Events
○ Nach Typ filtern
○ Bestimmte Events auswählen
```

**Schritt 2a - Bei "Nach Typ":**

```
☑ Trips
☑ Anniversaries
☑ Milestones
☑ Special Events
```

**Schritt 2b - Bei "Bestimmte Events":**

Dynamische Liste aller vorhandenen WhenHub-Events zur Auswahl.
Wird beim Setup aus `hass.config_entries.async_entries(DOMAIN)` geladen.

Der Scope ist später über den Options Flow änderbar.

---

## Technische Umsetzung

### Neue Datei: `calendar.py`

Implementiert `CalendarEntity` mit der Methode `async_get_events(start_datetime, end_datetime)`.

HA übergibt immer einen Zeitraum (z.B. "zeige mir April 2026"). Die Calendar-Entity berechnet alle Events in diesem Zeitraum und gibt sie zurück. HA und die Kalender-Karte entscheiden dann was angezeigt wird.

### Event-Mapping pro Typ

| Event-Typ | Kalender-Verhalten |
|-----------|-------------------|
| **Trip** | Einmaliger Eintrag mit Start- und Enddatum (mehrtägiger Block) |
| **Milestone** | Einmaliger Eintrag am Zieldatum |
| **Anniversary** | Alle Occurrences im angefragten Zeitraum, rückwärts ab Originaldatum |
| **Special Event** | Alle Occurrences im angefragten Zeitraum (jährlich) |

### Anniversary & Special Events: Alle Occurrences

Für wiederkehrende Events werden **alle Vorkommen im angefragten Zeitraum** berechnet und zurückgegeben - nicht nur das nächste. Das bedeutet:

- Eine Anniversary mit Originaldatum `1988-04-21` liefert bei Anfrage 2020–2027 alle 8 Occurrences
- Im Titel kann das Jubiläum angezeigt werden: `"Geburtstag Jon (40.)"` - `years_on_next` ist bereits im Coordinator verfügbar
- Rückwärts bis zum Originaldatum, vorwärts unbegrenzt

```
async_get_events(2020-01-01, 2027-12-31)
→ "Geburtstag Jon (32.)"  21.04.2020
→ "Geburtstag Jon (33.)"  21.04.2021
→ "Geburtstag Jon (34.)"  21.04.2022
→ "Geburtstag Jon (35.)"  21.04.2023
→ "Geburtstag Jon (36.)"  21.04.2024
→ "Geburtstag Jon (37.)"  21.04.2025
→ "Geburtstag Jon (38.)"  21.04.2026
→ "Geburtstag Jon (39.)"  21.04.2027
```

### CalendarEvent Felder

| Feld | Wert |
|------|------|
| `summary` | Event-Name (z.B. "Dänemark Urlaub") |
| `start` | Start-Datum des Events |
| `end` | End-Datum (bei Milestone/Anniversary = start + 1 Tag) |
| `description` | Event-Typ (z.B. "Trip", "Anniversary") |

**Hinweis:** `notes` und `url` existieren aktuell nicht in WhenHub-Events. Sobald diese Felder ergänzt werden (eigener FR), können sie hier eingebunden werden.

### State der Calendar-Entity

`STATE_ON` wenn gerade ein Event aktiv ist (z.B. Trip läuft), sonst `STATE_OFF`. Damit sind auch Automationen möglich: *"Wenn calendar.whenhub an ist, zeige die Event-Karte"*.

---

## Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| `calendar.py` | Neu - CalendarEntity Implementierung |
| `__init__.py` | `calendar` Platform registrieren |
| `manifest.json` | Version erhöhen |
| `config_flow.py` | Neuer Entry-Typ "calendar" + Config/Options Flow |
| `const.py` | Neue Konstanten für Calendar-Konfiguration |
| `translations/en.json` | Calendar Config Flow Texte |
| `translations/de.json` | Calendar Config Flow Texte |

---

## Bewertung der ursprünglichen User-Anforderungen (Issue #3)

| Anforderung | Bewertung |
|-------------|-----------|
| Events appear in HA calendar views | ✅ Vollständig umsetzbar |
| Event title matches configured event name | ✅ Trivial |
| Description includes notes, URL, image reference | ⚠️ Nur event_type vorerst - notes/url existieren noch nicht |
| Anniversary events expose next upcoming occurrence | ✅ Besser: alle Occurrences im Zeitraum, inkl. Jubiläumsnummer im Titel |
| Calendar publishing optional via configuration | ✅ Separater Config Entry, optional anzulegen |

---

## Umsetzungskonzept

### Kernproblem: Zwei Entry-Typen im gleichen Domain

Aktuell geht `async_setup_entry` davon aus, dass jeder Entry ein Event ist und lädt `SENSOR + IMAGE + BINARY_SENSOR`. Der Kalender-Entry muss stattdessen `CALENDAR` laden. Lösung: ein `entry_type`-Marker im Config Entry.

```python
# const.py (neu)
CONF_ENTRY_TYPE = "entry_type"
ENTRY_TYPE_EVENT = "event"       # Standard - alle bestehenden Entries
ENTRY_TYPE_CALENDAR = "calendar" # Neu - nur für Kalender-Entry
CONF_CALENDAR_SCOPE = "calendar_scope"
CONF_CALENDAR_TYPES = "calendar_types"
CONF_CALENDAR_EVENT_IDS = "calendar_event_ids"
```

---

### __init__.py

Zwei Platform-Listen, dynamisch je nach Entry-Typ:

```python
EVENT_PLATFORMS = [Platform.SENSOR, Platform.IMAGE, Platform.BINARY_SENSOR]
CALENDAR_PLATFORMS = [Platform.CALENDAR]

async def async_setup_entry(hass, entry):
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
    return True
```

`async_unload_entry` funktioniert unverändert - es unloaded die jeweiligen Platforms korrekt.

---

### config_flow.py

#### Neuer erster Schritt

`async_step_user` wird zum Auswahlschritt: Event oder Kalender?

```python
async def async_step_user(self, user_input=None):
    if user_input is None:
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("setup_type"): SelectSelector(SelectSelectorConfig(
                    options=["event", "calendar"],
                    translation_key="setup_type",
                ))
            })
        )
    if user_input["setup_type"] == "calendar":
        return await self.async_step_calendar()
    return await self._show_event_type_form()  # bisheriger Flow
```

#### Kalender-Config Flow (3 Schritte)

```python
async def async_step_calendar(self, user_input=None):
    # Schritt 1: Scope wählen (all / by_type / specific)

async def async_step_calendar_by_type(self, user_input=None):
    # Schritt 2a: Welche Event-Typen?
    # MultiSelectSelector: trip, milestone, anniversary, special

async def async_step_calendar_specific(self, user_input=None):
    # Schritt 2b: Welche konkreten Events?
    # Dynamisch aus hass.config_entries.async_entries(DOMAIN)
    # Filtert Calendar-Entries raus, zeigt nur Event-Entries
```

Config Entry data für Kalender:
```python
{
    CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
    CONF_CALENDAR_SCOPE: "all" | "by_type" | "specific",
    CONF_CALENDAR_TYPES: ["trip", "anniversary"],     # bei by_type
    CONF_CALENDAR_EVENT_IDS: ["entry_id_1", ...],     # bei specific
}
```

Title des Entries: `"WhenHub Calendar"` (fest).

**Uniqueness:** Nur ein Kalender-Entry erlaubt. Im `async_step_calendar`:
```python
existing = [e for e in self.hass.config_entries.async_entries(DOMAIN)
            if e.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR]
if existing:
    return self.async_abort(reason="calendar_already_configured")
```

#### Options Flow für Kalender-Entry

Neuer Branch in `OptionsFlowHandler` (analog zu Event-Typen):
```python
async def async_step_init(self, user_input=None):
    if self.config_entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
        return await self.async_step_calendar()
    # bisheriger Event-Options-Flow
```

---

### calendar.py (neue Datei)

```python
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from datetime import timedelta, date

class WhenHubCalendar(CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = "WhenHub"  # → entity_id: calendar.whenhub

    async def async_get_events(self, hass, start_datetime, end_datetime):
        start = start_datetime.date()
        end = end_datetime.date()
        events = []

        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
                continue
            if not self._entry_in_scope(entry):
                continue
            events.extend(_get_calendar_events(entry.data, start, end))

        return events

    @property
    def event(self):
        # Für STATE_ON/STATE_OFF: aktuell laufendes Event (z.B. Trip)
        # Wird von HA genutzt um den Binary-State zu bestimmen
        ...
```

#### Berechnung der Kalender-Events pro Typ

Die Berechnungsfunktionen aus `calculations.py` werden direkt genutzt - nicht über den Coordinator (der hat nur "nächste Occurrence").

```python
def _get_calendar_events(event_data, start, end):
    event_type = event_data.get(CONF_EVENT_TYPE)

    if event_type == EVENT_TYPE_TRIP:
        return _trip_events(event_data, start, end)

    elif event_type == EVENT_TYPE_MILESTONE:
        return _milestone_events(event_data, start, end)

    elif event_type == EVENT_TYPE_ANNIVERSARY:
        return _anniversary_events(event_data, start, end)

    elif event_type == EVENT_TYPE_SPECIAL:
        return _special_events(event_data, start, end)
```

**Trip:**
```python
def _trip_events(data, start, end):
    trip_start = parse_date(data[CONF_START_DATE])
    trip_end = parse_date(data[CONF_END_DATE])
    if trip_start <= end and trip_end >= start:
        return [CalendarEvent(
            summary=data[CONF_EVENT_NAME],
            start=trip_start, end=trip_end,
            description="Trip",
        )]
    return []
```

**Milestone:**
```python
def _milestone_events(data, start, end):
    target = parse_date(data[CONF_TARGET_DATE])
    if start <= target <= end:
        return [CalendarEvent(
            summary=data[CONF_EVENT_NAME],
            start=target, end=target + timedelta(days=1),
            description="Milestone",
        )]
    return []
```

**Anniversary** (alle Occurrences im Zeitraum, mit Jubiläumsnummer):
```python
def _anniversary_events(data, start, end):
    original = parse_date(data[CONF_TARGET_DATE])
    events = []
    for year in range(max(original.year, start.year), end.year + 1):
        occ = original.replace(year=year)  # Schaltjahr-Handling analog next_anniversary()
        if start <= occ <= end:
            year_number = year - original.year
            events.append(CalendarEvent(
                summary=f"{data[CONF_EVENT_NAME]} ({year_number}.)",
                start=occ, end=occ + timedelta(days=1),
                description="Anniversary",
            ))
    return events
```

**Special Event** (analog, jährliche Occurrences):
```python
def _special_events(data, start, end):
    # next_special_event() pro Jahr im Zeitraum aufrufen
    ...
```

---

### CalendarEvent Felder

| Feld | Wert | Hinweis |
|------|------|---------|
| `summary` | Event-Name | Anniversary + "(N.)" |
| `start` | Startdatum | `date`-Objekt (ganztägig) |
| `end` | Enddatum | Trip: echtes Ende; sonst start + 1 Tag |
| `description` | Event-Typ | Später: Memo aus FR11 |
| `location` | - | Später: URL aus FR11 |

---

### Übersetzungen (neue Schlüssel)

```json
// en.json
"setup_type": {
  "event": "Event (Trip, Anniversary, Milestone, Special)",
  "calendar": "WhenHub Calendar"
},
"calendar_scope": {
  "all": "All events",
  "by_type": "Filter by type",
  "specific": "Select specific events"
},
"abort": {
  "calendar_already_configured": "WhenHub Calendar is already set up"
}
```

---

### Betroffene Dateien (Zusammenfassung)

| Datei | Änderung |
|-------|----------|
| `calendar.py` | **Neu** — CalendarEntity + Event-Berechnung |
| `__init__.py` | Entry-Typ-Routing, zwei Platform-Listen |
| `config_flow.py` | Neuer erster Schritt, Kalender-Flow, Kalender-Options-Flow |
| `const.py` | `CONF_ENTRY_TYPE`, `ENTRY_TYPE_*`, `CONF_CALENDAR_*` |
| `manifest.json` | Version erhöhen |
| `translations/en.json` | Neue Texte |
| `translations/de.json` | Neue Texte |

---

## Status

- [ ] `const.py`: Neue Konstanten
- [ ] `__init__.py`: Entry-Typ-Routing
- [ ] `config_flow.py`: Erster Schritt + Kalender-Flow
- [ ] `config_flow.py`: Options Flow für Kalender-Entry
- [ ] `calendar.py`: CalendarEntity + `async_get_events`
- [ ] `calendar.py`: Event-Berechnung pro Typ (Trip, Milestone, Anniversary, Special)
- [ ] Übersetzungen (en + de)
- [ ] Tests
