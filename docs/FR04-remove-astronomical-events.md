# FR04: Remove Astronomical Special Events

## Problem

WhenHub enthält astronomische Events (Jahreszeitenanfänge), die redundant sind mit **solstice_season**:

| Aspekt | WhenHub | solstice_season |
|--------|---------|-----------------|
| **Berechnung** | Fixe Daten (z.B. immer 20. März) | Exakte Berechnung mit PyEphem |
| **Genauigkeit** | ±1-2 Tage Abweichung möglich | Sekundengenau |
| **Zusätzliche Features** | Nur Countdown | Daylight Trend, Season Age, etc. |
| **Wartung** | Doppelte Arbeit | Bereits gepflegt |

## Betroffene Events

Diese 4 Events sollen entfernt werden:

| Key | Name | Aktuelles fixes Datum |
|-----|------|----------------------|
| `spring_start` | Frühlingsanfang | 20. März |
| `summer_start` | Sommeranfang | 21. Juni |
| `autumn_start` | Herbstanfang | 23. September |
| `winter_start` | Winteranfang | 21. Dezember |

**Hinweis:** Die tatsächlichen astronomischen Daten variieren jährlich um ±1-2 Tage!

## Verbleibende Special Event Kategorien

Nach Entfernung:

| Kategorie | Events | Verbleibt |
|-----------|--------|-----------|
| **traditional** | Weihnachten, Ostern, Advent, etc. | ✅ Ja |
| **calendar** | Neujahr, Silvester | ✅ Ja |
| **astronomical** | Jahreszeitenanfänge | ❌ Entfernen |
| **dst** | Zeitumstellung | ✅ Ja |

## Zu entfernende Code-Stellen

### 1. const.py

**Kategorie entfernen:**
```python
# SPECIAL_EVENT_CATEGORIES - Diese Zeilen entfernen:
"astronomical": {
    "name": "Astronomische Events",
    "description": "Jahreszeitenanfänge",
    "icon": "mdi:weather-sunny"
},
```

**Events entfernen:**
```python
# SPECIAL_EVENTS - Diese Einträge entfernen:
"spring_start": { ... },
"summer_start": { ... },
"autumn_start": { ... },
"winter_start": { ... },
```

### 2. strings.json

```json
// selector.special_type.options - entfernen:
"spring_start": "Spring Equinox",
"summer_start": "Summer Solstice",
"autumn_start": "Autumn Equinox",
"winter_start": "Winter Solstice"

// selector.special_category.options - entfernen:
"astronomical": "Astronomical Events"
```

### 3. translations/en.json

Analog zu strings.json:
- `selector.special_type.options`: 4 Einträge entfernen
- `selector.special_category.options`: "astronomical" entfernen

### 4. translations/de.json

```json
// selector.special_type.options - entfernen:
"spring_start": "Frühlingsanfang",
"summer_start": "Sommeranfang",
"autumn_start": "Herbstanfang",
"winter_start": "Winteranfang"

// selector.special_category.options - entfernen:
"astronomical": "Astronomische Events"
```

### 5. README.md

Den Abschnitt "Astronomical Events" unter Special Events komplett entfernen.

## Migration für bestehende Nutzer

Falls Nutzer bereits astronomische Events in WhenHub konfiguriert haben:

1. **Vor Update:** Hinweis in Release Notes
2. **Nach Update:** Alte Config-Entries werden ungültig und müssen gelöscht werden

### Release Notes Vorschlag

```markdown
## Breaking Changes

- **Astronomical Events entfernt**: Die Events "Frühlingsanfang",
  "Sommeranfang", "Herbstanfang" und "Winteranfang" wurden entfernt.

  WhenHub konzentriert sich auf persönliche Events (Trips, Milestones,
  Anniversaries) und Feiertage. Astronomische Berechnungen gehören
  nicht zum Kernfokus der Integration.

  **Migration:** Bestehende astronomische Events müssen manuell
  gelöscht werden.
```

## Vorteile

- **Klarer Fokus** - WhenHub konzentriert sich auf persönliche Events und Feiertage
- **Weniger Wartungsaufwand** - keine astronomischen Berechnungen pflegen
- **Weniger Code** - einfachere Codebasis
- **Keine ungenauen Daten** - fixe Daten für astronomische Events waren ohnehin ungenau (±1-2 Tage)

## Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| `const.py` | Kategorie + 4 Events entfernen |
| `strings.json` | 5 Einträge entfernen |
| `translations/en.json` | 5 Einträge entfernen |
| `translations/de.json` | 5 Einträge entfernen |
| `README.md` | Abschnitt entfernen/anpassen |

## Status

✅ **Abgeschlossen** (2026-01-28)

- [x] const.py bereinigen
- [x] strings.json bereinigen (entfernt zugunsten translations/en.json)
- [x] translations/en.json bereinigen
- [x] translations/de.json bereinigen
- [x] README.md anpassen
- [x] Release Notes vorbereiten
- [x] Testen dass bestehende non-astronomical Events weiter funktionieren

**Commits:**
- `b961f4b` - FR04: Remove astronomical special events
- `34830ac` - Merge branch 'feature/fr04-remove-astronomical': FR04 + FR07
