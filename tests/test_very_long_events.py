"""Tests für sehr lange Events (>365 Tage)."""
import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from _helpers import at, setup_and_wait, get_state


@pytest.mark.asyncio
async def test_trip_very_long_event_behavior(hass: HomeAssistant):
    """
    Sehr langer Trip Verhalten: Stabilität über extreme Zeiträume.
    
    Warum:
      Sehr lange Events (mehrere Jahre) testen die mathematische Stabilität.
      Countdown-Text muss über Jahre hinweg verständlich strukturiert bleiben.
      Prozentberechnungen dürfen keine Überläufe oder Sprünge haben.
      Performance muss auch bei >1000 Tagen stabil bleiben.
      
    Wie:
      Sehr langer Trip (Start 2026-01-01, Ende 2030-12-31 = ~1826 Tage).
      Freeze drei Messpunkte: früh, Mitte, kurz vor Ende.
      Prüfe days_until_end, trip_left_percent und countdown_text Qualität.
      
    Erwartung:
      - days_until_end: groß & plausibel (positiv bis kurz vor Ende)
      - trip_left_percent: 0.0 <= value <= 100.0, monoton fallend
      - countdown_text: verständlich mit Jahren/Monaten/Wochen strukturiert
      - Keine Overflow-Exceptions oder Performance-Probleme
    """
    # Sehr langer Trip Fixture (fast 5 Jahre)
    very_long_trip = MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Fünfjahres-Weltreise",
            "event_type": "trip",
            "start_date": "2026-01-01",
            "end_date": "2030-12-31",  # ~1826 Tage
            "image_path": "",
            "website_url": "",
            "notes": "Sehr langer Trip Test >365 Tage"
        },
        unique_id="whenhub_very_long_trip",
        version=1,
    )
    
    percent_values = []
    
    # Messpunkt 1: FRÜH (10 Tage nach Start)
    with at("2026-01-11 10:00:00+00:00"):
        await setup_and_wait(hass, very_long_trip)
        
        # days_until_end sollte sehr groß sein (~1816 Tage)
        days_until_end = get_state(hass, "sensor.funfjahres_weltreise_days_until_end")
        days_val = int(days_until_end.state)
        assert days_val > 1800, f"Früh: days_until_end sollte >1800 sein, ist {days_val}"
        assert days_val < 1830, f"Früh: days_until_end sollte <1830 sein, ist {days_val}"
        
        # trip_left_percent sollte sehr hoch sein (>98%)
        left_percent = get_state(hass, "sensor.funfjahres_weltreise_trip_left_percent")
        percent_val = float(left_percent.state)
        assert 0.0 <= percent_val <= 100.0, f"Früh: Percent außerhalb [0,100]: {percent_val}%"
        assert percent_val > 98.0, f"Früh: Sollte >98% sein, ist {percent_val}%"
        percent_values.append(percent_val)
        
        # countdown_text sollte Jahre erwähnen
        countdown = get_state(hass, "sensor.funfjahres_weltreise_countdown_text")
        countdown_text = countdown.state
        assert any(word in countdown_text for word in ["Jahr", "Jahre"]), \
            f"Früh: Countdown sollte Jahre erwähnen: '{countdown_text}'"
        assert len(countdown_text) > 0, "Countdown text darf nicht leer sein"
        
        # Trip sollte aktiv sein
        active = get_state(hass, "binary_sensor.funfjahres_weltreise_trip_active_today")
        assert active.state == "on", "Trip sollte aktiv sein"
        
        print(f"✅ Früh: {days_val} Tage, {percent_val:.1f}%, Text: '{countdown_text}'")
    
    # Messpunkt 2: MITTE (~2.5 Jahre = ~913 Tage nach Start)
    with at("2028-07-01 10:00:00+00:00"):
        await hass.config_entries.async_reload(very_long_trip.entry_id)
        await hass.async_block_till_done()
        
        # days_until_end sollte etwa die Hälfte sein (~913 Tage)
        days_until_end = get_state(hass, "sensor.funfjahres_weltreise_days_until_end")
        days_val = int(days_until_end.state)
        assert 900 < days_val < 950, f"Mitte: days_until_end sollte ~913 sein, ist {days_val}"
        
        # trip_left_percent sollte etwa 50% sein
        left_percent = get_state(hass, "sensor.funfjahres_weltreise_trip_left_percent")
        percent_val = float(left_percent.state)
        assert 0.0 <= percent_val <= 100.0, f"Mitte: Percent außerhalb [0,100]: {percent_val}%"
        assert 48.0 <= percent_val <= 52.0, f"Mitte: Sollte ~50% sein, ist {percent_val}%"
        
        # Monotonie-Check: muss gefallen sein
        assert percent_val < percent_values[-1], \
            f"Mitte: Percent muss monoton fallen: {percent_values[-1]}% -> {percent_val}%"
        percent_values.append(percent_val)
        
        # countdown_text sollte immer noch strukturiert sein
        countdown = get_state(hass, "sensor.funfjahres_weltreise_countdown_text")
        countdown_text = countdown.state
        assert len(countdown_text) > 0, "Countdown text darf nicht leer sein"
        # Könnte Jahre oder Monate erwähnen
        assert any(word in countdown_text for word in ["Jahr", "Jahre", "Monat", "Monate"]), \
            f"Mitte: Countdown sollte strukturiert sein: '{countdown_text}'"
        
        print(f"✅ Mitte: {days_val} Tage, {percent_val:.1f}%, Text: '{countdown_text}'")
    
    # Messpunkt 3: KURZ VOR ENDE (30 Tage vor Ende)
    with at("2030-12-01 10:00:00+00:00"):
        await hass.config_entries.async_reload(very_long_trip.entry_id)
        await hass.async_block_till_done()
        
        # days_until_end sollte klein sein (~30 Tage)
        days_until_end = get_state(hass, "sensor.funfjahres_weltreise_days_until_end")
        days_val = int(days_until_end.state)
        assert days_val > 0, f"Kurz vor Ende: days_until_end sollte positiv sein, ist {days_val}"
        assert days_val <= 30, f"Kurz vor Ende: days_until_end sollte <=30 sein, ist {days_val}"
        
        # trip_left_percent sollte sehr niedrig sein (<2%)
        left_percent = get_state(hass, "sensor.funfjahres_weltreise_trip_left_percent")
        percent_val = float(left_percent.state)
        assert 0.0 <= percent_val <= 100.0, f"Kurz vor Ende: Percent außerhalb [0,100]: {percent_val}%"
        assert percent_val < 2.0, f"Kurz vor Ende: Sollte <2% sein, ist {percent_val}%"
        
        # Monotonie-Check: muss weiter gefallen sein
        assert percent_val < percent_values[-1], \
            f"Kurz vor Ende: Percent muss monoton fallen: {percent_values[-1]}% -> {percent_val}%"
        percent_values.append(percent_val)
        
        # countdown_text sollte jetzt Tage/Wochen zeigen
        countdown = get_state(hass, "sensor.funfjahres_weltreise_countdown_text")
        countdown_text = countdown.state
        assert any(word in countdown_text for word in ["Tag", "Tage", "Woche", "Wochen"]), \
            f"Kurz vor Ende: Countdown sollte Tage/Wochen zeigen: '{countdown_text}'"
        assert len(countdown_text) > 0, "Countdown text darf nicht leer sein"
        
        # Trip sollte immer noch aktiv sein
        active = get_state(hass, "binary_sensor.funfjahres_weltreise_trip_active_today")
        assert active.state == "on", "Trip sollte noch aktiv sein kurz vor Ende"
        
        print(f"✅ Kurz vor Ende: {days_val} Tage, {percent_val:.1f}%, Text: '{countdown_text}'")
    
    # Verifiziere strikte Monotonie über alle Messpunkte
    print(f"✅ Monotonie-Verifizierung: {percent_values}")
    for i in range(1, len(percent_values)):
        assert percent_values[i] < percent_values[i-1], \
            f"Percent muss strikt monoton fallen: {percent_values}"