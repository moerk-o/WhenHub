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
- ✅ **NEU**: Strikte 14-Tage-Erwartung ("2 Wochen", NICHT "14 Tage")

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

### Trip-Prozent-Berechnungen
- ✅ **NEU**: 1-Tages-Trips (100% → 0%)
- ✅ **NEU**: Lange Trips >365 Tage (Prozent-Stabilität)
- ✅ **NEU**: Grenzwert-Tests (niemals <0% oder >100%)
- ✅ **NEU**: Monotone Abnahme während Trip-Verlauf

### Special Events Vollständigkeit
- ✅ **NEU**: Alle 17 Events einzeln (Traditional, Calendar, Astronomical)
- ✅ **NEU**: Ostern + Pfingsten (Gauss-Algorithmus)
- ✅ **NEU**: Advent 1-4 (rückwärts vom 24.12.)
- ✅ **NEU**: Bewegliche vs. fixe Feiertage

### Error Handling & Robustheit
- ✅ **NEU**: Trip end_date < start_date (kein Crash)
- ✅ **NEU**: Zero-Day-Trips (start_date == end_date)
- ✅ **NEU**: Vergangene Milestones (negative Tage)
- ✅ **NEU**: Leere Event-Namen (Fallback-Verhalten)
- ✅ **NEU**: Ungültige special_type (definierte Fehlerbehandlung)
- ✅ **NEU**: Extreme Zukunftsdaten (Jahr 2099+)

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
└── test_error_handling_and_robustness.py # 🆕 Fehlerbehandlung
```

## Test-Utilities (_helpers.py)

Neue gemeinsame Hilfsfunktionen reduzieren Boilerplate und sorgen für Konsistenz:

- **`setup_and_wait(hass, entry)`**: Entry hinzufügen + Setup + block_till_done
- **`assert_entities_exist(hass, entity_ids)`**: Batch-Existenz-Prüfung
- **`get(hass, entity_id)`**: State-Getter mit klarer Fehlermeldung
- **`slug(name)`**: Einheitliche Entity-Name-Konvertierung 
- **`with_time(dtstr)`**: Kontextmanager für deterministische freezegun-Tests

## Wichtige Änderungen

### Strikte Countdown-Text-Erwartung
- **Vorher**: `assert "18 Tage" in text or "2 Wochen" in text` (Toleranz)
- **Jetzt**: `assert "2 Wochen" in text and "14 Tage" not in text` (deterministisch)
- **Grund**: Scheingrün-Risiko vermeiden; Integration bevorzugt ganze Wochen

### Parametrisierte Special Events Tests  
Alle 17 Special Event Typen werden systematisch getestet:
- **Traditional** (11): Christmas, Easter, Advent, Halloween, etc.
- **Calendar** (2): New Year, New Year's Eve  
- **Astronomical** (4): Equinoxes & Solstices

### Robuste Fehlerbehandlung
Tests dokumentieren das IST-Verhalten bei ungültigen Eingaben, ohne Produktionscode zu ändern.

## Nächste Schritte

1. Tests ausführen und Fehler beheben
2. Coverage erhöhen (Ziel: 80%)
3. Edge Cases abdecken
4. Integration Tests hinzufügen
5. CI/CD Pipeline aufsetzen (GitHub Actions)