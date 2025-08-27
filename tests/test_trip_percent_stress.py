"""Stress-Tests für Trip-Prozent-Berechnungen mit Randfällen."""
import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from _helpers import at, setup_and_wait, get_state


@pytest.mark.asyncio
async def test_single_day_trip_percent(hass: HomeAssistant):
    """
    Warum:
      1-Tages-Trips sind kritisch für Prozent-Berechnung (Division durch 1).
    Wie:
      Erstelle 1-Tages-Trip (Start=Ende); teste am Tag und danach.
    Erwartet:
      - Am Starttag: left_percent=100% (voller Tag verbleibt)
      - Am Folgetag: left_percent=0% (Trip vorbei)
      - left_days: 1 am Starttag (inklusiv), 0 danach
    """
    # 1-Tages-Trip Config
    single_day_entry = MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Tagesausflug",
            "event_type": "trip",
            "start_date": "2026-08-15",
            "end_date": "2026-08-15",  # Gleicher Tag!
            "image_path": "",
            "website_url": "",
            "notes": "Einzeltag-Test"
        },
        unique_id="whenhub_tagesausflug",
        version=1,
    )
    
    # Am Trip-Tag
    with at("2026-08-15 10:00:00+00:00"):
        await setup_and_wait(hass, single_day_entry)
        
        # Prozent sollte 100% sein (voller Tag verbleibt)
        percent = get_state(hass, "sensor.tagesausflug_trip_left_percent")
        assert float(percent.state) == 100.0
        
        # 1 Tag verbleibt (der aktuelle Tag)
        left_days = get_state(hass, "sensor.tagesausflug_trip_left_days")
        assert int(left_days.state) == 1
        
        # Trip ist aktiv
        assert get_state(hass, "binary_sensor.tagesausflug_trip_active_today").state == "on"
    
    # Tag nach dem Trip
    with at("2026-08-16 10:00:00+00:00"):
        await hass.config_entries.async_reload(single_day_entry.entry_id)
        await hass.async_block_till_done()
        
        # Prozent sollte 0% sein
        percent = get_state(hass, "sensor.tagesausflug_trip_left_percent")
        assert float(percent.state) == 0.0
        
        # Keine Tage verbleiben
        left_days = get_state(hass, "sensor.tagesausflug_trip_left_days")
        assert int(left_days.state) == 0
        
        # Trip ist nicht mehr aktiv
        assert get_state(hass, "binary_sensor.tagesausflug_trip_active_today").state == "off"


@pytest.mark.asyncio
async def test_long_trip_percent_midpoint(hass: HomeAssistant):
    """
    Warum:
      Lange Trips (>365 Tage) testen Prozent-Stabilität über lange Zeiträume.
    Wie:
      400-Tage-Trip; teste am Start, Mitte (~50%), kurz vor Ende (~10%).
    Erwartet:
      - Start: ~100%
      - Mitte (Tag 200): ~50% 
      - Tag 360: ~10%
      - Prozentwerte in sinnvollen Grenzen [0.0, 100.0]
    """
    # Langer Trip (400 Tage)
    long_trip_entry = MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Weltreise",
            "event_type": "trip",
            "start_date": "2026-01-01",
            "end_date": "2027-02-04",  # 400 Tage später
            "image_path": "",
            "website_url": "",
            "notes": "Langzeit-Trip"
        },
        unique_id="whenhub_weltreise",
        version=1,
    )
    
    # Am Starttag
    with at("2026-01-01 10:00:00+00:00"):
        await setup_and_wait(hass, long_trip_entry)
        
        percent = get_state(hass, "sensor.weltreise_trip_left_percent")
        assert 99.0 <= float(percent.state) <= 100.0  # ~100%
        
        left_days = get_state(hass, "sensor.weltreise_trip_left_days")
        assert int(left_days.state) == 400  # Volle 400 Tage
    
    # Mitte des Trips (Tag 200)
    with at("2026-07-20 10:00:00+00:00"):  # ~200 Tage nach Start
        await hass.config_entries.async_reload(long_trip_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get_state(hass, "sensor.weltreise_trip_left_percent")
        # Toleranz für Rundung: sollte etwa 50% sein
        assert 48.0 <= float(percent.state) <= 52.0  # ~50%
    
    # Kurz vor Ende (Tag 360 von 400)
    with at("2026-12-27 10:00:00+00:00"):  # ~360 Tage nach Start
        await hass.config_entries.async_reload(long_trip_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get_state(hass, "sensor.weltreise_trip_left_percent")
        # Sollte etwa 10% sein (40 von 400 Tagen übrig)
        assert 8.0 <= float(percent.state) <= 12.0  # ~10%


@pytest.mark.asyncio
async def test_trip_percent_boundaries(hass: HomeAssistant, trip_config_entry):
    """
    Warum:
      Prozente müssen strikt in [0.0, 100.0] bleiben; niemals negativ oder >100%.
    Wie:
      Teste vor Start (sollte 100%), während Trip, nach Ende (sollte 0%).
    Erwartet:
      - Vor Start: 100.0%
      - Während: 0% < x < 100%
      - Nach Ende: 0.0%
      - Niemals <0% oder >100%
    """
    # Vor Trip-Start
    with at("2026-07-10 10:00:00+00:00"):  # 2 Tage vor Start
        await setup_and_wait(hass, trip_config_entry)
        
        percent = get_state(hass, "sensor.danemark_2026_trip_left_percent")
        assert float(percent.state) == 100.0  # Volle 100% vor Start
    
    # Während des Trips
    with at("2026-07-19 10:00:00+00:00"):  # Mitte des Trips
        await hass.config_entries.async_reload(trip_config_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get_state(hass, "sensor.danemark_2026_trip_left_percent")
        percent_val = float(percent.state)
        assert 0.0 < percent_val < 100.0  # Zwischen 0 und 100
        assert 40.0 <= percent_val <= 60.0  # Etwa in der Mitte
    
    # Nach Trip-Ende
    with at("2026-07-28 10:00:00+00:00"):  # 2 Tage nach Ende
        await hass.config_entries.async_reload(trip_config_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get_state(hass, "sensor.danemark_2026_trip_left_percent")
        assert float(percent.state) == 0.0  # Exakt 0% nach Ende


@pytest.mark.asyncio
async def test_trip_percent_precision(hass: HomeAssistant):
    """
    Warum:
      Prozent-Rundung sollte konsistent und sinnvoll sein (max. 2 Dezimalstellen).
    Wie:
      3-Tages-Trip; teste Zwischenwerte die zu Rundung führen.
    Erwartet:
      - Tag 1: ~66.67% (2 von 3 Tagen übrig)
      - Tag 2: ~33.33% (1 von 3 Tagen übrig)
      - Rundung auf sinnvolle Dezimalstellen
    """
    three_day_entry = MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": "Kurz-Trip",
            "event_type": "trip",
            "start_date": "2026-09-01",
            "end_date": "2026-09-03",  # 3 Tage
            "image_path": "",
            "website_url": "",
            "notes": "Präzisions-Test"
        },
        unique_id="whenhub_kurztrip",
        version=1,
    )
    
    # Tag 2 des Trips
    with at("2026-09-02 10:00:00+00:00"):
        await setup_and_wait(hass, three_day_entry)
        
        percent = get_state(hass, "sensor.kurz_trip_trip_left_percent")
        percent_val = float(percent.state)
        
        # Sollte etwa 66.67% sein (2 von 3 Tagen übrig)
        assert 65.0 <= percent_val <= 68.0
        
        # Prüfe ob Wert sinnvoll gerundet (max 2 Dezimalstellen)
        percent_str = percent.state
        if '.' in percent_str:
            decimal_places = len(percent_str.split('.')[1])
            assert decimal_places <= 2, f"Too many decimal places: {percent_str}"


@pytest.mark.asyncio 
async def test_trip_percent_strict_monotonic_decrease(hass: HomeAssistant, trip_config_entry):
    """
    Warum:
      Vollständiger Lebenszyklus-Test der Prozent-Berechnung mit strikter Monotonie.
      Prozente dürfen NIEMALS ansteigen während eines Trips.
    Wie:
      Teste systematisch vor, am Start, während, am Ende, nach dem Trip.
    Erwartet:
      - STRIKT monoton fallende Prozentwerte während des Trips (nie gleich, nur kleiner)
      - Exakte Grenzen: 100.0% vor Start, 0.0% nach Ende
      - Keine Rundungsartefakte die Monotonie brechen
    """
    test_dates = [
        ("2026-07-11", 100.0, "vor Start", False),      # Vor Start
        ("2026-07-12", 100.0, "am Starttag", False),    # Starttag (noch 100%)
        ("2026-07-13", None, "Tag 2", True),            # Tag 2 (< 100%, streng fallend)
        ("2026-07-16", None, "Tag 5", True),            # Tag 5 (streng fallend)
        ("2026-07-19", None, "Mitte", True),            # Mitte (streng fallend)
        ("2026-07-22", None, "Tag 11", True),           # Tag 11 (streng fallend)
        ("2026-07-25", None, "vorletzter Tag", True),   # Vorletzter Tag (> 0%)
        ("2026-07-26", None, "Endtag", True),           # Endtag (≥ 0%, inklusiv)
        ("2026-07-27", 0.0, "nach Ende", False),        # Nach Ende (exakt 0%)
    ]
    
    previous_percent = 101.0  # Start mit unmöglichem Wert für ersten Check
    
    for date_str, expected, description, must_decrease in test_dates:
        with at(f"{date_str} 10:00:00+00:00"):
            if date_str == "2026-07-11":
                await setup_and_wait(hass, trip_config_entry)
            else:
                await hass.config_entries.async_reload(trip_config_entry.entry_id)
                await hass.async_block_till_done()
            
            percent = get_state(hass, "sensor.danemark_2026_trip_left_percent")
            percent_val = float(percent.state)
            
            # Prüfe erwartete exakte Werte
            if expected is not None:
                assert percent_val == expected, f"{description}: Expected exactly {expected}%, got {percent_val}%"
            
            # Prüfe STRIKTE Monotonie
            if previous_percent < 101.0:  # Skip ersten Durchlauf
                if must_decrease:
                    assert percent_val < previous_percent, f"{description}: Percent must strictly decrease from {previous_percent}% to {percent_val}%"
                else:
                    assert percent_val <= previous_percent, f"{description}: Percent must not increase from {previous_percent}% to {percent_val}%"
            
            # Prüfe exakte Grenzen
            assert 0.0 <= percent_val <= 100.0, f"{description}: Percent out of bounds: {percent_val}%"
            
            # Prüfe dass Werte sinnvoll gerundet sind (max 2 Dezimalstellen bei Rundung)
            percent_str = str(percent_val)
            if '.' in percent_str:
                decimal_places = len(percent_str.split('.')[1])
                assert decimal_places <= 2, f"{description}: Too many decimal places: {percent_val}"
            
            previous_percent = percent_val


@pytest.mark.asyncio
async def test_trip_percent_boundaries_exact(hass: HomeAssistant, trip_config_entry):
    """
    Warum:
      Exakte Grenzen-Tests: Prozente müssen EXAKT 0.0% oder 100.0% sein, niemals 99.99% oder 0.01%.
    Wie:
      Teste Vor-Start und Nach-Ende mit präzisen Erwartungen.
    Erwartet:
      - Vor Start: EXAKT 100.0% (nicht 99.x%)
      - Nach Ende: EXAKT 0.0% (nicht 0.x%)
      - Während Trip: Strikt zwischen 0.0 und 100.0 (exklusiv)
    """
    # Vor Trip-Start - MUSS exakt 100.0% sein
    with at("2026-07-10 10:00:00+00:00"):  # 2 Tage vor Start
        await setup_and_wait(hass, trip_config_entry)
        
        percent = get_state(hass, "sensor.danemark_2026_trip_left_percent")
        assert float(percent.state) == 100.0, f"Before start must be exactly 100.0%, got {percent.state}"
    
    # Nach Trip-Ende - MUSS exakt 0.0% sein  
    with at("2026-07-28 10:00:00+00:00"):  # 2 Tage nach Ende
        await hass.config_entries.async_reload(trip_config_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get_state(hass, "sensor.danemark_2026_trip_left_percent")
        assert float(percent.state) == 0.0, f"After end must be exactly 0.0%, got {percent.state}"
    
    # Während Trip - MUSS zwischen 0 und 100 liegen (exklusiv)
    with at("2026-07-19 10:00:00+00:00"):  # Mitte des Trips
        await hass.config_entries.async_reload(trip_config_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get_state(hass, "sensor.danemark_2026_trip_left_percent")
        percent_val = float(percent.state)
        assert 0.0 < percent_val < 100.0, f"During trip must be between 0 and 100 (exclusive), got {percent_val}"


@pytest.mark.asyncio
async def test_trip_percent_one_day(hass: HomeAssistant, trip_one_day_entry):
    """
    Prozent-Berechnung für 1-Tages-Trip mit exakten Grenzwerten.
    
    Warum:
      1-Tages-Trips sind kritische Grenzfälle für die Prozentberechnung.
      Division durch 1 Tag und Übergang von 100% zu 0% muss korrekt funktionieren.
      
    Wie:
      Trip mit start_date == end_date (gleicher Tag).
      Teste am Starttag selbst und am Folgetag.
      
    Erwartung:
      - Am Starttag: EXAKT 100% (voller Tag verbleibt noch)
      - Am Folgetag: EXAKT 0% (Trip ist vorbei)
      - left_days: 1 am Starttag, 0 am Folgetag
      - Binary sensor trip_active: ON am Starttag, OFF am Folgetag
    """
    # Test am Starttag (15.08.2026)
    with at("2026-08-15 10:00:00+00:00"):
        await setup_and_wait(hass, trip_one_day_entry)
        
        # Prozent muss exakt 100% sein
        percent = get_state(hass, "sensor.tagesausflug_munchen_trip_left_percent")
        assert float(percent.state) == 100.0, f"1-day trip on start day must be exactly 100%, got {percent.state}"
        
        # 1 Tag verbleibt
        left_days = get_state(hass, "sensor.tagesausflug_munchen_trip_left_days")
        assert int(left_days.state) == 1, f"Expected 1 day left, got {left_days.state}"
        
        # Trip ist aktiv
        active = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_active_today")
        assert active.state == "on", "Trip should be active on its single day"
        
        # Trip startet und endet heute
        starts = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_starts_today")
        ends = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_ends_today")
        assert starts.state == "on", "1-day trip should start today"
        assert ends.state == "on", "1-day trip should end today"
    
    # Test am Folgetag (16.08.2026)
    with at("2026-08-16 10:00:00+00:00"):
        await hass.config_entries.async_reload(trip_one_day_entry.entry_id)
        await hass.async_block_till_done()
        
        # Prozent muss exakt 0% sein
        percent = get_state(hass, "sensor.tagesausflug_munchen_trip_left_percent")
        assert float(percent.state) == 0.0, f"1-day trip day after must be exactly 0%, got {percent.state}"
        
        # Keine Tage verbleiben
        left_days = get_state(hass, "sensor.tagesausflug_munchen_trip_left_days")
        assert int(left_days.state) == 0, f"Expected 0 days left after trip, got {left_days.state}"
        
        # Trip ist nicht mehr aktiv
        active = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_active_today")
        assert active.state == "off", "Trip should not be active after its single day"
        
        # Kein Start oder Ende heute
        starts = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_starts_today")
        ends = get_state(hass, "binary_sensor.tagesausflug_munchen_trip_ends_today")
        assert starts.state == "off", "Trip should not start today"
        assert ends.state == "off", "Trip should not end today"


@pytest.mark.asyncio
async def test_trip_percent_very_long(hass: HomeAssistant, trip_very_long_entry):
    """
    Prozent-Berechnung für sehr langen Trip (2.5 Jahre / 912 Tage).
    
    Warum:
      Sehr lange Trips (>365 Tage) testen die Stabilität der Prozentberechnung.
      Werte müssen über lange Zeiträume plausibel und monoton fallend bleiben.
      
    Wie:
      Trip über 912 Tage (2026-01-01 bis 2028-06-30).
      Teste in Frühphase, Mitte und kurz vor Ende.
      Verifiziere monotone Abnahme der Prozentwerte.
      
    Erwartung:
      - Frühphase (Tag 10): >95% aber <100%
      - Mitte (Tag 456): ~50% 
      - Kurz vor Ende (Tag 900): <5% aber >0%
      - Werte immer zwischen 0 und 100
      - Strikt monoton fallend
    """
    percentages = []
    
    # Test in Frühphase (Tag 10 von 912)
    with at("2026-01-10 10:00:00+00:00"):
        await setup_and_wait(hass, trip_very_long_entry)
        
        percent = get_state(hass, "sensor.weltreise_2026_2028_trip_left_percent")
        percent_val = float(percent.state)
        
        # Sollte noch über 95% sein (902 von 912 Tagen verbleiben)
        assert 95.0 < percent_val < 100.0, f"Early phase should be >95%, got {percent_val}%"
        assert percent_val <= 99.0, f"Should not be too close to 100% on day 10, got {percent_val}%"
        percentages.append(percent_val)
        
        # Viele Tage verbleiben
        left_days = get_state(hass, "sensor.weltreise_2026_2028_trip_left_days")
        assert int(left_days.state) > 900, f"Should have >900 days left, got {left_days.state}"
        
        # Trip ist aktiv
        active = get_state(hass, "binary_sensor.weltreise_2026_2028_trip_active_today")
        assert active.state == "on", "Long trip should be active"
    
    # Test in der Mitte (Tag 456 von 912)
    with at("2027-04-01 10:00:00+00:00"):  # ~456 Tage nach Start
        await hass.config_entries.async_reload(trip_very_long_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get_state(hass, "sensor.weltreise_2026_2028_trip_left_percent")
        percent_val = float(percent.state)
        
        # Sollte etwa 50% sein (456 von 912 Tagen verbleiben)
        assert 48.0 <= percent_val <= 52.0, f"Middle phase should be ~50%, got {percent_val}%"
        assert percent_val < percentages[-1], f"Percent must decrease: {percentages[-1]}% -> {percent_val}%"
        percentages.append(percent_val)
        
        # Etwa halbe Tage verbleiben
        left_days = get_state(hass, "sensor.weltreise_2026_2028_trip_left_days")
        days_left = int(left_days.state)
        assert 450 <= days_left <= 460, f"Should have ~456 days left, got {days_left}"
    
    # Test kurz vor Ende (Tag 900 von 912)
    with at("2028-06-18 10:00:00+00:00"):  # 12 Tage vor Ende
        await hass.config_entries.async_reload(trip_very_long_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get_state(hass, "sensor.weltreise_2026_2028_trip_left_percent")
        percent_val = float(percent.state)
        
        # Sollte unter 5% sein (12 von 912 Tagen verbleiben)
        assert 0.0 < percent_val < 5.0, f"Near end should be <5%, got {percent_val}%"
        assert percent_val < percentages[-1], f"Percent must decrease: {percentages[-1]}% -> {percent_val}%"
        percentages.append(percent_val)
        
        # Wenige Tage verbleiben
        left_days = get_state(hass, "sensor.weltreise_2026_2028_trip_left_days")
        assert int(left_days.state) == 12, f"Should have 12 days left, got {left_days.state}"
        
        # Trip ist immer noch aktiv
        active = get_state(hass, "binary_sensor.weltreise_2026_2028_trip_active_today")
        assert active.state == "on", "Long trip should still be active near end"
    
    # Verifiziere strikt monotone Abnahme
    for i in range(1, len(percentages)):
        assert percentages[i] < percentages[i-1], f"Percentages must strictly decrease: {percentages}"
    
    # Test nach Ende (Tag nach dem Trip)
    with at("2028-07-01 10:00:00+00:00"):
        await hass.config_entries.async_reload(trip_very_long_entry.entry_id)
        await hass.async_block_till_done()
        
        # Prozent muss exakt 0% sein
        percent = get_state(hass, "sensor.weltreise_2026_2028_trip_left_percent")
        assert float(percent.state) == 0.0, f"After long trip must be exactly 0%, got {percent.state}"
        
        # Keine Tage verbleiben
        left_days = get_state(hass, "sensor.weltreise_2026_2028_trip_left_days")
        assert int(left_days.state) == 0, "Should have 0 days left after trip"
        
        # Trip ist nicht mehr aktiv
        active = get_state(hass, "binary_sensor.weltreise_2026_2028_trip_active_today")
        assert active.state == "off", "Long trip should not be active after end"