"""Stress-Tests für Trip-Prozent-Berechnungen mit Randfällen."""
import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from _helpers import with_time, setup_and_wait, get


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
    with with_time("2026-08-15 10:00:00+00:00"):
        await setup_and_wait(hass, single_day_entry)
        
        # Prozent sollte 100% sein (voller Tag verbleibt)
        percent = get(hass, "sensor.tagesausflug_trip_left_percent")
        assert float(percent.state) == 100.0
        
        # 1 Tag verbleibt (der aktuelle Tag)
        left_days = get(hass, "sensor.tagesausflug_trip_left_days")
        assert int(left_days.state) == 1
        
        # Trip ist aktiv
        assert get(hass, "binary_sensor.tagesausflug_trip_active_today").state == "on"
    
    # Tag nach dem Trip
    with with_time("2026-08-16 10:00:00+00:00"):
        await hass.config_entries.async_reload(single_day_entry.entry_id)
        await hass.async_block_till_done()
        
        # Prozent sollte 0% sein
        percent = get(hass, "sensor.tagesausflug_trip_left_percent")
        assert float(percent.state) == 0.0
        
        # Keine Tage verbleiben
        left_days = get(hass, "sensor.tagesausflug_trip_left_days")
        assert int(left_days.state) == 0
        
        # Trip ist nicht mehr aktiv
        assert get(hass, "binary_sensor.tagesausflug_trip_active_today").state == "off"


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
    with with_time("2026-01-01 10:00:00+00:00"):
        await setup_and_wait(hass, long_trip_entry)
        
        percent = get(hass, "sensor.weltreise_trip_left_percent")
        assert 99.0 <= float(percent.state) <= 100.0  # ~100%
        
        left_days = get(hass, "sensor.weltreise_trip_left_days")
        assert int(left_days.state) == 400  # Volle 400 Tage
    
    # Mitte des Trips (Tag 200)
    with with_time("2026-07-20 10:00:00+00:00"):  # ~200 Tage nach Start
        await hass.config_entries.async_reload(long_trip_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get(hass, "sensor.weltreise_trip_left_percent")
        # Toleranz für Rundung: sollte etwa 50% sein
        assert 48.0 <= float(percent.state) <= 52.0  # ~50%
    
    # Kurz vor Ende (Tag 360 von 400)
    with with_time("2026-12-27 10:00:00+00:00"):  # ~360 Tage nach Start
        await hass.config_entries.async_reload(long_trip_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get(hass, "sensor.weltreise_trip_left_percent")
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
    with with_time("2026-07-10 10:00:00+00:00"):  # 2 Tage vor Start
        await setup_and_wait(hass, trip_config_entry)
        
        percent = get(hass, "sensor.danemark_2026_trip_left_percent")
        assert float(percent.state) == 100.0  # Volle 100% vor Start
    
    # Während des Trips
    with with_time("2026-07-19 10:00:00+00:00"):  # Mitte des Trips
        await hass.config_entries.async_reload(trip_config_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get(hass, "sensor.danemark_2026_trip_left_percent")
        percent_val = float(percent.state)
        assert 0.0 < percent_val < 100.0  # Zwischen 0 und 100
        assert 40.0 <= percent_val <= 60.0  # Etwa in der Mitte
    
    # Nach Trip-Ende
    with with_time("2026-07-28 10:00:00+00:00"):  # 2 Tage nach Ende
        await hass.config_entries.async_reload(trip_config_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get(hass, "sensor.danemark_2026_trip_left_percent")
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
    with with_time("2026-09-02 10:00:00+00:00"):
        await setup_and_wait(hass, three_day_entry)
        
        percent = get(hass, "sensor.kurz_trip_trip_left_percent")
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
        with with_time(f"{date_str} 10:00:00+00:00"):
            if date_str == "2026-07-11":
                await setup_and_wait(hass, trip_config_entry)
            else:
                await hass.config_entries.async_reload(trip_config_entry.entry_id)
                await hass.async_block_till_done()
            
            percent = get(hass, "sensor.danemark_2026_trip_left_percent")
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
    with with_time("2026-07-10 10:00:00+00:00"):  # 2 Tage vor Start
        await setup_and_wait(hass, trip_config_entry)
        
        percent = get(hass, "sensor.danemark_2026_trip_left_percent")
        assert float(percent.state) == 100.0, f"Before start must be exactly 100.0%, got {percent.state}"
    
    # Nach Trip-Ende - MUSS exakt 0.0% sein  
    with with_time("2026-07-28 10:00:00+00:00"):  # 2 Tage nach Ende
        await hass.config_entries.async_reload(trip_config_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get(hass, "sensor.danemark_2026_trip_left_percent")
        assert float(percent.state) == 0.0, f"After end must be exactly 0.0%, got {percent.state}"
    
    # Während Trip - MUSS zwischen 0 und 100 liegen (exklusiv)
    with with_time("2026-07-19 10:00:00+00:00"):  # Mitte des Trips
        await hass.config_entries.async_reload(trip_config_entry.entry_id)
        await hass.async_block_till_done()
        
        percent = get(hass, "sensor.danemark_2026_trip_left_percent")
        percent_val = float(percent.state)
        assert 0.0 < percent_val < 100.0, f"During trip must be between 0 and 100 (exclusive), got {percent_val}"