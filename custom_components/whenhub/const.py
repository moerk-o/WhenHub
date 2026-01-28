"""Constants for the WhenHub integration.

This module defines all constants used throughout the WhenHub integration:
- Domain and event type identifiers
- Configuration keys for config flow
- Sensor type definitions with metadata (name, icon, unit)
- Binary sensor type definitions
- Special event categories and definitions
- Common text constants and patterns
"""
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
        "description": "Multi-day trip or event",
        "icon": "mdi:airplane",
        "model": "Trip Tracker",
    },
    EVENT_TYPE_MILESTONE: {
        "name": "Milestone",
        "description": "One-time important date",
        "icon": "mdi:flag-checkered",
        "model": "Milestone Tracker",
    },
    EVENT_TYPE_ANNIVERSARY: {
        "name": "Anniversary",
        "description": "Recurring yearly event",
        "icon": "mdi:calendar-heart",
        "model": "Anniversary Tracker",
    },
    EVENT_TYPE_SPECIAL: {
        "name": "Special Event",
        "description": "Special holidays and astronomical events",
        "icon": "mdi:star",
        "model": "Special Event Tracker",
    }
}

# Configuration keys
CONF_EVENT_TYPE = "event_type"
CONF_EVENT_NAME = "event_name"
CONF_START_DATE = "start_date"
CONF_END_DATE = "end_date"
CONF_TARGET_DATE = "target_date"  # For Milestone and Anniversary
CONF_SPECIAL_TYPE = "special_type"  # For Special Events
CONF_SPECIAL_CATEGORY = "special_category"  # For Special Event Categories
CONF_DST_TYPE = "dst_type"  # For DST Events
CONF_DST_REGION = "dst_region"  # For DST Events
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

# Common text constants (German - see prompt.md for rationale)
TEXT_ZERO_DAYS = "0 Tage"
TEXT_CALCULATION_RUNNING = "Berechnung läuft..."

# Device constants
MANUFACTURER = "WhenHub"
SW_VERSION = "2.1.0"

# Sensor types for Trip (multi-day events)
TRIP_SENSOR_TYPES = {
    "days_until": {
        "name": "Days Until Start",
        "icon": "mdi:calendar-clock",
        "unit": "d",
        "device_class": "duration",
    },
    "days_until_end": {
        "name": "Days Until End",
        "icon": "mdi:calendar-clock",
        "unit": "d",
        "device_class": "duration",
    },
    "event_date": {
        "name": "Event Date",
        "icon": "mdi:calendar",
        "unit": None,
        "device_class": "timestamp",
    },
    "trip_left_days": {
        "name": "Trip Left Days",
        "icon": "mdi:calendar-minus",
        "unit": "d",
        "device_class": "duration",
    },
    "trip_left_percent": {
        "name": "Trip Left Percent",
        "icon": "mdi:progress-clock",
        "unit": "%",
    },
}

# Sensor types for Milestone (single-day, one-time events)
MILESTONE_SENSOR_TYPES = {
    "days_until": {
        "name": "Days Until",
        "icon": "mdi:calendar-clock",
        "unit": "d",
        "device_class": "duration",
    },
    "event_date": {
        "name": "Event Date",
        "icon": "mdi:calendar",
        "unit": None,
        "device_class": "timestamp",
    },
}

# Sensor types for Anniversary (single-day, recurring yearly)
ANNIVERSARY_SENSOR_TYPES = {
    "days_until_next": {
        "name": "Days Until Next",
        "icon": "mdi:calendar-clock",
        "unit": "d",
        "device_class": "duration",
    },
    "days_since_last": {
        "name": "Days Since Last",
        "icon": "mdi:calendar-minus",
        "unit": "d",
        "device_class": "duration",
    },
    "event_date": {
        "name": "Event Date",
        "icon": "mdi:calendar",
        "unit": None,
        "device_class": "timestamp",
    },
    "occurrences_count": {
        "name": "Occurrences Count",
        "icon": "mdi:counter",
        "unit": None,
    },
    "next_date": {
        "name": "Next Date",
        "icon": "mdi:calendar-arrow-right",
        "unit": None,
        "device_class": "timestamp",
    },
    "last_date": {
        "name": "Last Date",
        "icon": "mdi:calendar-arrow-left",
        "unit": None,
        "device_class": "timestamp",
    },
}

# Binary sensor types for Trip
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

# Binary sensor types for Milestone
MILESTONE_BINARY_SENSOR_TYPES = {
    "is_today": {
        "name": "Is Today",
        "icon": "mdi:calendar-today",
        "device_class": "occurrence",
    },
}

# Binary sensor types for Anniversary
ANNIVERSARY_BINARY_SENSOR_TYPES = {
    "is_today": {
        "name": "Is Today",
        "icon": "mdi:calendar-today",
        "device_class": "occurrence",
    },
}

# Sensor types for Special Events
SPECIAL_SENSOR_TYPES = {
    "days_until": {
        "name": "Days Until",
        "icon": "mdi:calendar-clock",
        "unit": "d",
        "device_class": "duration",
    },
    "days_since_last": {
        "name": "Days Since Last",
        "icon": "mdi:calendar-minus",
        "unit": "d",
        "device_class": "duration",
    },
    "event_date": {
        "name": "Event Date",
        "icon": "mdi:calendar",
        "unit": None,
        "device_class": "timestamp",
    },
    "next_date": {
        "name": "Next Date",
        "icon": "mdi:calendar-arrow-right",
        "unit": None,
        "device_class": "timestamp",
    },
    "last_date": {
        "name": "Last Date",
        "icon": "mdi:calendar-arrow-left",
        "unit": None,
        "device_class": "timestamp",
    },
}

# Binary sensor types for Special Events
SPECIAL_BINARY_SENSOR_TYPES = {
    "is_today": {
        "name": "Is Today",
        "icon": "mdi:calendar-today",
        "device_class": "occurrence",
    },
}

# Binary sensor types for DST Events (extends SPECIAL_BINARY_SENSOR_TYPES)
DST_BINARY_SENSOR_TYPES = {
    "is_today": {
        "name": "Is Today",
        "icon": "mdi:calendar-today",
        "device_class": "occurrence",
    },
    "is_dst_active": {
        "name": "DST Active",
        "icon": "mdi:weather-sunny",
        "device_class": None,  # No standard device_class fits
    },
}

# Special Event Categories (German - see prompt.md for rationale)
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
    },
    "dst": {
        "name": "Zeitumstellung",
        "description": "Sommer- und Winterzeitwechsel",
        "icon": "mdi:clock-time-four"
    }
}

# Special Event Definitions (German - see prompt.md for rationale)
SPECIAL_EVENTS = {
    # Traditional Holidays (11 Events)
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

    # Calendar Holidays (2 Events)
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

    # Astronomical Events (4 Events)
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

# DST Event Types
DST_EVENT_TYPES = {
    "next_change": {
        "name": "Nächster Wechsel",
        "description": "Nächste Zeitumstellung (Sommer oder Winter)",
        "icon": "mdi:clock-time-four",
    },
    "next_summer": {
        "name": "Nächste Sommerzeit",
        "description": "Nächster Beginn der Sommerzeit (Uhr vor)",
        "icon": "mdi:weather-sunny",
    },
    "next_winter": {
        "name": "Nächste Winterzeit",
        "description": "Nächster Beginn der Winterzeit (Uhr zurück)",
        "icon": "mdi:weather-snowy",
    },
}

# DST Regions with transition rules
DST_REGIONS = {
    "eu": {
        "name": "EU",
        "summer": {
            "rule": "last",      # "last" or "nth"
            "weekday": 6,        # 0=Monday, 6=Sunday
            "month": 3,          # March
        },
        "winter": {
            "rule": "last",
            "weekday": 6,
            "month": 10,         # October
        },
    },
    "usa": {
        "name": "USA",
        "summer": {
            "rule": "nth",
            "weekday": 6,
            "month": 3,          # March
            "n": 2,              # 2nd Sunday
        },
        "winter": {
            "rule": "nth",
            "weekday": 6,
            "month": 11,         # November
            "n": 1,              # 1st Sunday
        },
    },
    "australia": {
        "name": "Australien",
        "summer": {
            "rule": "nth",
            "weekday": 6,
            "month": 10,         # October
            "n": 1,              # 1st Sunday
        },
        "winter": {
            "rule": "nth",
            "weekday": 6,
            "month": 4,          # April
            "n": 1,              # 1st Sunday
        },
    },
    "new_zealand": {
        "name": "Neuseeland",
        "summer": {
            "rule": "last",
            "weekday": 6,
            "month": 9,          # September
        },
        "winter": {
            "rule": "nth",
            "weekday": 6,
            "month": 4,          # April
            "n": 1,              # 1st Sunday
        },
    },
}

# Timezone to DST region mapping for auto-detection
TIMEZONE_TO_DST_REGION = {
    "Europe/": "eu",
    "America/New_York": "usa",
    "America/Chicago": "usa",
    "America/Denver": "usa",
    "America/Los_Angeles": "usa",
    "America/Toronto": "usa",
    "Australia/": "australia",
    "Pacific/Auckland": "new_zealand",
}

# Legacy compatibility - replaced by TRIP_SENSOR_TYPES
SENSOR_TYPES = TRIP_SENSOR_TYPES