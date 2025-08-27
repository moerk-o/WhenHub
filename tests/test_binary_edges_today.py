"""Test für exakte 'Today'-Kanten bei Binary-Sensoren für alle Event-Typen."""
import pytest
from homeassistant.core import HomeAssistant
from _helpers import with_time, setup_and_wait, get, assert_entities_exist


@pytest.mark.asyncio
async def test_trip_start_day_edges(hass: HomeAssistant, trip_config_entry):
    """
    Warum:
      Startag muss korrekt als trip_starts_today=ON und trip_active_today=ON erkannt werden.
      Ungleichbehandlungen bei >= / > sind klassische Fehler.
    Wie:
      Freeze auf Trip-Starttag (12.07.2026); Setup; Binary-Sensoren prüfen.
    Erwartet:
      - trip_starts_today: ON (heute startet der Trip)
      - trip_active_today: ON (Trip ist aktiv am Starttag)  
      - trip_ends_today: OFF (endet nicht heute)
    """
    with with_time("2026-07-12 10:00:00+00:00"):  # Trip-Starttag
        await setup_and_wait(hass, trip_config_entry)
        
        # Starttag-Sensor muss ON sein
        assert get(hass, "binary_sensor.danemark_2026_trip_starts_today").state == "on"
        
        # Trip ist aktiv (inklusiv Starttag)
        assert get(hass, "binary_sensor.danemark_2026_trip_active_today").state == "on"
        
        # Endtag-Sensor muss OFF sein
        assert get(hass, "binary_sensor.danemark_2026_trip_ends_today").state == "off"


@pytest.mark.asyncio
async def test_trip_end_day_edges(hass: HomeAssistant, trip_config_entry):
    """
    Warum:
      Endtag muss inklusiv behandelt werden; typische Fehler sind > statt >=.
    Wie:
      Freeze auf das Enddatum (26.07.2026); Entry setup; States prüfen.
    Erwartet:
      - trip_ends_today: ON
      - trip_active_today: ON (inklusive Endtag)
      - trip_starts_today: OFF
    """
    with with_time("2026-07-26 10:00:00+00:00"):  # Trip-Endtag
        await setup_and_wait(hass, trip_config_entry)
        
        # Endtag-Sensor muss ON sein
        assert get(hass, "binary_sensor.danemark_2026_trip_ends_today").state == "on"
        
        # Trip ist noch aktiv (inklusiv Endtag)
        assert get(hass, "binary_sensor.danemark_2026_trip_active_today").state == "on"
        
        # Starttag-Sensor muss OFF sein
        assert get(hass, "binary_sensor.danemark_2026_trip_starts_today").state == "off"


@pytest.mark.asyncio
async def test_trip_day_before_start(hass: HomeAssistant, trip_config_entry):
    """
    Warum:
      Einen Tag vor Start sollten alle Binary-Sensoren OFF sein.
    Wie:
      Freeze auf 11.07.2026 (Tag vor Start); Setup; Asserts.
    Erwartet:
      - Alle trip_*_today Sensoren: OFF
    """
    with with_time("2026-07-11 10:00:00+00:00"):  # Tag vor Trip-Start
        await setup_and_wait(hass, trip_config_entry)
        
        # Alle Binary-Sensoren müssen OFF sein
        assert get(hass, "binary_sensor.danemark_2026_trip_starts_today").state == "off"
        assert get(hass, "binary_sensor.danemark_2026_trip_active_today").state == "off"
        assert get(hass, "binary_sensor.danemark_2026_trip_ends_today").state == "off"


@pytest.mark.asyncio
async def test_trip_during_middle(hass: HomeAssistant, trip_config_entry):
    """
    Warum:
      Während des Trips (aber nicht am Start/Ende) sollte nur active_today ON sein.
    Wie:
      Freeze auf 20.07.2026 (Mitte des Trips); Setup; Asserts.
    Erwartet:
      - trip_active_today: ON
      - trip_starts_today: OFF
      - trip_ends_today: OFF
    """
    with with_time("2026-07-20 10:00:00+00:00"):  # Mitte des Trips
        await setup_and_wait(hass, trip_config_entry)
        
        # Nur active sollte ON sein
        assert get(hass, "binary_sensor.danemark_2026_trip_active_today").state == "on"
        assert get(hass, "binary_sensor.danemark_2026_trip_starts_today").state == "off"
        assert get(hass, "binary_sensor.danemark_2026_trip_ends_today").state == "off"


@pytest.mark.asyncio
async def test_milestone_is_today_edge(hass: HomeAssistant, milestone_config_entry):
    """
    Warum:
      is_today muss exakt am Zieldatum ON sein, sonst OFF.
    Wie:
      Teste Tag vor, am und nach dem Milestone.
    Erwartet:
      - Nur am 15.03.2026: is_today=ON
      - Davor und danach: is_today=OFF
    """
    # Tag vor Milestone
    with with_time("2026-03-14 10:00:00+00:00"):
        await setup_and_wait(hass, milestone_config_entry)
        assert get(hass, "binary_sensor.projektabgabe_is_today").state == "off"
    
    # Am Milestone-Tag
    with with_time("2026-03-15 10:00:00+00:00"):
        await hass.config_entries.async_reload(milestone_config_entry.entry_id)
        await hass.async_block_till_done()
        assert get(hass, "binary_sensor.projektabgabe_is_today").state == "on"
    
    # Tag nach Milestone
    with with_time("2026-03-16 10:00:00+00:00"):
        await hass.config_entries.async_reload(milestone_config_entry.entry_id)
        await hass.async_block_till_done()
        assert get(hass, "binary_sensor.projektabgabe_is_today").state == "off"


@pytest.mark.asyncio
async def test_anniversary_is_today_edge(hass: HomeAssistant, anniversary_config_entry):
    """
    Warum:
      Anniversary is_today muss nur am Jahrestag ON sein.
    Wie:
      Teste Tag vor, am und nach dem Anniversary (20.05.).
    Erwartet:
      - Nur am 20.05.: is_today=ON
    """
    # Tag vor Anniversary
    with with_time("2026-05-19 10:00:00+00:00"):
        await setup_and_wait(hass, anniversary_config_entry)
        assert get(hass, "binary_sensor.geburtstag_max_is_today").state == "off"
    
    # Am Anniversary-Tag
    with with_time("2026-05-20 10:00:00+00:00"):
        await hass.config_entries.async_reload(anniversary_config_entry.entry_id)
        await hass.async_block_till_done()
        assert get(hass, "binary_sensor.geburtstag_max_is_today").state == "on"
    
    # Tag nach Anniversary
    with with_time("2026-05-21 10:00:00+00:00"):
        await hass.config_entries.async_reload(anniversary_config_entry.entry_id)
        await hass.async_block_till_done()
        assert get(hass, "binary_sensor.geburtstag_max_is_today").state == "off"


@pytest.mark.asyncio
async def test_special_event_christmas_eve_today(hass: HomeAssistant, special_config_entry):
    """
    Warum:
      Special Events müssen exakt am Ereignistag is_today=ON zeigen.
    Wie:
      Teste Heiligabend (24.12.) mit Tag davor und danach.
    Erwartet:
      - Nur am 24.12.: is_today=ON
    """
    # Tag vor Heiligabend
    with with_time("2026-12-23 10:00:00+00:00"):
        await setup_and_wait(hass, special_config_entry)
        assert get(hass, "binary_sensor.weihnachts_countdown_is_today").state == "off"
    
    # Am Heiligabend
    with with_time("2026-12-24 10:00:00+00:00"):
        await hass.config_entries.async_reload(special_config_entry.entry_id)
        await hass.async_block_till_done()
        assert get(hass, "binary_sensor.weihnachts_countdown_is_today").state == "on"
    
    # 1. Weihnachtstag
    with with_time("2026-12-25 10:00:00+00:00"):
        await hass.config_entries.async_reload(special_config_entry.entry_id)
        await hass.async_block_till_done()
        assert get(hass, "binary_sensor.weihnachts_countdown_is_today").state == "off"


@pytest.mark.asyncio
async def test_special_event_easter_today(hass: HomeAssistant, special_event_entry_factory):
    """
    Warum:
      Bewegliche Feiertage wie Ostern müssen korrekt erkannt werden.
    Wie:
      Teste Ostersonntag 2026 (05.04.2026 - berechnet via Gauss-Algorithmus).
    Erwartet:
      - Nur am berechneten Ostersonntag: is_today=ON
    """
    easter_entry = special_event_entry_factory("easter", "Oster-Test")
    
    # Tag vor Ostern 2026
    with with_time("2026-04-04 10:00:00+00:00"):
        await setup_and_wait(hass, easter_entry)
        assert get(hass, "binary_sensor.oster_test_is_today").state == "off"
    
    # Ostersonntag 2026 (5. April)
    with with_time("2026-04-05 10:00:00+00:00"):
        await hass.config_entries.async_reload(easter_entry.entry_id)
        await hass.async_block_till_done()
        assert get(hass, "binary_sensor.oster_test_is_today").state == "on"
    
    # Ostermontag
    with with_time("2026-04-06 10:00:00+00:00"):
        await hass.config_entries.async_reload(easter_entry.entry_id)
        await hass.async_block_till_done()
        assert get(hass, "binary_sensor.oster_test_is_today").state == "off"