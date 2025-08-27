"""Tests für Szenarien nach dem Event-Datum und negative Tage."""
import pytest
from homeassistant.core import HomeAssistant
from _helpers import at, setup_and_wait, get_state


@pytest.mark.asyncio
async def test_trip_after_end_date(hass: HomeAssistant, trip_config_entry):
    """
    Warum:
      Nachlauf-Fehler (Off-by-one, falsche Binärzustände, negative Resttage) sind häufige Bugs.
    Wie:
      Freeze-Time auf Tag NACH Ende (27.07.2026, Trip endet 26.07.2026); Setup; Asserts.
    Erwartet:
      - days_until_start: negativ (< 0)
      - days_until_end: negativ (< 0)
      - trip_left_days: 0 (keine Restdauer)
      - trip_left_percent: 0.0 (keine Restprozente)
      - Binary-Sensoren: trip_active_today=OFF, trip_ends_today=OFF
      - countdown_text: "0 Tage" (gem. aktueller Logik)
    """
    with at("2026-07-27 10:00:00+00:00"):  # Tag nach Trip-Ende
        await setup_and_wait(hass, trip_config_entry)
        
        # Tage bis Start/Ende sollten negativ sein
        days_until_start = get_state(hass, "sensor.danemark_2026_days_until_start")
        assert int(days_until_start.state) < 0  # Negativer Wert nach Start
        
        days_until_end = get_state(hass, "sensor.danemark_2026_days_until_end")
        assert int(days_until_end.state) < 0  # Negativer Wert nach Ende
        
        # Keine verbleibenden Tage/Prozent
        left_days = get_state(hass, "sensor.danemark_2026_trip_left_days")
        assert int(left_days.state) == 0
        
        left_percent = get_state(hass, "sensor.danemark_2026_trip_left_percent")
        assert float(left_percent.state) == 0.0
        
        # Binary-Sensoren müssen OFF sein
        assert get_state(hass, "binary_sensor.danemark_2026_trip_active_today").state == "off"
        assert get_state(hass, "binary_sensor.danemark_2026_trip_ends_today").state == "off"
        assert get_state(hass, "binary_sensor.danemark_2026_trip_starts_today").state == "off"
        
        # Countdown-Text zeigt "0 Tage"
        countdown = get_state(hass, "sensor.danemark_2026_countdown_text")
        assert "0 Tage" in countdown.state


@pytest.mark.asyncio
async def test_milestone_after_target_date(hass: HomeAssistant, milestone_config_entry):
    """
    Warum:
      Nach dem Zieldatum sollten Sensoren konsistent bleiben.
    Wie:
      Freeze auf 2 Tage nach Milestone (17.03.2026); Setup; Asserts.
    Erwartet:
      - days_until: negativ (-2)
      - is_today: OFF
      - countdown_text: "0 Tage"
    """
    with at("2026-03-17 10:00:00+00:00"):  # 2 Tage nach Milestone
        await setup_and_wait(hass, milestone_config_entry)
        
        # Days until sollte negativ sein
        days_until = get_state(hass, "sensor.projektabgabe_days_until")
        assert int(days_until.state) == -2
        
        # Binary sensor muss OFF sein
        assert get_state(hass, "binary_sensor.projektabgabe_is_today").state == "off"
        
        # Countdown text zeigt "0 Tage"
        countdown = get_state(hass, "sensor.projektabgabe_countdown_text")
        assert "0 Tage" in countdown.state


@pytest.mark.asyncio
async def test_anniversary_after_event_date(hass: HomeAssistant, anniversary_config_entry):
    """
    Warum:
      Anniversaries sollten nach dem Jahrestag auf das nächste Jahr zeigen.
    Wie:
      Freeze auf 2 Tage nach Anniversary (22.05.2026); Setup; Asserts.
    Erwartet:
      - days_until_next: ~363 (zum nächsten Jahr)
      - days_since_last: 2
      - is_today: OFF
      - next_date: 2027-05-20
    """
    with at("2026-05-22 10:00:00+00:00"):  # 2 Tage nach Anniversary
        await setup_and_wait(hass, anniversary_config_entry)
        
        # Days until next sollte fast ein Jahr sein
        days_until_next = get_state(hass, "sensor.geburtstag_max_days_until_next")
        assert 360 < int(days_until_next.state) < 366  # ~363 Tage
        
        # Days since last sollte 2 sein
        days_since = get_state(hass, "sensor.geburtstag_max_days_since_last")
        assert int(days_since.state) == 2
        
        # Binary sensor muss OFF sein
        assert get_state(hass, "binary_sensor.geburtstag_max_is_today").state == "off"
        
        # Next date sollte 2027 sein
        next_date = get_state(hass, "sensor.geburtstag_max_next_date")
        assert next_date.state == "2027-05-20"


@pytest.mark.asyncio
async def test_special_after_christmas(hass: HomeAssistant, special_config_entry):
    """
    Warum:
      Special Events nach dem Datum sollten auf nächstes Jahr zeigen.
    Wie:
      Freeze auf 26.12.2026 (2 Tage nach Heiligabend); Setup; Asserts.
    Erwartet:
      - days_until: ~363 (zum nächsten Heiligabend)
      - days_since_last: 2
      - is_today: OFF
      - next_date: 2027-12-24
    """
    with at("2026-12-26 10:00:00+00:00"):  # 2 Tage nach Heiligabend
        await setup_and_wait(hass, special_config_entry)
        
        # Days until sollte fast ein Jahr sein
        days_until = get_state(hass, "sensor.weihnachts_countdown_days_until")
        assert 360 < int(days_until.state) < 366  # ~363 Tage
        
        # Days since last sollte 2 sein
        days_since = get_state(hass, "sensor.weihnachts_countdown_days_since_last")
        assert int(days_since.state) == 2
        
        # Binary sensor muss OFF sein
        assert get_state(hass, "binary_sensor.weihnachts_countdown_is_today").state == "off"
        
        # Next date sollte 2027 sein
        next_date = get_state(hass, "sensor.weihnachts_countdown_next_date")
        assert next_date.state == "2027-12-24"


# Nach-Event-Tests mit strikten Assertions
@pytest.mark.asyncio
async def test_trip_after_end_shows_zero(hass: HomeAssistant, trip_config_entry):
    """
    Trip einen Tag nach Ende: Alle Werte auf 0/OFF.
    
    Warum:
      Nach Trip-Ende müssen Sensoren definierte 0-Werte zeigen.
      Binäre Sensoren müssen OFF sein, keine aktive Trip-Anzeige mehr.
    Wie:
      Freeze auf 2026-07-27 (einen Tag nach Trip-Ende 26.07.2026);
      Setup; alle relevanten Sensoren prüfen.
    Erwartet:
      - countdown_text: "0 Tage"
      - days_until_start/end: < 0 (intern erlaubt)
      - trip_left_days: 0
      - trip_left_percent: 0.0
      - Alle Binary-Sensoren: OFF
    """
    with at("2026-07-27 10:00:00+00:00"):  # Einen Tag nach Trip-Ende
        await setup_and_wait(hass, trip_config_entry)
        
        # Countdown-Text zeigt "0 Tage"
        countdown = get_state(hass, "sensor.danemark_2026_countdown_text")
        assert countdown.state == "0 Tage", f" Expected '0 Tage' but got: {countdown.state}"
        
        # days_until < 0 intern erlaubt
        days_until_start = get_state(hass, "sensor.danemark_2026_days_until_start")
        assert int(days_until_start.state) < 0, f" days_until_start should be negative, got {days_until_start.state}"
        
        days_until_end = get_state(hass, "sensor.danemark_2026_days_until_end")
        assert int(days_until_end.state) < 0, f" days_until_end should be negative, got {days_until_end.state}"
        
        # Trip-spezifische Werte
        left_days = get_state(hass, "sensor.danemark_2026_trip_left_days")
        assert int(left_days.state) == 0, f" trip_left_days should be 0, got {left_days.state}"
        
        left_percent = get_state(hass, "sensor.danemark_2026_trip_left_percent")
        assert float(left_percent.state) == 0.0, f" trip_left_percent should be 0.0, got {left_percent.state}"
        
        # Alle Binary-Sensoren OFF
        assert get_state(hass, "binary_sensor.danemark_2026_trip_active_today").state == "off"
        assert get_state(hass, "binary_sensor.danemark_2026_trip_starts_today").state == "off"
        assert get_state(hass, "binary_sensor.danemark_2026_trip_ends_today").state == "off"


@pytest.mark.asyncio
async def test_milestone_after_target_shows_zero(hass: HomeAssistant, milestone_config_entry):
    """
    Milestone einen Tag nach Zieldatum: 0-Werte und OFF-Binaries.
    
    Warum:
      Nach Milestone-Zieldatum müssen Sensoren definierte Endwerte zeigen.
    Wie:
      Freeze auf 2026-03-16 (einen Tag nach Milestone 15.03.2026);
      Setup; relevante Sensoren prüfen.
    Erwartet:
      - countdown_text: "0 Tage"
      - days_until: < 0 (intern erlaubt)
      - is_today: OFF
    """
    with at("2026-03-16 10:00:00+00:00"):  # Einen Tag nach Milestone
        await setup_and_wait(hass, milestone_config_entry)
        
        # Countdown-Text zeigt "0 Tage"
        countdown = get_state(hass, "sensor.projektabgabe_countdown_text")
        assert countdown.state == "0 Tage", f" Expected '0 Tage' but got: {countdown.state}"
        
        # days_until < 0 intern erlaubt
        days_until = get_state(hass, "sensor.projektabgabe_days_until")
        assert int(days_until.state) < 0, f" days_until should be negative, got {days_until.state}"
        
        # Binary-Sensor OFF
        is_today = get_state(hass, "binary_sensor.projektabgabe_is_today")
        assert is_today.state == "off", f" is_today should be OFF, got {is_today.state}"


@pytest.mark.asyncio
async def test_anniversary_after_event_shows_zero_today(hass: HomeAssistant, anniversary_config_entry):
    """
    Anniversary einen Tag nach Jahrestag: is_today OFF, nächstes Jahr aktiv.
    
    Warum:
      Nach Anniversary sollte is_today OFF sein, aber nicht "0 Tage" (nächstes Jahr aktiv).
      Anniversary verhält sich anders als Trip/Milestone - zeigt nächstes Vorkommen.
    Wie:
      Freeze auf 2026-05-21 (einen Tag nach Anniversary 20.05.2026);
      Setup; prüfen dass is_today OFF aber countdown auf nächstes Jahr zeigt.
    Erwartet:
      - is_today: OFF
      - countdown_text: NICHT "0 Tage" (sondern Countdown zu 2027)
      - days_until_next: > 0 (nächstes Jahr)
      - days_since_last: > 0 (seit gestern)
    """
    with at("2026-05-21 10:00:00+00:00"):  # Einen Tag nach Anniversary
        await setup_and_wait(hass, anniversary_config_entry)
        
        # Binary-Sensor OFF
        is_today = get_state(hass, "binary_sensor.geburtstag_max_is_today")
        assert is_today.state == "off", f" is_today should be OFF, got {is_today.state}"
        
        # Anniversary-Spezialverhalten: zeigt nächstes Jahr (nicht "0 Tage")
        countdown = get_state(hass, "sensor.geburtstag_max_countdown_text")
        assert countdown.state != "0 Tage", f" Anniversary should NOT show '0 Tage', got {countdown.state}"
        
        # Positive Werte für nächstes Jahr
        days_until_next = get_state(hass, "sensor.geburtstag_max_days_until_next")
        assert int(days_until_next.state) > 0, f" days_until_next should be positive, got {days_until_next.state}"
        
        days_since_last = get_state(hass, "sensor.geburtstag_max_days_since_last")
        assert int(days_since_last.state) > 0, f" days_since_last should be positive, got {days_since_last.state}"


@pytest.mark.asyncio
async def test_special_christmas_after_event_shows_zero_today(hass: HomeAssistant, special_config_entry):
    """
    Special Event einen Tag nach Weihnachten: is_today OFF, nächstes Jahr aktiv.
    
    Warum:
      Special Events verhalten sich wie Anniversary - nach Event zeigt nächstes Jahr.
    Wie:
      Freeze auf 2026-12-25 (einen Tag nach Heiligabend 24.12.2026);
      Setup; prüfen dass is_today OFF aber countdown auf nächstes Jahr zeigt.
    Erwartet:
      - is_today: OFF  
      - countdown_text: NICHT "0 Tage" (sondern Countdown zu 2027)
      - days_until: > 0 (nächstes Jahr)
      - days_since_last: > 0 (seit gestern)
    """
    with at("2026-12-25 10:00:00+00:00"):  # Einen Tag nach Heiligabend
        await setup_and_wait(hass, special_config_entry)
        
        # Binary-Sensor OFF
        is_today = get_state(hass, "binary_sensor.weihnachts_countdown_is_today")
        assert is_today.state == "off", f" is_today should be OFF, got {is_today.state}"
        
        # Special Event-Spezialverhalten: zeigt nächstes Jahr (nicht "0 Tage")
        countdown = get_state(hass, "sensor.weihnachts_countdown_countdown_text")
        assert countdown.state != "0 Tage", f" Special Event should NOT show '0 Tage', got {countdown.state}"
        
        # Positive Werte für nächstes Jahr
        days_until = get_state(hass, "sensor.weihnachts_countdown_days_until")
        assert int(days_until.state) > 0, f" days_until should be positive (next year), got {days_until.state}"
        
        days_since_last = get_state(hass, "sensor.weihnachts_countdown_days_since_last") 
        assert int(days_since_last.state) > 0, f" days_since_last should be positive, got {days_since_last.state}"


# Explizite Tests für negative Werte (Ergänzung zu T02)
@pytest.mark.asyncio
async def test_explicit_negative_values_after_events(hass: HomeAssistant, trip_config_entry, milestone_config_entry):
    """
    Explizite Verifikation dass negative Werte nach Events erlaubt sind.
    
    Warum:
      Negative days_until Werte sind intern erlaubt und dokumentieren vergangene Events.
      Diese dürfen nicht zu Exceptions oder undefined behavior führen.
    Wie:
      Mehrere Events nach ihren Daten testen; explizit negative Werte verifizieren.
    Erwartet:
      - days_until < 0 für alle vergangenen Events
      - Werte sind definiert (nicht None, nicht NaN)  
      - Keine Exceptions bei negativen Berechnungen
    """
    # Trip: mehrere Tage nach Ende
    with at("2026-08-05 10:00:00+00:00"):  # 10 Tage nach Trip-Ende
        await setup_and_wait(hass, trip_config_entry)
        
        days_until_start = get_state(hass, "sensor.danemark_2026_days_until_start")
        start_val = int(days_until_start.state)
        assert start_val < -15, f" days_until_start should be very negative, got {start_val}"
        
        days_until_end = get_state(hass, "sensor.danemark_2026_days_until_end")
        end_val = int(days_until_end.state)
        assert end_val < -5, f" days_until_end should be negative, got {end_val}"
    
    # Milestone: 1 Monat nach Zieldatum
    with at("2026-04-15 10:00:00+00:00"):  # 31 Tage nach Milestone
        await setup_and_wait(hass, milestone_config_entry)
        
        days_until = get_state(hass, "sensor.projektabgabe_days_until")
        milestone_val = int(days_until.state)
        assert milestone_val < -25, f" milestone days_until should be very negative, got {milestone_val}"
        
        # Countdown-Text muss immer noch "0 Tage" sein (nie negativ angezeigt)
        countdown = get_state(hass, "sensor.projektabgabe_countdown_text")
        assert countdown.state == "0 Tage", f" countdown should still be '0 Tage', got {countdown.state}"