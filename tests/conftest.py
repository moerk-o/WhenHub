"""Common test fixtures for WhenHub integration tests."""
import pytest
import sys
import os

# Add project root to Python path so custom_components can be found
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use pytest-homeassistant-custom-component plugin
pytest_plugins = "pytest_homeassistant_custom_component"

# This fixture is required for custom components (versions >=2021.6.0b0)
@pytest.fixture(autouse=True)  
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom integrations in Home Assistant."""
    return enable_custom_integrations

@pytest.fixture
def trip_config_entry():
    """Create a mock config entry for a trip event."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    return MockConfigEntry(
        domain="whenhub",
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
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    return MockConfigEntry(
        domain="whenhub",
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
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    return MockConfigEntry(
        domain="whenhub",
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
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    return MockConfigEntry(
        domain="whenhub",
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

@pytest.fixture
def anniversary_leap_year_entry():
    """Create a mock config entry for an anniversary on Feb 29th."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Schaltjahr Anniversary",
            "event_type": "anniversary",
            "target_date": "2020-02-29",  # Schaltjahr - 29. Februar
            "image_path": "",
            "website_url": "",
            "notes": "Test für Schaltjahr-Handling"
        },
        unique_id="whenhub_schaltjahr_anniversary",
        version=1,
    )

@pytest.fixture
def trip_one_day_entry():
    """Create a mock config entry for a 1-day trip."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Tagesausflug München",
            "event_type": "trip",
            "start_date": "2026-08-15",
            "end_date": "2026-08-15",  # Same day = 1-day trip
            "image_path": "",
            "website_url": "",
            "notes": "1-Tages-Trip Test"
        },
        unique_id="whenhub_tagesausflug_muenchen",
        version=1,
    )

@pytest.fixture
def trip_very_long_entry():
    """Create a mock config entry for a very long trip (>2 years)."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Weltreise 2026-2028",
            "event_type": "trip",
            "start_date": "2026-01-01",
            "end_date": "2028-06-30",  # 2.5 years = 912 days
            "image_path": "",
            "website_url": "",
            "notes": "Sehr langer Trip Test"
        },
        unique_id="whenhub_weltreise_2026_2028",
        version=1,
    )

@pytest.fixture
def special_event_entry_factory():
    """Factory for creating special event config entries."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    def _create_entry(special_type: str, event_name: str = None, category: str = "traditional"):
        if not event_name:
            event_name = f"Test {special_type}"
        
        return MockConfigEntry(
            domain="whenhub",
            data={
                "event_name": event_name,
                "event_type": "special",
                "special_type": special_type,
                "special_category": category,
                "image_path": "",
                "website_url": "",
                "notes": f"Test für {special_type}"
            },
            unique_id=f"whenhub_test_{special_type}",
            version=1,
        )
    
    return _create_entry