"""Common test fixtures for WhenHub integration tests."""
import pytest
import sys
import os

# Add project root to Python path so custom_components can be found
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def get_date_from_state(state_value: str) -> str:
    """Extract date portion from a timestamp state value.

    Timestamp sensors return ISO 8601 format like '2026-07-12T00:00:00+00:00'.
    This helper extracts just the date part '2026-07-12' for test assertions.

    Args:
        state_value: The sensor state string (ISO timestamp or date)

    Returns:
        Date string in YYYY-MM-DD format
    """
    if "T" in state_value:
        return state_value.split("T")[0]
    return state_value

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


# =============================================================================
# Edge Case Fixtures
# =============================================================================

@pytest.fixture
def single_day_trip_config_entry():
    """Create a mock config entry for a single-day trip (start = end)."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Tagesausflug",
            "event_type": "trip",
            "start_date": "2026-08-15",
            "end_date": "2026-08-15",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_tagesausflug",
        version=1,
    )


@pytest.fixture
def past_trip_config_entry():
    """Create a mock config entry for a trip in the past."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Vergangener Urlaub",
            "event_type": "trip",
            "start_date": "2024-06-01",
            "end_date": "2024-06-14",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_vergangener_urlaub",
        version=1,
    )


@pytest.fixture
def past_milestone_config_entry():
    """Create a mock config entry for a milestone in the past."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Vergangener Milestone",
            "event_type": "milestone",
            "target_date": "2024-01-15",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_vergangener_milestone",
        version=1,
    )


@pytest.fixture
def long_trip_config_entry():
    """Create a mock config entry for a very long trip (> 365 days)."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Weltreise",
            "event_type": "trip",
            "start_date": "2026-01-01",
            "end_date": "2027-06-30",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_weltreise",
        version=1,
    )


@pytest.fixture
def leap_year_anniversary_config_entry():
    """Create a mock config entry for anniversary on Feb 29."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Schaltjahr Geburtstag",
            "event_type": "anniversary",
            "target_date": "2020-02-29",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_schaltjahr_geburtstag",
        version=1,
    )


@pytest.fixture
def easter_config_entry():
    """Create a mock config entry for Easter."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Ostern",
            "event_type": "special",
            "special_type": "easter",
            "special_category": "traditional",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_ostern",
        version=1,
    )


@pytest.fixture
def advent_config_entry():
    """Create a mock config entry for 1st Advent."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "1. Advent",
            "event_type": "special",
            "special_type": "advent_1",
            "special_category": "traditional",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_advent_1",
        version=1,
    )


# =============================================================================
# DST Event Fixtures
# =============================================================================

@pytest.fixture
def dst_eu_config_entry():
    """Create a mock config entry for EU DST event."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Zeitumstellung EU",
            "event_type": "special",
            "special_type": "dst",
            "special_category": "dst",
            "dst_type": "next_change",
            "dst_region": "eu",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_dst_eu",
        version=1,
    )


@pytest.fixture
def dst_usa_config_entry():
    """Create a mock config entry for USA DST event."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "DST USA",
            "event_type": "special",
            "special_type": "dst",
            "special_category": "dst",
            "dst_type": "next_change",
            "dst_region": "usa",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_dst_usa",
        version=1,
    )


@pytest.fixture
def dst_australia_config_entry():
    """Create a mock config entry for Australia DST event."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "DST Australia",
            "event_type": "special",
            "special_type": "dst",
            "special_category": "dst",
            "dst_type": "next_change",
            "dst_region": "australia",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_dst_australia",
        version=1,
    )


@pytest.fixture
def dst_nz_config_entry():
    """Create a mock config entry for New Zealand DST event."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "DST New Zealand",
            "event_type": "special",
            "special_type": "dst",
            "special_category": "dst",
            "dst_type": "next_change",
            "dst_region": "new_zealand",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_dst_nz",
        version=1,
    )


@pytest.fixture
def dst_eu_summer_config_entry():
    """Create a mock config entry for EU DST summer event."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Sommerzeit EU",
            "event_type": "special",
            "special_type": "dst",
            "special_category": "dst",
            "dst_type": "next_summer",
            "dst_region": "eu",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_dst_eu_summer",
        version=1,
    )


@pytest.fixture
def dst_eu_winter_config_entry():
    """Create a mock config entry for EU DST winter event."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Winterzeit EU",
            "event_type": "special",
            "special_type": "dst",
            "special_category": "dst",
            "dst_type": "next_winter",
            "dst_region": "eu",
            "image_path": "",
            "website_url": "",
            "notes": ""
        },
        unique_id="whenhub_dst_eu_winter",
        version=1,
    )


# =============================================================================
# Extended Edge Case Fixtures
# =============================================================================

@pytest.fixture
def umlaut_milestone_config_entry():
    """Create a mock config entry with German umlauts in name."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Frühjahrsputz Büro",
            "event_type": "milestone",
            "target_date": "2026-04-01",
            "image_path": "",
        },
        unique_id="whenhub_umlauts_test",
        version=1,
    )


@pytest.fixture
def sharp_s_milestone_config_entry():
    """Create a mock config entry with ß (sharp s) in name."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Großes Straßenfest",
            "event_type": "milestone",
            "target_date": "2026-06-15",
            "image_path": "",
        },
        unique_id="whenhub_sharp_s_test",
        version=1,
    )


@pytest.fixture
def ampersand_milestone_config_entry():
    """Create a mock config entry with & in name."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Tom & Jerry Party",
            "event_type": "milestone",
            "target_date": "2026-05-01",
            "image_path": "",
        },
        unique_id="whenhub_ampersand_test",
        version=1,
    )


@pytest.fixture
def emoji_trip_config_entry():
    """Create a mock config entry with emoji in name."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Urlaub Spanien 🌴",
            "event_type": "trip",
            "start_date": "2026-08-01",
            "end_date": "2026-08-15",
            "image_path": "",
        },
        unique_id="whenhub_emoji_test",
        version=1,
    )


@pytest.fixture
def long_name_milestone_config_entry():
    """Create a mock config entry with very long name."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Dieser extrem lange Event-Name testet ob die Integration auch mit sehr langen Namen korrekt umgehen kann",
            "event_type": "milestone",
            "target_date": "2026-09-01",
            "image_path": "",
        },
        unique_id="whenhub_long_name_test",
        version=1,
    )


@pytest.fixture
def silvester_special_config_entry():
    """Create a mock config entry for New Year's Eve."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Silvester Test",
            "event_type": "special",
            "special_type": "new_years_eve",
            "special_category": "calendar",
            "image_path": "",
        },
        unique_id="whenhub_nye_test",
        version=1,
    )


@pytest.fixture
def neujahr_special_config_entry():
    """Create a mock config entry for New Year."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Neujahr Test",
            "event_type": "special",
            "special_type": "new_year",
            "special_category": "calendar",
            "image_path": "",
        },
        unique_id="whenhub_ny_test",
        version=1,
    )


@pytest.fixture
def parallel_trip_1_config_entry():
    """Create first parallel trip config entry."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Parallel Trip 1",
            "event_type": "trip",
            "start_date": "2026-07-01",
            "end_date": "2026-07-15",
            "image_path": "",
        },
        unique_id="whenhub_parallel_1",
        version=1,
    )


@pytest.fixture
def parallel_trip_2_config_entry():
    """Create second parallel trip config entry."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Parallel Trip 2",
            "event_type": "trip",
            "start_date": "2026-07-10",
            "end_date": "2026-07-20",
            "image_path": "",
        },
        unique_id="whenhub_parallel_2",
        version=1,
    )