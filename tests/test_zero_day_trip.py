"""Tests für 0-Tage-Trip Verhalten (Start = Ende)."""
import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from _helpers import at, setup_and_wait, get_state


@pytest.mark.asyncio
async def test_trip_zero_day_behavior(hass: HomeAssistant):
    """
    0-Tage-Trip Verhalten: Start=Ende Semantik und IST-Verhalten.
    
    Warum:
      0-Tage-Trips (Start=Ende) sind kritische Grenzfälle für alle Berechnungen.
      Division-by-zero Risiko bei Prozentberechnungen muss behandelt werden.
      Binary-Sensor Logik muss definiert sein (alle gleichzeitig ON oder andere Semantik).
      IST-Verhalten der WhenHub Integration muss klar dokumentiert sein.
      
    Wie:
      Trip-Fixture mit Start=Ende (2026-07-12).
      Test am Event-Tag selbst und am Folgetag.
      Alle Sensor-Werte und Binary-Zustände prüfen.
      IST-Semantik dokumentieren ohne Produktionscode zu ändern.
      
    Erwartung:
      Am Tag:
        - days_until_start: "0" (heute ist Start)
        - trip_left_percent: "100.0" (IST: voller Tag verbleibt noch)
        - Binaries: starts_today ON, active_today ON, ends_today ON 
          (IST-Semantik: alle drei gleichzeitig ON bei 0-Tage-Trip)
      Folgetag:
        - trip_left_days: "0" (keine Tage mehr)
        - trip_left_percent: "0.0" (Trip vorbei)
        - Alle Binaries: OFF
      
    IST-Semantik Dokumentation:
      Die WhenHub Integration behandelt 0-Tage-Trips (Start=Ende) so:
      - Am Event-Tag sind ALLE drei Binary-Sensoren gleichzeitig ON
      - left_percent zeigt 100.0% (inklusiv-Semantik: ganzer Tag verbleibt)
      - left_days zeigt 1 (inklusiv: der heutige Tag zählt noch)
      - Nach dem Tag: Alles auf 0/OFF (Trip komplett vorbei)
    """
    # 0-Tage-Trip Fixture
    zero_day_trip = MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Null-Tage-Ausflug",
            "event_type": "trip",
            "start_date": "2026-07-12",
            "end_date": "2026-07-12",  # Gleicher Tag = 0-Tage-Trip
            "image_path": "",
            "website_url": "",
            "notes": "0-Tage-Trip Test (Start=Ende)"
        },
        unique_id="whenhub_zero_day_trip",
        version=1,
    )
    
    # Phase 1: Am 0-Tage-Trip Tag selbst (12.07.2026)
    with at("2026-07-12 10:00:00+00:00"):
        await setup_and_wait(hass, zero_day_trip)
        
        # days_until_start sollte 0 sein (heute ist Start)
        days_until_start = get_state(hass, "sensor.null_tage_ausflug_days_until_start")
        assert days_until_start.state == "0", f"IST: days_until_start = '{days_until_start.state}' am 0-Tage-Trip Tag"
        
        # trip_left_percent IST-Verhalten: 100.0% (voller Tag verbleibt)
        left_percent = get_state(hass, "sensor.null_tage_ausflug_trip_left_percent")
        assert left_percent.state == "100.0", f"IST: left_percent = '{left_percent.state}' am 0-Tage-Trip Tag"
        
        # trip_left_days IST-Verhalten: 1 (inklusiv - der heutige Tag)
        left_days = get_state(hass, "sensor.null_tage_ausflug_trip_left_days")
        assert left_days.state == "1", f"IST: left_days = '{left_days.state}' am 0-Tage-Trip Tag (inklusiv)"
        
        # Binary-Sensoren IST-Verhalten: ALLE drei gleichzeitig ON
        starts_today = get_state(hass, "binary_sensor.null_tage_ausflug_trip_starts_today")
        active_today = get_state(hass, "binary_sensor.null_tage_ausflug_trip_active_today")
        ends_today = get_state(hass, "binary_sensor.null_tage_ausflug_trip_ends_today")
        
        assert starts_today.state == "on", f"IST: starts_today = '{starts_today.state}' bei 0-Tage-Trip"
        assert active_today.state == "on", f"IST: active_today = '{active_today.state}' bei 0-Tage-Trip"
        assert ends_today.state == "on", f"IST: ends_today = '{ends_today.state}' bei 0-Tage-Trip"
        
        # Dokumentation der IST-Semantik
        print("✅ IST-Verhalten 0-Tage-Trip am Event-Tag:")
        print(f"   - Alle 3 Binaries gleichzeitig ON (starts, active, ends)")
        print(f"   - left_percent = 100.0% (voller Tag verbleibt)")
        print(f"   - left_days = 1 (inklusiv-Semantik)")
        
        # Countdown Text sollte sinnvoll sein
        countdown = get_state(hass, "sensor.null_tage_ausflug_countdown_text")
        assert len(countdown.state) > 0, "Countdown text should not be empty"
    
    # Phase 2: Einen Tag nach dem 0-Tage-Trip (13.07.2026)
    with at("2026-07-13 10:00:00+00:00"):
        await hass.config_entries.async_reload(zero_day_trip.entry_id)
        await hass.async_block_till_done()
        
        # trip_left_days sollte 0 sein (keine Tage verbleiben)
        left_days = get_state(hass, "sensor.null_tage_ausflug_trip_left_days")
        assert left_days.state == "0", f"IST: left_days = '{left_days.state}' nach 0-Tage-Trip"
        
        # trip_left_percent sollte 0.0% sein
        left_percent = get_state(hass, "sensor.null_tage_ausflug_trip_left_percent")
        assert left_percent.state == "0.0", f"IST: left_percent = '{left_percent.state}' nach 0-Tage-Trip"
        
        # Alle Binary-Sensoren sollten OFF sein
        starts_today = get_state(hass, "binary_sensor.null_tage_ausflug_trip_starts_today")
        active_today = get_state(hass, "binary_sensor.null_tage_ausflug_trip_active_today")
        ends_today = get_state(hass, "binary_sensor.null_tage_ausflug_trip_ends_today")
        
        assert starts_today.state == "off", f"IST: starts_today = '{starts_today.state}' nach 0-Tage-Trip"
        assert active_today.state == "off", f"IST: active_today = '{active_today.state}' nach 0-Tage-Trip"
        assert ends_today.state == "off", f"IST: ends_today = '{ends_today.state}' nach 0-Tage-Trip"
        
        # days_until_end sollte negativ sein (Trip ist vorbei)
        days_until_end = get_state(hass, "sensor.null_tage_ausflug_days_until_end")
        assert int(days_until_end.state) < 0, f"IST: days_until_end = {days_until_end.state} (negativ nach Trip)"
        
        # Dokumentation
        print("✅ IST-Verhalten 0-Tage-Trip am Folgetag:")
        print(f"   - Alle Binaries OFF")
        print(f"   - left_percent = 0.0%")
        print(f"   - left_days = 0")