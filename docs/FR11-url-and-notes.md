# FR11: URL und Memo-Felder für Events

## Referenz

- **GitHub Issue:** [#8 - Feature Request: URL and notes fields for events](https://github.com/moerk-o/WhenHub/issues/8)
- **Status:** Konzept / Planung

---

## Problem

WhenHub-Events haben aktuell keinen Platz für ergänzende Informationen wie eine Website-URL oder Notizen. Wer z.B. bei einem Trip die Buchungsseite des Ferienhauses oder bei einer Anniversary eine persönliche Notiz hinterlegen möchte, hat keine Möglichkeit dazu.

---

## Ziel

Zwei neue optionale Felder für alle Event-Typen (Trip, Milestone, Anniversary, Special Event):

| Feld | Beschreibung |
|------|-------------|
| **URL** | Beliebige URL, z.B. Buchungslink, Wikipedia-Seite, Webseite |
| **Memo** | Freitextfeld für Notizen, unterstützt Markdown-Inhalt |

---

## Config Flow

Beide Felder sind optional und erscheinen in allen Event-Typ-Formularen:

```
URL:   [https://...                    ]   ← TextSelector (type=url)
Memo:  [                               ]
       [                               ]   ← TextSelector (multiline=True)
       [                               ]
```

---

## Sensoren

Pro Event werden zwei neue Sensoren angelegt:

| Sensor | Key | Icon | Beispielwert |
|--------|-----|------|-------------|
| `url` | `CONF_URL` | `mdi:link` | `https://booking.com/...` |
| `memo` | `CONF_MEMO` | `mdi:note-text` | `Zimmer 204, Frühstück inklusive` |

### Markdown in Memo

Der Memo-Sensor speichert den Text unverändert. Markdown wird nicht innerhalb der Entity gerendert - aber ein Lovelace `markdown`-Card kann den Inhalt direkt rendern:

```yaml
type: markdown
content: "{{ states('sensor.daenemark_urlaub_memo') }}"
```

---

## Dynamisches Aktivieren / Deaktivieren

Beide Sensoren starten standardmäßig deaktiviert (`entity_registry_enabled_default=False`).

Die Integration verwaltet den Aktivierungsstatus automatisch via `RegistryEntryDisabler.INTEGRATION`:

| Zustand | Entity-Status |
|---------|--------------|
| Feld befüllt | Entity wird aktiviert (`disabled_by=None`) |
| Feld leer | Entity wird deaktiviert (`disabled_by=INTEGRATION`) |
| User hat manuell aktiviert | Wird respektiert - Integration überschreibt User-Entscheidungen nicht |

Das Aktivierungs-Update läuft nach dem initialen Setup und nach jedem Options-Flow-Update.

---

## Verbindung zu anderen FRs

- **FR08 (Calendar Entity):** `url` und `memo` können im `description`-Feld des CalendarEvents erscheinen, sobald FR08 implementiert ist (vgl. FR08-Dokument, Hinweis zu notes/url)
- **FR10 (Image Upload):** Das gleiche Entity-Enable/Disable-Pattern gilt analog für das Image-Entity wenn kein Bild konfiguriert ist

---

## Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| `const.py` | `CONF_URL`, `CONF_MEMO` Konstanten; Sensor-Descriptions für alle Event-Typen |
| `config_flow.py` | URL- und Memo-Felder in allen Event-Typ-Schritten (Setup + Options Flow) |
| `coordinator.py` | URL und Memo aus Config Entry in Event-Data übernehmen |
| `sensors/` | Neue Sensor-Klassen oder Erweiterung bestehender für URL und Memo |
| `__init__.py` | Entity-Registry-Logik für dynamisches Aktivieren/Deaktivieren |
| `translations/en.json` | Feldbezeichnungen, Sensor-Namen |
| `translations/de.json` | Feldbezeichnungen, Sensor-Namen |

---

## Status

- [ ] Konstanten (`CONF_URL`, `CONF_MEMO`)
- [ ] Config Flow: Felder in Setup und Options Flow
- [ ] Coordinator: Felder in Event-Data
- [ ] Sensoren: URL und Memo für alle Event-Typen
- [ ] Entity-Registry: Dynamisches Aktivieren/Deaktivieren
- [ ] Übersetzungen
- [ ] Tests
