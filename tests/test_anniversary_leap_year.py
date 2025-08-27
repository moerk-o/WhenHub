"""Tests für Anniversary 29. Februar Schaltjahr-Behandlung."""
import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from _helpers import at, setup_and_wait, get_state


@pytest.fixture
def anniversary_2902_config_entry():
    """Create a mock config entry for a 29.02. anniversary."""
    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Schaltjahr Anniversary 29.02.",
            "event_type": "anniversary",
            "target_date": "2020-02-29",  # Schaltjahr-Startdatum
            "image_path": "",
            "website_url": "",
            "notes": "29. Februar Anniversary Test"
        },
        unique_id="whenhub_anniversary_2902",
        version=1,
    )


@pytest.mark.asyncio
async def test_anniversary_2902_next_date_in_non_leap_year(hass: HomeAssistant, anniversary_2902_config_entry):
    """
    Anniversary 29.02. in Nicht-Schaltjahr: next_date auf 28.02. ausweichen.
    
    Warum:
      Anniversaries mit 29.02. Startdatum müssen in Nicht-Schaltjahren korrekt 
      auf 28.02. ausweichen, da 29.02. nicht existiert. Dies ist kritisch für
      korrekte Datumslogik und Benutzererwartungen.
      
    Wie:
      Anniversary mit Startdatum 2020-02-29. Tests in Nicht-Schaltjahr 2023:
      1. Am 2023-02-01: next_date sollte 2023-02-28 sein, is_today OFF
      2. Am 2023-02-28: is_today sollte ON sein (ausgewichenes Datum)
      
    Erwartung:
      - In Nicht-Schaltjahren: next_date = 28.02. (Ausweichlogik)
      - Am Ausweichtag (28.02.): is_today ON
      - Korrekte Datums-Arithmetik ohne Exceptions
    """
    # Phase 1: Anfang Februar 2023 (Nicht-Schaltjahr) 
    with at("2023-02-01 10:00:00+00:00"):
        await setup_and_wait(hass, anniversary_2902_config_entry)
        
        # next_date sollte auf 28.02. ausweichen (da 29.02. nicht existiert)
        next_date = get_state(hass, "sensor.schaltjahr_anniversary_29_02_next_date")
        assert next_date.state == "2023-02-28", f"Expected next_date '2023-02-28' in non-leap year, got {next_date.state}"
        
        # is_today sollte OFF sein (noch nicht der Tag)
        is_today = get_state(hass, "binary_sensor.schaltjahr_anniversary_29_02_is_today")
        assert is_today.state == "off", f"is_today should be OFF before anniversary, got {is_today.state}"
    
    # Phase 2: Am Ausweichtag 28.02.2023 (sollte als Anniversary gelten)
    with at("2023-02-28 10:00:00+00:00"):
        await hass.config_entries.async_reload(anniversary_2902_config_entry.entry_id)
        await hass.async_block_till_done()
        
        # is_today sollte ON sein (heute ist der ausgewichene Anniversary)
        is_today = get_state(hass, "binary_sensor.schaltjahr_anniversary_29_02_is_today")
        assert is_today.state == "on", f"is_today should be ON on fallback date 28.02., got {is_today.state}"


@pytest.mark.asyncio
async def test_anniversary_2902_next_date_in_leap_year(hass: HomeAssistant, anniversary_2902_config_entry):
    """
    Anniversary 29.02. in Schaltjahr: next_date korrekt auf 29.02.
    
    Warum:
      Anniversaries mit 29.02. Startdatum müssen in Schaltjahren korrekt
      auf 29.02. zeigen (nicht ausweichen). Dies verifiziert dass die Integration
      echte Schaltjahre erkennt und korrekt behandelt.
      
    Wie:
      Anniversary mit Startdatum 2020-02-29. Tests in Schaltjahr 2024:
      1. Am 2024-02-01: next_date sollte 2024-02-29 sein, is_today OFF
      2. Am 2024-02-29: is_today sollte ON sein (echter Schaltjahrstag)
      
    Erwartung:
      - In Schaltjahren: next_date = 29.02. (kein Ausweichen nötig)
      - Am echten Schaltjahrstag (29.02.): is_today ON  
      - Korrekte Schaltjahr-Erkennung ohne Ausweichlogik
    """
    # Phase 1: Anfang Februar 2024 (Schaltjahr)
    with at("2024-02-01 10:00:00+00:00"):
        await setup_and_wait(hass, anniversary_2902_config_entry)
        
        # next_date sollte echten 29.02. zeigen (da Schaltjahr)
        next_date = get_state(hass, "sensor.schaltjahr_anniversary_29_02_next_date")
        assert next_date.state == "2024-02-29", f"Expected next_date '2024-02-29' in leap year, got {next_date.state}"
        
        # is_today sollte OFF sein (noch nicht der Tag)
        is_today = get_state(hass, "binary_sensor.schaltjahr_anniversary_29_02_is_today")
        assert is_today.state == "off", f"is_today should be OFF before anniversary, got {is_today.state}"
    
    # Phase 2: Am echten Schaltjahrstag 29.02.2024
    with at("2024-02-29 10:00:00+00:00"):
        await hass.config_entries.async_reload(anniversary_2902_config_entry.entry_id)
        await hass.async_block_till_done()
        
        # is_today sollte ON sein (heute ist der echte Anniversary im Schaltjahr)
        is_today = get_state(hass, "binary_sensor.schaltjahr_anniversary_29_02_is_today")
        assert is_today.state == "on", f"is_today should be ON on actual leap day 29.02., got {is_today.state}"