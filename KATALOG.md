# WhenHub Test-Katalog

## Übersicht
Vollständiger Katalog aller Tests der WhenHub Home Assistant Integration mit Nummerierung, Beschreibung und Kategorisierung.

**Gesamtanzahl Tests:** 90  
**Test-Dateien:** 19  
**Branch:** feature/extended-tests-v2  

## Kategorien
- **Allgemeine Funktion**: Setup, Manifest, Integration-weite Tests, Error Handling
- **Trip**: Mehrtägige Events mit Start- und End-Datum
- **Milestone**: Einmalige Zieldatum-Events
- **Anniversary**: Jährlich wiederkehrende Events
- **Special**: Spezielle Feiertage und astronomische Events

## Test-Ausführung

### Einzelne Tests ausführen

**Schnelle Ausführung per Nummer:**
```bash
# Einzelnen Test ausführen
./tests/test_individual.sh 1
./tests/test_individual.sh 17

# Mehrere Tests gleichzeitig
./tests/test_individual.sh 1 5 42

# Python-Version (alternativ)
python3 tests/run_test.py 1
```

**Alle Tests auflisten:**
```bash
./tests/test_individual.sh --list
```

**Tests nach Kategorie filtern:**
```bash
./tests/test_individual.sh --category trip      # Nur Trip-Tests
./tests/test_individual.sh --category special   # Nur Special-Tests
./tests/test_individual.sh --category "Allgemeine Funktion"
```

### Manuelle pytest-Ausführung

**Voraussetzung:** Virtuelle Umgebung aktivieren
```bash
source .venv/bin/activate
```

**Einzelne Tests direkt:**
```bash
pytest -v tests/test_simple_setup.py::test_whenhub_integration_loads  # Test 1
pytest -v tests/test_after_event_and_negative.py::test_explicit_negative_values_after_events  # Test 17
```

**Alle Tests einer Datei:**
```bash
pytest -v tests/test_simple_setup.py
```

**Alle Tests ausführen:**
```bash
pytest -v tests/
```

---

## Test-Katalog

### Allgemeine Funktion

| # | Test-Funktion | Datei | Beschreibung |
|---|---------------|--------|--------------|
| 001 | `test_whenhub_integration_loads` | test_simple_setup.py | Integration lädt erfolgreich in Home Assistant |
| 002 | `test_setup_component_minimal` | test_simple_setup.py | Minimales Component-Setup funktioniert |
| 003 | `test_manual_config_entry_setup` | test_simple_setup.py | Manuelle Config-Entry-Erstellung funktioniert |
| 004 | `test_debug_path` | test_debug_path.py | Debug-Pfad und Logging funktionieren |
| 005 | `test_empty_event_name` | test_error_handling_and_robustness.py | Leerer Event-Name Robustheit |
| 006 | `test_extreme_future_dates` | test_error_handling_and_robustness.py | Extreme Zukunftsdaten |
| 007 | `test_invalid_date_format_robustness` | test_error_handling_and_robustness.py | Ungültige Datumsformate |
| 008 | `test_missing_required_fields_robustness` | test_error_handling_and_robustness.py | Fehlende Pflichtfelder |
| 009 | `test_very_long_event_name_truncation` | test_error_handling_and_robustness.py | Sehr lange Event-Namen |
| 010 | `test_concurrent_setup_stability` | test_error_handling_and_robustness.py | Gleichzeitiges Setup mehrerer Events |
| 011 | `test_invalid_date_is_unknown_and_logged` | test_error_handling_and_robustness.py | Ungültiges Datum mit Logging |
| 012 | `test_missing_required_field_is_unknown_and_logged` | test_error_handling_and_robustness.py | Fehlende Felder mit Logging |
| 013 | `test_countdown_text_formatting_very_long_durations` | test_very_long_events_behavior.py | Countdown-Text über sehr lange Zeiträume |
| 014 | `test_performance_stability_extreme_calculations` | test_very_long_events_behavior.py | Performance bei extremen Berechnungen |

### Trip (Mehrtägige Events)

| # | Test-Funktion | Datei | Beschreibung |
|---|---------------|--------|--------------|
| 015 | `test_trip_setup_creates_entities` | test_manifest_and_setup.py | Trip-Setup erstellt alle erforderlichen Entities |
| 016 | `test_trip_countdown_future_18_days` | test_sensor_countdown.py | Countdown 18 Tage vor Trip-Start |
| 017 | `test_trip_active_during_trip` | test_sensor_countdown.py | Trip ist während Laufzeit aktiv |
| 018 | `test_trip_starts_today` | test_binary_today.py | Binary-Sensor für Trip-Start-Tag |
| 019 | `test_trip_ends_today` | test_binary_today.py | Binary-Sensor für Trip-End-Tag |
| 020 | `test_trip_start_day_edges` | test_binary_edges_today.py | Edge-Cases am Trip-Start-Tag |
| 021 | `test_trip_end_day_edges` | test_binary_edges_today.py | Edge-Cases am Trip-End-Tag |
| 022 | `test_trip_day_before_start` | test_binary_edges_today.py | Tag vor Trip-Start |
| 023 | `test_trip_during_middle` | test_binary_edges_today.py | Trip-Mitte Verhalten |
| 024 | `test_trip_after_end_date` | test_after_event_and_negative.py | Verhalten nach Trip-Ende |
| 025 | `test_trip_after_end_shows_zero` | test_after_event_and_negative.py | Null-Werte nach Trip-Ende |
| 026 | `test_trip_day_after_end_shows_zero_and_binaries_off` | test_after_event_and_negative.py | Exakte Nach-Trip-Semantik |
| 027 | `test_explicit_negative_values_after_events` | test_after_event_and_negative.py | Negative Werte nach Event-Ende erlaubt |
| 028 | `test_single_day_trip_percent` | test_trip_percent_stress.py | 1-Tages-Trip Prozentberechnungen |
| 029 | `test_long_trip_percent_midpoint` | test_trip_percent_stress.py | Lange Trip Prozent-Mittelpunkt |
| 030 | `test_trip_percent_boundaries` | test_trip_percent_stress.py | Trip-Prozent Grenzwerte |
| 031 | `test_trip_percent_precision` | test_trip_percent_stress.py | Präzision der Prozentberechnungen |
| 032 | `test_trip_percent_strict_monotonic_decrease` | test_trip_percent_stress.py | Strikte monotone Abnahme |
| 033 | `test_trip_percent_boundaries_exact` | test_trip_percent_stress.py | Exakte Prozent-Grenzwerte |
| 034 | `test_trip_percent_one_day` | test_trip_percent_stress.py | 1-Tages-Trip detaillierte Prozent-Tests |
| 035 | `test_trip_percent_very_long` | test_trip_percent_stress.py | Sehr lange Trip Prozent-Stabilität |
| 036 | `test_trip_percent_one_day_trip_exact_bounds` | test_trip_percent_stress.py | 1-Tages-Trip exakte Bounds |
| 037 | `test_trip_percent_very_long_trip_monotonic_and_bounds` | test_trip_percent_stress.py | Sehr lange Trip Monotonie |
| 038 | `test_trip_zero_day_behavior` | test_zero_day_trip.py | 0-Tage-Trip Verhalten (Start=Ende) |
| 039 | `test_zero_day_trip_edge_cases` | test_trip_zero_day_behavior.py | 0-Tage-Trip Edge-Cases verschiedene Uhrzeiten |
| 040 | `test_zero_day_trip_no_division_by_zero` | test_trip_zero_day_behavior.py | Division-by-Zero Robustheit |
| 041 | `test_zero_day_trip_vs_regular_trip_comparison` | test_trip_zero_day_behavior.py | 0-Tage vs reguläre Trip Vergleich |
| 042 | `test_trip_very_long_event_behavior` | test_very_long_events.py | Sehr lange Events (>365 Tage) |
| 043 | `test_countdown_text_exact_two_weeks` | test_countdown_text_exact.py | Strikte 14-Tage → "2 Wochen" |
| 044 | `test_trip_end_before_start_with_logging` | test_error_handling_and_robustness.py | End-Datum vor Start-Datum mit Logging |
| 045 | `test_trip_end_before_start_is_robust_and_logs_warning` | test_error_handling_and_robustness.py | End<Start Robustheit |
| 046 | `test_zero_day_trip_ist_verhalten_dokumentiert` | test_error_handling_and_robustness.py | 0-Tage-Trip IST-Verhalten |

### Milestone (Einmalige Zieldatum-Events)

| # | Test-Funktion | Datei | Beschreibung |
|---|---------------|--------|--------------|
| 047 | `test_milestone_setup_creates_entities` | test_manifest_and_setup.py | Milestone-Setup erstellt alle Entities |
| 048 | `test_milestone_countdown_future` | test_sensor_countdown.py | Milestone Countdown in der Zukunft |
| 049 | `test_milestone_is_today` | test_sensor_countdown.py | Milestone am Zieldatum |
| 050 | `test_milestone_is_today_true` | test_binary_today.py | Binary-Sensor am Milestone-Tag |
| 051 | `test_milestone_is_today_false` | test_binary_today.py | Binary-Sensor nicht am Milestone-Tag |
| 052 | `test_milestone_is_today_edge` | test_binary_edges_today.py | Edge-Cases am Milestone-Tag |
| 053 | `test_milestone_after_target_date` | test_after_event_and_negative.py | Verhalten nach Milestone-Datum |
| 054 | `test_milestone_after_target_shows_zero` | test_after_event_and_negative.py | Null-Werte nach Milestone |
| 055 | `test_milestone_day_after_target_shows_zero_and_binary_off` | test_after_event_and_negative.py | Tag nach Milestone |
| 056 | `test_milestone_past_date` | test_error_handling_and_robustness.py | Milestone mit vergangenem Datum |
| 057 | `test_milestone_multi_decade_stability` | test_very_long_events_behavior.py | Multi-Dekaden-Milestone (30 Jahre) |

### Anniversary (Jährlich wiederkehrende Events)

| # | Test-Funktion | Datei | Beschreibung |
|---|---------------|--------|--------------|
| 058 | `test_anniversary_setup_creates_entities` | test_manifest_and_setup.py | Anniversary-Setup erstellt Entities |
| 059 | `test_anniversary_next_occurrence` | test_sensor_countdown.py | Anniversary nächstes Vorkommen |
| 060 | `test_anniversary_is_today` | test_binary_today.py | Anniversary Binary-Sensor am Jahrestag |
| 061 | `test_anniversary_is_today_edge` | test_binary_edges_today.py | Edge-Cases am Anniversary-Tag |
| 062 | `test_anniversary_after_event_date` | test_after_event_and_negative.py | Nach Anniversary-Tag Verhalten |
| 063 | `test_anniversary_after_event_shows_zero_today` | test_after_event_and_negative.py | Anniversary Tag-danach Semantik |
| 064 | `test_anniversary_day_after_jumps_to_next_year` | test_after_event_and_negative.py | Anniversary Sprung nächstes Jahr |
| 065 | `test_anniversary_future_original_date` | test_error_handling_and_robustness.py | Anniversary mit Zukunftsdatum |
| 066 | `test_anniversary_feb29_in_non_leap_year` | test_leap_year_anniversary.py | 29.02. Anniversary in Nicht-Schaltjahr |
| 067 | `test_anniversary_feb29_in_leap_year` | test_leap_year_anniversary.py | 29.02. Anniversary in Schaltjahr |
| 068 | `test_anniversary_feb29_on_feb28_non_leap_year` | test_leap_year_anniversary.py | 29.02.→28.02. Fallback |
| 069 | `test_anniversary_feb29_on_actual_leap_day` | test_leap_year_anniversary.py | 29.02. am echten Schaltjahrstag |
| 070 | `test_anniversary_feb29_year_calculation` | test_leap_year_anniversary.py | 29.02. Jahr-Berechnungen |
| 071 | `test_anniversary_leap_year_behavior` | test_leap_year_anniversary.py | Schaltjahr-Anniversary Gesamtverhalten |
| 072 | `test_anniversary_2902_next_date_in_non_leap_year` | test_anniversary_leap_year.py | 29.02. in Nicht-Schaltjahr |
| 073 | `test_anniversary_2902_next_date_in_leap_year` | test_anniversary_leap_year.py | 29.02. in Schaltjahr |
| 074 | `test_anniversary_century_occurrence_calculation` | test_very_long_events_behavior.py | Jahrhundert-Anniversary (100+ Jahre) |

### Special (Spezielle Feiertage und Events)

| # | Test-Funktion | Datei | Beschreibung |
|---|---------------|--------|--------------|
| 075 | `test_special_setup_creates_entities` | test_manifest_and_setup.py | Special Event Setup erstellt Entities |
| 076 | `test_special_christmas_countdown` | test_sensor_countdown.py | Weihnachts-Countdown |
| 077 | `test_special_christmas_is_today` | test_binary_today.py | Binary-Sensor an Weihnachten |
| 078 | `test_special_christmas_not_today` | test_binary_today.py | Binary-Sensor nicht an Weihnachten |
| 079 | `test_special_event_christmas_eve_today` | test_binary_edges_today.py | Heiligabend Edge-Cases |
| 080 | `test_special_event_easter_today` | test_binary_edges_today.py | Ostern Edge-Cases |
| 081 | `test_special_after_christmas` | test_after_event_and_negative.py | Nach Weihnachten Verhalten |
| 082 | `test_special_christmas_after_event_shows_zero_today` | test_after_event_and_negative.py | Special Event Tag-danach |
| 083 | `test_special_day_after_jumps_to_next_year` | test_after_event_and_negative.py | Special Event nächstes Jahr |
| 084 | `test_special_event_invalid_type` | test_error_handling_and_robustness.py | Ungültiger Special Event Type |
| 085 | `test_special_events_complete` | test_special_events_completeness.py | ALLE Special Events (parametrisiert) |
| 086 | `test_movable_feasts_correct_dates` | test_special_events_completeness.py | Bewegliche Feste (Ostern) |
| 087 | `test_special_events_entities_complete` | test_special_events_dynamic_complete.py | Special Events Entity-Vollständigkeit |
| 088 | `test_special_events_next_date_valid_iso` | test_special_events_dynamic_complete.py | Special Events ISO-Datum Validität |
| 089 | `test_special_events_is_today_logic_precision` | test_special_events_dynamic_complete.py | Special Events is_today Präzision |
| 090 | `test_special_events_after_event_behavior` | test_special_events_dynamic_complete.py | Special Events Nach-Event-Verhalten |

---

## Kategorien-Zusammenfassung

| Kategorie | Anzahl Tests | Beschreibung |
|-----------|---------------|--------------|
| **Trip** | 32 | Mehrtägige Events mit Start- und End-Datum |
| **Special** | 16 | Spezielle Feiertage und astronomische Events |
| **Anniversary** | 17 | Jährlich wiederkehrende Events |
| **Allgemeine Funktion** | 14 | Setup, Integration, Error Handling |
| **Milestone** | 11 | Einmalige Zieldatum-Events |
| **GESAMT** | **90** | Vollständige Test-Abdeckung |

---

## Branch & Status
- **Branch:** `feature/extended-tests-v2`
- **Status:** Alle Tests implementiert und committed
- **Letzter Commit:** `15790fe` - QA Documentation Finalized
- **Bereit für:** Review und Integration

---

*Generiert am: $(date)*  
*WhenHub Home Assistant Integration Test Suite*