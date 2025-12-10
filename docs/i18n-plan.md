# WhenHub i18n Umsetzungsplan

## Aktueller Stand

- `strings.json` existiert - aber nur auf Deutsch (falsch!)
- Kein `translations/` Ordner
- Keine Entity-Übersetzungen (Sensor-Namen hardcoded in `const.py`)
- Special Events haben deutsche Namen in `const.py`

## Ziel-Dateistruktur

```
custom_components/whenhub/
├── strings.json          # Englisch (Fallback/Basis)
└── translations/
    └── de.json           # Deutsche Übersetzung
```

## Phase 1: Dateistruktur anlegen

1. `translations/` Ordner erstellen
2. Aktuelle `strings.json` (Deutsch) nach `translations/de.json` kopieren
3. `strings.json` ins Englische übersetzen

## Phase 2: Entity-Übersetzungen hinzufügen

### strings.json erweitern um `entity`-Sektion:

```json
{
  "entity": {
    "sensor": {
      "days_until": { "name": "Days until start" },
      "days_until_end": { "name": "Days until end" },
      "event_date": { "name": "Event date" },
      "trip_left_days": { "name": "Trip days remaining" },
      "trip_left_percent": { "name": "Trip percent remaining" },
      "days_until_next": { "name": "Days until next" },
      "days_since_last": { "name": "Days since last" },
      "occurrences_count": { "name": "Occurrences count" },
      "next_date": { "name": "Next date" },
      "last_date": { "name": "Last date" }
    },
    "binary_sensor": {
      "trip_starts_today": { "name": "Trip starts today" },
      "trip_active_today": { "name": "Trip active today" },
      "trip_ends_today": { "name": "Trip ends today" },
      "is_today": { "name": "Is today" }
    }
  }
}
```

### Code-Änderungen in Sensor-Klassen:

In `sensors/base.py` (BaseSensor.__init__):
```python
self._attr_has_entity_name = True
self._attr_translation_key = sensor_type  # z.B. "days_until"
# ENTFERNEN: self._attr_name = f"{event_name} {sensor_name}"
```

In `binary_sensor.py` (BaseBinarySensor.__init__):
```python
self._attr_has_entity_name = True
self._attr_translation_key = sensor_type
# ENTFERNEN: self._attr_name = ...
```

## Phase 3: Special Events übersetzen

### Problem:
Special Events (Heilig Abend, Ostersonntag, etc.) sind in `const.py` hardcoded auf Deutsch.

### Lösung:
`selector`-Sektion in strings.json verwenden + Config Flow anpassen.

### strings.json:
```json
{
  "selector": {
    "special_type": {
      "options": {
        "christmas_eve": "Christmas Eve",
        "christmas_day": "Christmas Day",
        "boxing_day": "Boxing Day",
        "halloween": "Halloween",
        "easter": "Easter Sunday",
        "pentecost": "Pentecost Sunday",
        "nikolaus": "St. Nicholas Day",
        "advent_1": "1st Advent",
        "advent_2": "2nd Advent",
        "advent_3": "3rd Advent",
        "advent_4": "4th Advent",
        "new_year": "New Year's Day",
        "new_years_eve": "New Year's Eve",
        "spring_start": "Spring Equinox",
        "summer_start": "Summer Solstice",
        "autumn_start": "Autumn Equinox",
        "winter_start": "Winter Solstice"
      }
    },
    "special_category": {
      "options": {
        "traditional": "Traditional Holidays",
        "calendar": "Calendar Holidays",
        "astronomical": "Astronomical Events"
      }
    }
  }
}
```

### Config Flow anpassen:
`vol.In()` ersetzen durch `SelectSelector` mit `translation_key`:

```python
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

# Statt:
vol.Required(CONF_SPECIAL_TYPE): vol.In(special_options)

# Neu:
vol.Required(CONF_SPECIAL_TYPE): SelectSelector(
    SelectSelectorConfig(
        options=[{"value": k, "label": k} for k in special_options.keys()],
        translation_key="special_type",
    )
)
```

## Phase 4: Vollständige Übersetzungsliste

### Config Flow (7 Steps):
| Key | English | German |
|-----|---------|--------|
| config.step.user.title | Choose WhenHub event type | WhenHub Event-Typ wählen |
| config.step.trip.title | Set up trip | Trip einrichten |
| config.step.milestone.title | Set up milestone | Milestone einrichten |
| config.step.anniversary.title | Set up anniversary | Anniversary einrichten |
| config.step.special_category.title | Choose special event category | Special Event Kategorie wählen |
| config.step.special_event.title | Set up special event | Special Event einrichten |

### Data Fields:
| Key | English | German |
|-----|---------|--------|
| event_name | Event name | Name des Events |
| start_date | Start date (YYYY-MM-DD) | Startdatum (YYYY-MM-DD) |
| end_date | End date (YYYY-MM-DD) | Enddatum (YYYY-MM-DD) |
| target_date | Target date (YYYY-MM-DD) | Zieldatum (YYYY-MM-DD) |
| image_path | Image path (optional) | Bildpfad (optional) |
| website_url | Website URL (optional) | Website URL (optional) |
| notes | Notes (optional) | Notizen (optional) |

### Errors:
| Key | English | German |
|-----|---------|--------|
| invalid_dates | End date must be after start date | Das Enddatum muss nach dem Startdatum liegen |
| invalid_date_format | Invalid date format. Use YYYY-MM-DD | Ungültiges Datumsformat. Verwende YYYY-MM-DD |

### Sensors (15):
| translation_key | English | German |
|-----------------|---------|--------|
| days_until | Days until start | Tage bis Start |
| days_until_end | Days until end | Tage bis Ende |
| event_date | Event date | Ereignisdatum |
| trip_left_days | Trip days remaining | Verbleibende Reisetage |
| trip_left_percent | Trip percent remaining | Verbleibende Reise in Prozent |
| days_until_next | Days until next | Tage bis zum nächsten |
| days_since_last | Days since last | Tage seit dem letzten |
| occurrences_count | Occurrences count | Anzahl Vorkommen |
| next_date | Next date | Nächstes Datum |
| last_date | Last date | Letztes Datum |

### Binary Sensors (4):
| translation_key | English | German |
|-----------------|---------|--------|
| trip_starts_today | Trip starts today | Trip startet heute |
| trip_active_today | Trip active today | Trip aktiv heute |
| trip_ends_today | Trip ends today | Trip endet heute |
| is_today | Is today | Ist heute |

## Umsetzungsreihenfolge

1. [ ] Feature-Branch erstellen: `feature/i18n-translations`
2. [ ] `translations/` Ordner anlegen
3. [ ] `strings.json` ins Englische konvertieren
4. [ ] `translations/de.json` mit deutschen Texten erstellen
5. [ ] `entity`-Sektion hinzufügen (Sensor-Namen)
6. [ ] `selector`-Sektion hinzufügen (Special Events)
7. [ ] `sensors/base.py` anpassen (`has_entity_name`, `translation_key`)
8. [ ] `binary_sensor.py` anpassen (`has_entity_name`, `translation_key`)
9. [ ] `config_flow.py` anpassen (SelectSelector für Special Events)
10. [ ] Tests laufen lassen
11. [ ] In Testumgebung validieren
12. [ ] Commit und Merge in `feature/i18n`

## Referenzen

- HA Docs Internationalization: https://developers.home-assistant.io/docs/internationalization/core/
- HA Docs Custom Integration i18n: https://developers.home-assistant.io/docs/internationalization/custom_integration
- HA Docs Entity Naming: https://developers.home-assistant.io/docs/core/entity/#entity-naming
