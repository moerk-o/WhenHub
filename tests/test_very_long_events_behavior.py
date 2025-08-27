"""Tests für sehr lange Events (mehrere Jahre bis Jahrzehnte)."""
import pytest
from homeassistant.core import HomeAssistant
from _helpers import at, setup_and_wait, get_state


@pytest.mark.asyncio
async def test_trip_very_long_event_behavior(hass: HomeAssistant, trip_multi_year_entry):
    """
    Vollständiger Test für sehr langen Trip (5 Jahre: 2026-2030).
    
    Warum:
      Sehr lange Events testen die Stabilität der Berechnungen über große Zeiträume.
      Prozent-Berechnungen, Countdown-Text-Formatierung und Performance bei >1800 Tagen.
      Overflow-Schutz und plausible Werteentwicklung über Jahre.
      
    Wie:
      5-Jahres-Trip (2026-01-01 bis 2030-12-31).
      Teste zu verschiedenen Zeitpunkten: Start, nach 1 Jahr, Mitte, vor Ende.
      Verifiziere monotone Prozent-Abnahme und plausible Countdown-Texte.
      
    Erwartung:
      - days_until: >1800 am Start, monoton fallend
      - left_percent: 100% → 0%, niemals außerhalb [0,100]
      - Countdown-Text: strukturiert mit Jahren/Monaten
      - Keine Overflow-Exceptions oder Performance-Probleme
    """
    percentages = []
    days_values = []
    
    # Phase 1: Kurz nach Start (10 Tage nach Beginn)
    with at("2026-01-10 10:00:00+00:00"):
        await setup_and_wait(hass, trip_multi_year_entry)
        
        # Days until start sollte negativ sein (bereits gestartet)
        days_until_start = get_state(hass, "sensor.funfjahres_weltreise_days_until_start")
        assert int(days_until_start.state) < 0, f"Trip should have started, got {days_until_start.state}"
        
        # Left days sollte sehr groß sein (~1816 Tage verbleiben)
        left_days = get_state(hass, "sensor.funfjahres_weltreise_trip_left_days")
        left_days_val = int(left_days.state)
        assert left_days_val > 1800, f"Should have >1800 days left at start, got {left_days_val}"
        days_values.append(left_days_val)
        
        # Left percent sollte sehr hoch sein (>99%)
        left_percent = get_state(hass, "sensor.funfjahres_weltreise_trip_left_percent")
        percent_val = float(left_percent.state)
        assert 99.0 <= percent_val <= 100.0, f"Should be >99% at start, got {percent_val}%"
        percentages.append(percent_val)
        
        # Countdown text sollte Jahre enthalten
        countdown = get_state(hass, "sensor.funfjahres_weltreise_countdown_text")
        countdown_text = countdown.state
        assert any(word in countdown_text for word in ["Jahr", "Jahre"]), \
            f"Long countdown should mention years: {countdown_text}"
        
        # Trip sollte aktiv sein
        active = get_state(hass, "binary_sensor.funfjahres_weltreise_trip_active_today")
        assert active.state == "on", "Long trip should be active"
        
    # Phase 2: Nach einem Jahr (2027-01-01)
    with at("2027-01-01 10:00:00+00:00"):
        await hass.config_entries.async_reload(trip_multi_year_entry.entry_id)
        await hass.async_block_till_done()
        
        left_days = get_state(hass, "sensor.funfjahres_weltreise_trip_left_days")
        left_days_val = int(left_days.state)
        assert 1400 <= left_days_val <= 1500, f"After 1 year should have ~1460 days left, got {left_days_val}"
        days_values.append(left_days_val)
        
        left_percent = get_state(hass, "sensor.funfjahres_weltreise_trip_left_percent")
        percent_val = float(left_percent.state)
        assert 75.0 <= percent_val <= 85.0, f"After 1 year should be ~80%, got {percent_val}%"
        assert percent_val < percentages[-1], "Percent should decrease over time"
        percentages.append(percent_val)
        
        # Countdown sollte immer noch Jahre enthalten
        countdown = get_state(hass, "sensor.funfjahres_weltreise_countdown_text")
        assert "Jahr" in countdown.state, f"Should still mention years: {countdown.state}"
        
    # Phase 3: In der Mitte (2028-07-01, ~2.5 Jahre)
    with at("2028-07-01 10:00:00+00:00"):
        await hass.config_entries.async_reload(trip_multi_year_entry.entry_id)
        await hass.async_block_till_done()
        
        left_days = get_state(hass, "sensor.funfjahres_weltreise_trip_left_days")
        left_days_val = int(left_days.state)
        assert 800 <= left_days_val <= 1000, f"At middle should have ~900 days left, got {left_days_val}"
        days_values.append(left_days_val)
        
        left_percent = get_state(hass, "sensor.funfjahres_weltreise_trip_left_percent")
        percent_val = float(left_percent.state)
        assert 45.0 <= percent_val <= 55.0, f"At middle should be ~50%, got {percent_val}%"
        assert percent_val < percentages[-1], "Percent should continue decreasing"
        percentages.append(percent_val)
        
    # Phase 4: Kurz vor Ende (2030-12-01, 30 Tage vor Ende)
    with at("2030-12-01 10:00:00+00:00"):
        await hass.config_entries.async_reload(trip_multi_year_entry.entry_id)
        await hass.async_block_till_done()
        
        left_days = get_state(hass, "sensor.funfjahres_weltreise_trip_left_days")
        left_days_val = int(left_days.state)
        assert 25 <= left_days_val <= 35, f"Near end should have ~30 days left, got {left_days_val}"
        days_values.append(left_days_val)
        
        left_percent = get_state(hass, "sensor.funfjahres_weltreise_trip_left_percent")
        percent_val = float(left_percent.state)
        assert 0.0 < percent_val < 5.0, f"Near end should be <5%, got {percent_val}%"
        assert percent_val < percentages[-1], "Percent should continue decreasing"
        percentages.append(percent_val)
        
        # Countdown sollte jetzt Tage/Wochen anzeigen
        countdown = get_state(hass, "sensor.funfjahres_weltreise_countdown_text")
        countdown_text = countdown.state
        assert any(word in countdown_text for word in ["Tag", "Tage", "Woche", "Wochen"]), \
            f"Near end should show days/weeks: {countdown_text}"
    
    # Verifiziere strikte Monotonie über alle Phasen
    for i in range(1, len(percentages)):
        assert percentages[i] < percentages[i-1], f"Percentages not monotonic: {percentages}"
    
    for i in range(1, len(days_values)):
        assert days_values[i] < days_values[i-1], f"Days values not monotonic: {days_values}"
    
    # Phase 5: Nach Ende (2031-01-05)
    with at("2031-01-05 10:00:00+00:00"):
        await hass.config_entries.async_reload(trip_multi_year_entry.entry_id)
        await hass.async_block_till_done()
        
        left_days = get_state(hass, "sensor.funfjahres_weltreise_trip_left_days")
        left_percent = get_state(hass, "sensor.funfjahres_weltreise_trip_left_percent")
        active = get_state(hass, "binary_sensor.funfjahres_weltreise_trip_active_today")
        
        assert int(left_days.state) == 0, "After long trip should have 0 days left"
        assert float(left_percent.state) == 0.0, "After long trip should have 0% left"
        assert active.state == "off", "Long trip should not be active after end"


@pytest.mark.asyncio
async def test_milestone_multi_decade_stability(hass: HomeAssistant, milestone_multi_decade_entry):
    """
    Stabilitätstest für Multi-Dekaden Milestone (30 Jahre in die Zukunft).
    
    Warum:
      Extreme Zukunftsdaten testen mathematische Stabilität.
      >10.000 Tage bis zum Ziel - Overflow-Schutz und Performance.
      Countdown-Text Formatierung bei sehr großen Zeitspannen.
      
    Wie:
      Milestone 30 Jahre in der Zukunft (2056-06-15).
      Teste verschiedene Jahre davor und Countdown-Text Qualität.
      
    Erwartung:
      - days_until: >10.000, korrekt berechnet
      - Countdown-Text: strukturiert, lesbar, nicht überladen
      - Keine Overflow- oder Performance-Probleme
      - is_today korrekt am Zieldatum
    """
    # Phase 1: 30 Jahre vor Ziel (2026-06-15)
    with at("2026-06-15 10:00:00+00:00"):
        await setup_and_wait(hass, milestone_multi_decade_entry)
        
        # Days until sollte etwa 30*365 = ~10.950 Tage sein
        days_until = get_state(hass, "sensor.generationen_ziel_days_until")
        days_val = int(days_until.state)
        assert 10800 <= days_val <= 11000, f"30 years should be ~10950 days, got {days_val}"
        
        # Countdown text sollte Jahrzehnte sinnvoll darstellen
        countdown = get_state(hass, "sensor.generationen_ziel_countdown_text")
        countdown_text = countdown.state
        assert "Jahr" in countdown_text, f"Multi-decade should mention years: {countdown_text}"
        
        # Text sollte nicht übermäßig detailliert sein
        word_count = len(countdown_text.split())
        assert word_count <= 15, f"Countdown text too verbose for long duration: {countdown_text}"
        
        # is_today sollte OFF sein
        is_today = get_state(hass, "binary_sensor.generationen_ziel_is_today")
        assert is_today.state == "off", "Should not be today 30 years before"
        
    # Phase 2: 10 Jahre vor Ziel (2046-06-15)
    with at("2046-06-15 10:00:00+00:00"):
        await hass.config_entries.async_reload(milestone_multi_decade_entry.entry_id)
        await hass.async_block_till_done()
        
        days_until = get_state(hass, "sensor.generationen_ziel_days_until")
        days_val = int(days_until.state)
        assert 3600 <= days_val <= 3700, f"10 years should be ~3653 days, got {days_val}"
        
        # Countdown sollte immer noch Jahre erwähnen
        countdown = get_state(hass, "sensor.generationen_ziel_countdown_text")
        assert "Jahr" in countdown.state, f"10 years should mention years: {countdown.state}"
        
    # Phase 3: Am Zieldatum (2056-06-15)
    with at("2056-06-15 10:00:00+00:00"):
        await hass.config_entries.async_reload(milestone_multi_decade_entry.entry_id)
        await hass.async_block_till_done()
        
        # is_today sollte ON sein
        is_today = get_state(hass, "binary_sensor.generationen_ziel_is_today")
        assert is_today.state == "on", "Should be today on target date after 30 years"
        
        # days_until sollte 0 sein
        days_until = get_state(hass, "sensor.generationen_ziel_days_until")
        assert int(days_until.state) == 0, "Should be 0 days on target date"
        
        # Countdown sollte "0 Tage" zeigen
        countdown = get_state(hass, "sensor.generationen_ziel_countdown_text")
        assert "0 Tage" in countdown.state, f"Should show '0 Tage' on target date: {countdown.state}"


@pytest.mark.asyncio
async def test_anniversary_century_occurrence_calculation(hass: HomeAssistant, anniversary_century_entry):
    """
    Test für Jahrhundert-Anniversary (100+ Jahre Vorkommen).
    
    Warum:
      Sehr alte Original-Daten testen occurrence_count Berechnungen.
      100+ Vorkommen müssen korrekt gezählt werden.
      Performance bei vielen Anniversary-Berechnungen.
      
    Wie:
      Anniversary mit Original-Datum 1925-05-20.
      Teste in 2026 - sollte 100+ Vorkommen haben.
      
    Erwartung:
      - occurrences_count: 100+ (1925-2025)
      - next_date: 2026-05-20
      - days_until_next: plausibel
      - Keine Performance-Probleme bei vielen Vorkommen
    """
    with at("2026-03-15 10:00:00+00:00"):
        await setup_and_wait(hass, anniversary_century_entry)
        
        # Occurrence count sollte etwa 101 sein (1925-2025)
        occurrences = get_state(hass, "sensor.jahrhundert_jubilaeum_occurrences_count")
        occurrences_val = int(occurrences.state)
        assert 100 <= occurrences_val <= 102, f"Century anniversary should have ~101 occurrences, got {occurrences_val}"
        
        # Next date sollte 2026-05-20 sein
        next_date = get_state(hass, "sensor.jahrhundert_jubilaeum_next_date")
        assert next_date.state == "2026-05-20", f"Next occurrence should be 2026-05-20, got {next_date.state}"
        
        # Days until next sollte plausibel sein (März bis Mai = ~66 Tage)
        days_until = get_state(hass, "sensor.jahrhundert_jubilaeum_days_until_next")
        days_val = int(days_until.state)
        assert 60 <= days_val <= 70, f"March to May should be ~66 days, got {days_val}"
        
        # Days since last sollte etwa 365 sein (letztes Jahr)
        days_since = get_state(hass, "sensor.jahrhundert_jubilaeum_days_since_last")
        days_since_val = int(days_since.state)
        assert 290 <= days_since_val <= 310, f"Since last year should be ~298 days, got {days_since_val}"
        
        # Am Anniversary-Tag (2026-05-20)
        with at("2026-05-20 10:00:00+00:00"):
            await hass.config_entries.async_reload(anniversary_century_entry.entry_id)
            await hass.async_block_till_done()
            
            is_today = get_state(hass, "binary_sensor.jahrhundert_jubilaeum_is_today")
            assert is_today.state == "on", "Should be today on 101st occurrence"
            
            # Occurrence count sollte jetzt 101 sein
            occurrences_now = get_state(hass, "sensor.jahrhundert_jubilaeum_occurrences_count")
            assert int(occurrences_now.state) == occurrences_val, f"Occurrences should be consistent"


@pytest.mark.asyncio
async def test_countdown_text_formatting_very_long_durations(hass: HomeAssistant, trip_multi_year_entry):
    """
    Spezifischer Test für Countdown-Text Formatierung bei sehr langen Zeiträumen.
    
    Warum:
      Countdown-Texte müssen auch bei Jahren/Jahrzehnten lesbar bleiben.
      Hierarchische Darstellung: Jahre > Monate > Wochen > Tage.
      Nicht überladen oder zu detailliert bei langen Zeiträumen.
      
    Wie:
      5-Jahres-Trip zu verschiedenen Zeitpunkten.
      Analysiere Countdown-Text Struktur und Lesbarkeit.
      
    Erwartung:
      - Bei Jahren: Fokus auf Jahre/Monate, weniger Detail
      - Bei Monaten: Jahre + Monate + ggf. Wochen
      - Konsistente, hierarchische Formatierung
      - Keine "0 Jahre, 0 Monate, 0 Wochen, X Tage" Redundanz
    """
    test_scenarios = [
        ("2026-01-10", "4+ Jahre", ["Jahr", "Jahre"]),  # Fast 5 Jahre verbleiben
        ("2027-06-15", "3+ Jahre", ["Jahr", "Jahre"]),  # ~3.5 Jahre verbleiben
        ("2029-01-15", "1+ Jahr", ["Jahr", "Monat"]),   # ~2 Jahre verbleiben
        ("2030-09-01", "Monate", ["Monat", "Woche"]),   # ~4 Monate verbleiben
        ("2030-12-01", "Tage/Wochen", ["Tag", "Woche"]), # ~30 Tage verbleiben
    ]
    
    for date_str, expected_range, expected_words in test_scenarios:
        with at(f"{date_str} 10:00:00+00:00"):
            await setup_and_wait(hass, trip_multi_year_entry)
            
            countdown = get_state(hass, "sensor.funfjahres_weltreise_countdown_text")
            countdown_text = countdown.state
            
            # Prüfe dass erwartete Zeiteinheiten erwähnt werden
            word_found = any(word in countdown_text for word in expected_words)
            assert word_found, f"Expected words {expected_words} in '{countdown_text}' for {expected_range}"
            
            # Prüfe Textlänge - sollte nicht übermäßig detailliert sein
            word_count = len(countdown_text.split())
            assert word_count <= 20, f"Countdown too verbose ({word_count} words): {countdown_text}"
            
            # Prüfe dass Text nicht leer ist
            assert len(countdown_text) > 0, "Countdown text should not be empty"
            
            # Prüfe keine redundanten Null-Werte bei langen Zeiträumen
            if "Jahr" in countdown_text:
                # Bei Jahren sollte nicht "0 Monate, 0 Wochen" stehen
                redundant_patterns = ["0 Monate", "0 Wochen", "0 Tage"]
                redundant_found = any(pattern in countdown_text for pattern in redundant_patterns)
                assert not redundant_found, f"Redundant zero values in long duration: {countdown_text}"


@pytest.mark.asyncio
async def test_performance_stability_extreme_calculations(hass: HomeAssistant):
    """
    Performance-Stabilitätstest für extreme Berechnungen.
    
    Warum:
      Sehr lange Events könnten Performance-Probleme verursachen.
      Setup-Zeit, Berechnungsdauer, Memory-Usage bei großen Zahlen.
      
    Wie:
      Multiple sehr lange Events parallel setup.
      Messe keine Timeouts oder Exceptions bei extremen Werten.
      
    Erwartung:
      - Setup funktioniert in angemessener Zeit
      - Alle Berechnungen erfolgreich
      - Keine Memory-Leaks oder Overflow-Exceptions
    """
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    import time
    
    # Erstelle mehrere extreme Events
    extreme_events = []
    for i in range(3):
        # Verschiedene sehr lange Zeiträume
        start_year = 2026 + i
        end_year = 2040 + i * 5  # 14, 19, 24 Jahre
        
        extreme_entry = MockConfigEntry(
            domain="whenhub",
            data={
                "event_name": f"Extreme Event {i+1}",
                "event_type": "trip",
                "start_date": f"{start_year}-01-01",
                "end_date": f"{end_year}-12-31",
                "image_path": "",
                "website_url": "",
                "notes": f"Performance test {i+1}"
            },
            unique_id=f"whenhub_extreme_{i+1}",
            version=1,
        )
        extreme_events.append(extreme_entry)
    
    # Performance-Test: Setup sollte in angemessener Zeit erfolgen
    with at("2026-06-15 10:00:00+00:00"):
        start_time = time.time()
        
        for entry in extreme_events:
            await setup_and_wait(hass, entry)
        
        setup_time = time.time() - start_time
        assert setup_time < 10.0, f"Setup took too long: {setup_time:.2f} seconds"
        
        # Verifiziere dass alle Entities korrekte Werte haben
        for i in range(3):
            entity_name = f"extreme_event_{i+1}"
            
            # Days left sollte sehr groß aber definiert sein
            left_days = get_state(hass, f"sensor.{entity_name}_trip_left_days")
            left_days_val = int(left_days.state)
            assert left_days_val > 5000, f"Extreme event should have >5000 days, got {left_days_val}"
            
            # Percent sollte sehr hoch aber unter 100 sein
            left_percent = get_state(hass, f"sensor.{entity_name}_trip_left_percent")
            percent_val = float(left_percent.state)
            assert 99.0 <= percent_val <= 100.0, f"Extreme event percent should be ~100%, got {percent_val}%"
            
            # Countdown text sollte existieren und sinnvoll sein
            countdown = get_state(hass, f"sensor.{entity_name}_countdown_text")
            assert len(countdown.state) > 0, f"Countdown text should exist for extreme event {i+1}"
            assert "Jahr" in countdown.state, f"Extreme duration should mention years: {countdown.state}"