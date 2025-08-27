"""Tests für 0-Tage-Trip Verhalten (start_date == end_date)."""
import pytest
from homeassistant.core import HomeAssistant
from _helpers import at, setup_and_wait, get_state


@pytest.mark.asyncio
async def test_trip_zero_day_behavior(hass: HomeAssistant, trip_one_day_entry):
    """
    Vollständiger Test für 0-Tage-Trip Verhalten (start_date == end_date).
    
    Warum:
      0-Tage-Trips sind kritische Grenzfälle für alle Berechnungen.
      Division-by-zero Risiko, Binary-Sensor Logik, Prozent-Berechnungen.
      IST-Verhalten der WhenHub Integration muss dokumentiert sein.
      
    Wie:
      Trip mit start_date == end_date (15.08.2026).
      Teste am Ereignistag selbst und am Folgetag.
      Verifiziere alle Sensor-Werte und Binary-Zustände.
      
    Erwartung:
      - Am Ereignistag: Alle Binary-Sensoren gleichzeitig ON
      - left_days=1, left_percent=100.0% (inklusiv-Semantik)
      - Am Folgetag: Alles auf 0/OFF
      - Keine Division-by-zero Exceptions
    """
    # Phase 1: Am 0-Tage-Trip Tag selbst (15.08.2026)
    with at("2026-08-15 10:00:00+00:00"):
        await setup_and_wait(hass, trip_one_day_entry)
        
        # Days until start sollte 0 sein (heute ist Start)
        days_until_start = get_state(hass, "sensor.tagesausflug_munchen_days_until_start")
        assert int(days_until_start.state) == 0, f"days_until_start should be 0 on zero-day trip day, got {days_until_start.state}"
        
        # Days until end sollte auch 0 sein (heute ist auch Ende)
        days_until_end = get_state(hass, "sensor.tagesausflug_munchen_days_until_end")
        assert int(days_until_end.state) == 0, f"days_until_end should be 0 on zero-day trip day, got {days_until_end.state}"
        
        # Left days: IST-Verhalten ist 1 (inklusiver Tag)
        left_days = get_state(hass, "sensor.tagesausflug_munchen_trip_left_days")
        assert int(left_days.state) == 1, f"zero-day trip should have 1 left_day (inclusive), got {left_days.state}"
        
        # Left percent: IST-Verhalten ist 100% (voller Tag verbleibt)
        left_percent = get_state(hass, "sensor.tagesausflug_munchen_trip_left_percent")
        assert float(left_percent.state) == 100.0, f"zero-day trip should have 100% left on event day, got {left_percent.state}%"
        
        # Binary-Sensoren: IST-Verhalten - alle drei gleichzeitig ON
        starts_today = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_starts_today")
        ends_today = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_ends_today") 
        active_today = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_active_today")
        
        assert starts_today.state == "on", "zero-day trip should START today"
        assert ends_today.state == "on", "zero-day trip should END today"
        assert active_today.state == "on", "zero-day trip should be ACTIVE today"
        
        # Countdown text sollte sinnvoll sein
        countdown = get_state(hass, "sensor.tagesausflug_munchen_countdown_text")
        assert len(countdown.state) > 0, "countdown_text should not be empty"
        # Am Start/Ende Tag könnte "0 Tage" oder aktueller Status stehen
        
    # Phase 2: Einen Tag nach dem 0-Tage-Trip (16.08.2026)
    with at("2026-08-16 10:00:00+00:00"):
        await hass.config_entries.async_reload(trip_one_day_entry.entry_id)
        await hass.async_block_till_done()
        
        # Days until start/end sollten negativ sein (Vergangenheit)
        days_until_start = get_state(hass, "sensor.tagesausflug_munchen_days_until_start")
        assert int(days_until_start.state) < 0, f"days_until_start should be negative after trip, got {days_until_start.state}"
        
        days_until_end = get_state(hass, "sensor.tagesausflug_munchen_days_until_end") 
        assert int(days_until_end.state) < 0, f"days_until_end should be negative after trip, got {days_until_end.state}"
        
        # Left days sollte 0 sein (keine Tage verbleiben)
        left_days = get_state(hass, "sensor.tagesausflug_munchen_trip_left_days")
        assert int(left_days.state) == 0, f"left_days should be 0 after zero-day trip, got {left_days.state}"
        
        # Left percent sollte 0.0% sein
        left_percent = get_state(hass, "sensor.tagesausflug_munchen_trip_left_percent")
        assert float(left_percent.state) == 0.0, f"left_percent should be 0.0% after zero-day trip, got {left_percent.state}%"
        
        # Binary-Sensoren: Alle sollten OFF sein
        starts_today = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_starts_today")
        ends_today = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_ends_today")
        active_today = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_active_today")
        
        assert starts_today.state == "off", "trip should NOT start today (day after)"
        assert ends_today.state == "off", "trip should NOT end today (day after)" 
        assert active_today.state == "off", "trip should NOT be active today (day after)"


@pytest.mark.asyncio
async def test_zero_day_trip_edge_cases(hass: HomeAssistant, trip_one_day_entry):
    """
    Edge Cases für 0-Tage-Trips: verschiedene Tageszeiten.
    
    Warum:
      Tageszeit könnte Edge Cases bei 0-Tage-Trips verursachen.
      Mitternacht-Übergänge, verschiedene Uhrzeiten testen.
      
    Wie:
      Selber 0-Tage-Trip zu verschiedenen Uhrzeiten testen.
      Früh am Morgen, Mittag, späte Nacht.
      
    Erwartung:
      - Verhalten unabhängig von Uhrzeit
      - Konsistente Werte über den ganzen Tag
      - Mitternacht-Übergang korrekt behandelt
    """
    test_times = [
        "2026-08-15 00:01:00+00:00",  # Früh am Morgen
        "2026-08-15 12:00:00+00:00",  # Mittag
        "2026-08-15 23:59:00+00:00",  # Spät am Abend
    ]
    
    for time_str in test_times:
        with at(time_str):
            await setup_and_wait(hass, trip_one_day_entry)
            
            # Konsistente Werte unabhängig von Uhrzeit
            left_days = get_state(hass, "sensor.tagesausflug_munchen_trip_left_days")
            left_percent = get_state(hass, "sensor.tagesausflug_munchen_trip_left_percent")
            active_today = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_active_today")
            
            # IST-Verhalten: Sollte unabhängig von Uhrzeit konstant sein
            assert int(left_days.state) == 1, f"left_days inconsistent at {time_str}: {left_days.state}"
            assert float(left_percent.state) == 100.0, f"left_percent inconsistent at {time_str}: {left_percent.state}"
            assert active_today.state == "on", f"active_today inconsistent at {time_str}: {active_today.state}"


@pytest.mark.asyncio
async def test_zero_day_trip_no_division_by_zero(hass: HomeAssistant):
    """
    Verifikation dass 0-Tage-Trips keine Division-by-zero Exceptions verursachen.
    
    Warum:
      Duration = 1 Tag könnte zu Division-by-zero in Berechnungen führen.
      Mathematische Robustheit bei Grenzfall-Berechnungen sicherstellen.
      
    Wie:
      0-Tage-Trip mit verschiedenen Start-/End-Daten.
      Setup und alle Berechnungen durchführen lassen.
      
    Erwartung:
      - Keinerlei Exceptions während Setup oder Berechnungen
      - Alle Werte sind definiert (nicht None, nicht NaN)
      - Prozent-Berechnungen funktionieren (0% bis 100%)
    """
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    # Verschiedene 0-Tage-Trips mit unterschiedlichen Daten
    zero_day_dates = [
        ("2026-01-01", "Neujahr Zero-Trip"),
        ("2026-06-15", "Mitte Jahr Zero-Trip"), 
        ("2026-12-31", "Silvester Zero-Trip"),
    ]
    
    for date_str, event_name in zero_day_dates:
        zero_trip_entry = MockConfigEntry(
            domain="whenhub",
            data={
                "event_name": event_name,
                "event_type": "trip", 
                "start_date": date_str,
                "end_date": date_str,  # Gleicher Tag = 0-Tage-Trip
                "image_path": "",
                "website_url": "",
                "notes": "Division-by-zero Test"
            },
            unique_id=f"whenhub_zero_trip_{date_str.replace('-', '_')}",
            version=1,
        )
        
        # Test am Trip-Tag
        with at(f"{date_str} 10:00:00+00:00"):
            # Setup sollte nicht crashen
            await setup_and_wait(hass, zero_trip_entry)
            
            # Alle Sensoren sollten definierte Werte haben
            from _helpers import slug
            entity_prefix = slug(event_name)
            
            sensors_to_check = [
                f"sensor.{entity_prefix}_days_until_start",
                f"sensor.{entity_prefix}_days_until_end", 
                f"sensor.{entity_prefix}_trip_left_days",
                f"sensor.{entity_prefix}_trip_left_percent",
                f"sensor.{entity_prefix}_countdown_text",
            ]
            
            for sensor_id in sensors_to_check:
                sensor = hass.states.get(sensor_id)
                assert sensor is not None, f"Sensor {sensor_id} should exist"
                assert sensor.state is not None, f"Sensor {sensor_id} should have a state"
                assert sensor.state != "unknown", f"Sensor {sensor_id} should not be unknown"
                
                # Für numerische Sensoren: nicht NaN oder Inf
                if "percent" in sensor_id or "days" in sensor_id:
                    try:
                        value = float(sensor.state)
                        assert not (value != value), f"Sensor {sensor_id} should not be NaN: {value}"  # NaN check
                        assert abs(value) != float('inf'), f"Sensor {sensor_id} should not be Inf: {value}"
                    except ValueError:
                        # Countdown-Text ist String, das ist OK
                        if "countdown_text" not in sensor_id:
                            pytest.fail(f"Numeric sensor {sensor_id} has non-numeric value: {sensor.state}")


@pytest.mark.asyncio
async def test_zero_day_trip_vs_regular_trip_comparison(hass: HomeAssistant, trip_one_day_entry, trip_config_entry):
    """
    Vergleichstest: 0-Tage-Trip vs. regulärer Trip.
    
    Warum:
      0-Tage-Trip sollte sich logisch von regulären Trips unterscheiden.
      Aber grundlegende Mechanismen sollten ähnlich funktionieren.
      
    Wie:
      0-Tage-Trip und regulären Trip parallel setup.
      Verhalten an verschiedenen Tagen vergleichen.
      
    Erwartung:
      - 0-Tage-Trip: starts+ends+active gleichzeitig ON
      - Regulärer Trip: starts/ends/active an verschiedenen Tagen
      - Beide: Korrekte Nachbehandlung am Tag danach
    """
    # Test am 15.08. - 0-Tage-Trip Tag
    with at("2026-08-15 10:00:00+00:00"):
        await setup_and_wait(hass, trip_one_day_entry)
        
        # 0-Tage-Trip: Alle Binary-Sensoren ON
        zero_starts = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_starts_today")
        zero_ends = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_ends_today")
        zero_active = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_active_today")
        
        assert zero_starts.state == "on", "Zero-day trip should start today"
        assert zero_ends.state == "on", "Zero-day trip should end today"
        assert zero_active.state == "on", "Zero-day trip should be active today"
        
    # Test am 12.07. - Regulärer Trip Start (aber nicht Ende)
    with at("2026-07-12 10:00:00+00:00"):
        await setup_and_wait(hass, trip_config_entry)
        
        # Regulärer Trip: Nur starts und active ON, ends OFF
        regular_starts = get_state(hass, "binary_sensor.danemark_2026_trip_starts_today")
        regular_ends = get_state(hass, "binary_sensor.danemark_2026_trip_ends_today")
        regular_active = get_state(hass, "binary_sensor.danemark_2026_trip_active_today")
        
        assert regular_starts.state == "on", "Regular trip should start today"
        assert regular_ends.state == "off", "Regular trip should NOT end today (starts 12th, ends 26th)"
        assert regular_active.state == "on", "Regular trip should be active today"
        
        # Vergleiche left_percent Logik
        zero_percent = get_state(hass, "sensor.tagesausflug_munchen_trip_left_percent")
        regular_percent = get_state(hass, "sensor.danemark_2026_trip_left_percent")
        
        # 0-Tage-Trip: 100% (voller Tag verbleibt)
        # Regulärer Trip: 100% (am Starttag, noch alles verbleibt)
        assert float(zero_percent.state) == 100.0
        assert float(regular_percent.state) == 100.0
        
        # Aber left_days unterscheidet sich
        zero_left_days = get_state(hass, "sensor.tagesausflug_munchen_trip_left_days")
        regular_left_days = get_state(hass, "sensor.danemark_2026_trip_left_days")
        
        assert int(zero_left_days.state) == 1  # 0-Tage-Trip: 1 Tag verbleibt
        assert int(regular_left_days.state) == 15  # Regulärer Trip: 15 Tage verbleiben (12.-26. Juli)