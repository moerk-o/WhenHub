"""Test für Szenarien nach dem Event-Datum und negative Tage."""
import pytest
from homeassistant.core import HomeAssistant
from _helpers import with_time, setup_and_wait, get


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
    with with_time("2026-07-27 10:00:00+00:00"):  # Tag nach Trip-Ende
        await setup_and_wait(hass, trip_config_entry)
        
        # Tage bis Start/Ende sollten negativ sein
        days_until_start = get(hass, "sensor.danemark_2026_days_until_start")
        assert int(days_until_start.state) < 0  # Negativer Wert nach Start
        
        days_until_end = get(hass, "sensor.danemark_2026_days_until_end")
        assert int(days_until_end.state) < 0  # Negativer Wert nach Ende
        
        # Keine verbleibenden Tage/Prozent
        left_days = get(hass, "sensor.danemark_2026_trip_left_days")
        assert int(left_days.state) == 0
        
        left_percent = get(hass, "sensor.danemark_2026_trip_left_percent")
        assert float(left_percent.state) == 0.0
        
        # Binary-Sensoren müssen OFF sein
        assert get(hass, "binary_sensor.danemark_2026_trip_active_today").state == "off"
        assert get(hass, "binary_sensor.danemark_2026_trip_ends_today").state == "off"
        assert get(hass, "binary_sensor.danemark_2026_trip_starts_today").state == "off"
        
        # Countdown-Text zeigt "0 Tage"
        countdown = get(hass, "sensor.danemark_2026_countdown_text")
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
    with with_time("2026-03-17 10:00:00+00:00"):  # 2 Tage nach Milestone
        await setup_and_wait(hass, milestone_config_entry)
        
        # Days until sollte negativ sein
        days_until = get(hass, "sensor.projektabgabe_days_until")
        assert int(days_until.state) == -2
        
        # Binary sensor muss OFF sein
        assert get(hass, "binary_sensor.projektabgabe_is_today").state == "off"
        
        # Countdown text zeigt "0 Tage"
        countdown = get(hass, "sensor.projektabgabe_countdown_text")
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
    with with_time("2026-05-22 10:00:00+00:00"):  # 2 Tage nach Anniversary
        await setup_and_wait(hass, anniversary_config_entry)
        
        # Days until next sollte fast ein Jahr sein
        days_until_next = get(hass, "sensor.geburtstag_max_days_until_next")
        assert 360 < int(days_until_next.state) < 366  # ~363 Tage
        
        # Days since last sollte 2 sein
        days_since = get(hass, "sensor.geburtstag_max_days_since_last")
        assert int(days_since.state) == 2
        
        # Binary sensor muss OFF sein
        assert get(hass, "binary_sensor.geburtstag_max_is_today").state == "off"
        
        # Next date sollte 2027 sein
        next_date = get(hass, "sensor.geburtstag_max_next_date")
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
    with with_time("2026-12-26 10:00:00+00:00"):  # 2 Tage nach Heiligabend
        await setup_and_wait(hass, special_config_entry)
        
        # Days until sollte fast ein Jahr sein
        days_until = get(hass, "sensor.weihnachts_countdown_days_until")
        assert 360 < int(days_until.state) < 366  # ~363 Tage
        
        # Days since last sollte 2 sein
        days_since = get(hass, "sensor.weihnachts_countdown_days_since_last")
        assert int(days_since.state) == 2
        
        # Binary sensor muss OFF sein
        assert get(hass, "binary_sensor.weihnachts_countdown_is_today").state == "off"
        
        # Next date sollte 2027 sein
        next_date = get(hass, "sensor.weihnachts_countdown_next_date")
        assert next_date.state == "2027-12-24"