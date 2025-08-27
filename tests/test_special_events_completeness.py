"""Vollständigkeitstests für alle Special Events mit dynamischer Parametrisierung."""
import pytest
import sys
import os
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from _helpers import at, setup_and_wait, get_state

# Dynamischer Import der SPECIAL_EVENTS aus dem Produktionscode
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from custom_components.whenhub.const import SPECIAL_EVENTS


def create_special_event_config(special_type: str):
    """Helper to create a special event config entry."""
    event_info = SPECIAL_EVENTS.get(special_type, {})
    return MockConfigEntry(
        domain="whenhub",
        data={
            "event_name": f"Test {event_info.get('name', special_type)}",
            "event_type": "special",
            "special_type": special_type,
            "special_category": event_info.get('category', 'traditional'),
            "image_path": "",
            "website_url": "",
            "notes": f"Vollständigkeitstest für {special_type}"
        },
        unique_id=f"whenhub_test_{special_type}",
        version=1,
    )


def slug(text):
    """Convert text to slug format for entity IDs."""
    import re
    text = text.lower()
    text = re.sub(r'[äöü]', lambda m: {'ä':'a', 'ö':'o', 'ü':'u'}[m.group()], text)
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')


@pytest.mark.parametrize("special_type", list(SPECIAL_EVENTS.keys()))
@pytest.mark.asyncio
async def test_special_events_complete(hass: HomeAssistant, special_type: str):
    """
    Vollständigkeitstest für ALLE Special Events mit 3 Phasen pro Event.
    
    Warum:
      Jedes Special Event aus SPECIAL_EVENTS muss korrekt funktionieren.
      Dynamische Parametrisierung garantiert Vollständigkeit ohne Hardcoding.
      Regression-Schutz bei neuen Events durch automatische Tests.
      
    Wie:
      Parametrisierung über alle Keys aus SPECIAL_EVENTS (dynamisch importiert).
      Pro Event 3 Phasen: Weit vorher, am Event-Tag, Tag danach.
      Prüfung aller Entities und korrekter Werte.
      
    Erwartung:
      Phase 1 (weit vorher): Entities existieren, is_today OFF, days_until > 0, next_date valide
      Phase 2 (Event-Tag): is_today ON, countdown_text "0 Tage"
      Phase 3 (Tag danach): is_today OFF, days_until ~365/366 (wiederkehrend)
    """
    event_info = SPECIAL_EVENTS[special_type]
    event_name = event_info.get('name', special_type)
    entity_prefix = slug(f"test_{event_name}")
    
    # Bestimme Event-Datum für 2026 (bekanntes Referenzjahr)
    if special_type == "easter":
        event_date = "2026-04-05"  # Ostern 2026
    elif special_type == "pentecost":
        event_date = "2026-05-24"  # Pfingsten 2026
    elif special_type == "advent_1":
        event_date = "2026-11-29"  # 1. Advent 2026
    elif special_type == "advent_2":
        event_date = "2026-12-06"  # 2. Advent 2026
    elif special_type == "advent_3":
        event_date = "2026-12-13"  # 3. Advent 2026
    elif special_type == "advent_4":
        event_date = "2026-12-20"  # 4. Advent 2026
    elif event_info.get('type') == 'fixed':
        # Fixe Daten
        month = event_info['month']
        day = event_info['day']
        event_date = f"2026-{month:02d}-{day:02d}"
    elif special_type == "spring_start":
        event_date = "2026-03-20"  # Frühlingsanfang 2026
    elif special_type == "summer_start":
        event_date = "2026-06-21"  # Sommeranfang 2026
    elif special_type == "autumn_start":
        event_date = "2026-09-23"  # Herbstanfang 2026
    elif special_type == "winter_start":
        event_date = "2026-12-21"  # Winteranfang 2026
    else:
        pytest.skip(f"Unknown event type for {special_type}")
    
    config_entry = create_special_event_config(special_type)
    
    # Phase 1: Weit vorher (1. Januar 2026)
    with at("2026-01-01 10:00:00+00:00"):
        await setup_and_wait(hass, config_entry)
        
        # Entities müssen existieren
        days_until = get_state(hass, f"sensor.{entity_prefix}_days_until")
        countdown_text = get_state(hass, f"sensor.{entity_prefix}_countdown_text")
        next_date = get_state(hass, f"sensor.{entity_prefix}_next_date")
        last_date = get_state(hass, f"sensor.{entity_prefix}_last_date")
        is_today = get_state(hass, f"binary_sensor.{entity_prefix}_is_today")
        image = get_state(hass, f"image.{entity_prefix}_image")
        
        # Validierungen
        assert days_until is not None, f"{special_type}: days_until entity missing"
        assert int(days_until.state) > 0, f"{special_type}: days_until should be positive"
        assert is_today.state == "off", f"{special_type}: is_today should be OFF weit vorher"
        assert next_date.state == event_date, f"{special_type}: next_date should be {event_date}"
        assert countdown_text.state != "0 Tage", f"{special_type}: Should not be '0 Tage' weit vorher"
    
    # Phase 2: Am Event-Tag
    with at(f"{event_date} 10:00:00+00:00"):
        await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done()
        
        is_today = get_state(hass, f"binary_sensor.{entity_prefix}_is_today")
        countdown_text = get_state(hass, f"sensor.{entity_prefix}_countdown_text")
        
        assert is_today.state == "on", f"{special_type}: is_today should be ON on event day"
        assert countdown_text.state == "0 Tage", f"{special_type}: Should be '0 Tage' on event day"
    
    # Phase 3: Tag danach (wiederkehrend -> springt aufs nächste Jahr)
    year, month, day = event_date.split('-')
    next_day = f"{year}-{month}-{int(day)+1:02d}"
    
    # Spezialbehandlung für Monatsende
    if special_type == "halloween":
        next_day = "2026-11-01"
    elif special_type == "new_year":
        next_day = "2026-01-02"
    elif special_type == "new_years_eve":
        next_day = "2027-01-01"
        
    with at(f"{next_day} 10:00:00+00:00"):
        await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done()
        
        is_today = get_state(hass, f"binary_sensor.{entity_prefix}_is_today")
        days_until = get_state(hass, f"sensor.{entity_prefix}_days_until")
        
        assert is_today.state == "off", f"{special_type}: is_today should be OFF day after"
        # Wiederkehrend: springt aufs nächste Jahr (~365/366 Tage)
        days_val = int(days_until.state)
        assert 360 <= days_val <= 370, f"{special_type}: Should jump to next year (~365), got {days_val}"


@pytest.mark.asyncio
async def test_movable_feasts_correct_dates(hass: HomeAssistant):
    """
    Expliziter Test für bewegliche Feste (Ostern) mit bekannten Referenzdaten.
    
    Warum:
      Bewegliche Feste wie Ostern haben jedes Jahr andere Daten.
      Die Berechnung muss für bekannte Jahre verifiziert werden.
      
    Wie:
      Ostern 2026 ist am 5. April (bekannt).
      Teste dass is_today ON ist am korrekten Datum.
      
    Erwartung:
      Am 2026-04-05: is_today ON für Ostern
      Am 2026-04-04: is_today OFF
      Am 2026-04-06: is_today OFF
    """
    config_entry = create_special_event_config("easter")
    entity_prefix = slug("test_ostersonntag")
    
    # Tag vor Ostern
    with at("2026-04-04 10:00:00+00:00"):
        await setup_and_wait(hass, config_entry)
        is_today = get_state(hass, f"binary_sensor.{entity_prefix}_is_today")
        assert is_today.state == "off", "Should be OFF day before Easter"
    
    # Ostersonntag 2026
    with at("2026-04-05 10:00:00+00:00"):
        await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done()
        is_today = get_state(hass, f"binary_sensor.{entity_prefix}_is_today")
        assert is_today.state == "on", "Should be ON on Easter Sunday 2026"
    
    # Tag nach Ostern
    with at("2026-04-06 10:00:00+00:00"):
        await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done()
        is_today = get_state(hass, f"binary_sensor.{entity_prefix}_is_today")
        assert is_today.state == "off", "Should be OFF day after Easter"