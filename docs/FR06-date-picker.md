# FR06: Date Picker im Config Flow

## Problem

Aktuell werden Datumsfelder als einfache Textfelder mit Hinweis "YYYY-MM-DD" dargestellt:

```python
vol.Required(CONF_START_DATE): str,
vol.Required(CONF_END_DATE): str,
```

Das ist:
- Fehleranfällig (Tippfehler, falsches Format)
- Nicht benutzerfreundlich
- Erfordert manuelle Validierung

## Lösung

Home Assistant bietet native `DateSelector` und `DateTimeSelector`:

```python
from homeassistant.helpers.selector import DateSelector, DateSelectorConfig

# Im Schema:
vol.Required(CONF_START_DATE): DateSelector(DateSelectorConfig()),
```

### Vorteile

- **Native UI**: Kalender-Popup im Browser
- **Automatische Validierung**: Nur gültige Daten möglich
- **Benutzerfreundlich**: Klicken statt Tippen
- **Lokalisiert**: Datumsformat je nach HA-Einstellung

## Implementation

### Import hinzufügen

```python
# In config_flow.py (einfache Variante wie in StreakHub)
from homeassistant.helpers import selector
```

### Schema ändern

**Vorher (Textfeld):**
```python
data_schema = vol.Schema({
    vol.Required(CONF_EVENT_NAME): str,
    vol.Required(CONF_START_DATE): str,
    vol.Required(CONF_END_DATE): str,
})
```

**Nachher (Date Picker):**
```python
data_schema = vol.Schema({
    vol.Required(CONF_EVENT_NAME): str,
    vol.Required(CONF_START_DATE): selector.DateSelector(),
    vol.Required(CONF_END_DATE): selector.DateSelector(),
})
```

### Rückgabewert

Der DateSelector gibt ein `datetime.date` Objekt zurück, nicht einen String.

**Vorher (String-Parsing nötig):**
```python
start_date = user_input[CONF_START_DATE]
if isinstance(start_date, str):
    start_date = date.fromisoformat(start_date)
```

**Nachher (direkt verwendbar):**
```python
start_date = user_input[CONF_START_DATE]  # Ist bereits datetime.date
```

## Betroffene Stellen

### config_flow.py

| Step | Felder |
|------|--------|
| `async_step_trip` | `start_date`, `end_date` |
| `async_step_milestone` | `target_date` |
| `async_step_anniversary` | `target_date` |
| Options: `async_step_trip_options` | `start_date`, `end_date` |
| Options: `async_step_milestone_options` | `target_date` |
| Options: `async_step_anniversary_options` | `target_date` |

### Validierung vereinfachen

Die manuelle String-Parsing-Logik kann entfernt werden:

```python
# Diese Zeilen können entfallen:
if isinstance(start_date, str):
    start_date = date.fromisoformat(start_date)
```

### Übersetzungen anpassen

Die Hinweise "Format: YYYY-MM-DD" in `data_description` können entfernt werden, da der Date Picker selbsterklärend ist.

## Bekannte Einschränkung

Laut [GitHub Issue #12329](https://github.com/home-assistant/frontend/issues/12329):

> Der DateSelector erlaubt keine Daten vor 01.01.1970

Für WhenHub ist das kein Problem:
- **Trip**: Reisen in der Vergangenheit sind unüblich
- **Milestone**: Countdown zu vergangenen Daten macht keinen Sinn
- **Anniversary**: Ursprungsdatum könnte vor 1970 liegen (z.B. Geburtstag 1965)

### Workaround für Anniversary

Falls Nutzer ein Datum vor 1970 benötigen:
- Nur Jahr und Monat/Tag speichern
- Oder: Textfeld als Fallback beibehalten

**Empfehlung:** Zunächst DateSelector verwenden, bei Nutzerbeschwerden Fallback evaluieren.

## Beispiel: Vollständiger Trip-Step

```python
from homeassistant.helpers import selector

async def async_step_trip(
    self, user_input: dict[str, Any] | None = None
) -> FlowResult:
    """Handle trip event configuration."""
    errors: dict[str, str] = {}

    if user_input is not None:
        start_date = user_input[CONF_START_DATE]
        end_date = user_input[CONF_END_DATE]

        # Direkte Validierung ohne String-Parsing
        if start_date >= end_date:
            errors["base"] = "invalid_dates"
        else:
            # Speichern...
            pass

    data_schema = vol.Schema({
        vol.Required(CONF_EVENT_NAME): str,
        vol.Required(CONF_START_DATE): selector.DateSelector(),
        vol.Required(CONF_END_DATE): selector.DateSelector(),
    })

    return self.async_show_form(
        step_id="trip",
        data_schema=data_schema,
        errors=errors,
    )
```

## Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| `config_flow.py` | DateSelector Import, Schemas ändern, Validierung vereinfachen |
| `strings.json` | "YYYY-MM-DD" Hinweise entfernen |
| `translations/en.json` | "YYYY-MM-DD" Hinweise entfernen |
| `translations/de.json` | "YYYY-MM-DD" Hinweise entfernen |

## Status

- [x] DateSelector Import hinzufügen
- [x] Trip-Schema ändern (Config + Options)
- [x] Milestone-Schema ändern (Config + Options)
- [x] Anniversary-Schema ändern (Config + Options)
- [x] String-Parsing-Code entfernen
- [x] Übersetzungen anpassen
- [ ] Testen mit verschiedenen Datumsformaten (manuell in HA)
- [ ] Testen: Anniversary mit Datum vor 1970 (manuell in HA)

**Erledigt:** 2026-01-28

## Referenz: StreakHub

In StreakHub ist der DateSelector bereits implementiert:

**Import:**
```python
from homeassistant.helpers import selector
```

**Verwendung:**
```python
vol.Optional(
    CONF_INITIAL_DATE,
    default=date.today().isoformat(),
): selector.DateSelector(),
```

**Hinweis:** Der Default-Wert muss als ISO-String übergeben werden (`date.today().isoformat()`), nicht als date-Objekt.

Siehe: `StreakHub/custom_components/streakhub/config_flow.py`

## Weitere Referenzen

- [Home Assistant Data Entry Flow](https://developers.home-assistant.io/docs/data_entry_flow_index/)
- [GitHub Issue: DateSelector vor 1970](https://github.com/home-assistant/frontend/issues/12329)
