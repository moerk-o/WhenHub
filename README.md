# WhenHub

![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1+-green.svg)

WhenHub ist eine Home Assistant Integration zum Verfolgen verschiedener Events und wichtiger Termine. Die Integration stellt Countdown-Sensoren, Status-Informationen und visuelle Darstellungen für deine Events bereit.

## Überblick

**Die Entstehungsgeschichte:** Die Kinder haben ständig gefragt "Wie lange noch bis zum Urlaub?" oder "Wie viele Tage noch bis zu meinem Geburtstag?". Ich dachte mir, da kann doch was mit HomeAssistant Machen! Nun zeigt WhenHub auf dem Tablet ein Bild des Ereignisses mit einer großen Zahl für die verbleibenden Tage und darunter die Dauer noch einmal als Text.

### Event-Typen

**Trip** - Mehrtägige Events wie Urlaub oder der Besuch von Oma  
**Milestone** - Einmalige wichtige Termine wie Schulveranstaltungen oder 'wann kommt das neue Haustier'  
**Anniversary** - Jährlich wiederkehrende Events wie Geburtstage oder Feiertage  

## Installation

### Manuelle Installation

1. Lade die neueste Version von der [Releases-Seite](https://github.com/yourusername/whenhub/releases) herunter
2. Entpacke die Dateien in das `custom_components/whenhub` Verzeichnis deiner Home Assistant Installation
3. Starte Home Assistant neu
4. Gehe zu **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen**
5. Suche nach "WhenHub" und folge dem Konfigurationsassistenten

## Trip Events

Trip Events haben ein **Startdatum** und ein **Enddatum** und bieten umfassende Tracking-Funktionen für mehrtägige Events.

### Konfiguration

Bei der Einrichtung eines Trip Events konfigurierst du:

- **Event Name**: z.B. "Dänemarkurlaub 2025"
- **Startdatum**: Wann der Trip beginnt (Format: YYYY-MM-DD)
- **Enddatum**: Wann der Trip endet (Format: YYYY-MM-DD)
- **Bildpfad** *(optional)*: 
  - Leer lassen = Automatisch generiertes Standard-Bild (blaues Flugzeug-Icon)
  - Dateipfad = z.B. `/local/images/daenemark.jpg` für eigene Bilder
  - Base64-String = Direkt eingefügtes, kodiertes Bild
- **Website URL** *(optional)*: Link zur Unterkunft oder anderen relevanten Infos
- **Notizen** *(optional)*: Zusätzliche Informationen

### Verfügbare Entitäten

#### Sensoren
- **Days Until Start** - Tage bis zum Trip-Beginn
- **Days Until End** - Tage bis zum Trip-Ende  
- **Countdown Text** - Formatierter Countdown-Text ("2 Jahre, 3 Monate, 1 Woche, 4 Tage")
  - **Attribute**: 
    - `event_name` - Name des Events
    - `event_type` - Typ des Events (trip)
    - `start_date` - Startdatum (ISO-Format)
    - `end_date` - Enddatum (ISO-Format)
    - `total_days` - Gesamte Trip-Dauer in Tagen
    - `text_years` - Jahre aus dem Countdown-Text bis Start
    - `text_months` - Monate aus dem Countdown-Text bis Start
    - `text_weeks` - Wochen aus dem Countdown-Text bis Start
    - `text_days` - Tage aus dem Countdown-Text bis Start
- **Trip Left Days** - Verbleibende Tage während des Trips
- **Trip Left Percent** - Verbleibender Trip-Anteil in Prozent (0-100%)

#### Binary Sensoren
- **Trip Starts Today** - `true` wenn der Trip heute beginnt
- **Trip Active Today** - `true` wenn der Trip heute aktiv ist
- **Trip Ends Today** - `true` wenn der Trip heute endet

#### Image
- **Event Image** - Zeigt das konfigurierte Bild oder Standard-Bild
  - **Attribute**: 
    - `image_type` - "user_defined" (eigenes Bild) oder "system_defined" (Standard-Icon)
    - `image_path` - Pfad zum Bild, "base64_data" oder "default_svg"

## Milestone Events

Milestone Events haben ein einzelnes **Zieldatum** und fokussieren sich auf den Countdown zu diesem wichtigen Termin.

### Konfiguration

Bei der Einrichtung eines Milestone Events konfigurierst du:

- **Event Name**: z.B. "Geburtstag Max" oder "Projektabgabe"
- **Zieldatum**: Das wichtige Datum (Format: YYYY-MM-DD)
- **Bildpfad** *(optional)*: 
  - Leer lassen = Automatisch generiertes Standard-Bild (rotes Flaggen-Icon)
  - Dateipfad = z.B. `/local/images/geburtstag.jpg` für eigene Bilder
  - Base64-String = Direkt eingefügtes, kodiertes Bild
- **Website URL** *(optional)*: Relevante URL zum Event
- **Notizen** *(optional)*: Zusätzliche Informationen

### Verfügbare Entitäten

#### Sensoren
- **Days Until** - Tage bis zum Milestone (kann negativ werden wenn das Datum vorbei ist)
- **Countdown Text** - Formatierter Countdown-Text bis zum Milestone
  - **Attribute**: 
    - `event_name` - Name des Events
    - `event_type` - Typ des Events (milestone)
    - `date` - Zieldatum (ISO-Format)
    - `text_years` - Jahre aus dem Countdown-Text bis Ziel
    - `text_months` - Monate aus dem Countdown-Text bis Ziel
    - `text_weeks` - Wochen aus dem Countdown-Text bis Ziel
    - `text_days` - Tage aus dem Countdown-Text bis Ziel

#### Binary Sensoren
- **Is Today** - `true` wenn heute der Milestone-Tag ist

#### Image
- **Event Image** - Zeigt das konfigurierte Bild oder Standard-Bild
  - **Attribute**: 
    - `image_type` - "user_defined" (eigenes Bild) oder "system_defined" (Standard-Icon)
    - `image_path` - Pfad zum Bild, "base64_data" oder "default_svg"

## Anniversary Events

Anniversary Events wiederholen sich jährlich basierend auf einem **ursprünglichen Datum** und bieten sowohl Rückblick- als auch Vorschau-Funktionen.

### Konfiguration

Bei der Einrichtung eines Anniversary Events konfigurierst du:

- **Event Name**: z.B. "Hochzeitstag" oder "Firmenjubiläum"
- **Ursprüngliches Datum**: Das Datum des ersten Events (Format: YYYY-MM-DD)
- **Bildpfad** *(optional)*: 
  - Leer lassen = Automatisch generiertes Standard-Bild (pinkes Herz-Icon)
  - Dateipfad = z.B. `/local/images/hochzeit.jpg` für eigene Bilder
  - Base64-String = Direkt eingefügtes, kodiertes Bild
- **Website URL** *(optional)*: Relevante URL zum Event
- **Notizen** *(optional)*: Zusätzliche Informationen

### Verfügbare Entitäten

#### Sensoren
- **Days Until Next** - Tage bis zum nächsten Anniversary
- **Days Since Last** - Tage seit dem letzten Anniversary
- **Countdown Text** - Formatierter Countdown-Text zum nächsten Anniversary
  - **Attribute**: 
    - `event_name` - Name des Events
    - `event_type` - Typ des Events (anniversary)
    - `initial_date` - Ursprüngliches Datum (ISO-Format)
    - `next_anniversary` - Datum des nächsten Anniversary (ISO-Format)
    - `years_on_next` - Anzahl Jahre beim nächsten Anniversary
    - `text_years` - Jahre aus dem Countdown-Text bis nächstes Anniversary
    - `text_months` - Monate aus dem Countdown-Text bis nächstes Anniversary
    - `text_weeks` - Wochen aus dem Countdown-Text bis nächstes Anniversary
    - `text_days` - Tage aus dem Countdown-Text bis nächstes Anniversary
- **Occurrences Count** - Anzahl der bisherigen Wiederholungen
- **Next Date** - Datum des nächsten Anniversary (ISO-Format)
- **Last Date** - Datum des letzten Anniversary (ISO-Format)

#### Binary Sensoren
- **Is Today** - `true` wenn heute ein Anniversary-Tag ist

#### Image
- **Event Image** - Zeigt das konfigurierte Bild oder Standard-Bild
  - **Attribute**: 
    - `image_type` - "user_defined" (eigenes Bild) oder "system_defined" (Standard-Icon)
    - `image_path` - Pfad zum Bild, "base64_data" oder "default_svg"

### Schaltjahr-Behandlung
Anniversary Events handhaben Schaltjahre intelligent: Wenn das ursprüngliche Datum der 29. Februar ist, wird in Nicht-Schaltjahren automatisch der 28. Februar verwendet.

## Erweiterte Features

### Bildverwaltung

WhenHub unterstützt verschiedene Arten von Bildern für deine Events:

1. **Benutzerdefinierte Bilder**: Verwende `/local/images/mein-event.jpg` für eigene Bilder
2. **Automatisch generierte Icons**: 
   - **Trip**: Blaues Flugzeug-Icon
   - **Milestone**: Rote Flagge
   - **Anniversary**: Pinkes Herz
3. **Unterstützte Formate**: JPEG, PNG, WebP, GIF, SVG

Bilder werden im `www/` Verzeichnis von Home Assistant gespeichert und über `/local/` Pfade referenziert.

### Countdown-Text Formatierung

Der Countdown-Text verwendet eine intelligente deutsche Formatierung:

- **Vollständig**: "2 Jahre, 3 Monate, 1 Woche, 4 Tage"
- **Verkürzt**: "5 Tage" (null-Werte werden weggelassen)
- **Erreicht**: "0 Tage" wenn das Datum erreicht oder überschritten ist

Die Berechnung verwendet Näherungswerte (365 Tage/Jahr, 30 Tage/Monat) für konsistente Ergebnisse.

### Optionen-Flow

Alle Event-Konfigurationen können nach der Ersteinrichtung über den **Optionen-Flow** bearbeitet werden:

1. Gehe zu **Einstellungen** → **Geräte & Dienste** → **WhenHub**
2. Klicke auf **Konfigurieren** bei dem gewünschten Event
3. Ändere die Einstellungen für das jeweilige Event (Trip, Milestone oder Anniversary) und speichere

**Hinweis:** Eine Umwandlung zwischen den Event-Typen (z.B. Trip zu Anniversary) ist nicht möglich.

Alle Sensoren werden automatisch mit den neuen Daten aktualisiert.

## Contributors Welcome

Dieses Projekt ist Open Source und Beiträge sind herzlich willkommen! Issues für Bugs oder Feature-Requests sind genauso geschätzt wie Pull Requests für Code-Verbesserungen.

---

⭐ **Gefällt dir WhenHub?** Anstatt mir einen Kaffee zu spendieren, spendiere dem Projekt ein Stern auf GitHub!
