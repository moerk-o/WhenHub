# FR12: Entity-verknüpfte Datumswerte

## Referenz

- **GitHub Issue:** [#9 - Feature Request: Use existing HA entities or calendar events as date source](https://github.com/moerk-o/WhenHub/issues/9)
- **Status:** Konzept / Planung

---

## Idee

WhenHub wird zur **Berechnungsschicht** für beliebige Datumswerte in Home Assistant. Statt ein Datum manuell einzugeben, kann der User eine bestehende HA-Entity als Datenquelle verknüpfen. WhenHub rechnet darauf: Countdown, "ist gerade aktiv", Prozentsatz usw.

---

## Anwendungsbeispiele

| Quelle | WhenHub-Event | Mehrwert |
|--------|--------------|---------|
| Astro-Integration: "Frühlingsanfang" | Milestone | Countdown auf den ersten Frühlingstag |
| Eintrag aus einem Geburtstagskalender | Anniversary | WhenHub-Berechnungen auf einen Kalender-Geburtstag |
| Flug-API-Sensor: "Abflug", "Landung" | Trip | Live-Countdown auf echte Flugzeiten |
| Beliebiger `device_class: timestamp`-Sensor | Milestone | WhenHub-Berechnungen ohne manuelle Eingabe |

---

## Config Flow Design

Der Datumspicker wird pro Datumsfeld um eine Entity-Option erweitert. Manuell bleibt immer verfügbar - Entity ist eine zusätzliche Alternative:

### Milestone / Anniversary / Special Event (ein Datum)

```
Datum:   ○ Manuell   [2026-12-24          ]
         ● Entity    [sensor.naechste_abholung ▼]
```

### Trip (Start + End)

Zwei unabhängige Selektoren - jeder kann manuell oder Entity sein:

```
Startdatum:  ○ Manuell   [2026-07-01      ]
             ● Entity    [sensor.abflug ▼ ]

Enddatum:    ● Manuell   [2026-07-14      ]
             ○ Entity    [________________]
```

Das ermöglicht z.B. einen gebuchten Rückflug als Entity, während das Startdatum noch manuell festgelegt ist.

### Akzeptierte Entity-Typen

- `input_datetime`
- `input_date`
- `sensor` mit `device_class: date`
- `sensor` mit `device_class: timestamp`

---

## Verhalten bei Problemen

### Quelle unavailable
Wenn die verknüpfte Entity den State `unavailable` oder `unknown` hat, werden alle WhenHub-Sensoren des Events ebenfalls `unavailable`. Kein Fallback, kein Raten.

### Enddatum vor Startdatum (Trip)
Wenn durch eine Änderung der Quell-Entity das Enddatum vor dem Startdatum liegt, werden alle Sensoren des Events `unavailable` **und** ein HA-Repairs-Issue wird erstellt:

> **WhenHub: Ungültige Datumsreihenfolge**
> Event "Dänemark Urlaub": Das Enddatum liegt vor dem Startdatum.
> Bitte die verknüpfte Entity oder die Konfiguration prüfen.

- `is_fixable=False` — WhenHub kann die externe Entity nicht ändern
- Das Repairs-Issue wird automatisch entfernt sobald die Daten wieder gültig sind (`async_delete_issue()` im nächsten Coordinator-Update)

---

## Architektur

### Coordinator
- Liest bei verknüpften Events den State der Quell-Entity aus `hass.states.get(entity_id)`
- Zusätzlich zu stündlichem Update: `async_track_state_change_event()` auf alle verknüpften Entities → sofortige Reaktion auf Änderungen
- Repairs-Logik im Coordinator-Update-Zyklus

### Config Entry
Speichert pro Datumsfeld entweder den manuellen Wert oder die Entity-ID:

```python
# Manuell (wie bisher)
CONF_TARGET_DATE: "2026-12-24"

# Entity-verknüpft (neu)
CONF_TARGET_DATE_ENTITY: "sensor.naechste_abholung"
```

---

## Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| `const.py` | Neue Konstanten `CONF_*_ENTITY` für alle Datumsfelder |
| `config_flow.py` | Manuell/Entity-Umschalter in allen Event-Typ-Schritten |
| `coordinator.py` | Entity-State lesen, `async_track_state_change_event`, Repairs-Logik |
| `strings.json` / `translations/` | Repairs-Texte, neue UI-Labels |

---

## Offen / Ideen

### Kalender-Eintrag als Quelle (Erweiterung)

Neben einer Sensor-Entity könnte auch ein konkreter **Kalendereintrag** als Quelle dienen. Der User wählt dabei nicht per Stichwort, sondern direkt aus seinen echten Kalendereinträgen:

```
Schritt 1:  Kalender wählen   [calendar.google_privat  ▼]

Schritt 2:  Event wählen      (WhenHub lädt Einträge der nächsten ~90 Tage)
            [● Urlaub Dänemark   01.07. – 14.07.2026   ]
            [○ Zahnarzt          12.04.2026             ]
            [○ Geburtstag Mama   21.04.2026             ]
```

Für Trip ist das besonders elegant: der Kalendereintrag hat bereits Start **und** Ende - statt zwei Entity-Selektoren reicht eine einzige Auswahl.

**Offene Frage: Wiederkehrende Events**
Wenn der User einen Eintrag aus einer Wiederholungsserie auswählt (z.B. "Zahnarzt" alle 6 Monate) - verfolgt WhenHub dann nur genau diesen einen Termin, oder immer das nächste Vorkommen der Serie? Aktuell Tendenz: nur der konkrete gewählte Termin, kein automatisches "nächstes Vorkommen".

**→ Erst angehen wenn Basis-FR12 (Entity-Quelle) stabil implementiert ist.**

---

### Entity als RRULE-Ankerpunkt (Kombination mit FR09)
Eine verknüpfte Entity könnte nicht nur ein festes Datum ersetzen, sondern als dynamischer `dtstart` für ein Custom Pattern (FR09 RRULE) dienen. Beispiel: `sensor.auto_letzte_inspektion` + `FREQ=YEARLY` → nächster Servicetermin verschiebt sich automatisch wenn die Inspektion eingetragen wird.

Technisch reizvoll, aber eigenes Komplexitätsniveau:
- Strenge Datumsformat-Validierung der Entity nötig
- Timezone-Konflikte zwischen Entity und RRULE-Berechnung
- COUNT-Regeln zählen neu wenn dtstart sich ändert
- Zusätzliche Repair-Fälle (unparsebares Datum, keine gültige Occurrence)

**→ Erst angehen wenn FR09 und FR12 stabil implementiert sind.**

---

## Status

- [ ] Konstanten für Entity-Datumsfelder
- [ ] Config Flow: Manuell/Entity-Umschalter
- [ ] Coordinator: Entity-State lesen + State-Change-Tracking
- [ ] Coordinator: Repairs-Issue bei End-vor-Start
- [ ] Coordinator: Repairs-Issue automatisch auflösen
- [ ] Übersetzungen (inkl. Repairs-Texte)
- [ ] Tests
