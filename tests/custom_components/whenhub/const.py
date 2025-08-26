"""Constants for the WhenHub integration."""
from __future__ import annotations

DOMAIN = "whenhub"

# Event Types
EVENT_TYPE_TRIP = "trip"
EVENT_TYPE_MILESTONE = "milestone"  
EVENT_TYPE_ANNIVERSARY = "anniversary"
EVENT_TYPE_SPECIAL = "special"

EVENT_TYPES = {
    EVENT_TYPE_TRIP: {
        "name": "Trip",
        "description": "Mehrtägige Reise oder Event",
        "icon": "mdi:airplane",
        "model": "Trip Tracker",
    },
    EVENT_TYPE_MILESTONE: {
        "name": "Milestone", 
        "description": "Einmaliges wichtiges Datum",
        "icon": "mdi:flag-checkered",
        "model": "Milestone Tracker",
    },
    EVENT_TYPE_ANNIVERSARY: {
        "name": "Anniversary",
        "description": "Wiederkehrendes jährliches Event", 
        "icon": "mdi:calendar-heart",
        "model": "Anniversary Tracker",
    },
    EVENT_TYPE_SPECIAL: {
        "name": "Special Event",
        "description": "Spezielle Feiertage und astronomische Events",
        "icon": "mdi:star",
        "model": "Special Event Tracker",
    }
}

# Configuration keys
CONF_EVENT_TYPE = "event_type"
CONF_EVENT_NAME = "event_name"
CONF_START_DATE = "start_date"
CONF_END_DATE = "end_date"
CONF_TARGET_DATE = "target_date"  # Für Milestone und Anniversary
CONF_SPECIAL_TYPE = "special_type"  # Für Special Events
CONF_SPECIAL_CATEGORY = "special_category"  # Für Special Event Kategorien
CONF_IMAGE_PATH = "image_path"
CONF_IMAGE_UPLOAD = "image_upload"
CONF_WEBSITE_URL = "website_url"
CONF_NOTES = "notes"

# Default values
DEFAULT_IMAGE = "/local/whenhub/default_event.png"

# Common string patterns
UNIQUE_ID_PATTERN = "{entry_id}_{sensor_type}"
BINARY_UNIQUE_ID_PATTERN = "{entry_id}_binary_{sensor_type}"
SENSOR_NAME_PATTERN = "{event_name} {sensor_name}"

# Common text constants
TEXT_ZERO_DAYS = "0 Tage"
TEXT_CALCULATION_RUNNING = "Berechnung läuft..."

# Device constants
MANUFACTURER = "WhenHub"
SW_VERSION = "1.0.0"

# Sensor types - für Trip (mehrtägig)
TRIP_SENSOR_TYPES = {
    "days_until": {
        "name": "Days Until Start",
        "icon": "mdi:calendar-clock",
        "unit": "days",
    },
    "days_until_end": {
        "name": "Days Until End",
        "icon": "mdi:calendar-clock",
        "unit": "days",
    },
    "countdown_text": {
        "name": "Countdown Text",
        "icon": "mdi:calendar-text",
        "unit": None,
    },
    "trip_left_days": {
        "name": "Trip Left Days",
        "icon": "mdi:calendar-minus",
        "unit": "days",
    },
    "trip_left_percent": {
        "name": "Trip Left Percent",
        "icon": "mdi:progress-clock",
        "unit": "%",
    },
}

# Sensor types - für Milestone (eintägig, einmalig)
MILESTONE_SENSOR_TYPES = {
    "days_until": {
        "name": "Days Until",
        "icon": "mdi:calendar-clock",
        "unit": "days",
    },
    "countdown_text": {
        "name": "Countdown Text", 
        "icon": "mdi:calendar-text",
        "unit": None,
    },
}

# Sensor types - für Anniversary (eintägig, wiederkehrend)
ANNIVERSARY_SENSOR_TYPES = {
    "days_until_next": {
        "name": "Days Until Next",
        "icon": "mdi:calendar-clock",
        "unit": "days",
    },
    "days_since_last": {
        "name": "Days Since Last",
        "icon": "mdi:calendar-minus",
        "unit": "days",
    },
    "countdown_text": {
        "name": "Countdown Text",
        "icon": "mdi:calendar-text", 
        "unit": None,
    },
    "occurrences_count": {
        "name": "Occurrences Count",
        "icon": "mdi:counter",
        "unit": "times",
    },
    "next_date": {
        "name": "Next Date",
        "icon": "mdi:calendar-arrow-right",
        "unit": None,
    },
    "last_date": {
        "name": "Last Date",
        "icon": "mdi:calendar-arrow-left",
        "unit": None,
    },
}

# Binary sensor types - für Trip
TRIP_BINARY_SENSOR_TYPES = {
    "trip_starts_today": {
        "name": "Trip Starts Today",
        "icon": "mdi:calendar-start",
        "device_class": "occurrence",
    },
    "trip_active_today": {
        "name": "Trip Active Today",
        "icon": "mdi:calendar-check",
        "device_class": "occurrence",
    },
    "trip_ends_today": {
        "name": "Trip Ends Today",
        "icon": "mdi:calendar-end",
        "device_class": "occurrence",
    },
}

# Binary sensor types - für Milestone
MILESTONE_BINARY_SENSOR_TYPES = {
    "is_today": {
        "name": "Is Today",
        "icon": "mdi:calendar-today",
        "device_class": "occurrence",
    },
}

# Binary sensor types - für Anniversary
ANNIVERSARY_BINARY_SENSOR_TYPES = {
    "is_today": {
        "name": "Is Today",
        "icon": "mdi:calendar-today",
        "device_class": "occurrence",
    },
}

# Sensor types - für Special Events
SPECIAL_SENSOR_TYPES = {
    "days_until": {
        "name": "Days Until",
        "icon": "mdi:calendar-clock",
        "unit": "days",
    },
    "days_since_last": {
        "name": "Days Since Last",
        "icon": "mdi:calendar-minus",
        "unit": "days",
    },
    "countdown_text": {
        "name": "Countdown Text",
        "icon": "mdi:calendar-text",
        "unit": None,
    },
    "next_date": {
        "name": "Next Date",
        "icon": "mdi:calendar-arrow-right",
        "unit": None,
    },
    "last_date": {
        "name": "Last Date",
        "icon": "mdi:calendar-arrow-left",
        "unit": None,
    },
}

# Binary sensor types - für Special Events
SPECIAL_BINARY_SENSOR_TYPES = {
    "is_today": {
        "name": "Is Today",
        "icon": "mdi:calendar-today",
        "device_class": "occurrence",
    },
}

# Special Event Kategorien
SPECIAL_EVENT_CATEGORIES = {
    "traditional": {
        "name": "Traditionelle Feiertage",
        "description": "Weihnachten, Ostern, Advent und andere traditionelle Feste",
        "icon": "mdi:cross"
    },
    "calendar": {
        "name": "Kalendarische Feiertage",
        "description": "Neujahr und Silvester",
        "icon": "mdi:calendar"
    },
    "astronomical": {
        "name": "Astronomische Events",
        "description": "Jahreszeitenanfänge",
        "icon": "mdi:weather-sunny"
    }
}

# Special Event Definitionen
SPECIAL_EVENTS = {
    # Traditionelle Feiertage (11 Events)
    "christmas_eve": {
        "name": "Heilig Abend",
        "category": "traditional",
        "type": "fixed",
        "month": 12,
        "day": 24,
    },
    "christmas_day": {
        "name": "1. Weihnachtstag",
        "category": "traditional",
        "type": "fixed",
        "month": 12,
        "day": 25,
    },
    "boxing_day": {
        "name": "2. Weihnachtstag",
        "category": "traditional",
        "type": "fixed",
        "month": 12,
        "day": 26,
    },
    "halloween": {
        "name": "Halloween",
        "category": "traditional",
        "type": "fixed",
        "month": 10,
        "day": 31,
    },
    "easter": {
        "name": "Ostersonntag",
        "category": "traditional",
        "type": "calculated",
        "calculation": "easter",
    },
    "pentecost": {
        "name": "Pfingstsonntag",
        "category": "traditional",
        "type": "calculated",
        "calculation": "pentecost",
    },
    "nikolaus": {
        "name": "Nikolaus",
        "category": "traditional",
        "type": "fixed",
        "month": 12,
        "day": 6,
    },
    "advent_1": {
        "name": "1. Advent",
        "category": "traditional",
        "type": "calculated",
        "calculation": "advent_1",
    },
    "advent_2": {
        "name": "2. Advent",
        "category": "traditional",
        "type": "calculated",
        "calculation": "advent_2",
    },
    "advent_3": {
        "name": "3. Advent",
        "category": "traditional",
        "type": "calculated",
        "calculation": "advent_3",
    },
    "advent_4": {
        "name": "4. Advent",
        "category": "traditional",
        "type": "calculated",
        "calculation": "advent_4",
    },
    
    # Kalendarische Feiertage (2 Events)
    "new_year": {
        "name": "Neujahr",
        "category": "calendar",
        "type": "fixed",
        "month": 1,
        "day": 1,
    },
    "new_years_eve": {
        "name": "Silvester",
        "category": "calendar",
        "type": "fixed",
        "month": 12,
        "day": 31,
    },
    
    # Astronomische Events (4 Events)
    "spring_start": {
        "name": "Frühlingsanfang",
        "category": "astronomical",
        "type": "fixed",
        "month": 3,
        "day": 20,
    },
    "summer_start": {
        "name": "Sommeranfang",
        "category": "astronomical",
        "type": "fixed",
        "month": 6,
        "day": 21,
    },
    "autumn_start": {
        "name": "Herbstanfang",
        "category": "astronomical",
        "type": "fixed",
        "month": 9,
        "day": 23,
    },
    "winter_start": {
        "name": "Winteranfang",
        "category": "astronomical",
        "type": "fixed",
        "month": 12,
        "day": 21,
    },
}

# Legacy compatibility - wird durch TRIP_SENSOR_TYPES ersetzt
SENSOR_TYPES = TRIP_SENSOR_TYPES