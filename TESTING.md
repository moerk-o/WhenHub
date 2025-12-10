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

### Countdown-Logik
- ✅ Trip: 18 Tage vor Start
- ✅ Trip: Aktiv während der Reise
- ✅ Milestone: Countdown in die Zukunft
- ✅ Milestone: Am Zieldatum (0 Tage)
- ✅ Anniversary: Nächstes Vorkommen berechnen
- ✅ Special: Weihnachts-Countdown

### Binary "Is Today" Sensoren
- ✅ Trip: Start-Tag, End-Tag, Aktiv-Status
- ✅ Milestone: Am Zieldatum true/false
- ✅ Anniversary: Am Jahrestag
- ✅ Special: Am Feiertag (Heiligabend)

### Edge Cases (test_edge_cases.py)
- ✅ Eintägiger Trip (Start = Ende)
- ✅ Vergangene Events (negative Tage)
- ✅ Sehr lange Trips (> 365 Tage)
- ✅ Schaltjahr-Handling (29. Februar in Schalt-/Nicht-Schaltjahr)
- ✅ Ostern-Berechnung (2026, 2027)
- ✅ Advent-Berechnung (2025, 2026)

### Pure Calculation Functions (test_calculations.py)
- ✅ Date Parsing (ISO string, date objects, invalid input)
- ✅ days_until (future, past, same date)
- ✅ days_between (multi-day, single day)
- ✅ Trip calculations (left days, percent, is_active)
- ✅ is_date_today
- ✅ Countdown breakdown (years, months, weeks, days)
- ✅ format_countdown_text (German output, singular/plural)
- ✅ Anniversary calculations (for_year, next, last, count)
- ✅ Leap year handling (Feb 29 in leap/non-leap years)
- ✅ Easter calculation (Gauss algorithm)
- ✅ Pentecost calculation (49 days after Easter)
- ✅ Advent calculation (1st-4th Advent)
- ✅ Special event date calculation (fixed, calculated)
- ✅ next_special_event / last_special_event

## Bekannte Lücken (für spätere Tests)

### Spezialfälle
- ⏳ DST-Übergänge (Sommer-/Winterzeit)

### Edge Cases
- ⏳ Ungültige Datumsangaben
- ⏳ Fehlende Pflichtfelder

### Integration Tests
- ⏳ Config Flow UI Tests
- ⏳ Options Flow Updates
- ⏳ Entity Registry Cleanup
- ⏳ Device Info Consistency

### Performance
- ⏳ Viele Events gleichzeitig
- ⏳ Update-Koordination
- ⏳ Memory Leaks bei Reload

## Test-Struktur

```
tests/
├── conftest.py                 # Fixtures für alle Tests
├── test_basic_logic.py         # Basis-Logik ohne HA
├── test_binary_today.py        # Binary Sensor Tests
├── test_calculations.py        # Pure calculation functions (66 tests)
├── test_debug_path.py          # Debug/Pfad-Tests
├── test_edge_cases.py          # Edge Cases (Schaltjahr, lange Trips, etc.)
├── test_manifest_and_setup.py  # Setup & Entity-Erstellung
├── test_sensor_countdown.py    # Countdown-Berechnungen
└── test_simple_setup.py        # Basis-Setup Tests
```

## Nächste Schritte

1. ~~Tests ausführen und Fehler beheben~~ ✅
2. Coverage erhöhen (Ziel: 80%)
3. ~~Edge Cases abdecken~~ ✅
4. Integration Tests hinzufügen
5. CI/CD Pipeline aufsetzen (GitHub Actions)