# FR05: Cleanup - Optionale Felder (Notes/URL/Image)

## Entscheidung

| Feld | Entscheidung |
|------|--------------|
| `website_url` | **ENTFERNEN** |
| `notes` | **ENTFERNEN** |
| `image_path` | **BEHALTEN**, aber im Config Flow standardmäßig ausgeblendet |

## Begründung

- `website_url` und `notes` werden nur als Attribute gespeichert, ohne echte Funktion
- `image_path` ist Kernfunktionalität (Origin Story: "Bild auf dem Tablet")
- Einfacherer Config Flow durch weniger Felder

## Teil 1: website_url und notes entfernen

### Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| `const.py` | `CONF_NOTES`, `CONF_WEBSITE_URL` entfernen |
| `config_flow.py` | Felder aus allen Schemas entfernen (Trip, Milestone, Anniversary, Special, DST) |
| `binary_sensor.py` | Attribute-Ausgabe entfernen |
| `strings.json` | Übersetzungen entfernen |
| `translations/en.json` | Übersetzungen entfernen |
| `translations/de.json` | Übersetzungen entfernen |

### Code-Stellen in config_flow.py

Folgende Zeilen in allen Event-Schemas entfernen:
```python
vol.Optional(CONF_WEBSITE_URL, default=""): str,
vol.Optional(CONF_NOTES, default=""): str,
```

### Code-Stellen in binary_sensor.py

In allen `extra_state_attributes` Properties entfernen:
```python
if self._event_data.get(CONF_WEBSITE_URL):
    attributes["website_url"] = self._event_data[CONF_WEBSITE_URL]

if self._event_data.get(CONF_NOTES):
    attributes["notes"] = self._event_data[CONF_NOTES]
```

## Teil 2: image_path standardmäßig ausblenden

### Problem

Das Feld `image_path` soll im Config Flow nicht standardmäßig angezeigt werden, aber trotzdem verfügbar sein für Nutzer die es brauchen.

### Bekannte Schwierigkeit

> **ACHTUNG:** Dies wurde bereits versucht und war tricky zu implementieren!
> Home Assistant Config Flows haben keine native "collapsed section" oder "advanced options" Funktion.

### Mögliche Lösungsansätze

#### Ansatz A: Zweistufiger Flow

1. Erst Pflichtfelder abfragen
2. Dann "Möchten Sie ein Bild hinzufügen?" (Ja/Nein)
3. Falls Ja → Extra-Step für image_path

**Pro:** Saubere UX
**Contra:** Mehr Steps, mehr Code

#### Ansatz B: Checkbox "Bild hinzufügen"

```python
vol.Optional(CONF_ADD_IMAGE, default=False): bool,
# Falls True, wird image_path Feld angezeigt
```

**Pro:** Ein Step
**Contra:** Dynamische Felder in Config Flow sind komplex

#### Ansatz C: Nur im Options Flow

- Config Flow: Kein image_path
- Options Flow: image_path verfügbar

**Pro:** Einfachste Lösung
**Contra:** Nutzer muss nach Erstellung nochmal konfigurieren

#### Ansatz D: Immer anzeigen, aber ans Ende

- image_path bleibt, wird aber als letztes optionales Feld angezeigt
- Kein Default-Platzhaltertext, nur leeres Feld

**Pro:** Keine Code-Änderung nötig, nur Reihenfolge
**Contra:** Feld ist immer sichtbar

### Empfehlung

**Ansatz C (Nur im Options Flow)** als pragmatische Lösung:
- Config Flow wird schlanker
- Power-User können Bild nachträglich hinzufügen
- Keine komplexe dynamische UI nötig

### Recherche erforderlich

Vor Implementation prüfen:
- [ ] Gibt es in HA 2024+ neue Config Flow Features für optionale Sections?
- [ ] Wie machen andere Integrationen das?
- [ ] Ist dynamisches Anzeigen/Ausblenden von Feldern möglich?

## Breaking Changes

### Release Notes Vorschlag

```markdown
## Breaking Changes

- **Felder entfernt**: Die optionalen Felder `website_url` und `notes`
  wurden aus allen Event-Typen entfernt. Diese Daten wurden nur als
  Attribute gespeichert und hatten keine Funktion.

  **Migration:** Keine Aktion erforderlich. Die Felder werden bei
  bestehenden Events ignoriert.

- **Image-Konfiguration**: Das Bildfeld wird nicht mehr im initialen
  Setup angezeigt. Bilder können nachträglich über "Konfigurieren"
  hinzugefügt werden.
```

## Status

### Teil 1: website_url und notes entfernen
- [ ] const.py bereinigen
- [ ] config_flow.py bereinigen (alle Event-Typen)
- [ ] binary_sensor.py bereinigen
- [ ] strings.json bereinigen
- [ ] translations/en.json bereinigen
- [ ] translations/de.json bereinigen

### Teil 2: image_path ausblenden
- [ ] Recherche: HA Config Flow Möglichkeiten
- [ ] Lösungsansatz wählen
- [ ] Implementation
