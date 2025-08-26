"""Common test fixtures for WhenHub integration tests."""
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from datetime import date

DOMAIN = "whenhub"

@pytest.fixture
def trip_config_entry():
    """Create a mock config entry for a trip event."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "event_name": "Dänemark 2026",
            "event_type": "trip",
            "start_date": "2026-07-12",
            "end_date": "2026-07-26",
            "image_path": "",
            "website_url": "",
            "notes": "Sommerurlaub"
        },
        unique_id="whenhub_daenemark_2026",
        version=1,
    )

@pytest.fixture
def milestone_config_entry():
    """Create a mock config entry for a milestone event."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "event_name": "Projektabgabe",
            "event_type": "milestone",
            "target_date": "2026-03-15",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_projektabgabe",
        version=1,
    )

@pytest.fixture
def anniversary_config_entry():
    """Create a mock config entry for an anniversary event."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "event_name": "Geburtstag Max",
            "event_type": "anniversary",
            "target_date": "2010-05-20",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_geburtstag_max",
        version=1,
    )

@pytest.fixture
def special_config_entry():
    """Create a mock config entry for a special event."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "event_name": "Weihnachts-Countdown",
            "event_type": "special",
            "special_type": "christmas_eve",
            "special_category": "traditional",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_weihnachts_countdown",
        version=1,
    )