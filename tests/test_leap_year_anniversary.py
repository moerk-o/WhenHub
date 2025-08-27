"""Test für Anniversary Events am 29. Februar (Schaltjahr-Spezialfall)."""
import pytest
from homeassistant.core import HomeAssistant
from _helpers import at, setup_and_wait, get_state


@pytest.mark.asyncio
async def test_anniversary_feb29_in_non_leap_year(hass: HomeAssistant, anniversary_leap_year_entry):
    """
    Warum:
      Hoher Fehlerfaktor bei Jahrestagen am 29.02. in Nicht-Schaltjahren.
      Die Integration sollte auf 28.02. ausweichen.
    Wie:
      Fixture für Anniversary mit original_date=2020-02-29.
      Freeze auf 2023-02-01 (Nicht-Schaltjahr) → next_date sollte 2023-02-28 sein.
    Erwartet:
      - next_date: 2023-02-28 (nicht 29., da 2023 kein Schaltjahr)
      - days_until_next: 27 (vom 01.02. bis 28.02.)
      - is_today: OFF (da nicht der 28.02.)
    """
    with at("2023-02-01 10:00:00+00:00"):  # Nicht-Schaltjahr 2023
        await setup_and_wait(hass, anniversary_leap_year_entry)
        
        # Next date sollte 28. Februar sein (kein 29. in 2023)
        next_date = get_state(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2023-02-28"
        
        # Days until sollte 27 sein (01.02. bis 28.02.)
        days_until = get_state(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 27
        
        # Binary sensor muss OFF sein
        assert get_state(hass, "binary_sensor.schaltjahr_anniversary_is_today").state == "off"


@pytest.mark.asyncio 
async def test_anniversary_feb29_in_leap_year(hass: HomeAssistant, anniversary_leap_year_entry):
    """
    Warum:
      In Schaltjahren sollte der 29. Februar korrekt erkannt werden.
    Wie:
      Fixture für Anniversary mit original_date=2020-02-29.
      Freeze auf 2024-02-01 (Schaltjahr) → next_date sollte 2024-02-29 sein.
    Erwartet:
      - next_date: 2024-02-29 (korrekter 29. im Schaltjahr)
      - days_until_next: 28 (vom 01.02. bis 29.02.)
      - is_today: OFF
    """
    with at("2024-02-01 10:00:00+00:00"):  # Schaltjahr 2024
        await setup_and_wait(hass, anniversary_leap_year_entry)
        
        # Next date sollte 29. Februar sein (Schaltjahr!)
        next_date = get_state(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2024-02-29"
        
        # Days until sollte 28 sein (01.02. bis 29.02.)
        days_until = get_state(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 28
        
        # Binary sensor muss OFF sein
        assert get_state(hass, "binary_sensor.schaltjahr_anniversary_is_today").state == "off"


@pytest.mark.asyncio
async def test_anniversary_feb29_on_feb28_non_leap_year(hass: HomeAssistant, anniversary_leap_year_entry):
    """
    Warum:
      Am 28.02. in Nicht-Schaltjahren sollte die Anniversary als "heute" gelten.
    Wie:
      Freeze auf 2023-02-28 (Ersatztag für 29.02. in Nicht-Schaltjahr).
    Erwartet:
      - is_today: ON (28.02. gilt als Anniversary-Tag)
      - days_until_next: 0
      - occurrences_count: 3 (2020, 2021, 2022, heute 2023)
    """
    with at("2023-02-28 10:00:00+00:00"):  # 28.02.2023 - Ersatz für 29.02.
        await setup_and_wait(hass, anniversary_leap_year_entry)
        
        # Binary sensor sollte ON sein (heute ist der Anniversary-Tag)
        assert get_state(hass, "binary_sensor.schaltjahr_anniversary_is_today").state == "on"
        
        # Days until sollte 0 sein
        days_until = get_state(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 0
        
        # Occurrences count (2020 original, 2021, 2022, 2023)
        count = get_state(hass, "sensor.schaltjahr_anniversary_occurrences_count")
        assert int(count.state) == 3  # 3 vergangene Vorkommen


@pytest.mark.asyncio
async def test_anniversary_feb29_on_actual_leap_day(hass: HomeAssistant, anniversary_leap_year_entry):
    """
    Warum:
      Am tatsächlichen 29.02. in Schaltjahren muss alles korrekt funktionieren.
    Wie:
      Freeze auf 2024-02-29 (tatsächlicher Schaltjahr-Tag).
    Erwartet:
      - is_today: ON
      - days_until_next: 0  
      - next_date: 2024-02-29 (heute)
      - occurrences_count: 4 (2020, 2021, 2022, 2023, heute 2024)
    """
    with at("2024-02-29 10:00:00+00:00"):  # 29.02.2024 - Schaltjahr!
        await setup_and_wait(hass, anniversary_leap_year_entry)
        
        # Binary sensor sollte ON sein
        assert get_state(hass, "binary_sensor.schaltjahr_anniversary_is_today").state == "on"
        
        # Days until sollte 0 sein
        days_until = get_state(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 0
        
        # Next date sollte heute sein
        next_date = get_state(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2024-02-29"
        
        # Occurrences (2020, 2021, 2022, 2023, 2024)
        count = get_state(hass, "sensor.schaltjahr_anniversary_occurrences_count")
        assert int(count.state) == 4  # 4 vergangene Vorkommen


@pytest.mark.asyncio
async def test_anniversary_feb29_year_calculation(hass: HomeAssistant, anniversary_leap_year_entry):
    """
    Warum:
      Jahre seit Original-Datum sollten korrekt berechnet werden.
    Wie:
      Freeze auf verschiedene Zeitpunkte und prüfe Jahresberechnung.
    Erwartet:
      - Korrekte Anzahl Jahre in den Attributen
    """
    with at("2025-03-01 10:00:00+00:00"):  # Tag nach Anniversary 2025
        await setup_and_wait(hass, anniversary_leap_year_entry)
        
        # Sollte 5 Jahre zeigen (2020 bis 2025)
        count = get_state(hass, "sensor.schaltjahr_anniversary_occurrences_count")
        assert int(count.state) == 5
        
        # Next date sollte 2026-02-28 sein (kein Schaltjahr)
        next_date = get_state(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2026-02-28"


@pytest.mark.asyncio
async def test_anniversary_leap_year_behavior(hass: HomeAssistant, anniversary_leap_year_entry):
    """
    Vollständiges Leap-Year Handling für Anniversaries mit 29.02.
    
    Warum:
      Anniversaries am 29.02. müssen in Nicht-Schaltjahren auf 28.02. ausweichen.
      Im nächsten Schaltjahr muss der 29.02. wieder korrekt erkannt werden.
      Binary-Sensor 'is_today' soll nur an den korrekten Ersatztagen 'on' sein.
      
    Wie:
      Anniversary mit Startdatum 29.02.2020 (Schaltjahr).
      Teste verschiedene Jahre: 2023 (kein Schaltjahr), 2024 (Schaltjahr).
      Freeze auf spezifische Daten und prüfe next_date, is_today, days_until.
      
    Erwartung:
      - 2023-02-01: next_date=2023-02-28, is_today=OFF
      - 2023-02-28: next_date=2023-02-28, is_today=ON  
      - 2024-02-01: next_date=2024-02-29, is_today=OFF
      - 2024-02-29: next_date=2024-02-29, is_today=ON
    """
    
    # Szenario 1: 2023-02-01 → nächster Jahrestag soll 2023-02-28 sein, is_today=OFF
    with at("2023-02-01 10:00:00+00:00"):  # Nicht-Schaltjahr 2023
        await setup_and_wait(hass, anniversary_leap_year_entry)
        
        # next_date muss auf 28.02. ausweichen (2023 ist kein Schaltjahr)
        next_date = get_state(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2023-02-28", f"Expected 2023-02-28 in non-leap year, got {next_date.state}"
        
        # is_today muss OFF sein (nicht der Ersatztag)
        is_today = get_state(hass, "binary_sensor.schaltjahr_anniversary_is_today")
        assert is_today.state == "off", f"is_today should be OFF on Feb 1st, got {is_today.state}"
        
        # days_until sollte plausibel sein (27 Tage vom 01.02 bis 28.02)
        days_until = get_state(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 27, f"Expected 27 days until, got {days_until.state}"
    
    # Szenario 2: 2023-02-28 → is_today=ON, next_date=2023-02-28
    with at("2023-02-28 10:00:00+00:00"):  # Ersatztag für 29.02 in Nicht-Schaltjahr
        await hass.config_entries.async_reload(anniversary_leap_year_entry.entry_id)
        await hass.async_block_till_done()
        
        # is_today muss ON sein (28.02 ist der korrekte Ersatztag)
        is_today = get_state(hass, "binary_sensor.schaltjahr_anniversary_is_today")
        assert is_today.state == "on", f"is_today should be ON on replacement day Feb 28th, got {is_today.state}"
        
        # next_date sollte heute sein
        next_date = get_state(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2023-02-28", f"next_date should be today (2023-02-28), got {next_date.state}"
        
        # days_until sollte 0 sein
        days_until = get_state(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 0, f"days_until should be 0 on anniversary day, got {days_until.state}"
    
    # Szenario 3: 2024-02-01 → nächster Jahrestag soll 2024-02-29 sein
    with at("2024-02-01 10:00:00+00:00"):  # Schaltjahr 2024
        await hass.config_entries.async_reload(anniversary_leap_year_entry.entry_id)
        await hass.async_block_till_done()
        
        # next_date muss 29.02. sein (2024 ist Schaltjahr!)
        next_date = get_state(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2024-02-29", f"Expected 2024-02-29 in leap year, got {next_date.state}"
        
        # is_today muss OFF sein (nicht der Jahrestag)
        is_today = get_state(hass, "binary_sensor.schaltjahr_anniversary_is_today")
        assert is_today.state == "off", f"is_today should be OFF on Feb 1st, got {is_today.state}"
        
        # days_until sollte 28 sein (vom 01.02 bis 29.02)
        days_until = get_state(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 28, f"Expected 28 days until leap day, got {days_until.state}"
    
    # Szenario 4: 2024-02-29 → is_today=ON, next_date=2024-02-29
    with at("2024-02-29 10:00:00+00:00"):  # Echter Schaltjahr-Tag
        await hass.config_entries.async_reload(anniversary_leap_year_entry.entry_id)
        await hass.async_block_till_done()
        
        # is_today muss ON sein (echter 29.02 im Schaltjahr)
        is_today = get_state(hass, "binary_sensor.schaltjahr_anniversary_is_today")
        assert is_today.state == "on", f"is_today should be ON on real leap day, got {is_today.state}"
        
        # next_date sollte heute sein
        next_date = get_state(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2024-02-29", f"next_date should be today (2024-02-29), got {next_date.state}"
        
        # days_until sollte 0 sein
        days_until = get_state(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 0, f"days_until should be 0 on leap day anniversary, got {days_until.state}"