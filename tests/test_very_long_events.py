"""Tests für sehr lange Events >365 Tage (T11)."""
import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from _helpers import at, setup_and_wait, get_state


@pytest.mark.asyncio
async def test_very_long_trip_over_365_days(hass: HomeAssistant):
    """
    Warum:
      Sehr lange Trips (>365 Tage) testen Überläufe und Countdown-Text-Qualität.
      Jahre/Monate müssen korrekt heruntergebrochen werden.
    Wie:
      Trip über 500 Tage; Countdown-Text, days_until, Prozent-Werte prüfen.
    Erwartet:
      - Countdown-Text enthält Jahre/Monate/Wochen sinnvoll strukturiert
      - days_until > 365, konsistent
      - left_percent < 100% vor Ende, keine Überläufe
    """
    # 500-Tage-Trip 
    very_long_trip = MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Weltreise Extrem",
            "event_type": "trip",
            "start_date": "2026-01-01",
            "end_date": "2027-05-16",  # ~500 Tage später
            "image_path": "",
            "website_url": "",
            "notes": "Sehr langer Trip Test"
        },
        unique_id="whenhub_weltreise_extrem",
        version=1,
    )
    
    # Test vor Start (Countdown-Text soll Jahre enthalten)
    with at("2025-06-15 10:00:00+00:00"):  # ~200 Tage vor Start
        await setup_and_wait(hass, very_long_trip)
        
        countdown = get_state(hass, "sensor.weltreise_extrem_countdown_text")
        days_until_start = get_state(hass, "sensor.weltreise_extrem_days_until_start")
        
        # days_until sollte >200 sein
        assert int(days_until_start.state) > 200
        
        # Countdown-Text sollte strukturiert sein (Jahre/Monate)
        countdown_text = countdown.state
        assert len(countdown_text) > 0
        # Bei >6 Monaten sollten Monate oder Jahre erscheinen
        assert any(word in countdown_text for word in ["Jahr", "Jahre", "Monat", "Monate"]), f"Long countdown should contain years/months: {countdown_text}"
    
    # Test am Starttag (left_percent = 100%)
    with at("2026-01-01 10:00:00+00:00"):
        await hass.config_entries.async_reload(very_long_trip.entry_id)
        await hass.async_block_till_done()
        
        left_percent = get_state(hass, "sensor.weltreise_extrem_trip_left_percent")
        left_days = get_state(hass, "sensor.weltreise_extrem_trip_left_days")
        
        # Am Start: 100% und volle Tage
        assert float(left_percent.state) == 100.0
        assert int(left_days.state) >= 500  # Mindestens 500 Tage
    
    # Test in der Mitte (~250 Tage nach Start)
    with at("2026-09-07 10:00:00+00:00"):  # ~250 Tage nach Start
        await hass.config_entries.async_reload(very_long_trip.entry_id)
        await hass.async_block_till_done()
        
        left_percent = get_state(hass, "sensor.weltreise_extrem_trip_left_percent")
        left_days = get_state(hass, "sensor.weltreise_extrem_trip_left_days")
        
        # Etwa 50% verbleiben
        percent_val = float(left_percent.state)
        assert 40.0 <= percent_val <= 60.0, f"Expected ~50% remaining, got {percent_val}%"
        
        # left_days sollte etwa 250 sein
        days_val = int(left_days.state)
        assert 200 <= days_val <= 300, f"Expected ~250 days remaining, got {days_val}"
        
        # Grenzen prüfen
        assert 0.0 <= percent_val <= 100.0


@pytest.mark.asyncio
async def test_very_long_milestone_over_365_days(hass: HomeAssistant):
    """
    Warum:
      Milestone weit in der Zukunft (>365 Tage) muss Countdown-Text korrekt strukturieren.
    Wie:
      Milestone ~400 Tage in Zukunft; Countdown-Text und days_until prüfen.
    Erwartet:
      - days_until > 365
      - Countdown-Text mit Jahren/Monaten strukturiert  
      - Keine Überläufe bei großen Zahlen
    """
    very_long_milestone = MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Fernes Ziel",
            "event_type": "milestone",
            "target_date": "2027-03-15",  # ~400 Tage in Zukunft
            "image_path": "",
            "website_url": "",
            "notes": "Sehr fernes Milestone"
        },
        unique_id="whenhub_fernes_ziel",
        version=1,
    )
    
    with at("2026-02-01 10:00:00+00:00"):  # ~400 Tage vor Ziel
        await setup_and_wait(hass, very_long_milestone)
        
        days_until = get_state(hass, "sensor.fernes_ziel_days_until")
        countdown = get_state(hass, "sensor.fernes_ziel_countdown_text")
        
        # days_until sollte ~400 sein
        days_val = int(days_until.state)
        assert 350 <= days_val <= 450, f"Expected ~400 days, got {days_val}"
        
        # Countdown-Text sollte über Jahr strukturiert sein
        countdown_text = countdown.state
        assert "Jahr" in countdown_text or "Jahre" in countdown_text, f"Long milestone should contain years: {countdown_text}"


@pytest.mark.asyncio
async def test_very_long_anniversary_years_calculation(hass: HomeAssistant):
    """
    Warum:
      Anniversary mit sehr altem Originaldatum (>20 Jahre) muss occurrences_count korrekt berechnen.
    Wie:
      Anniversary mit original_date von 2000; aktuelle Zählung und next_date prüfen.
    Erwartet:
      - occurrences_count > 20
      - next_date korrekt für aktuelles Jahr
      - days_until plausibel
    """
    very_old_anniversary = MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "25 Jahre Jubiläum",
            "event_type": "anniversary",
            "target_date": "2000-05-20",  # 26 Jahre zurück
            "image_path": "",
            "website_url": "",
            "notes": "Sehr altes Anniversary"
        },
        unique_id="whenhub_25_jahre",
        version=1,
    )
    
    with at("2026-03-01 10:00:00+00:00"):  # März 2026
        await setup_and_wait(hass, very_old_anniversary)
        
        occurrences = get_state(hass, "sensor.25_jahre_jubiläum_occurrences_count")
        next_date = get_state(hass, "sensor.25_jahre_jubiläum_next_date")
        days_until = get_state(hass, "sensor.25_jahre_jubiläum_days_until_next")
        countdown = get_state(hass, "sensor.25_jahre_jubiläum_countdown_text")
        
        # Occurrences sollte 26 sein (2000-2025)
        assert int(occurrences.state) == 26, f"Expected 26 occurrences (2000-2025), got {occurrences.state}"
        
        # next_date sollte 2026-05-20 sein
        assert next_date.state == "2026-05-20"
        
        # days_until sollte etwa 80 sein (März bis Mai)
        days_val = int(days_until.state)
        assert 70 <= days_val <= 90, f"Expected ~80 days until May, got {days_val}"
        
        # Countdown sollte strukturiert sein
        countdown_text = countdown.state
        assert len(countdown_text) > 0


@pytest.mark.asyncio
async def test_multi_year_countdown_text_structure(hass: HomeAssistant):
    """
    Warum:
      Multi-Jahr Countdowns müssen lesbar strukturiert sein ohne Überläufe.
    Wie:
      Event 3+ Jahre in Zukunft; Countdown-Text-Struktur analysieren.
    Erwartet:
      - Jahre/Monate/Wochen/Tage hierarchisch
      - Keine "0 Jahre, 0 Monate" wenn nur Tage verbleiben
      - Konsistente Formatierung
    """
    multi_year_milestone = MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Ferne Zukunft",
            "event_type": "milestone",
            "target_date": "2029-06-15",  # ~3 Jahre in Zukunft
            "image_path": "",
            "website_url": "",
            "notes": "Multi-Jahr Test"
        },
        unique_id="whenhub_ferne_zukunft",
        version=1,
    )
    
    with at("2026-06-15 10:00:00+00:00"):  # Exakt 3 Jahre vorher
        await setup_and_wait(hass, multi_year_milestone)
        
        countdown = get_state(hass, "sensor.ferne_zukunft_countdown_text")
        days_until = get_state(hass, "sensor.ferne_zukunft_days_until")
        
        # days_until sollte etwa 1095 sein (3*365)
        days_val = int(days_until.state)
        assert 1090 <= days_val <= 1100, f"Expected ~1095 days (3 years), got {days_val}"
        
        # Countdown-Text sollte "3 Jahre" enthalten
        countdown_text = countdown.state
        assert "3 Jahre" in countdown_text or "3 Jahr" in countdown_text, f"Should contain '3 Jahre': {countdown_text}"
        
        # Sollte nicht übermäßig detailliert sein
        # (kein "3 Jahre, 0 Monate, 0 Wochen, 0 Tage" - sollte auf "3 Jahre" reduziert sein)
        word_count = len(countdown_text.split())
        assert word_count <= 10, f"Countdown text too verbose: {countdown_text}"


@pytest.mark.asyncio
async def test_extreme_future_date_stability(hass: HomeAssistant):
    """
    Warum:
      Extreme Zukunftsdaten (Jahrzehnte) dürfen nicht zu Überläufen führen.
    Wie:
      Event im Jahr 2050; Berechnungen auf Stabilität prüfen.  
    Erwartet:
      - days_until sehr groß aber valide
      - Countdown-Text handhabbar
      - Keine Integer-Overflows oder Exceptions
    """
    extreme_future = MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Jahrhundertereignis",
            "event_type": "milestone",
            "target_date": "2050-01-01",  # 24 Jahre in Zukunft
            "image_path": "",
            "website_url": "",
            "notes": "Extreme Future Test"
        },
        unique_id="whenhub_jahrhundert",
        version=1,
    )
    
    with at("2026-01-01 10:00:00+00:00"):  # 24 Jahre vorher
        await setup_and_wait(hass, extreme_future)
        
        days_until = get_state(hass, "sensor.jahrhundertereignis_days_until")
        countdown = get_state(hass, "sensor.jahrhundertereignis_countdown_text")
        
        # days_until sollte etwa 8760 sein (24*365)
        days_val = int(days_until.state)
        assert 8700 <= days_val <= 8800, f"Expected ~8760 days (24 years), got {days_val}"
        
        # Countdown sollte Jahre enthalten
        countdown_text = countdown.state
        assert "Jahr" in countdown_text, f"Extreme future should contain years: {countdown_text}"
        
        # Text sollte nicht crashed oder leer sein
        assert len(countdown_text) > 0
        assert countdown_text != "None"
        assert "error" not in countdown_text.lower()