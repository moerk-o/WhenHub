# FR01: Version Single Source of Truth

## Problem

Aktuell wird die Versionsnummer an mehreren Stellen gepflegt bzw. ist inkonsistent:

1. **manifest.json** → `version: "2.1.0"` - Offizielle Integrationsversion für Home Assistant/HACS
2. **sensors/base.py** → `sw_version="1.0.0"` - **HARDCODED und FALSCH!** Zeigt veraltete Version in Device-Info

Bei jedem Release müssen mehrere Dateien manuell synchron gehalten werden, was fehleranfällig ist.

## Ziel

Eine einzige Quelle für die Versionsnummer (`manifest.json`), die automatisch an allen relevanten Stellen verwendet wird.

## Lösung

### 1. Version aus manifest.json laden

Wie in `solstice_season` implementiert:

```python
# sensors/base.py (oder eigene version.py)
import json
from pathlib import Path

MANIFEST = json.loads((Path(__file__).parent.parent / "manifest.json").read_text())
VERSION = MANIFEST["version"]
```

### 2. Device Info aktualisieren

```python
# sensors/base.py - get_device_info()
def get_device_info(config_entry: ConfigEntry, event_data: dict) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, config_entry.entry_id)},
        name=event_info["name"],
        manufacturer="WhenHub",
        model=event_info["model"],
        sw_version=VERSION,  # Aus manifest.json
    )
```

### 3. SW_VERSION aus const.py entfernen

Falls `SW_VERSION` in `const.py` existiert, diese Konstante entfernen und durch den Import aus der neuen Lösung ersetzen.

## Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| `sensors/base.py` | VERSION laden, sw_version dynamisch setzen |
| `const.py` | SW_VERSION entfernen (falls vorhanden) |
| `binary_sensor.py` | Falls device_info dort definiert, ebenfalls anpassen |
| `image.py` | Falls device_info dort definiert, ebenfalls anpassen |

## Vorteile

- manifest.json ist der Standard für HA-Integrationen
- HACS und HA nutzen diese Datei bereits
- Keine Doppelpflege mehr
- Device-Info zeigt immer korrekte Version

## Nachteile

- Minimaler Overhead beim Laden (einmalig beim Import)

## Release-Workflow

Nach dieser Änderung:

1. Version nur in `manifest.json` erhöhen
2. Commit & Tag erstellen: `git tag v2.2.0`
3. GitHub Release erstellen
4. Fertig - keine weiteren Dateien zu ändern

## Status

- [x] Implementierung
- [x] Tests anpassen
- [x] Alte Datei `docs/version-single-source.md` löschen

**Erledigt:** 2026-01-28 (Commit a322ce9)
