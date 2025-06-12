"""Constants for the WhenHub integration - Internationalized Version."""
from __future__ import annotations

DOMAIN = "whenhub"

# Event Types
EVENT_TYPE_TRIP = "trip"
EVENT_TYPE_MILESTONE = "milestone"  
EVENT_TYPE_ANNIVERSARY = "anniversary"

EVENT_TYPES = {
    EVENT_TYPE_TRIP: {
        "name": "Trip",
        "description_key": "trip_description",  # Translation key instead of German text
        "icon": "mdi:airplane",
        "model": "Trip Tracker",
    },
    EVENT_TYPE_MILESTONE: {
        "name": "Milestone", 
        "description_key": "milestone_description",  # Translation key instead of German text
        "icon": "mdi:flag-checkered",
        "model": "Milestone Tracker",
    },
    EVENT_TYPE_ANNIVERSARY: {
        "name": "Anniversary",
        "description_key": "anniversary_description",  # Translation key instead of German text
        "icon": "mdi:calendar-heart",
        "model": "Anniversary Tracker",
    }
}

# Configuration keys
CONF_EVENT_TYPE = "event_type"
CONF_EVENT_NAME = "event_name"
CONF_START_DATE = "start_date"
CONF_END_DATE = "end_date"
CONF_TARGET_DATE = "target_date"  # Für Milestone und Anniversary
CONF_IMAGE_PATH = "image_path"
CONF_IMAGE_UPLOAD = "image_upload"
CONF_WEBSITE_URL = "website_url"
CONF_NOTES = "notes"

# Default values
DEFAULT_IMAGE = "/local/whenhub/default_event.png"

# Translation keys instead of hard-coded text
TEXT_ZERO_DAYS = "zero_days"  # Will be translated
TEXT_CALCULATION_RUNNING = "calculation_running"  # Will be translated

# Device constants
MANUFACTURER = "WhenHub"
SW_VERSION = "1.3.0"

# Sensor types - für Trip (mehrtägig) - NOW WITH UNIT TRANSLATION
TRIP_SENSOR_TYPES = {
    "days_until": {
        "translation_key": "days_until_start",
        "icon": "mdi:calendar-clock",
        "unit": None,  # UPDATED: Changed from "days" to None for unit translation
    },
    "days_until_end": {
        "translation_key": "days_until_end",
        "icon": "mdi:calendar-clock",
        "unit": None,  # UPDATED: Changed from "days" to None for unit translation
    },
    "countdown_text": {
        "translation_key": "countdown_text",
        "icon": "mdi:calendar-text",
        "unit": None,  # No unit for text - stays None
    },
    "trip_left_days": {
        "translation_key": "trip_left_days",
        "icon": "mdi:calendar-minus",
        "unit": None,  # UPDATED: Changed from "days" to None for unit translation
    },
    "trip_left_percent": {
        "translation_key": "trip_left_percent",
        "icon": "mdi:progress-clock",
        "unit": None,  # UPDATED: Changed from "%" to None for unit translation
    },
}

# Sensor types - für Milestone (eintägig, einmalig) - NOW WITH UNIT TRANSLATION
MILESTONE_SENSOR_TYPES = {
    "days_until": {
        "translation_key": "days_until",
        "icon": "mdi:calendar-clock",
        "unit": None,  # UPDATED: Changed from "days" to None for unit translation
    },
    "countdown_text": {
        "translation_key": "countdown_text",
        "icon": "mdi:calendar-text",
        "unit": None,  # No unit for text - stays None
    },
}

# Sensor types - für Anniversary (eintägig, wiederkehrend) - NOW WITH UNIT TRANSLATION
ANNIVERSARY_SENSOR_TYPES = {
    "days_until_next": {
        "translation_key": "days_until_next",
        "icon": "mdi:calendar-clock",
        "unit": None,  # UPDATED: Changed from "days" to None for unit translation
    },
    "days_since_last": {
        "translation_key": "days_since_last",
        "icon": "mdi:calendar-minus",
        "unit": None,  # UPDATED: Changed from "days" to None for unit translation
    },
    "countdown_text": {
        "translation_key": "countdown_text",
        "icon": "mdi:calendar-text", 
        "unit": None,  # No unit for text - stays None
    },
    "occurrences_count": {
        "translation_key": "occurrences_count",
        "icon": "mdi:counter",
        "unit": None,  # UPDATED: Changed from "times" to None for unit translation
    },
    "next_date": {
        "translation_key": "next_date",
        "icon": "mdi:calendar-arrow-right",
        "unit": None,  # No unit for date - stays None
    },
    "last_date": {
        "translation_key": "last_date",
        "icon": "mdi:calendar-arrow-left",
        "unit": None,  # No unit for date - stays None
    },
}

# Binary sensor types - für Trip - NOW WITH TRANSLATION KEYS
TRIP_BINARY_SENSOR_TYPES = {
    "trip_starts_today": {
        "translation_key": "trip_starts_today",
        "icon": "mdi:calendar-start",
        "device_class": "occurrence",
    },
    "trip_active_today": {
        "translation_key": "trip_active_today",
        "icon": "mdi:calendar-check",
        "device_class": "occurrence",
    },
    "trip_ends_today": {
        "translation_key": "trip_ends_today",
        "icon": "mdi:calendar-end",
        "device_class": "occurrence",
    },
}

# Binary sensor types - für Milestone - NOW WITH TRANSLATION KEYS
MILESTONE_BINARY_SENSOR_TYPES = {
    "is_today": {
        "translation_key": "is_today",
        "icon": "mdi:calendar-today",
        "device_class": "occurrence",
    },
}

# Binary sensor types - für Anniversary - NOW WITH TRANSLATION KEYS
ANNIVERSARY_BINARY_SENSOR_TYPES = {
    "is_today": {
        "translation_key": "is_today",
        "icon": "mdi:calendar-today",
        "device_class": "occurrence",
    },
}

# Legacy compatibility - wird durch TRIP_SENSOR_TYPES ersetzt
SENSOR_TYPES = TRIP_SENSOR_TYPES

# NEW: Countdown translation keys for internationalized formatting
COUNTDOWN_TRANSLATION_KEYS = {
    "units": {
        "year": "year",
        "month": "month", 
        "week": "week",
        "day": "day"
    },
    "zero": "zero_days",
    "calculating": "calculation_running",
    "separator": "countdown_separator"  # For comma/space between units
}