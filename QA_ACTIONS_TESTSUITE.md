# QA_ACTIONS_TESTSUITE.md

> **Ziel:** Alle zuvor geforderten Edge-Case-Tests vollständig und lückenlos umsetzen.  
> **Wichtig:** **Kein Produktionscode ändern**. Nur Tests + TESTING.md.  
> **Keine Lücken**: Jede Vorgabe unten ist verpflichtend. Keine „später“-Marker.  
> **Hinweis:** Die internen Kürzel (T01–T11) dienen NUR in diesem Dokument zur Navigation. In Code/Doku nicht verwenden.

## Branch & Commits

1. Ausgehend von `feature/extended-tests-v2` arbeiten.  
2. Kleine, thematische Commits pro Block unten (Commit-Message klar & prägnant).  
3. Nach jedem Block: `pytest -q` → grün.

---

## [T01] Strikter 14-Tage-Text ✅ **ERLEDIGT**

**Datei:** `tests/test_countdown_text_exact.py` ✅ **ERSTELLT**  
**Funktion:** `test_countdown_text_exact_two_weeks()` ✅ **IMPLEMENTIERT**  
**Kontext:** Trip „Dänemark 2026", Start: `2026-07-12` → 14 Tage vorher ist `2026-06-28`.

**Vorgaben:** ✅ **ALLE ERFÜLLT**
- Zeit einfrieren: `2026-06-28 10:00:00+00:00` ✅
- Setup via vorhandener Trip-Fixture ✅
- `sensor.danemark_2026_countdown_text` prüfen: ✅
  - `assert "2 Wochen" in text` ✅
  - `assert "14 Tage" not in text` ✅
- Docstring mit **Warum/Wie/Erwartung** ✅

**Doku:** `TESTING.md` – Abschnitt „Countdown-Text Exakte Formatierung" ✅ **HINZUGEFÜGT**
**Commit:** 4d75870 ✅ **COMMITTED**

---

## [T02/T06] „Tag danach"-Fälle / negative Werte ✅ **ERLEDIGT**

**Datei:** `tests/test_after_event_and_negative.py` ✅ **ERGÄNZT**  
**Neue Funktionen (4 Stück):** ✅ **ALLE IMPLEMENTIERT**
- `test_trip_day_after_end_shows_zero_and_binaries_off()` ✅
- `test_milestone_day_after_target_shows_zero_and_binary_off()` ✅
- `test_anniversary_day_after_jumps_to_next_year()` ✅
- `test_special_day_after_jumps_to_next_year()` ✅

**Vorgaben:** ✅ **ALLE ERFÜLLT**
- **Trip:** (12.–26.07.2026) ✅
  - Freeze: `2026-07-27 10:00:00+00:00` ✅
  - `sensor.danemark_2026_countdown_text == "0 Tage"` ✅
  - `int(sensor.danemark_2026_days_until_end.state) < 0` ✅
  - Binaries (`…_starts_today`, `…_ends_today`, `…_active_today`) **off** ✅
  - `sensor.danemark_2026_trip_left_days == "0"` ✅
  - `sensor.danemark_2026_trip_left_percent == "0.0"` ✅
- **Milestone** (Zieldatum 2026-03-15) ✅
  - Freeze: `2026-03-16 10:00:00+00:00` ✅
  - Text „0 Tage", `int(days_until) < 0`, Binary `…_is_today == "off"` ✅
- **Anniversary** (Jahrestag 20.05.) ✅
  - Freeze: `2026-05-21 10:00:00+00:00` ✅
  - **Kein „0 Tage"**: `days_until` springt auf ~**365/366** (nächstes Jahr), `…_is_today == "off"` ✅
- **Special (Weihnachten, 24.12.)** ✅
  - Freeze: `2026-12-25 10:00:00+00:00` ✅
  - **Kein „0 Tage"**: `days_until` ~**365/366**, `…_is_today == "off"` ✅

**Doku:** `TESTING.md` – Abschnitt „Nach-Datum-Szenarien (Einmalige vs. Wiederkehrende Events)" ✅ **HINZUGEFÜGT**
**Commit:** 52a947a ✅ **COMMITTED**

---

## [T03] Anniversary 29. Februar – Integrationstest ✅ **ERLEDIGT**

**Datei:** `tests/test_anniversary_leap_year.py` ✅ **ERSTELLT**  
**Fixture:** `anniversary_2902_config_entry` ✅ **IMPLEMENTIERT** (lokal im Test), Startdatum: `2020-02-29` ✅

**Neue Funktionen:** ✅ **BEIDE IMPLEMENTIERT**
- `test_anniversary_2902_next_date_in_non_leap_year()` ✅
  - Freeze: `2023-02-01 10:00:00+00:00` → `sensor.…_next_date == "2023-02-28"`, `…_is_today == "off"` ✅
  - Freeze: `2023-02-28 10:00:00+00:00` → `…_is_today == "on"` ✅
- `test_anniversary_2902_next_date_in_leap_year()` ✅
  - Freeze: `2024-02-01 10:00:00+00:00` → `next_date == "2024-02-29"` ✅
  - Freeze: `2024-02-29 10:00:00+00:00` → `is_today == "on"` ✅

**Doku:** `TESTING.md` – Abschnitt „Schaltjahr-Jahrestage (29. Februar Behandlung)" ✅ **HINZUGEFÜGT**
**Commit:** 68b2801 ✅ **COMMITTED**

---

## [T07] Prozent-Berechnung (kurz/lang, Monotonie)

**Datei:** `tests/test_trip_percent_stress.py` (ergänzen)  
**Neue Funktionen:**
- `test_trip_percent_one_day_trip_exact_bounds()`
  - 1-Tages-Trip-Fixture (Start=2026-07-12, Ende=2026-07-13)
  - Am Starttag: `…_trip_left_percent == "100.0"`
  - Am Folgetag: `…_trip_left_percent == "0.0"`
- `test_trip_percent_very_long_trip_monotonic_and_bounds()`
  - Sehr langer Trip (z. B. Start 2026-01-01, Ende 2030-12-31)
  - Freeze 3 Messpunkte: früh / Mitte / kurz vor Ende
  - An jedem Punkt: `0.0 <= float(percent) <= 100.0`
  - **Monoton fallend** zwischen den Messpunkten

**Doku:** `TESTING.md` – Abschnitt „Prozent-Berechnung Trips“.

---

## [T08] Special Events – Vollständigkeit (parametrisiert)

**Datei:** `tests/test_special_events_completeness.py` (ergänzen)  

**Parametrisierung:**
- Per `pytest.mark.parametrize` **über alle Keys** aus `SPECIAL_EVENTS` (dynamisch aus dem Code lesen, keine harte Liste).

**Pro Key prüfen (3 Situationen):**
1. **Weit vorher** (z. B. `YYYY-01-01 10:00:00+00:00`):
   - Entities existieren:  
     `sensor.…_days_until`, `sensor.…_countdown_text`, `sensor.…_next_date`, `sensor.…_last_date`,  
     `binary_sensor.…_is_today`, `image.…_image`
   - `…_is_today == "off"`, `days_until` plausibel > 0, `next_date` ISO-Datum
2. **Ereignistag**:
   - `…_is_today == "on"`, `countdown_text == "0 Tage"`
3. **Tag danach**:
   - **Wiederkehrend:** `days_until ≈ 365/366`, `…_is_today == "off"`

**Bewegliche Feste:** Mindestens **Ostern**: Referenzjahr mit bekanntem Datum (z. B. 2026-04-05) explizit prüfen.

**Doku:** `TESTING.md` – Abschnitt „Special Events Vollständigkeit“ (Warum/Wie/Erwartung).

---

## [T09] Fehlerfälle / Robustheit (mit caplog)

**Datei:** `tests/test_error_handling_and_robustness.py` (ergänzen)  
**Neue Funktionen:**
- `test_trip_end_before_start_is_robust_and_logs_warning(caplog)`
  - Trip-ConfigEntry mit `end_date < start_date`
  - **Kein Crash**, Entities existieren, sinnvolle Fallbacks (z. B. left_days="0", left_percent="0.0" ODER state "unknown" – IST dokumentieren)
  - `caplog` enthält Warn/Fehler-Log, **kein** Traceback-Spam
- `test_invalid_date_is_unknown_and_logged(caplog)`
  - Ungültiges Datum (z. B. 2025-02-30)
  - **Kein Crash**, betroffene States = "unknown"/None
  - `caplog` Eintrag vorhanden
- `test_missing_required_field_is_unknown_and_logged(caplog)`
  - Pflichtfeld (z. B. start_date) fehlt
  - **Kein Crash**, Entities existieren mit "unknown", Log vorhanden

**Doku:** `TESTING.md` – Abschnitt „Fehlerfälle/Robustheit“.

---

## [T10] 0-Tage-Trip (Start = Ende)

**Datei:** `tests/test_zero_day_trip.py` (neu)  
**Funktion:** `test_trip_zero_day_behavior()`  

**Vorgaben:**
- Fixture: Trip mit Start=Ende (`2026-07-12`)
- **Am Tag:**  
  `sensor.…_days_until_start == "0"`  
  `sensor.…_trip_left_percent == "100.0"`  
  Binaries: `…_starts_today == "on"`, `…_active_today == "on"`, `…_ends_today == "on"` (IST-Semantik dokumentieren)  
- **Folgetag:**  
  `sensor.…_trip_left_days == "0"`, `…_trip_left_percent == "0.0"`, Binaries **off**
- Docstring erklärt **Warum/Wie/Erwartung** + **IST-Semantik** (ohne Code-Änderung).

**Doku:** `TESTING.md` – Abschnitt „0-Tage-Trips“.

---

## [T11] Sehr lange Events (>365 Tage)

**Datei:** `tests/test_very_long_events.py` (neu)  
**Funktion:** `test_trip_very_long_event_behavior()`  

**Vorgaben:**
- Fixture: sehr langer Trip (Start 2026-01-01, Ende 2030-12-31)
- Freeze drei Messpunkte: **früh**, **Mitte**, **kurz vor Ende**
- Prüfen:
  - `sensor.…_days_until_end` groß & plausibel (positiv bis kurz vor Ende)
  - `sensor.…_trip_left_percent`: `0.0 <= value <= 100.0`, **monoton fallend** zwischen den Messpunkten
  - `sensor.…_countdown_text` gibt lange Spannen **verständlich** wieder (enthält Jahre/Monate/Wochen in sinnvoller Kombination)

**Doku:** `TESTING.md` – Abschnitt „Sehr lange Events“.

---

## Gemeinsame Anforderungen (für ALLE obigen Blöcke)

- **freezegun** immer mit UTC-Offset (z. B. `…+00:00`), keine lokalen TZ.  
- **Setup-Muster** beibehalten (add_to_hass → async_setup → block_till_done).  
- **Keine weichen Checks** (keine ODER-Toleranz beim 14-Tage-Fall, keine „contains irgendwas“ wenn exakte Form erwartet).  
- **Kommentare/Docstrings:** Jeder Test mit **Warum / Wie / Erwartung**.  
- **Parametrisierung** nutzen, wo sinnvoll (v. a. Special Events).  
- **Keine T-Nummern** in Code/Doku.  
- **TESTING.md** aktualisieren:
  - Pro hinzugefügtem Test: Kurzbeschreibung (Warum/Wie/Erwartung)
  - Am Ende: **SOLL-vs-IST Tabelle** (ohne T-Nummern; sprechende Bezeichnungen verwenden) mit Verweisen `datei::testname`.

---

## Abnahme-Checkliste (muss erfüllt sein)

- [ ] Alle oben gelisteten Dateien/Funktionen existieren und sind grün.  
- [ ] `TESTING.md` aktualisiert: neue Abschnitte + Soll-vs-Ist.  
- [ ] Keine „Bekannte Lücken“ mehr für die oben adressierten Punkte.  
- [ ] **Kein** Produktionscode geändert.  
- [ ] Kurzbericht im PR:  
  - Welche Tests ergänzt (Liste `datei::testname`)  
  - `pytest -q` Output (grün)  
  - Besonderheiten/IST-Semantik sauber dokumentiert.
