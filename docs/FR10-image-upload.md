# FR10: Image Upload im Config Flow

## Referenz

- **GitHub Issue:** [#7 - Feature Request: Image upload via drag & drop in Config Flow](https://github.com/moerk-o/WhenHub/issues/7)
- **Status:** Konzept / Planung

---

## Problem

Aktuell unterstützt WhenHub nur einen manuell eingetippten Dateipfad (`CONF_IMAGE_PATH`) für Event-Bilder. Der User muss das Bild also vorher manuell in das HA-Dateisystem hochladen (z.B. per Samba in den `www/`-Ordner) und dann den Pfad kennen und korrekt eingeben. Das ist umständlich und nicht intuitiv.

---

## Ziel

Bild direkt im Config Flow hochladen - per Drag & Drop oder Dateiauswahl. Kein manuelles Hochladen in den Server nötig. Das Bild wird intern in der Integration (als base64 im Config Entry) gespeichert, ohne externe Dateiabhängigkeiten.

---

## Was bereits vorhanden ist

Die Backend-Infrastruktur ist **bereits vollständig implementiert**:

| Komponente | Status | Datei |
|------------|--------|-------|
| `CONF_IMAGE_UPLOAD` | Konstante existiert | `const.py` |
| `image_data` (base64) | Wird gelesen und dekodiert | `image.py:93,145` |
| Fallback-Hierarchie | base64 → Pfad → SVG | `image.py:142-157` |
| MIME-Type-Erkennung | Für bekannte Formate | `image.py:265-278` |
| Fehler-String | `image_upload_failed` | `translations/*.json` |

**Einzige Lücke:** Im Config Flow wird `CONF_IMAGE_UPLOAD` nie befüllt - die Verbindung zwischen UI und `image_data` fehlt.

---

## Lösung: HA FileSelector

Home Assistant stellt einen nativen `FileSelector` bereit, der im Frontend automatisch Drag & Drop und Dateiauswahl liefert - ohne eigene Frontend-Komponenten.

**Referenz-Implementierung:** [homeconnect_local_hass](https://github.com/chris-mc1/homeconnect_local_hass) nutzt exakt diesen Ansatz für Konfigurations-ZIP-Uploads.

### Schema

```python
from homeassistant.components.selector import FileSelector, FileSelectorConfig

vol.Optional(CONF_IMAGE_UPLOAD): FileSelector(
    config=FileSelectorConfig(accept=".jpg,.jpeg,.png,.webp,.gif")
)
```

### Verarbeitung im Config Flow Handler

```python
from homeassistant.components.file_upload import process_uploaded_file
import base64

if uploaded_file_id := user_input.get(CONF_IMAGE_UPLOAD):
    with process_uploaded_file(self.hass, uploaded_file_id) as path:
        image_bytes = path.read_bytes()
        image_data = base64.b64encode(image_bytes).decode()
        # image_data → config entry data["image_data"]
```

Der `FileSelector` liefert eine temporäre `uploaded_file_id`. `process_uploaded_file()` stellt den Zugriff auf die Temp-Datei sicher und räumt danach auf.

---

## Config Flow Design

Beide bestehenden Bild-Optionen bleiben erhalten - der User kann eine oder keine wählen:

```
Bild (optional)

Hochladen:  [ Datei hierher ziehen oder klicken ]   ← FileSelector (Drag & Drop)

oder

Pfad:       [________________________________]       ← bestehendes CONF_IMAGE_PATH
```

**Priorität bei beiden Angaben:** Upload schlägt Pfad (entspricht der bestehenden Hierarchie in `image.py`).

---

## Speicherung

Das base64-kodierte Bild wird direkt im Config Entry gespeichert:

```python
config_entry.data = {
    ...
    "image_data": "iVBORw0KGgoAAAANS...",   # base64-String
}
```

### Größenüberlegung

| Format | 1 MP Foto | 2 MP Foto |
|--------|-----------|-----------|
| JPEG (komprimiert) | ~300 KB | ~600 KB |
| base64-Overhead | +33% | +33% |
| Im Config Entry | ~400 KB | ~800 KB |

Config Entries liegen als JSON in `.storage/core.config_entries`. Große Bilder erhöhen die Datei spürbar, sind aber technisch kein Problem. Empfehlung: Maximalgröße von **5 MB** für den Upload erzwingen (HA's File-Upload-Infrastruktur unterstützt Limits).

---

## MIME-Type-Erkennung

Die bestehende Erkennung in `image.py` basiert auf Dateiendungen. Bei Uploads sollte zusätzlich der tatsächliche Datei-Magic-Byte geprüft werden:

| Magic Bytes | Format |
|-------------|--------|
| `FF D8 FF` | JPEG |
| `89 50 4E 47` | PNG |
| `52 49 46 46 ... 57 45 42 50` | WebP |
| `47 49 46 38` | GIF |

Die MIME-Type-Erkennung kann entweder per Magic Bytes oder durch Speicherung des Typs beim Upload erfolgen:

```python
# Typ beim Upload ermitteln und mitspeichern
suffix = path.suffix.lower()
mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}
image_mime = mime_map.get(suffix, "image/jpeg")
# image_mime → config entry data["image_mime"]
```

---

## Options Flow

Das Bild muss auch nachträglich änderbar oder löschbar sein:

- Neues Bild hochladen → überschreibt das gespeicherte
- Feld leer lassen → bestehendes Bild bleibt erhalten
- Explizite "Bild löschen"-Checkbox → setzt `image_data` auf `None`

---

## Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| `config_flow.py` | `FileSelector` in allen Event-Typ-Schritten hinzufügen, Upload-Verarbeitung |
| `image.py` | MIME-Type-Erkennung auf `image_mime` aus Config Entry erweitern |
| `const.py` | Ggf. `CONF_IMAGE_MIME` Konstante ergänzen |
| `translations/en.json` | UI-Texte für Upload-Feld |
| `translations/de.json` | UI-Texte für Upload-Feld |

---

## Status

- [ ] Config Flow: FileSelector in allen Event-Typ-Schritten
- [ ] Config Flow: Upload-Verarbeitung (base64-Speicherung)
- [ ] Config Flow: MIME-Type-Speicherung
- [ ] Options Flow: Bild ändern / löschen
- [ ] image.py: MIME-Type aus Config Entry lesen
- [ ] Übersetzungen
- [ ] Tests
