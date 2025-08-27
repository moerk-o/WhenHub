"""Test für Anniversary Events am 29. Februar (Schaltjahr-Spezialfall)."""
import pytest
from homeassistant.core import HomeAssistant
from _helpers import with_time, setup_and_wait, get


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
    with with_time("2023-02-01 10:00:00+00:00"):  # Nicht-Schaltjahr 2023
        await setup_and_wait(hass, anniversary_leap_year_entry)
        
        # Next date sollte 28. Februar sein (kein 29. in 2023)
        next_date = get(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2023-02-28"
        
        # Days until sollte 27 sein (01.02. bis 28.02.)
        days_until = get(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 27
        
        # Binary sensor muss OFF sein
        assert get(hass, "binary_sensor.schaltjahr_anniversary_is_today").state == "off"


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
    with with_time("2024-02-01 10:00:00+00:00"):  # Schaltjahr 2024
        await setup_and_wait(hass, anniversary_leap_year_entry)
        
        # Next date sollte 29. Februar sein (Schaltjahr!)
        next_date = get(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2024-02-29"
        
        # Days until sollte 28 sein (01.02. bis 29.02.)
        days_until = get(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 28
        
        # Binary sensor muss OFF sein
        assert get(hass, "binary_sensor.schaltjahr_anniversary_is_today").state == "off"


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
    with with_time("2023-02-28 10:00:00+00:00"):  # 28.02.2023 - Ersatz für 29.02.
        await setup_and_wait(hass, anniversary_leap_year_entry)
        
        # Binary sensor sollte ON sein (heute ist der Anniversary-Tag)
        assert get(hass, "binary_sensor.schaltjahr_anniversary_is_today").state == "on"
        
        # Days until sollte 0 sein
        days_until = get(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 0
        
        # Occurrences count (2020 original, 2021, 2022, 2023)
        count = get(hass, "sensor.schaltjahr_anniversary_occurrences_count")
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
    with with_time("2024-02-29 10:00:00+00:00"):  # 29.02.2024 - Schaltjahr!
        await setup_and_wait(hass, anniversary_leap_year_entry)
        
        # Binary sensor sollte ON sein
        assert get(hass, "binary_sensor.schaltjahr_anniversary_is_today").state == "on"
        
        # Days until sollte 0 sein
        days_until = get(hass, "sensor.schaltjahr_anniversary_days_until_next")
        assert int(days_until.state) == 0
        
        # Next date sollte heute sein
        next_date = get(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2024-02-29"
        
        # Occurrences (2020, 2021, 2022, 2023, 2024)
        count = get(hass, "sensor.schaltjahr_anniversary_occurrences_count")
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
    with with_time("2025-03-01 10:00:00+00:00"):  # Tag nach Anniversary 2025
        await setup_and_wait(hass, anniversary_leap_year_entry)
        
        # Sollte 5 Jahre zeigen (2020 bis 2025)
        count = get(hass, "sensor.schaltjahr_anniversary_occurrences_count")
        assert int(count.state) == 5
        
        # Next date sollte 2026-02-28 sein (kein Schaltjahr)
        next_date = get(hass, "sensor.schaltjahr_anniversary_next_date")
        assert next_date.state == "2026-02-28"