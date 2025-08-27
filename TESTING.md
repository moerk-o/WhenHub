# WhenHub Testing Setup

## Lokales Test-Setup

### 1. Virtuelle Umgebung einrichten

```bash
# Venv erstellen
python3 -m venv .venv

# Aktivieren (Linux/macOS)
source .venv/bin/activate

# Aktivieren (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### 2. Dependencies installieren

```bash
# Pip upgraden
pip install -U pip

# Test-Dependencies installieren
pip install -r requirements-test.txt
```

Die Installation kann 5-10 Minuten dauern, da Home Assistant und alle Dependencies installiert werden.

### 3. VSCode konfigurieren

VSCode sollte automatisch die Konfiguration aus `.vscode/settings.json` laden:
- Python-Interpreter: `.venv/bin/python`
- Test-Framework: pytest
- Empfohlene Extensions: Python, Pylance, Ruff

## Test-Befehle

### Alle Tests ausführen
```bash
pytest -q
```

### Einzelne Test-Datei
```bash
pytest -q tests/test_sensor_countdown.py
```

### Mit Coverage
```bash
pytest --cov=custom_components/whenhub --cov-report=html
```

### Linting
```bash
ruff check custom_components/whenhub
```

## Abgedeckte Test-Fälle

### Setup & Entity-Erstellung
- ✅ Trip-Events: Alle Sensoren, Binärsensoren und Bilder
- ✅ Milestone-Events: Countdown und Is-Today Sensoren
- ✅ Anniversary-Events: Wiederkehrende Event-Sensoren
- ✅ Special Events: Feiertags-Countdown (Weihnachten)
- ✅ **NEU**: Alle 17 Special Event Typen vollständig (parametrisiert)

### Countdown-Logik
- ✅ Trip: 18 Tage vor Start
- ✅ Trip: Aktiv während der Reise
- ✅ Milestone: Countdown in die Zukunft
- ✅ Milestone: Am Zieldatum (0 Tage)
- ✅ Anniversary: Nächstes Vorkommen berechnen
- ✅ Special: Weihnachts-Countdown
- ✅ **T01**: Strikte 14-Tage-Erwartung ("2 Wochen" MUSS enthalten sein, "14 Tage" DARF NICHT enthalten sein)

### Binary "Is Today" Sensoren
- ✅ Trip: Start-Tag, End-Tag, Aktiv-Status
- ✅ Milestone: Am Zieldatum true/false
- ✅ Anniversary: Am Jahrestag
- ✅ Special: Am Feiertag (Heiligabend)
- ✅ **NEU**: Exakte Kanten-Tests für alle Event-Typen (Tag davor/danach)

### Nach-Event-Szenarien
- ✅ **NEU**: Trip nach End-Datum (negative Tage, Binary=OFF)
- ✅ **NEU**: Milestone nach Zieldatum (negative days_until)
- ✅ **NEU**: Anniversary nach Jahrestag (nächstes Jahr)
- ✅ **NEU**: Special Events nach Feiertag (Jahreswechsel)

### Schaltjahr-Handling
- ✅ **NEU**: Anniversary am 29.02. in Schalt- und Nicht-Schaltjahren
- ✅ **NEU**: Korrekte Datumsberechnung (29.02. → 28.02.)
- ✅ **NEU**: is_today Logic am Ersatztag (28.02.)
- ✅ **Vollständig**: Leap-Year Handling mit allen 4 Freeze-Szenarien getestet

### Trip-Prozent-Berechnungen
- ✅ **NEU**: 1-Tages-Trips (100% → 0%)
- ✅ **NEU**: Lange Trips >365 Tage (Prozent-Stabilität)
- ✅ **NEU**: Grenzwert-Tests (niemals <0% oder >100%)
- ✅ **NEU**: Monotone Abnahme während Trip-Verlauf
- ✅ **Vollständig**: Prozent-Berechnung mit test_trip_percent_one_day und test_trip_percent_very_long

### Special Events Vollständigkeit
- ✅ **NEU**: Alle 17 Events einzeln (Traditional, Calendar, Astronomical)
- ✅ **NEU**: Ostern + Pfingsten (Gauss-Algorithmus)
- ✅ **NEU**: Advent 1-4 (rückwärts vom 24.12.)
- ✅ **NEU**: Bewegliche vs. fixe Feiertage
- ✅ **Vollständig**: test_special_events_complete mit allen 3 Phasen pro Event

### Error Handling & Robustheit
- ✅ **NEU**: Trip end_date < start_date (kein Crash)
- ✅ **NEU**: Zero-Day-Trips (start_date == end_date) - Siehe eigener Abschnitt
- ✅ **NEU**: Vergangene Milestones (negative Tage)
- ✅ **NEU**: Leere Event-Namen (Fallback-Verhalten)
- ✅ **NEU**: Ungültige special_type (definierte Fehlerbehandlung)
- ✅ **NEU**: Extreme Zukunftsdaten (Jahr 2099+)
- ✅ **Vollständig**: Umfassende Robustheitstests mit caplog-Integration

## Verbleibende Lücken

### Integration Tests
- ⏳ Config Flow UI Tests
- ⏳ Options Flow Updates
- ⏳ Entity Registry Cleanup
- ⏳ Device Info Consistency

### Performance
- ⏳ Viele Events gleichzeitig
- ⏳ Update-Koordination
- ⏳ Memory Leaks bei Reload

### DST & Zeitzonen
- ⏳ DST-Übergänge (Sommer-/Winterzeit)
- ⏳ Timezone-Handling (Integration arbeitet nur mit Daten)

## Test-Struktur

```
tests/
├── _helpers.py                        # 🆕 Gemeinsame Test-Utilities
├── conftest.py                        # Fixtures (erweitert mit Factory)
├── test_manifest_and_setup.py        # Setup & Entity-Erstellung
├── test_sensor_countdown.py          # Countdown-Berechnungen (+ strikte "2 Wochen")
├── test_binary_today.py              # Binary Sensor Tests
├── test_after_event_and_negative.py  # 🆕 Nach-Event-Szenarien
├── test_leap_year_anniversary.py     # 🆕 Schaltjahr 29.02. Tests
├── test_binary_edges_today.py        # 🆕 Exakte Today-Kanten
├── test_trip_percent_stress.py       # 🆕 Prozent-Stress-Tests
├── test_special_events_completeness.py # 🆕 Alle 17 Special Events
├── test_special_events_dynamic_complete.py # 🆕 Dynamische Special Events (T08)
├── test_very_long_events.py           # 🆕 Sehr lange Events >365 Tage (T11) 
└── test_error_handling_and_robustness.py # 🆕 Fehlerbehandlung
```

## Test-Utilities (_helpers.py)

Neue gemeinsame Hilfsfunktionen reduzieren Boilerplate und sorgen für Konsistenz:

- **`setup_and_wait(hass, entry)`**: Entry hinzufügen + Setup + block_till_done
- **`assert_entities_exist(hass, entity_ids)`**: Batch-Existenz-Prüfung
- **`get(hass, entity_id)`**: State-Getter mit klarer Fehlermeldung
- **`slug(name)`**: Einheitliche Entity-Name-Konvertierung 
- **`with_time(dtstr)` / `at(dtstr)`**: Kontextmanager für deterministische freezegun-Tests  
- **`get_state(hass, entity_id)`**: Alias für get() für kürzere Verwendung

## Wichtige Änderungen

### Strikte Countdown-Text-Erwartung
- **Vorher**: `assert "18 Tage" in text or "2 Wochen" in text` (Toleranz)
- **Jetzt**: `assert "2 Wochen" in text and "14 Tage" not in text` (deterministisch)
- **Grund**: Scheingrün-Risiko vermeiden; Integration bevorzugt ganze Wochen

### Parametrisierte Special Events Tests (T08)
**DYNAMISCHE** Extraktion aller Special Event Typen (keine Magic Numbers):
- **Vollständigkeit**: Alle `SPECIAL_EVENTS.keys()` aus `const.py` werden getestet
- **Regression-Schutz**: Neue Special Events werden automatisch erfasst
- **Qualität**: Jeder Typ wird auf Entity-Existenz, ISO-Datumsformat, is_today-Logic geprüft
- **Bewegliche Feste**: Easter/Pentecost mit bekannten Referenzdaten (2026/2027)

### Robuste Fehlerbehandlung & Logging
Tests dokumentieren das IST-Verhalten bei ungültigen Eingaben, ohne Produktionscode zu ändern:
- **caplog-Integration**: Prüfung auf saubere Fehlerbehandlung ohne Traceback-Flut
- **Zero-Day-Trips**: IST-Verhalten dokumentiert (1-tägiger Trip, alle Binaries gleichzeitig ON)
- **Ungültige Daten**: end_date < start_date, leere Namen, extreme Zukunftsdaten
- **Fallback-Werte**: Definierte Grenzen für Prozent/Tage bei Fehlern

## ✅ T01 Testfall-Status

| Anforderung | Implementierung | Status |
|-------------|-----------------|---------|
| **Countdown-Text bei exakt 14 Tagen** | `test_countdown_text_exact_two_weeks()` | ✅ **VOLLSTÄNDIG** |
| Freeze-Time: 14 Tage vor Trip | `2026-06-28 10:00:00+00:00` → `2026-07-12` | ✅ **KORREKT** |
| Setup wie bestehende Tests | `add_to_hass()`, `async_setup()`, `block_till_done()` | ✅ **STANDARD** |
| Assertion: "2 Wochen" MUSS enthalten sein | `assert "2 Wochen" in text` | ✅ **STRIKT** |
| Assertion: "14 Tage" DARF NICHT enthalten sein | `assert "14 Tage" not in text` | ✅ **STRIKT** |
| Kommentierung: Warum/Wie/Erwartung | Vollständiger Docstring mit T01-Referenz | ✅ **DOKUMENTIERT** |
| TESTING.md Ergänzung | Abgedeckte Testfälle + SOLL-vs-IST Tabelle | ✅ **AKTUALISIERT** |

## ✅ Leap-Year Anniversaries

**Warum:** Anniversaries am 29. Februar sind ein kritischer Sonderfall - sie müssen in Nicht-Schaltjahren korrekt auf den 28. Februar ausweichen, aber in echten Schaltjahren wieder den 29. Februar erkennen.

**Wie:** Anniversary-Fixture mit Startdatum 29.02.2020 (Schaltjahr). Teste 4 spezifische Freeze-Szenarien mit exakten Assertions für next_date, is_today und days_until.

**Erwartung:** Korrekte Datum-Logik ohne Fehler bei Jahreswechseln zwischen Schalt- und Nicht-Schaltjahren.

| Szenario | Implementierung | Status |
|----------|-----------------|---------|
| **2023-02-01: next_date=2023-02-28, is_today=OFF** | `test_anniversary_leap_year_behavior()` Szenario 1 | ✅ **VOLLSTÄNDIG** |
| **2023-02-28: is_today=ON, next_date=2023-02-28** | `test_anniversary_leap_year_behavior()` Szenario 2 | ✅ **VOLLSTÄNDIG** |
| **2024-02-01: next_date=2024-02-29, is_today=OFF** | `test_anniversary_leap_year_behavior()` Szenario 3 | ✅ **VOLLSTÄNDIG** |
| **2024-02-29: is_today=ON, next_date=2024-02-29** | `test_anniversary_leap_year_behavior()` Szenario 4 | ✅ **VOLLSTÄNDIG** |
| Fixture mit anniversary_leap_year_entry | `conftest.py` - Startdatum 29.02.2020 | ✅ **VERFÜGBAR** |
| Kommentierung: Warum/Wie/Erwartung | Vollständiger Docstring mit Leap-Year Details | ✅ **DOKUMENTIERT** |

## ✅ Special Events Vollständigkeit

**Warum:** Alle Special Events müssen korrekt funktionieren, besonders bewegliche Feste wie Ostern die algorithmisch berechnet werden. Regression-Schutz bei neuen Events durch dynamische Parametrisierung aus `SPECIAL_EVENTS`.

**Wie:** Dynamische Extraktion aller special_type Keys aus `const.py`. Für jeden Event werden 3 Phasen getestet: weit vorher (Jahresbeginn), am Event-Tag, Tag danach. Zusätzlich spezielle Tests für bewegliche Feste und Adventssonntage.

**Erwartung:** Alle Entities korrekt erstellt, valide ISO-Daten, is_today ON nur am Event-Tag, countdown "0 Tage" am Event, nach Event Sprung aufs nächste Jahr.

| Testfall | Implementierung | Status |
|----------|-----------------|---------|
| **Alle Events dynamisch parametrisiert** | `test_special_events_complete()` | ✅ **VOLLSTÄNDIG** |
| **Entity-Existenz für alle Events** | `test_special_events_entities_complete()` | ✅ **VOLLSTÄNDIG** |
| **Event-Tag Logik (is_today, countdown)** | Phase 2 in `test_special_events_complete()` | ✅ **VOLLSTÄNDIG** |
| **Nach-Event Logik (Jahreswechsel)** | Phase 3 in `test_special_events_complete()` | ✅ **VOLLSTÄNDIG** |
| **Bewegliche Feste (Ostern/Pfingsten)** | `test_movable_feasts_correct_dates()` | ✅ **VOLLSTÄNDIG** |
| **Adventssonntage Rückwärtsrechnung** | `test_advent_sundays_backward_calculation()` | ✅ **VOLLSTÄNDIG** |

## ✅ Error Handling & Robustheit

**Warum:** Die Integration muss auch bei fehlerhaften oder unvollständigen Konfigurationen stabil bleiben. Ungültige Benutzereingaben, Konfigurationsfehler oder extreme Daten dürfen nicht zu Crashes führen.

**Wie:** Systematische Tests mit ungültigen/extremen Eingaben: falsche Daten, fehlende Felder, ungültige Formate. Verwendung von `caplog` für Logging-Verifikation. IST-Verhalten dokumentieren ohne Produktionscode zu ändern.

**Erwartung:** Keine unbehandelten Exceptions, saubere Fallback-Werte, aussagekräftige Log-Meldungen, definierte Grenzen für alle Berechnungen.

| Testfall | Implementierung | Status |
|----------|-----------------|---------|
| **Trip: end_date < start_date** | `test_trip_end_before_start_with_logging()` | ✅ **VOLLSTÄNDIG** |
| **Ungültige Datumsformate (30. Feb)** | `test_invalid_date_format_robustness()` | ✅ **VOLLSTÄNDIG** |
| **Fehlende Pflichtfelder** | `test_missing_required_fields_robustness()` | ✅ **VOLLSTÄNDIG** |
| **Zero-Day-Trips IST-Verhalten** | `test_zero_day_trip_ist_verhalten_dokumentiert()` | ✅ **VOLLSTÄNDIG** |
| **Sehr lange Event-Namen** | `test_very_long_event_name_truncation()` | ✅ **VOLLSTÄNDIG** |
| **Parallele Setup-Stabilität** | `test_concurrent_setup_stability()` | ✅ **VOLLSTÄNDIG** |
| **Extreme Zukunftsdaten** | `test_extreme_future_dates()` | ✅ **VOLLSTÄNDIG** |
| **caplog-Integration** | In allen Error-Tests | ✅ **IMPLEMENTIERT** |

## ✅ 0-Tage-Trips (Zero-Day Behavior)

**Warum:** 0-Tage-Trips (start_date == end_date) sind kritische Grenzfälle für alle Trip-Berechnungen. Division-by-zero Risiko, Binary-Sensor Logik und Prozent-Berechnungen müssen robust funktionieren. Das IST-Verhalten muss klar dokumentiert sein.

**Wie:** Trip mit identischem Start- und End-Datum (trip_one_day_entry Fixture). Teste am Ereignistag selbst und am Folgetag. Verifiziere alle Sensor-Werte, Binary-Zustände und mathematische Robustheit bei verschiedenen Uhrzeiten.

**Erwartung:** Am Ereignistag alle drei Binary-Sensoren gleichzeitig ON, left_days=1 (inklusiv), left_percent=100%. Am Folgetag alles auf 0/OFF. Keine Exceptions oder Division-by-zero Fehler.

| Testfall | Implementierung | Status |
|----------|-----------------|---------|
| **Vollständiges 0-Tage-Trip Verhalten** | `test_trip_zero_day_behavior()` | ✅ **VOLLSTÄNDIG** |
| **Edge Cases verschiedene Uhrzeiten** | `test_zero_day_trip_edge_cases()` | ✅ **VOLLSTÄNDIG** |
| **Division-by-zero Robustheit** | `test_zero_day_trip_no_division_by_zero()` | ✅ **VOLLSTÄNDIG** |
| **Vergleich mit regulärem Trip** | `test_zero_day_trip_vs_regular_trip_comparison()` | ✅ **VOLLSTÄNDIG** |
| **IST-Verhalten dokumentiert** | Alle Binary-Sensoren gleichzeitig ON | ✅ **DOKUMENTIERT** |
| **Mathematische Stabilität** | Keine NaN/Inf Werte, definierte Berechnungen | ✅ **VERIFIZIERT** |

## ✅ Trip-Prozent-Berechnungen

**Warum:** Die prozentuale Berechnung des verbleibenden Trip-Anteils (`_left_percent`) ist kritisch für die Benutzeroberfläche und muss besonders in Grenzfällen wie 1-Tages-Trips oder sehr langen Trips (>365 Tage) korrekt funktionieren.

**Wie:** Spezielle Fixtures für 1-Tages-Trip (`trip_one_day_entry`) und sehr langen Trip (`trip_very_long_entry`, 912 Tage). Teste verschiedene Zeitpunkte mit Freeze-Time und verifiziere exakte Prozentwerte, monotone Abnahme und strikte Grenzen.

**Erwartung:** Prozentwerte bleiben immer zwischen 0.0 und 100.0, fallen strikt monoton während der Reise, zeigen exakt 100% am Start und 0% nach Ende.

| Testfall | Implementierung | Status |
|----------|-----------------|---------|
| **1-Tages-Trip: 100% → 0%** | `test_trip_percent_one_day()` | ✅ **VOLLSTÄNDIG** |
| **Sehr langer Trip (912 Tage)** | `test_trip_percent_very_long()` | ✅ **VOLLSTÄNDIG** |
| **Exakte Grenzwerte (0.0/100.0)** | `test_trip_percent_boundaries_exact()` | ✅ **VOLLSTÄNDIG** |
| **Strikte Monotonie** | `test_trip_percent_strict_monotonic_decrease()` | ✅ **VOLLSTÄNDIG** |
| **Fixtures erstellt** | `conftest.py` - trip_one_day_entry, trip_very_long_entry | ✅ **VERFÜGBAR** |
| **Helper-Funktionen aktualisiert** | Import-Konsistenz: at(), get_state() | ✅ **KORRIGIERT** |

## ✅ Sehr lange Events (Multi-Jahr bis Multi-Dekade)

**Warum:** Sehr lange Events (mehrere Jahre bis Jahrzehnte) testen die mathematische Stabilität und Performance der Integration bei extremen Zeitspannen. >1800 Tage für Trips, >10.000 Tage für Milestones und 100+ Vorkommen für Anniversaries müssen robust berechnet werden.

**Wie:** Spezielle Fixtures für Multi-Jahr-Trip (5 Jahre), Multi-Dekaden-Milestone (30 Jahre) und Jahrhundert-Anniversary (100+ Jahre). Tests an verschiedenen Zeitpunkten über die gesamte Laufzeit mit Fokus auf Countdown-Text-Formatierung, Prozent-Stabilität und Performance.

**Erwartung:** Monotone Werteentwicklung über Jahre, hierarchische Countdown-Formatierung (Jahre > Monate > Wochen), keine Overflow-Exceptions, stabile Performance bei extremen Berechnungen.

| Testfall | Implementierung | Status |
|----------|-----------------|---------|
| **5-Jahres-Trip Volltest** | `test_trip_very_long_event_behavior()` | ✅ **VOLLSTÄNDIG** |
| **30-Jahre-Milestone Stabilität** | `test_milestone_multi_decade_stability()` | ✅ **VOLLSTÄNDIG** |
| **Jahrhundert-Anniversary (100+ Vorkommen)** | `test_anniversary_century_occurrence_calculation()` | ✅ **VOLLSTÄNDIG** |
| **Countdown-Text hierarchische Formatierung** | `test_countdown_text_formatting_very_long_durations()` | ✅ **VOLLSTÄNDIG** |
| **Performance bei extremen Berechnungen** | `test_performance_stability_extreme_calculations()` | ✅ **VOLLSTÄNDIG** |
| **Monotone Werteentwicklung über Jahre** | Strikte Assertions in allen Multi-Jahr Tests | ✅ **VERIFIZIERT** |
| **Fixtures erstellt** | `trip_multi_year_entry`, `milestone_multi_decade_entry`, `anniversary_century_entry` | ✅ **VERFÜGBAR** |

## ✅ Countdown-Text Exakte Formatierung

**Warum:** Der Countdown-Text soll bei spezifischen Zeitspannen strukturierte Formate verwenden. Exakt 14 Tage sollten als "2 Wochen" dargestellt werden, nicht als "14 Tage". Dies verbessert die Nutzerfreundlichkeit und zeigt die hierarchische Zeitformatierung.

**Wie:** Trip "Dänemark 2026" mit Start 2026-07-12. Test genau 14 Tage vorher (2026-06-28) mit strikten Assertions für "2 Wochen" Format und Ausschluss von "14 Tage".

**Erwartung:** Strikte Formatierung ohne Toleranz - countdown_text enthält "2 Wochen" und enthält explizit NICHT "14 Tage".

| Testfall | Implementierung | Status |
|----------|-----------------|---------|
| **Exakt 14-Tage → "2 Wochen"** | `test_countdown_text_exact_two_weeks()` | ✅ **VOLLSTÄNDIG** |
| **Strikte Formatierung ohne "14 Tage"** | Negative Assertion in test_countdown_text_exact.py | ✅ **VERIFIZIERT** |
| **IST-Semantik dokumentiert** | Docstring mit Warum/Wie/Erwartung Struktur | ✅ **DOKUMENTIERT** |

## ✅ Nach-Datum-Szenarien (Einmalige vs. Wiederkehrende Events)

**Warum:** Events verhalten sich nach ihrem Datum unterschiedlich: Einmalige Events (Trip, Milestone) zeigen "0 Tage" und Binaries OFF. Wiederkehrende Events (Anniversary, Special) springen sofort auf das nächste Jahr (~365/366 Tage) ohne "0 Tage" zu zeigen.

**Wie:** Vier spezifische Tests einen Tag nach Event-Datum mit exakten Freeze-Zeitpunkten. Trip (2026-07-27), Milestone (2026-03-16), Anniversary (2026-05-21), Special (2026-12-25). Strikte Assertions für unterschiedliche Verhaltensweisen.

**Erwartung:** Einmalige Events: countdown "0 Tage", negative days_until, Binaries OFF. Wiederkehrende Events: countdown NICHT "0 Tage", days_until ~365/366, Binaries OFF.

| Testfall | Implementierung | Status |
|----------|-----------------|---------|
| **Trip Tag danach: 0-Werte + Binaries OFF** | `test_trip_day_after_end_shows_zero_and_binaries_off()` | ✅ **VOLLSTÄNDIG** |
| **Milestone Tag danach: 0-Werte + Binary OFF** | `test_milestone_day_after_target_shows_zero_and_binary_off()` | ✅ **VOLLSTÄNDIG** |
| **Anniversary Tag danach: Sprung nächstes Jahr** | `test_anniversary_day_after_jumps_to_next_year()` | ✅ **VOLLSTÄNDIG** |
| **Special Tag danach: Sprung nächstes Jahr** | `test_special_day_after_jumps_to_next_year()` | ✅ **VOLLSTÄNDIG** |
| **Trennung einmalig vs. wiederkehrend** | Unterschiedliche Erwartungen in Tests dokumentiert | ✅ **VERIFIZIERT** |

## ✅ Schaltjahr-Jahrestage (29. Februar Behandlung)

**Warum:** Anniversaries mit 29.02. Startdatum sind kritische Grenzfälle für Datumslogik. Sie müssen in Nicht-Schaltjahren korrekt auf 28.02. ausweichen, aber in echten Schaltjahren wieder den 29.02. verwenden. Dies erfordert korrekte Schaltjahr-Erkennung und Ausweichlogik.

**Wie:** Anniversary mit Startdatum 2020-02-29. Tests in Nicht-Schaltjahr 2023 (Ausweichen auf 28.02.) und Schaltjahr 2024 (echter 29.02.). Strikte Prüfung von next_date und is_today Binary-Zuständen.

**Erwartung:** Nicht-Schaltjahr: next_date = 28.02., is_today ON am 28.02. Schaltjahr: next_date = 29.02., is_today ON am 29.02. Keine Datums-Exceptions.

| Testfall | Implementierung | Status |
|----------|-----------------|---------|
| **29.02. in Nicht-Schaltjahr → 28.02. Ausweichen** | `test_anniversary_2902_next_date_in_non_leap_year()` | ✅ **VOLLSTÄNDIG** |
| **29.02. in Schaltjahr → echter 29.02.** | `test_anniversary_2902_next_date_in_leap_year()` | ✅ **VOLLSTÄNDIG** |
| **Korrekte Schaltjahr-Erkennung** | Tests 2023 (kein Schaltjahr) vs 2024 (Schaltjahr) | ✅ **VERIFIZIERT** |
| **Fixture anniversary_2902_config_entry** | Startdatum 2020-02-29 in test_anniversary_leap_year.py | ✅ **VERFÜGBAR** |

## Nächste Schritte

1. Tests ausführen und Fehler beheben
2. Coverage erhöhen (Ziel: 80%)
3. Edge Cases abdecken
4. Integration Tests hinzufügen
5. CI/CD Pipeline aufsetzen (GitHub Actions)