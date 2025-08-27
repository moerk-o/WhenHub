"""Dynamische Vollständigkeitstests für alle Special Events (T08)."""
import pytest
from homeassistant.core import HomeAssistant
from _helpers import at, setup_and_wait, get_state, assert_entities_exist, slug

# Import SPECIAL_EVENTS dynamisch aus der Produktionsumgebung
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'whenhub'))
from const import SPECIAL_EVENTS


def get_dynamic_special_events():
    """
    Warum:
      Dynamisch aus SPECIAL_EVENTS extrahieren statt hardcodierte Liste.
      Schutz gegen Regressionen wenn neue Special Events hinzugefügt werden.
    Wie:
      SPECIAL_EVENTS.keys() auslesen und für Parametrisierung aufbereiten.
    Erwartet:
      Liste aller verfügbaren special_type Keys mit Metadaten.
    """
    events = []
    for key, info in SPECIAL_EVENTS.items():
        events.append((key, info.get("name", key), info.get("category", "unknown")))
    return events


# Dynamische Parametrisierung - KEINE Magic Numbers!
DYNAMIC_SPECIAL_EVENTS = get_dynamic_special_events()


@pytest.mark.parametrize("special_type,display_name,category", DYNAMIC_SPECIAL_EVENTS)
@pytest.mark.asyncio
async def test_special_events_entities_complete(
    hass: HomeAssistant,
    special_event_entry_factory,
    special_type,
    display_name,
    category
):
    """
    Warum:
      Vollständigkeit & Schutz gegen Regressionen bei neu hinzugefügten Events.
      JEDEN Special Event Typ aus SPECIAL_EVENTS testen (dynamisch, nicht hardcodiert).
    Wie:
      Pro special_type: ConfigEntry erzeugen, Setup, alle erwarteten Entities prüfen.
    Erwartet:
      - Alle 5 Entity-Typen existieren (days_until, days_since_last, countdown_text, next_date, last_date, is_today, image)
      - Korrekte Benennung basierend auf slug(event_name)
    """
    event_name = f"Test {display_name}"
    entry = special_event_entry_factory(special_type, event_name, category)
    
    with at("2026-06-15 10:00:00+00:00"):  # Neutrales Datum
        await setup_and_wait(hass, entry)
        
        # Erwartete Entity-IDs basierend auf slug
        entity_prefix = slug(event_name)
        expected_entities = [
            f"sensor.{entity_prefix}_days_until",
            f"sensor.{entity_prefix}_days_since_last", 
            f"sensor.{entity_prefix}_countdown_text",
            f"sensor.{entity_prefix}_next_date",
            f"sensor.{entity_prefix}_last_date",
            f"binary_sensor.{entity_prefix}_is_today",
            f"image.{entity_prefix}_image",
        ]
        
        # Prüfe Existenz aller Entities
        assert_entities_exist(hass, expected_entities)


@pytest.mark.parametrize("special_type,display_name,category", DYNAMIC_SPECIAL_EVENTS)
@pytest.mark.asyncio
async def test_special_events_next_date_valid_iso(
    hass: HomeAssistant,
    special_event_entry_factory,
    special_type,
    display_name,
    category
):
    """
    Warum:
      next_date muss immer valides ISO-Datum (YYYY-MM-DD) sein für alle Special Events.
    Wie:
      Pro special_type: Setup, next_date auslesen, ISO-Format validieren.
    Erwartet:
      - next_date ist parsebares ISO-Datum
      - Liegt im aktuellen oder nächsten Jahr (je nach Freeze-Datum)
    """
    event_name = f"ISO {display_name}"
    entry = special_event_entry_factory(special_type, event_name, category)
    entity_prefix = slug(event_name)
    
    with at("2026-06-15 10:00:00+00:00"):
        await setup_and_wait(hass, entry)
        
        next_date_sensor = get_state(hass, f"sensor.{entity_prefix}_next_date")
        next_date_str = next_date_sensor.state
        
        # Validiere ISO-Format (YYYY-MM-DD)
        import datetime
        try:
            parsed_date = datetime.datetime.fromisoformat(next_date_str).date()
            # Sollte 2026 oder 2027 sein (abhängig vom Event-Datum)
            assert 2026 <= parsed_date.year <= 2027, f"next_date year out of range: {parsed_date.year}"
        except ValueError as e:
            pytest.fail(f"Invalid ISO date format for {special_type}: {next_date_str} - {e}")


@pytest.mark.parametrize("special_type,display_name,category", DYNAMIC_SPECIAL_EVENTS)
@pytest.mark.asyncio
async def test_special_events_is_today_logic_precision(
    hass: HomeAssistant,
    special_event_entry_factory,
    special_type,
    display_name,
    category
):
    """
    Warum:
      is_today muss exakt am Ereignistag ON sein, davor/danach OFF.
      Präzision für alle Special Event Typen sicherstellen.
    Wie:
      Pro special_type: Setup, next_date ermitteln, freeze auf Event-Tag, is_today prüfen.
    Erwartet:
      - Am next_date: is_today=ON, days_until=0
      - Tag davor: is_today=OFF, days_until>0
    """
    event_name = f"Today {display_name}"
    entry = special_event_entry_factory(special_type, event_name, category)
    entity_prefix = slug(event_name)
    
    # Schritt 1: next_date ermitteln
    with at("2026-06-15 10:00:00+00:00"):
        await setup_and_wait(hass, entry)
        next_date_str = get_state(hass, f"sensor.{entity_prefix}_next_date").state
    
    # Schritt 2: Am Event-Tag testen
    with at(f"{next_date_str} 10:00:00+00:00"):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        
        # is_today muss ON sein
        is_today = get_state(hass, f"binary_sensor.{entity_prefix}_is_today")
        assert is_today.state == "on", f"{special_type}: is_today should be ON on event day"
        
        # days_until muss 0 sein
        days_until = get_state(hass, f"sensor.{entity_prefix}_days_until")
        assert int(days_until.state) == 0, f"{special_type}: days_until should be 0 on event day"


@pytest.mark.parametrize("special_type,display_name,category", DYNAMIC_SPECIAL_EVENTS)
@pytest.mark.asyncio
async def test_special_events_after_event_behavior(
    hass: HomeAssistant,
    special_event_entry_factory,
    special_type,
    display_name,
    category
):
    """
    Warum:
      Nach dem Event: Text "0 Tage", days_until < 0 (intern erlaubt), is_today OFF.
      Jahreswechsel-Verhalten für alle Special Events prüfen.
    Wie:
      Pro special_type: next_date ermitteln, freeze auf Tag NACH Event.
    Erwartet:
      - countdown_text: "0 Tage"
      - days_until: negativ (intern)
      - is_today: OFF
      - days_since_last: positiv
    """
    event_name = f"After {display_name}"
    entry = special_event_entry_factory(special_type, event_name, category)
    entity_prefix = slug(event_name)
    
    # Schritt 1: next_date ermitteln
    with at("2026-06-15 10:00:00+00:00"):
        await setup_and_wait(hass, entry)
        next_date_str = get_state(hass, f"sensor.{entity_prefix}_next_date").state
    
    # Schritt 2: 2 Tage nach dem Event
    import datetime
    event_date = datetime.datetime.fromisoformat(next_date_str).date()
    after_date = event_date + datetime.timedelta(days=2)
    
    with at(f"{after_date.isoformat()} 10:00:00+00:00"):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        
        # countdown_text sollte "0 Tage" zeigen
        countdown = get_state(hass, f"sensor.{entity_prefix}_countdown_text")
        assert "0 Tage" in countdown.state, f"{special_type}: countdown_text should show '0 Tage' after event"
        
        # days_until sollte negativ sein (intern erlaubt)
        days_until = get_state(hass, f"sensor.{entity_prefix}_days_until")
        assert int(days_until.state) < 0, f"{special_type}: days_until should be negative after event"
        
        # is_today sollte OFF sein
        is_today = get_state(hass, f"binary_sensor.{entity_prefix}_is_today")
        assert is_today.state == "off", f"{special_type}: is_today should be OFF after event"
        
        # days_since_last sollte positiv sein
        days_since = get_state(hass, f"sensor.{entity_prefix}_days_since_last")
        assert int(days_since.state) > 0, f"{special_type}: days_since_last should be positive after event"


@pytest.mark.asyncio
async def test_special_events_count_verification():
    """
    Warum:
      Verifiziere dass unsere dynamische Liste korrekt aus SPECIAL_EVENTS extrahiert wurde.
      Schutz gegen leere oder fehlerhafte Extraktion.
    Wie:
      Zähle DYNAMIC_SPECIAL_EVENTS und prüfe auf Plausibilität.
    Erwartet:
      - Mindestens 10 Events (bekannte Baseline)
      - Alle Keys sind Strings
      - Alle Namen sind verfügbar
    """
    assert len(DYNAMIC_SPECIAL_EVENTS) >= 10, f"Too few special events: {len(DYNAMIC_SPECIAL_EVENTS)}"
    
    for special_type, display_name, category in DYNAMIC_SPECIAL_EVENTS:
        assert isinstance(special_type, str) and len(special_type) > 0, f"Invalid special_type: {special_type}"
        assert isinstance(display_name, str) and len(display_name) > 0, f"Invalid display_name: {display_name}"
        assert isinstance(category, str) and len(category) > 0, f"Invalid category: {category}"
    
    # Verifiziere dass bekannte Events dabei sind
    special_types = [evt[0] for evt in DYNAMIC_SPECIAL_EVENTS]
    known_events = ["christmas_eve", "easter", "new_year"]
    for known in known_events:
        assert known in special_types, f"Missing known special event: {known}"


# Spezifische Tests für bewegliche Feste
@pytest.mark.asyncio
async def test_easter_calculation_known_years(hass: HomeAssistant, special_event_entry_factory):
    """
    Warum:
      Ostern (bewegliches Fest) muss via Gauss-Algorithmus korrekt berechnet werden.
      Bekannte Referenzjahre gegen Regression prüfen.
    Wie:
      Easter-Event Setup, bekannte Osterdaten für 2026/2027 prüfen.
    Erwartet:
      - 2026: Ostern am 05.04.2026
      - 2027: Ostern am 28.03.2027
    """
    easter_entry = special_event_entry_factory("easter", "Ostern Test")
    
    # Test für 2026
    with at("2026-03-01 10:00:00+00:00"):
        await setup_and_wait(hass, easter_entry)
        next_date = get_state(hass, "sensor.ostern_test_next_date").state
        assert next_date == "2026-04-05", f"Wrong Easter date for 2026: {next_date}"
    
    # Test für 2027 (nach Ostern 2026)
    with at("2026-12-01 10:00:00+00:00"):
        await hass.config_entries.async_reload(easter_entry.entry_id)
        await hass.async_block_till_done()
        next_date = get_state(hass, "sensor.ostern_test_next_date").state
        assert next_date == "2027-03-28", f"Wrong Easter date for 2027: {next_date}"


@pytest.mark.asyncio
async def test_pentecost_relative_to_easter(hass: HomeAssistant, special_event_entry_factory):
    """
    Warum:
      Pfingsten muss exakt 49 Tage nach Ostern berechnet werden.
    Wie:
      Easter+Pentecost Setup, Differenz zwischen next_dates prüfen.
    Erwartet:
      - Pfingsten = Ostern + 49 Tage
      - 2026: Ostern 05.04. → Pfingsten 24.05.
    """
    easter_entry = special_event_entry_factory("easter", "Ostern Ref")
    pentecost_entry = special_event_entry_factory("pentecost", "Pfingsten Test")
    
    with at("2026-03-01 10:00:00+00:00"):
        await setup_and_wait(hass, easter_entry)
        await setup_and_wait(hass, pentecost_entry)
        
        easter_date = get_state(hass, "sensor.ostern_ref_next_date").state
        pentecost_date = get_state(hass, "sensor.pfingsten_test_next_date").state
        
        # Parse Daten
        import datetime
        easter_dt = datetime.datetime.fromisoformat(easter_date).date()
        pentecost_dt = datetime.datetime.fromisoformat(pentecost_date).date()
        
        # Prüfe 49-Tage-Differenz
        diff = (pentecost_dt - easter_dt).days
        assert diff == 49, f"Pentecost should be 49 days after Easter, got {diff} days"
        
        # Explizite Datumsverifikation für 2026
        assert easter_date == "2026-04-05"
        assert pentecost_date == "2026-05-24"