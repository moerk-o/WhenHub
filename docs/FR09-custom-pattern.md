# FR09: Custom Pattern (Benutzerdefinierte Wiederholungsmuster)

## Referenz

- **GitHub Issue:** [#6 - Feature Request: Support for "Nth Weekday of Month"](https://github.com/moerk-o/WhenHub/issues/6)
- **Standard:** [RFC 5545 - Internet Calendaring and Scheduling Core Object Specification (iCalendar)](https://www.rfc-editor.org/rfc/rfc5545)
- **Status:** Konzept / Planung

---

## Problem

WhenHub bietet aktuell nur vordefinierte Special Events (Weihnachten, Ostern, DST etc.). Es gibt keine Möglichkeit, eigene wiederkehrende Ereignisse nach einer Regel zu definieren - z.B. "4. Donnerstag im November" (Thanksgiving) oder "Jeden zweiten Montag".

---

## Ziel

Benutzerdefinierte Wiederholungsmuster als neue Kategorie **"Custom Pattern"** in den Special Events, basierend auf dem RFC 5545 iCalendar Standard (RRULE).

---

## Einordnung im Config Flow

Custom Pattern wird als neue Kategorie unter Special Events eingeführt:

```
Special Event - Kategorie wählen:

○ Traditional Holidays    →  Traditionelle Feiertage
○ Calendar Holidays       →  Kalendarische Feiertage
○ Daylight Saving Time    →  Zeitumstellung
○ Custom Pattern          →  Eigenes Muster          ← NEU
```

---

## Unterstützte Muster (vollständiger RFC 5545 RRULE-Support)

Der RFC 5545 RRULE-Standard wird vollständig unterstützt:

### Frequenz (FREQ)

| Wert | Bedeutung | Beispiel |
|------|-----------|---------|
| `YEARLY` | Jährlich | Jedes Jahr am gleichen Tag |
| `MONTHLY` | Monatlich | Jeden Monat |
| `WEEKLY` | Wöchentlich | Jede Woche |
| `DAILY` | Täglich | Jeden Tag |

### Intervall (INTERVAL)

Wiederholt die Frequenz in N-Schritten:

| RRULE | Bedeutung |
|-------|-----------|
| `FREQ=WEEKLY;INTERVAL=2;BYDAY=MO` | Jeden zweiten Montag |
| `FREQ=MONTHLY;INTERVAL=3` | Jeden dritten Monat |

### Wochentag-Regeln (BYDAY)

| RRULE | Bedeutung |
|-------|-----------|
| `FREQ=YEARLY;BYMONTH=11;BYDAY=+4TH` | 4. Donnerstag im November (Thanksgiving) |
| `FREQ=YEARLY;BYMONTH=5;BYDAY=-1MO` | Letzter Montag im Mai (Memorial Day) |
| `FREQ=YEARLY;BYMONTH=5;BYDAY=+2SU` | 2. Sonntag im Mai (Muttertag) |
| `FREQ=WEEKLY;BYDAY=MO,WE,FR` | Jeden Montag, Mittwoch und Freitag |
| `FREQ=MONTHLY;BYDAY=+1MO` | Ersten Montag jeden Monats |

### Letzter Wochentag des Monats (BYSETPOS)

| RRULE | Bedeutung |
|-------|-----------|
| `FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=-1` | Letzter Werktag des Monats |
| `FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=1` | Erster Werktag des Monats |

### Fester Tag im Monat (BYMONTHDAY)

| RRULE | Bedeutung |
|-------|-----------|
| `FREQ=MONTHLY;BYMONTHDAY=15` | Jeden 15. des Monats |
| `FREQ=MONTHLY;BYMONTHDAY=-1` | Letzter Tag des Monats |

### Ende der Wiederholung (UNTIL / COUNT)

| RRULE | Bedeutung |
|-------|-----------|
| `FREQ=WEEKLY;UNTIL=20261231` | Wöchentlich bis 31.12.2026 |
| `FREQ=MONTHLY;COUNT=12` | Monatlich, endet nach 12 Vorkommen |

### Ausnahmen (EXDATE)

Bestimmte Daten von der Wiederholung ausschließen:

```
RRULE:FREQ=WEEKLY;BYDAY=MO
EXDATE:20261225,20270101
→ Jeden Montag, außer Weihnachten und Neujahr
```

### Zusätzliche Einzeldaten (RDATE)

Ergänzt die Regel um einmalige Zusatzdaten:

```
RRULE:FREQ=YEARLY;BYMONTH=12;BYMONTHDAY=25
RDATE:20261226
→ Jedes Jahr am 25. Dezember + einmalig auch am 26.12.2026
```

---

## Config Flow Design

### Schritt 1 - Frequenz wählen

```
Custom Pattern - Häufigkeit

○ Yearly   - Jährlich
○ Monthly  - Monatlich
○ Weekly   - Wöchentlich
```

### Schritt 2a - Bei "Yearly"

```
Monat:      [November          ▼]
Regel:      [Nth Wochentag     ▼]  (Nth Wochentag / Letzter Wochentag / Fester Tag)
N:          [4                 ▼]  (1. / 2. / 3. / 4.)
Wochentag:  [Donnerstag        ▼]
```

### Schritt 2b - Bei "Monthly"

```
Regel:      [Nth Wochentag     ▼]  (Nth Wochentag / Letzter Wochentag / Fester Tag)
N:          [1                 ▼]
Wochentag:  [Montag            ▼]
```

### Schritt 2c - Bei "Weekly"

```
Intervall:  [2                 ▼]  (Jeden / Jeden 2. / Jeden 3. ...)
Wochentag:  [Montag            ▼]
```

---

## Berechnungslogik

### Bereits vorhanden in calculations.py

Die Kernfunktionen für einfache jährliche Muster existieren bereits - entwickelt für DST:

```python
nth_weekday_of_month(year, month, weekday, n)
# → 4. Donnerstag im November

last_weekday_of_month(year, month, weekday)
# → Letzter Montag im Mai
```

### Implementierungsstrategie: python-dateutil

Für den vollständigen RFC 5545 Support empfiehlt sich die Nutzung von `python-dateutil` (Modul `dateutil.rrule`). Diese Bibliothek ist bereits eine Abhängigkeit von Home Assistant selbst und muss nicht separat installiert werden.

```python
from dateutil.rrule import rrule, rrulestr, WEEKLY, MO

# Beispiel: Jeden zweiten Montag
rule = rrule(WEEKLY, interval=2, byweekday=MO, dtstart=start_date)
next_occurrence = rule.after(today)
last_occurrence = rule.before(today)
```

Der RRULE-String aus der Config wird direkt per `rrulestr()` geparst - kein eigener Parser nötig. Das deckt automatisch FREQ, INTERVAL, BYDAY, BYMONTH, BYMONTHDAY, BYSETPOS, UNTIL, COUNT, EXDATE und RDATE ab.

---

## Sensoren

Custom Pattern Events verwenden dieselben Sensoren wie andere Special Events:

| Sensor | Beschreibung |
|--------|-------------|
| `days_until` | Tage bis zur nächsten Occurrence |
| `days_since_last` | Tage seit der letzten Occurrence |
| `event_date` | Datum der nächsten Occurrence (Timestamp) |
| `next_date` | Datum der nächsten Occurrence (Timestamp) |
| `last_date` | Datum der letzten Occurrence (Timestamp) |
| `is_today` | Binary Sensor - heute ist Occurrence |

---

## Verbindung zu FR08 (Calendar Entity)

Custom Pattern Events werden automatisch in `calendar.whenhub` erscheinen (sobald FR08 implementiert ist). Für wiederkehrende Muster liefert `async_get_events()` alle Occurrences im angefragten Zeitraum.

---

## Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| `calculations.py` | Neue Funktionen für Monthly/Weekly Patterns |
| `const.py` | Neue Konstanten für Custom Pattern |
| `config_flow.py` | Neuer Flow für Custom Pattern |
| `coordinator.py` | `_calculate_custom_pattern_data()` |
| `translations/en.json` | Config Flow Texte, Wochentage, Monate |
| `translations/de.json` | Config Flow Texte, Wochentage, Monate |

---

## Status

- [ ] Konzept finalisieren
- [ ] Implementierung calculations.py
- [ ] Config Flow
- [ ] Coordinator
- [ ] Übersetzungen
- [ ] Tests
