# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

---

## [2.2.0] - 2026-01-29

### Behoben
- **OptionsFlow Fehler behoben**: 500 Internal Server Error beim Klicken auf "Konfigurieren" in neueren Home Assistant Versionen
  - Ursache: `config_entry` ist in neueren HA Versionen eine read-only Property der `OptionsFlow` Basisklasse
  - Fix: `__init__` Methode aus `OptionsFlowHandler` entfernt

### Hinzugefügt
- **FR07: Verbesserte Testabdeckung** (50 neue Tests, 173 → 223 gesamt)
  - Special Events Tests (Weihnachten, Ostern, Advent)
  - DST Events Tests (EU, USA, Australien, Neuseeland)
  - Config Flow Tests (User Step, Routing, Complete Flows)
  - Options Flow Tests (alle Event-Typen)
  - Edge Case Tests (Unicode, Emojis, lange Namen)
  - Internationale Zeichensätze (Kyrillisch, Chinesisch, Japanisch, Arabisch, Hebräisch)

### Geändert
- **Device Info bereinigt**: Firmware-Version aus Geräte-Info entfernt (WhenHub Events sind virtuelle Geräte ohne echte Firmware)

### Weitere Bugfixes
- **DSTBinarySensor Icon Bug**: `AttributeError` beim Zugriff auf `_attr_icon` behoben
- **Options Flow Error Display**: Validierungsfehler werden jetzt korrekt angezeigt

---

## [2.1.0] - 2026-01-28

### Hinzugefügt
- **FR02: Sprachbasierte Entity IDs**
  - Entity IDs basieren jetzt auf der konfigurierten HA-Sprache
  - Korrekte Übersetzungen für Sensornamen in DE/EN
  - `EntityDescription` für einheitliche Namensgebung

- **FR04: Astronomische Events entfernt**
  - Sonnenaufgang, Sonnenuntergang, Sonnenwende, Tagundnachtgleiche entfernt
  - Diese werden besser durch dedizierte Integrationen (z.B. Sun) abgedeckt

### Geändert
- **FR06: Verbesserter Datepicker**
  - Native Home Assistant `DateSelector` für Datumsauswahl
  - Bessere UX im Config Flow

---

## [2.0.0] - 2026-01-27

### Hinzugefügt
- **DST (Sommerzeit/Winterzeit) Events**
  - Unterstützung für EU, USA, Australien, Neuseeland
  - Binary Sensor für aktiven DST-Status
  - Verschiedene DST-Typen: nächste Umstellung, nur Sommer, nur Winter

- **DataUpdateCoordinator**
  - Zentrale Datenverwaltung für alle Sensoren
  - Effizientere Updates

- **Berechnungsmodul**
  - Ausgelagerte Datumsberechnungen in `calculations.py`
  - Bessere Testbarkeit

### Geändert
- **Refactoring der Sensor-Architektur**
  - Basisklassen für verschiedene Event-Typen
  - Einheitliche Struktur für alle Sensoren

---

## [1.0.0] - 2026-01-15

### Erste Veröffentlichung
- **Trip Events**: Countdown zu Reisen mit Start- und Enddatum
- **Milestone Events**: Countdown zu einmaligen Ereignissen
- **Anniversary Events**: Jährlich wiederkehrende Ereignisse mit Jubiläumsberechnung
- **Special Events**: Feiertage und besondere Tage
  - Feste Feiertage (Weihnachten, Neujahr, etc.)
  - Bewegliche Feiertage (Ostern, Pfingsten, Advent)
- **Image Entity**: Optionales Bild pro Event
- **Config Flow**: Vollständige UI-Konfiguration
- **Mehrsprachigkeit**: Deutsch und Englisch
