# FR02: Entity Name Translation Fix

## Problem

Entity-Namen werden nicht korrekt übersetzt, obwohl Übersetzungen in `translations/de.json` und `translations/en.json` definiert sind.

### Hintergrund: USER-Sprache vs SYSTEM-Sprache

Home Assistant unterscheidet zwischen zwei Sprachebenen:

| Ebene | Quelle | Funktion |
|-------|--------|----------|
| **SYSTEM-Sprache** | `strings.json` | Definiert Entity-IDs (müssen englisch/stabil bleiben) |
| **USER-Sprache** | `translations/*.json` | Definiert Anzeigenamen (friendly_name) je nach Benutzersprache |

**Wichtig:** Entity-IDs dürfen sich nie ändern, wenn der Benutzer die Sprache wechselt!

## Aktuelle Situation in WhenHub

### Was bereits funktioniert

In `sensors/base.py` ist bereits korrekt implementiert:

```python
# Zeile 104-105
self._attr_has_entity_name = True
self._attr_translation_key = sensor_type
```

### Was nicht funktioniert

1. **strings.json ist nicht synchron mit translations/en.json**

   | Eintrag | strings.json | translations/en.json |
   |---------|-------------|---------------------|
   | `dst_event` step | **FEHLT** | Vorhanden |
   | `dst_options` step | **FEHLT** | Vorhanden |
   | `dst_type` selector | **FEHLT** | Vorhanden |
   | `dst_region` selector | **FEHLT** | Vorhanden |
   | `is_dst_active` binary_sensor | **FEHLT** | Vorhanden |

2. **Keine hassfest Validierung**

   Es gibt keinen GitHub Workflow, der die Übersetzungen validiert.

## Referenz: solstice_season

In solstice_season funktioniert es so:

### Sensor-Klassen

```python
# base_sensor.py
class SolsticeBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    # In EntityDescription:
    BaseSensorEntityDescription(
        key=SENSOR_SOLAR_LONGITUDE,
        translation_key=SENSOR_SOLAR_LONGITUDE,  # <- Wichtig!
        ...
    )
```

### Übersetzungsdateien

```
translations/
├── en.json   # Englische Anzeigenamen (USER-Sprache)
├── de.json   # Deutsche Anzeigenamen (USER-Sprache)
└── nl.json   # Niederländische Anzeigenamen (USER-Sprache)
```

**Hinweis:** solstice_season hat KEINE `strings.json` - für Custom Integrations reicht `translations/en.json` als Fallback.

### GitHub Workflow (validate.yaml)

```yaml
name: Validate

on:
  push:
  pull_request:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:

jobs:
  hassfest:
    name: Hassfest
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master

  hacs:
    name: HACS
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: HACS validation
        uses: hacs/action@main
        with:
          category: integration
```

## Lösung

### Option A: strings.json entfernen (Empfohlen)

Für Custom Integrations ist `strings.json` optional. Wenn nur `translations/en.json` existiert, wird diese als Fallback verwendet.

**Vorteil:** Keine Synchronisierungsprobleme mehr.

### Option B: strings.json synchron halten

Falls `strings.json` beibehalten wird:

1. `strings.json` = `translations/en.json` (identischer Inhalt)
2. Bei jeder Änderung beide Dateien aktualisieren

### Zusätzliche Maßnahmen

1. **hassfest Workflow hinzufügen** (`.github/workflows/validate.yaml`)
2. **HACS Validation hinzufügen** (für zukünftige HACS-Veröffentlichung)

## Betroffene Dateien

| Datei | Aktion |
|-------|--------|
| `custom_components/whenhub/strings.json` | LÖSCHEN (Option A) oder synchronisieren (Option B) |
| `.github/workflows/validate.yaml` | NEU erstellen |
| `sensors/base.py` | Keine Änderung nötig (bereits korrekt) |
| `binary_sensor.py` | Prüfen ob `translation_key` gesetzt |
| `image.py` | Prüfen ob `translation_key` gesetzt |

## Testplan

1. Integration mit deutscher Sprache testen:
   - Anzeigenamen sollten deutsch sein ("Tage bis Start")
   - Entity-IDs sollten englisch bleiben (`sensor.xxx_days_until`)

2. hassfest lokal ausführen:
   ```bash
   docker run --rm -v $(pwd):/github/workspace ghcr.io/home-assistant/hassfest
   ```

3. Sprache in HA wechseln und prüfen:
   - Entity-IDs bleiben stabil
   - Anzeigenamen wechseln

## Referenzen

- [Home Assistant Developer Docs: Hassfest](https://developers.home-assistant.io/blog/2020/04/16/hassfest/)
- [GitHub: home-assistant/actions](https://github.com/home-assistant/actions)
- [HA Community: Translations not working](https://community.home-assistant.io/t/translations-not-working-and-failing-hassfest/595023)

## Status

- [x] Entscheidung: Option A (strings.json entfernen)
- [x] strings.json gelöscht
- [x] validate.yaml Workflow erstellen (bereits in FR03 erledigt)
- [x] Alle Entity-Klassen auf translation_key prüfen (bereits korrekt in base.py)
- [ ] Lokaler hassfest Test (manuell)
- [ ] Test mit deutscher Sprache (manuell)

**Erledigt:** 2026-01-28
