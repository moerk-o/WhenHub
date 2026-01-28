# DST (Daylight Saving Time) Feature Konzept

## Übersicht

Dieses Dokument beschreibt das Konzept zur Integration von Zeitumstellungs-Events (Daylight Saving Time / DST) in die WhenHub Home Assistant Integration.

**Version:** Draft 1.2
**Datum:** 2026-01-28
**Status:** Konzept finalisiert - bereit zur Implementierung
**Letzte Änderung:** Offene Punkte geklärt, Region im Options Flow änderbar

---

## 1. Motivation

Benutzer möchten wissen:
- Wann ist die nächste Zeitumstellung?
- Wann beginnt die Sommerzeit?
- Wann beginnt die Winterzeit?

DST ist **kein astronomisches Ereignis**, sondern eine **administrative/politische Regelung**. Die Daten variieren je nach Region und können sich durch politische Entscheidungen ändern.

---

## 2. Unterstützte Regionen

### 2.1 Regionen und ihre Regeln

| Region | Sommerzeit beginnt | Winterzeit beginnt |
|--------|--------------------|--------------------|
| **EU** | Letzter Sonntag im März, 02:00 → 03:00 | Letzter Sonntag im Oktober, 03:00 → 02:00 |
| **USA** | 2. Sonntag im März, 02:00 → 03:00 | 1. Sonntag im November, 02:00 → 01:00 |
| **Australien** | 1. Sonntag im Oktober, 02:00 → 03:00 | 1. Sonntag im April, 03:00 → 02:00 |
| **Neuseeland** | Letzter Sonntag im September, 02:00 → 03:00 | 1. Sonntag im April, 03:00 → 02:00 |

### 2.2 Hinweise

- **Australien:** Nur einige Bundesstaaten haben DST (NSW, VIC, TAS, SA, ACT). Queensland, NT, WA haben keine DST.
- **USA:** Arizona (außer Navajo Nation) und Hawaii haben keine DST.
- **Viele Länder haben KEINE DST:** China, Japan, Indien, Russland, Brasilien, Mexiko (seit 2022), etc.

### 2.3 Regions-Erkennung

Die Region wird basierend auf `hass.config.time_zone` vorbelegt:

```python
TIMEZONE_TO_REGION = {
    "Europe/": "eu",
    "America/New_York": "usa",
    "America/Chicago": "usa",
    "America/Denver": "usa",
    "America/Los_Angeles": "usa",
    "America/Toronto": "usa",
    "Australia/": "australia",
    "Pacific/Auckland": "new_zealand",
}
```

**Wenn keine Region erkannt wird:** Keine Vorbelegung, User muss manuell wählen.

**Erlaubnis:** User dürfen immer jede Region wählen, auch wenn sie in einer DST-freien Zone leben (Use Case: Expats).

---

## 3. Config Flow Design

### 3.1 Flow-Übersicht

```
1. Event-Typ wählen         → "Special Event"
2. Kategorie wählen         → "Zeitumstellung" (dst)
3. DST-Typ wählen           → [Nächster Wechsel | Sommerzeit | Winterzeit]
4. Region + Details         → Region auswählen + Event-Name + optionale Felder
```

### 3.2 Neue Steps

#### Step: `async_step_dst_type`

```
┌─────────────────────────────────────────────────────────┐
│  Zeitumstellung - Typ wählen                            │
│                                                         │
│  Welches Zeitumstellungs-Event möchtest du tracken?     │
│                                                         │
│  ○ Nächster Wechsel - Nächste Zeitumstellung            │
│  ○ Sommerzeit - Nächster Beginn der Sommerzeit          │
│  ○ Winterzeit - Nächster Beginn der Winterzeit          │
│                                                         │
│                                        [Weiter]         │
└─────────────────────────────────────────────────────────┘
```

#### Step: `async_step_dst_region`

```
┌─────────────────────────────────────────────────────────┐
│  Zeitumstellung - Region & Details                      │
│                                                         │
│  Region:       [EU (vorbelegt)              ▼]          │
│                                                         │
│  Event-Name:   [Sommerzeit EU                ]          │
│  Bild (optional):     [                      ]          │
│  Website (optional):  [                      ]          │
│  Notizen (optional):  [                      ]          │
│                                                         │
│                                        [Erstellen]      │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Routing in config_flow.py

```python
async def async_step_special_category(self, user_input):
    # ...
    self._special_category = user_input[CONF_SPECIAL_CATEGORY]

    # NEU: Routing für DST
    if self._special_category == "dst":
        return await self.async_step_dst_type()

    return await self.async_step_special_event()
```

---

## 4. Datenstrukturen (const.py)

### 4.1 Neue Konfigurationsschlüssel

```python
# Neue Config Keys
CONF_DST_TYPE = "dst_type"
CONF_DST_REGION = "dst_region"
```

### 4.2 DST-Typen

```python
DST_EVENT_TYPES = {
    "next_change": {
        "name": "Nächster Wechsel",
        "description": "Nächste Zeitumstellung (Sommer oder Winter)",
        "icon": "mdi:clock-time-four",
    },
    "next_summer": {
        "name": "Nächste Sommerzeit",
        "description": "Nächster Beginn der Sommerzeit (Uhr vor)",
        "icon": "mdi:weather-sunny",
    },
    "next_winter": {
        "name": "Nächste Winterzeit",
        "description": "Nächster Beginn der Winterzeit (Uhr zurück)",
        "icon": "mdi:weather-snowy",
    },
}
```

### 4.3 DST-Regionen

```python
DST_REGIONS = {
    "eu": {
        "name": "EU",
        "summer": {
            "rule": "last",      # "last" oder "nth"
            "weekday": 6,        # 0=Montag, 6=Sonntag
            "month": 3,          # März
        },
        "winter": {
            "rule": "last",
            "weekday": 6,
            "month": 10,         # Oktober
        },
    },
    "usa": {
        "name": "USA",
        "summer": {
            "rule": "nth",
            "weekday": 6,
            "month": 3,          # März
            "n": 2,              # 2. Sonntag
        },
        "winter": {
            "rule": "nth",
            "weekday": 6,
            "month": 11,         # November
            "n": 1,              # 1. Sonntag
        },
    },
    "australia": {
        "name": "Australien",
        "summer": {
            "rule": "nth",
            "weekday": 6,
            "month": 10,         # Oktober
            "n": 1,              # 1. Sonntag
        },
        "winter": {
            "rule": "nth",
            "weekday": 6,
            "month": 4,          # April
            "n": 1,              # 1. Sonntag
        },
    },
    "new_zealand": {
        "name": "Neuseeland",
        "summer": {
            "rule": "last",
            "weekday": 6,
            "month": 9,          # September
        },
        "winter": {
            "rule": "nth",
            "weekday": 6,
            "month": 4,          # April
            "n": 1,              # 1. Sonntag
        },
    },
}
```

### 4.4 Neue Special Event Kategorie

```python
SPECIAL_EVENT_CATEGORIES = {
    # ... bestehende Kategorien ...
    "dst": {
        "name": "Zeitumstellung",
        "description": "Sommer- und Winterzeitwechsel",
        "icon": "mdi:clock-time-four"
    }
}
```

### 4.5 Gespeicherte Config-Entry Daten

```python
{
    "event_type": "special",
    "special_category": "dst",
    "dst_type": "next_summer",       # NEU
    "dst_region": "eu",              # NEU
    "event_name": "Sommerzeit EU",
    "image_path": "",
    "website_url": "",
    "notes": "",
}
```

---

## 5. Berechnungslogik (calculations.py)

### 5.1 Bestehende Funktionen nutzen

Die folgenden bestehenden Funktionen werden wiederverwendet:

| Funktion | Verwendung für DST |
|----------|-------------------|
| `days_until(target_date, today)` | Tage bis zum DST-Event |
| `is_date_today(target_date, today)` | Prüfen ob DST heute ist |
| `days_between(start_date, end_date)` | Tage seit letztem Event (indirekt) |

### 5.2 Neue Funktionen

#### 5.2.1 `nth_weekday_of_month`

Berechnet den n-ten Wochentag eines Monats (z.B. 2. Sonntag im März).

```python
def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> Optional[date]:
    """Calculate the nth occurrence of a weekday in a month.

    Args:
        year: Year to calculate for
        month: Month (1-12)
        weekday: Weekday (0=Monday, 6=Sunday)
        n: Which occurrence (1=first, 2=second, etc.)

    Returns:
        Date of the nth weekday, or None if n is too large for the month

    Example:
        nth_weekday_of_month(2026, 3, 6, 2)  # 2. Sonntag im März 2026
        -> date(2026, 3, 8)
    """
    # Erster Tag des Monats
    first_day = date(year, month, 1)

    # Wochentag des ersten Tags (0=Montag, 6=Sonntag)
    first_weekday = first_day.weekday()

    # Tage bis zum ersten gewünschten Wochentag
    days_until_first = (weekday - first_weekday) % 7

    # Datum des ersten gewünschten Wochentags
    first_occurrence = first_day + timedelta(days=days_until_first)

    # n-te Vorkommen (n-1 Wochen nach dem ersten)
    result = first_occurrence + timedelta(weeks=n - 1)

    # Prüfen ob noch im selben Monat
    if result.month != month:
        return None

    return result
```

#### 5.2.2 `last_weekday_of_month`

Berechnet den letzten Wochentag eines Monats (z.B. letzter Sonntag im Oktober).

```python
def last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    """Calculate the last occurrence of a weekday in a month.

    Args:
        year: Year to calculate for
        month: Month (1-12)
        weekday: Weekday (0=Monday, 6=Sunday)

    Returns:
        Date of the last weekday in the month

    Example:
        last_weekday_of_month(2026, 10, 6)  # Letzter Sonntag im Oktober 2026
        -> date(2026, 10, 25)
    """
    # Letzter Tag des Monats
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # Wochentag des letzten Tags
    last_weekday = last_day.weekday()

    # Tage zurück zum gewünschten Wochentag
    days_back = (last_weekday - weekday) % 7

    return last_day - timedelta(days=days_back)
```

#### 5.2.3 `calculate_dst_date`

Berechnet das DST-Datum basierend auf Region und Typ.

```python
def calculate_dst_date(region_info: dict, dst_type: str, year: int) -> Optional[date]:
    """Calculate DST transition date for a region and type.

    Args:
        region_info: Region definition dict from DST_REGIONS (summer/winter rules)
        dst_type: "summer" or "winter"
        year: Year to calculate for

    Returns:
        Date of the DST transition, or None on error

    Example:
        calculate_dst_date(DST_REGIONS["eu"], "summer", 2026)
        -> date(2026, 3, 29)  # Letzter Sonntag im März 2026
    """
    if dst_type not in ("summer", "winter"):
        return None

    rule_info = region_info.get(dst_type)
    if not rule_info:
        return None

    rule = rule_info.get("rule")
    weekday = rule_info.get("weekday", 6)  # Default: Sonntag
    month = rule_info.get("month")

    if not month:
        return None

    if rule == "last":
        return last_weekday_of_month(year, month, weekday)
    elif rule == "nth":
        n = rule_info.get("n", 1)
        return nth_weekday_of_month(year, month, weekday, n)

    return None
```

#### 5.2.4 `next_dst_event`

Berechnet das nächste DST-Event.

```python
def next_dst_event(
    region_info: dict,
    dst_type: str,
    today: date
) -> Optional[date]:
    """Calculate next DST event date.

    Args:
        region_info: Region definition dict from DST_REGIONS
        dst_type: "next_change", "next_summer", or "next_winter"
        today: Current date

    Returns:
        Date of the next DST event
    """
    if dst_type == "next_summer":
        # Nächste Sommerzeit
        this_year = calculate_dst_date(region_info, "summer", today.year)
        if this_year and this_year >= today:
            return this_year
        return calculate_dst_date(region_info, "summer", today.year + 1)

    elif dst_type == "next_winter":
        # Nächste Winterzeit
        this_year = calculate_dst_date(region_info, "winter", today.year)
        if this_year and this_year >= today:
            return this_year
        return calculate_dst_date(region_info, "winter", today.year + 1)

    elif dst_type == "next_change":
        # Nächster Wechsel (egal welcher)
        next_summer = next_dst_event(region_info, "next_summer", today)
        next_winter = next_dst_event(region_info, "next_winter", today)

        if next_summer and next_winter:
            return min(next_summer, next_winter)
        return next_summer or next_winter

    return None
```

#### 5.2.5 `last_dst_event`

Berechnet das letzte DST-Event.

```python
def last_dst_event(
    region_info: dict,
    dst_type: str,
    today: date
) -> Optional[date]:
    """Calculate last DST event date.

    Args:
        region_info: Region definition dict from DST_REGIONS
        dst_type: "next_change", "next_summer", or "next_winter"
        today: Current date

    Returns:
        Date of the last DST event
    """
    if dst_type == "next_summer":
        # Letzte Sommerzeit
        this_year = calculate_dst_date(region_info, "summer", today.year)
        if this_year and this_year < today:
            return this_year
        return calculate_dst_date(region_info, "summer", today.year - 1)

    elif dst_type == "next_winter":
        # Letzte Winterzeit
        this_year = calculate_dst_date(region_info, "winter", today.year)
        if this_year and this_year < today:
            return this_year
        return calculate_dst_date(region_info, "winter", today.year - 1)

    elif dst_type == "next_change":
        # Letzter Wechsel (egal welcher)
        last_summer = last_dst_event(region_info, "next_summer", today)
        last_winter = last_dst_event(region_info, "next_winter", today)

        if last_summer and last_winter:
            return max(last_summer, last_winter)
        return last_summer or last_winter

    return None
```

#### 5.2.6 `is_dst_active` (NEU - nur für DST)

Prüft ob aktuell Sommerzeit (DST) aktiv ist.

```python
def is_dst_active(region_info: dict, today: date) -> bool:
    """Check if daylight saving time is currently active.

    Determines whether we are currently in summer time (DST) or
    winter time (standard time) by comparing the most recent
    summer and winter transitions.

    Args:
        region_info: Region definition dict from DST_REGIONS
        today: Current date

    Returns:
        True if summer time (DST) is currently active,
        False if winter time (standard time) is active

    Example:
        # EU, 1. Juni 2026 (zwischen März und Oktober)
        is_dst_active(DST_REGIONS["eu"], date(2026, 6, 1))
        -> True  # Sommerzeit aktiv

        # EU, 1. Dezember 2026 (nach Oktober)
        is_dst_active(DST_REGIONS["eu"], date(2026, 12, 1))
        -> False  # Winterzeit aktiv
    """
    # Letzte Sommerzeit-Umstellung
    last_summer = last_dst_event(region_info, "next_summer", today)
    # Letzte Winterzeit-Umstellung
    last_winter = last_dst_event(region_info, "next_winter", today)

    # Wenn keine Events gefunden wurden
    if last_summer is None and last_winter is None:
        return False
    if last_summer is None:
        return False  # Nur Winterzeit bekannt -> Winterzeit aktiv
    if last_winter is None:
        return True   # Nur Sommerzeit bekannt -> Sommerzeit aktiv

    # Das neuere Event bestimmt den aktuellen Zustand
    # Wenn Sommerzeit zuletzt war -> Sommerzeit aktiv
    # Wenn Winterzeit zuletzt war -> Winterzeit aktiv
    return last_summer > last_winter
```

**Timeline-Beispiel (EU 2026):**

```
Jan  Feb  Mär  Apr  Mai  Jun  Jul  Aug  Sep  Okt  Nov  Dez
|-------- Winterzeit --------|
                    29.3.    |---------- Sommerzeit ----------|
                                                        25.10. |-- Winterzeit --|

is_dst_active:  false        true                              false
```

---

## 6. Sensor-Implementierung

### 6.1 Sensor-Übersicht

DST-Events nutzen die gleichen Basis-Sensoren wie andere Special Events, plus einen **exklusiven Binary Sensor** `is_dst_active`.

#### Reguläre Sensoren (5 Stück - wie andere Special Events)

| Sensor | Typ | Device Class | Beschreibung |
|--------|-----|--------------|--------------|
| `event_date` | Timestamp | `timestamp` | Datum der nächsten Zeitumstellung |
| `next_date` | Timestamp | `timestamp` | Identisch mit event_date (expliziter Name) |
| `last_date` | Timestamp | `timestamp` | Datum der letzten Zeitumstellung |
| `days_until` | Integer | `duration` | Tage bis zur nächsten Umstellung |
| `days_since_last` | Integer | `duration` | Tage seit der letzten Umstellung |

#### Binary Sensoren (2 Stück - 1 mehr als andere Special Events)

| Sensor | Beschreibung | Nur DST? |
|--------|--------------|----------|
| `is_today` | Heute ist Zeitumstellung | Nein (alle Special Events) |
| `is_dst_active` | **Sommerzeit ist gerade aktiv** | **Ja (nur DST)** |

### 6.2 Wichtig: Typ-Abhängigkeit der Sensoren

Die Sensor-Werte hängen vom gewählten `dst_type` ab:

| dst_type | `next_date` / `days_until` | `last_date` / `days_since_last` |
|----------|---------------------------|--------------------------------|
| `next_change` | Nächste Umstellung (Sommer **ODER** Winter) | Letzte Umstellung (Sommer **ODER** Winter) |
| `next_summer` | Nächste **Sommerzeit** | Letzte **Sommerzeit** |
| `next_winter` | Nächste **Winterzeit** | Letzte **Winterzeit** |

**Beispiel (EU, heute = 1. Juni 2026):**

| dst_type | next_date | last_date | days_until | days_since_last |
|----------|-----------|-----------|------------|-----------------|
| `next_change` | 25.10.2026 (Winter) | 29.03.2026 (Sommer) | 146 | 64 |
| `next_summer` | 28.03.2027 | 29.03.2026 | 300 | 64 |
| `next_winter` | 25.10.2026 | 26.10.2025 | 146 | 219 |

### 6.3 Der `is_dst_active` Binary Sensor

Dieser Sensor ist **unabhängig vom gewählten `dst_type`** und zeigt immer den aktuellen Zustand an:

| Wert | Bedeutung |
|------|-----------|
| `true` / `on` | Sommerzeit ist aktiv (Uhren vorgestellt) |
| `false` / `off` | Winterzeit/Normalzeit ist aktiv |

**Implementierung in const.py:**

```python
# Binary Sensor Types für DST (erweitert SPECIAL_BINARY_SENSOR_TYPES)
DST_BINARY_SENSOR_TYPES = {
    "is_today": {
        "name": "Is Today",
        "icon": "mdi:calendar-today",
        "device_class": "occurrence",
    },
    "is_dst_active": {  # NEU - nur für DST
        "name": "DST Active",
        "icon": "mdi:weather-sunny",
        "device_class": None,  # Kein Standard device_class passt
    },
}
```

### 6.4 Coordinator-Erweiterung

In `coordinator.py` muss `_calculate_special_data()` erweitert werden:

```python
def _calculate_special_data(self, config_data: dict, today: date) -> dict:
    special_category = config_data.get(CONF_SPECIAL_CATEGORY)

    # NEU: DST-Kategorie
    if special_category == "dst":
        return self._calculate_dst_data(config_data, today)

    # Bestehende Special Event Logik
    special_type = config_data.get(CONF_SPECIAL_TYPE)
    special_info = SPECIAL_EVENTS.get(special_type, {})
    # ...
```

```python
def _calculate_dst_data(self, config_data: dict, today: date) -> dict:
    """Calculate DST event data."""
    from .const import DST_REGIONS
    from .calculations import (
        next_dst_event,
        last_dst_event,
        is_dst_active,
        days_until,
    )

    dst_type = config_data.get(CONF_DST_TYPE, "next_change")
    dst_region = config_data.get(CONF_DST_REGION, "eu")
    region_info = DST_REGIONS.get(dst_region, {})

    next_date = next_dst_event(region_info, dst_type, today)
    last_date = last_dst_event(region_info, dst_type, today)

    return {
        # Reguläre Sensoren (typ-abhängig)
        "days_until": days_until(next_date, today) if next_date else None,
        "days_since_last": days_until(today, last_date) if last_date else None,
        "event_date": self._date_to_datetime(next_date),
        "next_date": self._date_to_datetime(next_date),
        "last_date": self._date_to_datetime(last_date),

        # Binary Sensoren
        "is_today": next_date == today if next_date else False,
        "is_dst_active": is_dst_active(region_info, today),  # NEU

        # Metadaten
        "dst_type": dst_type,
        "dst_region": dst_region,
    }
```

### 6.5 Zusammenfassung: Alle DST-Sensoren

```
DST Event (z.B. "Sommerzeit EU")
│
├── Reguläre Sensoren (5 Stück)
│   ├── event_date        → Timestamp nächstes Event (typ-abhängig)
│   ├── next_date         → Timestamp nächstes Event (typ-abhängig)
│   ├── last_date         → Timestamp letztes Event (typ-abhängig)
│   ├── days_until        → Tage bis nächstes Event (typ-abhängig)
│   └── days_since_last   → Tage seit letztem Event (typ-abhängig)
│
└── Binary Sensoren (2 Stück)
    ├── is_today          → Heute ist Zeitumstellung (typ-abhängig)
    └── is_dst_active     → Sommerzeit aktiv (typ-UNABHÄNGIG, nur bei DST)
```

---

## 7. Übersetzungen

### 7.1 de.json Erweiterungen

```json
{
  "config": {
    "step": {
      "dst_type": {
        "title": "Zeitumstellung - Typ wählen",
        "description": "Welches Zeitumstellungs-Event möchtest du tracken?",
        "data": {
          "dst_type": "Event-Typ"
        },
        "data_description": {
          "dst_type": "Wähle ob du den nächsten Wechsel, die Sommerzeit oder die Winterzeit tracken möchtest"
        }
      },
      "dst_region": {
        "title": "Zeitumstellung - Region & Details",
        "description": "Wähle die Region und gib dem Event einen Namen",
        "data": {
          "dst_region": "Region",
          "event_name": "Event-Name",
          "image_path": "Bildpfad (optional)",
          "website_url": "Website URL (optional)",
          "notes": "Notizen (optional)"
        },
        "data_description": {
          "dst_region": "In welcher Region gelten die DST-Regeln?",
          "event_name": "z.B. 'Sommerzeit EU' oder 'Zeitumstellung'",
          "image_path": "Pfad zu einem Bild, z.B. /local/images/dst.jpg",
          "website_url": "Relevante URL zum Event",
          "notes": "Zusätzliche Informationen"
        }
      }
    }
  },
  "selector": {
    "dst_type": {
      "options": {
        "next_change": "Nächster Wechsel - Nächste Zeitumstellung (Sommer oder Winter)",
        "next_summer": "Sommerzeit - Nächster Beginn der Sommerzeit",
        "next_winter": "Winterzeit - Nächster Beginn der Winterzeit"
      }
    },
    "dst_region": {
      "options": {
        "eu": "EU - Letzter Sonntag März/Oktober",
        "usa": "USA - 2. Sonntag März / 1. Sonntag November",
        "australia": "Australien - 1. Sonntag Oktober/April",
        "new_zealand": "Neuseeland - Letzter Sonntag September / 1. Sonntag April"
      }
    },
    "special_category": {
      "options": {
        "traditional": "Traditionelle Feiertage",
        "calendar": "Kalendarische Feiertage",
        "astronomical": "Astronomische Events",
        "dst": "Zeitumstellung"
      }
    }
  },
  "entity": {
    "binary_sensor": {
      "is_dst_active": {
        "name": "Sommerzeit aktiv"
      }
    }
  }
}
```

### 7.2 en.json Erweiterungen

```json
{
  "config": {
    "step": {
      "dst_type": {
        "title": "Daylight Saving Time - Choose type",
        "description": "Which DST event do you want to track?",
        "data": {
          "dst_type": "Event type"
        },
        "data_description": {
          "dst_type": "Choose whether to track the next change, summer time, or winter time"
        }
      },
      "dst_region": {
        "title": "Daylight Saving Time - Region & Details",
        "description": "Select the region and name your event",
        "data": {
          "dst_region": "Region",
          "event_name": "Event name",
          "image_path": "Image path (optional)",
          "website_url": "Website URL (optional)",
          "notes": "Notes (optional)"
        },
        "data_description": {
          "dst_region": "Which region's DST rules apply?",
          "event_name": "e.g. 'Summer Time EU' or 'DST Change'",
          "image_path": "Path to an image, e.g. /local/images/dst.jpg",
          "website_url": "Relevant URL for the event",
          "notes": "Additional information"
        }
      }
    }
  },
  "selector": {
    "dst_type": {
      "options": {
        "next_change": "Next change - Next DST transition (summer or winter)",
        "next_summer": "Summer time - Next start of daylight saving time",
        "next_winter": "Winter time - Next start of standard time"
      }
    },
    "dst_region": {
      "options": {
        "eu": "EU - Last Sunday March/October",
        "usa": "USA - 2nd Sunday March / 1st Sunday November",
        "australia": "Australia - 1st Sunday October/April",
        "new_zealand": "New Zealand - Last Sunday September / 1st Sunday April"
      }
    },
    "special_category": {
      "options": {
        "traditional": "Traditional Holidays",
        "calendar": "Calendar Holidays",
        "astronomical": "Astronomical Events",
        "dst": "Daylight Saving Time"
      }
    }
  },
  "entity": {
    "binary_sensor": {
      "is_dst_active": {
        "name": "Daylight Saving Time active"
      }
    }
  }
}
```

---

## 8. Testing

### 8.1 Test-Strategie

Alle Berechnungen müssen für **jede Region** und **jeden Typ** getestet werden.

### 8.2 Test-Matrix

#### Reguläre Sensor-Tests

| Region | next_change | next_summer | next_winter |
|--------|-------------|-------------|-------------|
| EU | ✓ | ✓ | ✓ |
| USA | ✓ | ✓ | ✓ |
| Australien | ✓ | ✓ | ✓ |
| Neuseeland | ✓ | ✓ | ✓ |

**Gesamt: 4 Regionen × 3 Typen = 12 Basis-Kombinationen**

#### is_dst_active Tests (NEU)

| Region | Winterzeit | Sommerzeit | Übergang Sommer | Übergang Winter |
|--------|------------|------------|-----------------|-----------------|
| EU | ✓ | ✓ | ✓ | ✓ |
| USA | ✓ | ✓ | ✓ | ✓ |
| Australien | ✓ | ✓ | ✓ | ✓ |
| Neuseeland | ✓ | ✓ | ✓ | ✓ |

**Gesamt: 4 Regionen × 4 Szenarien = 16 is_dst_active Tests**

### 8.3 Test-Szenarien pro Kombination

Für jede der 12 Kombinationen (reguläre Sensoren):

1. **Vor dem Event** - `today` ist vor dem nächsten Event
2. **Am Event-Tag** - `today` ist genau am Event-Tag
3. **Nach dem Event** - `today` ist nach dem Event (nächstes Jahr relevant)
4. **Jahreswechsel** - Event im Januar, heute im Dezember
5. **last_dst_event** - Berechnung des letzten Events

Für is_dst_active (pro Region):

1. **Mitten in Winterzeit** - z.B. Januar (EU)
2. **Mitten in Sommerzeit** - z.B. Juni (EU)
3. **Tag vor Sommerzeit-Wechsel** - noch Winterzeit
4. **Tag des Sommerzeit-Wechsels** - bereits Sommerzeit
5. **Tag vor Winterzeit-Wechsel** - noch Sommerzeit
6. **Tag des Winterzeit-Wechsels** - bereits Winterzeit

**Gesamt: 12 × 5 + 4 × 6 = 60 + 24 = 84 Tests (mindestens)**

### 8.4 Zusätzliche Tests

#### 8.4.1 Basis-Funktionen

```python
# test_calculations.py

class TestNthWeekdayOfMonth:
    """Tests for nth_weekday_of_month function."""

    def test_first_sunday_march_2026(self):
        """1. Sonntag im März 2026 = 1. März"""
        result = nth_weekday_of_month(2026, 3, 6, 1)
        assert result == date(2026, 3, 1)

    def test_second_sunday_march_2026(self):
        """2. Sonntag im März 2026 = 8. März (USA DST)"""
        result = nth_weekday_of_month(2026, 3, 6, 2)
        assert result == date(2026, 3, 8)

    def test_fifth_sunday_returns_none(self):
        """5. Sonntag existiert nicht immer"""
        result = nth_weekday_of_month(2026, 2, 6, 5)
        assert result is None


class TestLastWeekdayOfMonth:
    """Tests for last_weekday_of_month function."""

    def test_last_sunday_march_2026(self):
        """Letzter Sonntag im März 2026 = 29. März (EU DST)"""
        result = last_weekday_of_month(2026, 3, 6)
        assert result == date(2026, 3, 29)

    def test_last_sunday_october_2026(self):
        """Letzter Sonntag im Oktober 2026 = 25. Oktober (EU Winter)"""
        result = last_weekday_of_month(2026, 10, 6)
        assert result == date(2026, 10, 25)
```

#### 8.4.2 DST-Berechnungen

```python
class TestDSTCalculations:
    """Tests for DST date calculations."""

    # === EU Tests ===

    @freeze_time("2026-01-15")
    def test_eu_next_summer_before_march(self):
        """EU: Vor März -> Sommerzeit dieses Jahr"""
        region = DST_REGIONS["eu"]
        result = next_dst_event(region, "next_summer", date(2026, 1, 15))
        assert result == date(2026, 3, 29)

    @freeze_time("2026-04-01")
    def test_eu_next_summer_after_march(self):
        """EU: Nach März -> Sommerzeit nächstes Jahr"""
        region = DST_REGIONS["eu"]
        result = next_dst_event(region, "next_summer", date(2026, 4, 1))
        assert result == date(2027, 3, 28)

    @freeze_time("2026-03-29")
    def test_eu_summer_is_today(self):
        """EU: Am Tag der Sommerzeit"""
        region = DST_REGIONS["eu"]
        result = next_dst_event(region, "next_summer", date(2026, 3, 29))
        assert result == date(2026, 3, 29)  # Heute ist noch gültig

    @freeze_time("2026-06-01")
    def test_eu_next_change_after_summer(self):
        """EU: Nach Sommerzeit -> Winterzeit ist näher"""
        region = DST_REGIONS["eu"]
        result = next_dst_event(region, "next_change", date(2026, 6, 1))
        assert result == date(2026, 10, 25)  # Winterzeit

    # === USA Tests ===

    @freeze_time("2026-01-15")
    def test_usa_next_summer_before_march(self):
        """USA: 2. Sonntag im März 2026"""
        region = DST_REGIONS["usa"]
        result = next_dst_event(region, "next_summer", date(2026, 1, 15))
        assert result == date(2026, 3, 8)

    @freeze_time("2026-10-01")
    def test_usa_next_winter(self):
        """USA: 1. Sonntag im November 2026"""
        region = DST_REGIONS["usa"]
        result = next_dst_event(region, "next_winter", date(2026, 10, 1))
        assert result == date(2026, 11, 1)

    # === Australien Tests ===

    @freeze_time("2026-09-01")
    def test_australia_next_summer(self):
        """Australien: 1. Sonntag im Oktober 2026"""
        region = DST_REGIONS["australia"]
        result = next_dst_event(region, "next_summer", date(2026, 9, 1))
        assert result == date(2026, 10, 4)

    # === Neuseeland Tests ===

    @freeze_time("2026-09-01")
    def test_new_zealand_next_summer(self):
        """Neuseeland: Letzter Sonntag im September 2026"""
        region = DST_REGIONS["new_zealand"]
        result = next_dst_event(region, "next_summer", date(2026, 9, 1))
        assert result == date(2026, 9, 27)


class TestLastDSTEvent:
    """Tests for last DST event calculations."""

    @freeze_time("2026-06-01")
    def test_eu_last_summer(self):
        """EU: Letzter Sommerzeit-Wechsel war März 2026"""
        region = DST_REGIONS["eu"]
        result = last_dst_event(region, "next_summer", date(2026, 6, 1))
        assert result == date(2026, 3, 29)

    @freeze_time("2026-02-01")
    def test_eu_last_winter(self):
        """EU: Letzter Winterzeit-Wechsel war Oktober 2025"""
        region = DST_REGIONS["eu"]
        result = last_dst_event(region, "next_winter", date(2026, 2, 1))
        assert result == date(2025, 10, 26)


class TestIsDSTActive:
    """Tests for is_dst_active function."""

    # === EU Tests ===

    @freeze_time("2026-01-15")
    def test_eu_winter_january(self):
        """EU: Januar -> Winterzeit aktiv"""
        region = DST_REGIONS["eu"]
        assert is_dst_active(region, date(2026, 1, 15)) is False

    @freeze_time("2026-03-28")
    def test_eu_day_before_summer(self):
        """EU: Tag vor Sommerzeit -> noch Winterzeit"""
        region = DST_REGIONS["eu"]
        assert is_dst_active(region, date(2026, 3, 28)) is False

    @freeze_time("2026-03-29")
    def test_eu_summer_transition_day(self):
        """EU: Tag der Sommerzeit-Umstellung -> Sommerzeit aktiv"""
        region = DST_REGIONS["eu"]
        # Am Tag der Umstellung gilt bereits die neue Zeit
        assert is_dst_active(region, date(2026, 3, 29)) is True

    @freeze_time("2026-06-15")
    def test_eu_summer_june(self):
        """EU: Juni -> Sommerzeit aktiv"""
        region = DST_REGIONS["eu"]
        assert is_dst_active(region, date(2026, 6, 15)) is True

    @freeze_time("2026-10-24")
    def test_eu_day_before_winter(self):
        """EU: Tag vor Winterzeit -> noch Sommerzeit"""
        region = DST_REGIONS["eu"]
        assert is_dst_active(region, date(2026, 10, 24)) is True

    @freeze_time("2026-10-25")
    def test_eu_winter_transition_day(self):
        """EU: Tag der Winterzeit-Umstellung -> Winterzeit aktiv"""
        region = DST_REGIONS["eu"]
        assert is_dst_active(region, date(2026, 10, 25)) is False

    @freeze_time("2026-12-15")
    def test_eu_winter_december(self):
        """EU: Dezember -> Winterzeit aktiv"""
        region = DST_REGIONS["eu"]
        assert is_dst_active(region, date(2026, 12, 15)) is False

    # === USA Tests ===

    @freeze_time("2026-03-07")
    def test_usa_day_before_summer(self):
        """USA: Tag vor Sommerzeit (7. März) -> noch Winterzeit"""
        region = DST_REGIONS["usa"]
        assert is_dst_active(region, date(2026, 3, 7)) is False

    @freeze_time("2026-03-08")
    def test_usa_summer_transition_day(self):
        """USA: 2. Sonntag März (8. März 2026) -> Sommerzeit aktiv"""
        region = DST_REGIONS["usa"]
        assert is_dst_active(region, date(2026, 3, 8)) is True

    @freeze_time("2026-11-01")
    def test_usa_winter_transition_day(self):
        """USA: 1. Sonntag November (1. Nov 2026) -> Winterzeit aktiv"""
        region = DST_REGIONS["usa"]
        assert is_dst_active(region, date(2026, 11, 1)) is False

    # === Australien Tests (Südhalbkugel!) ===

    @freeze_time("2026-04-05")
    def test_australia_winter_transition_day(self):
        """Australien: 1. Sonntag April -> Winterzeit aktiv"""
        region = DST_REGIONS["australia"]
        assert is_dst_active(region, date(2026, 4, 5)) is False

    @freeze_time("2026-07-15")
    def test_australia_winter_july(self):
        """Australien: Juli (Winter auf Südhalbkugel) -> Winterzeit"""
        region = DST_REGIONS["australia"]
        assert is_dst_active(region, date(2026, 7, 15)) is False

    @freeze_time("2026-10-04")
    def test_australia_summer_transition_day(self):
        """Australien: 1. Sonntag Oktober -> Sommerzeit aktiv"""
        region = DST_REGIONS["australia"]
        assert is_dst_active(region, date(2026, 10, 4)) is True

    @freeze_time("2026-12-15")
    def test_australia_summer_december(self):
        """Australien: Dezember (Sommer auf Südhalbkugel) -> Sommerzeit"""
        region = DST_REGIONS["australia"]
        assert is_dst_active(region, date(2026, 12, 15)) is True
```

### 8.5 Bekannte DST-Daten zur Verifizierung

#### EU

| Jahr | Sommerzeit (März) | Winterzeit (Oktober) |
|------|-------------------|----------------------|
| 2025 | 30. März | 26. Oktober |
| 2026 | 29. März | 25. Oktober |
| 2027 | 28. März | 31. Oktober |
| 2028 | 26. März | 29. Oktober |

#### USA

| Jahr | Sommerzeit (März) | Winterzeit (November) |
|------|-------------------|----------------------|
| 2025 | 9. März | 2. November |
| 2026 | 8. März | 1. November |
| 2027 | 14. März | 7. November |
| 2028 | 12. März | 5. November |

---

## 9. Implementierungsreihenfolge

### Phase 1: Berechnungslogik
1. `nth_weekday_of_month()` in calculations.py
2. `last_weekday_of_month()` in calculations.py
3. `calculate_dst_date()` in calculations.py
4. `next_dst_event()` in calculations.py
5. `last_dst_event()` in calculations.py
6. `is_dst_active()` in calculations.py **(NEU)**
7. Unit-Tests für alle Funktionen (inkl. is_dst_active)

### Phase 2: Konstanten
1. `CONF_DST_TYPE`, `CONF_DST_REGION` in const.py
2. `DST_EVENT_TYPES` in const.py
3. `DST_REGIONS` in const.py
4. `DST_BINARY_SENSOR_TYPES` in const.py **(NEU - enthält is_dst_active)**
5. `SPECIAL_EVENT_CATEGORIES["dst"]` in const.py

### Phase 3: Config Flow
1. `async_step_dst_type()` in config_flow.py
2. `async_step_dst_region()` in config_flow.py
3. Routing in `async_step_special_category()`
4. Options Flow Erweiterung **(Region änderbar: JA)**

### Phase 4: Coordinator & Sensoren
1. `_calculate_dst_data()` in coordinator.py (inkl. is_dst_active)
2. Erweiterung von `_calculate_special_data()` für DST-Routing
3. DST-spezifischer Binary Sensor für `is_dst_active` in binary_sensor.py

### Phase 5: Übersetzungen
1. de.json Erweiterungen (inkl. is_dst_active)
2. en.json Erweiterungen (inkl. is_dst_active)

### Phase 6: Integration Tests
1. Config Flow Tests
2. Sensor-Erstellungs-Tests
3. is_dst_active Binary Sensor Tests
4. End-to-End Tests

---

## 10. Referenzen

- [Daylight saving time by country - Wikipedia](https://en.wikipedia.org/wiki/Daylight_saving_time_by_country)
- [Daylight Saving Time Around the World - timeanddate.com](https://www.timeanddate.com/time/dst/)
- [Home Assistant Config Flow Documentation](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
