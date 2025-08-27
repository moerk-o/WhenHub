"""Vollständigkeitstests für alle Special Events mit parametrisierten Tests."""
import pytest
from homeassistant.core import HomeAssistant
from _helpers import with_time, setup_and_wait, get, assert_entities_exist, slug


# Alle 17 Special Events mit erwarteten Daten
SPECIAL_EVENTS = [
    # Traditional Holidays (11)
    ("christmas_eve", "Heiligabend", "2026-12-24", "traditional"),
    ("christmas_day", "1. Weihnachtstag", "2026-12-25", "traditional"),
    ("christmas_second", "2. Weihnachtstag", "2026-12-26", "traditional"),
    ("halloween", "Halloween", "2026-10-31", "traditional"),
    ("nicholas", "Nikolaus", "2026-12-06", "traditional"),
    ("easter", "Ostersonntag", "2026-04-05", "traditional"),  # Gauss-berechnet für 2026
    ("pentecost", "Pfingstsonntag", "2026-05-24", "traditional"),  # 49 Tage nach Ostern
    ("advent_1", "1. Advent", "2026-11-29", "traditional"),  # 4. Sonntag vor 24.12.
    ("advent_2", "2. Advent", "2026-12-06", "traditional"),  # 3. Sonntag vor 24.12.
    ("advent_3", "3. Advent", "2026-12-13", "traditional"),  # 2. Sonntag vor 24.12.
    ("advent_4", "4. Advent", "2026-12-20", "traditional"),  # Sonntag vor 24.12.
    
    # Calendar Holidays (2)
    ("new_year", "Neujahr", "2026-01-01", "calendar"),
    ("new_years_eve", "Silvester", "2026-12-31", "calendar"),
    
    # Astronomical Events (4)
    ("spring_equinox", "Frühlingsanfang", "2026-03-20", "astronomical"),
    ("summer_solstice", "Sommeranfang", "2026-06-21", "astronomical"),
    ("autumn_equinox", "Herbstanfang", "2026-09-23", "astronomical"),
    ("winter_solstice", "Winteranfang", "2026-12-21", "astronomical"),
]


@pytest.mark.parametrize("special_type,display_name,expected_date,category", SPECIAL_EVENTS)
@pytest.mark.asyncio
async def test_all_special_events_entities(
    hass: HomeAssistant, 
    special_event_entry_factory,
    special_type,
    display_name,
    expected_date,
    category
):
    """
    Warum:
      Vollständigkeit & Schutz gegen Regressionen bei neu hinzugefügten Events.
      Jeder der 17 Special Event Typen muss alle erwarteten Entities erzeugen.
    Wie:
      Erzeuge pro Special-Typ ein ConfigEntry (parametrisiert über alle 17 Typen).
      Prüfe mit assert_entities_exist ALLE erwarteten Entitäten.
    Erwartet:
      - Alle 4 Entity-Typen existieren (days_until, countdown_text, is_today, image)
      - Korrekte Benennung basierend auf Event-Name
    """
    # Erstelle Event mit spezifischem Typ
    event_name = f"Test {display_name}"
    entry = special_event_entry_factory(special_type, event_name, category)
    
    # Setup
    with with_time("2026-01-15 10:00:00+00:00"):  # Neutrales Datum
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


@pytest.mark.parametrize("special_type,display_name,expected_date,category", SPECIAL_EVENTS)
@pytest.mark.asyncio
async def test_special_event_is_today_logic(
    hass: HomeAssistant,
    special_event_entry_factory,
    special_type,
    display_name,
    expected_date,
    category
):
    """
    Warum:
      is_today muss exakt am Ereignistag ON sein, sonst OFF.
    Wie:
      Freeze auf repräsentative Tage: weit-vorher, am Tag, knapp danach.
    Erwartet:
      - Weit vorher: is_today=OFF, days_until > 0
      - Am Tag: is_today=ON, days_until = 0
      - Knapp danach: is_today=OFF, days_since_last > 0
    """
    event_name = f"Today {display_name}"
    entry = special_event_entry_factory(special_type, event_name, category)
    entity_prefix = slug(event_name)
    
    # Parse expected date für Tests
    year, month, day = expected_date.split('-')
    
    # Test 1: Weit vor dem Event (10 Tage)
    before_date = f"{year}-{month:0>2}-{int(day)-10:0>2} 10:00:00+00:00" if int(day) > 10 else "2026-01-01 10:00:00+00:00"
    with with_time(before_date):
        await setup_and_wait(hass, entry)
        
        # is_today muss OFF sein
        assert get(hass, f"binary_sensor.{entity_prefix}_is_today").state == "off"
        
        # days_until sollte positiv sein
        days_until = get(hass, f"sensor.{entity_prefix}_days_until")
        assert int(days_until.state) > 0
    
    # Test 2: Am Event-Tag
    with with_time(f"{expected_date} 10:00:00+00:00"):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        
        # is_today muss ON sein
        assert get(hass, f"binary_sensor.{entity_prefix}_is_today").state == "on"
        
        # days_until sollte 0 sein
        days_until = get(hass, f"sensor.{entity_prefix}_days_until")
        assert int(days_until.state) == 0
    
    # Test 3: Nach dem Event (2 Tage)
    after_date = f"{year}-{month:0>2}-{int(day)+2:0>2} 10:00:00+00:00" if int(day) < 29 else f"{year}-12-28 10:00:00+00:00"
    with with_time(after_date):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        
        # is_today muss OFF sein
        assert get(hass, f"binary_sensor.{entity_prefix}_is_today").state == "off"
        
        # days_since_last sollte positiv sein
        days_since = get(hass, f"sensor.{entity_prefix}_days_since_last")
        assert int(days_since.state) > 0


@pytest.mark.parametrize("special_type,display_name,expected_date,category", SPECIAL_EVENTS)
@pytest.mark.asyncio
async def test_special_event_next_date_calculation(
    hass: HomeAssistant,
    special_event_entry_factory,
    special_type,
    display_name,
    expected_date,
    category
):
    """
    Warum:
      next_date muss korrekt berechnet werden, besonders bei beweglichen Festen.
    Wie:
      Prüfe next_date für verschiedene Zeitpunkte im Jahr.
    Erwartet:
      - next_date ist plausibel (passende Kalenderdaten)
      - Bei beweglichen Festen (Ostern, Advent) korrekte Berechnung
      - Nach dem Event: next_date zeigt auf nächstes Jahr
    """
    event_name = f"Date {display_name}"
    entry = special_event_entry_factory(special_type, event_name, category)
    entity_prefix = slug(event_name)
    
    # Test vor dem Event
    with with_time("2026-01-01 10:00:00+00:00"):
        await setup_and_wait(hass, entry)
        
        next_date = get(hass, f"sensor.{entity_prefix}_next_date")
        assert next_date.state == expected_date
    
    # Test nach dem Event (sollte nächstes Jahr zeigen)
    with with_time("2026-12-28 10:00:00+00:00"):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        
        next_date = get(hass, f"sensor.{entity_prefix}_next_date")
        
        # Für Events vor 28.12. sollte es 2027 zeigen
        if expected_date < "2026-12-28":
            assert next_date.state.startswith("2027-")
        else:
            # Für Events nach 28.12. (z.B. Silvester) noch 2026
            assert next_date.state == expected_date


@pytest.mark.asyncio
async def test_special_events_countdown_text(hass: HomeAssistant, special_event_entry_factory):
    """
    Warum:
      Countdown-Text muss konsistent formatiert sein für alle Event-Typen.
    Wie:
      Teste mehrere Events mit verschiedenen Abständen.
    Erwartet:
      - Text enthält Zeitangabe (Tage/Wochen/Monate)
      - "0 Tage" am Event-Tag
      - Konsistente Formatierung
    """
    test_cases = [
        ("christmas_eve", "Weihnacht", "2026-12-10 10:00:00+00:00", 14),  # 14 Tage vor
        ("easter", "Ostern", "2026-03-22 10:00:00+00:00", 14),  # 14 Tage vor Ostern
        ("new_year", "Neujahr", "2025-12-25 10:00:00+00:00", 7),  # 7 Tage vor
    ]
    
    for special_type, event_name, freeze_date, expected_days in test_cases:
        entry = special_event_entry_factory(special_type, event_name)
        entity_prefix = slug(event_name)
        
        with with_time(freeze_date):
            await setup_and_wait(hass, entry)
            
            countdown = get(hass, f"sensor.{entity_prefix}_countdown_text")
            
            # Bei 14 Tagen sollte "2 Wochen" erscheinen
            if expected_days == 14:
                assert "2 Wochen" in countdown.state
            elif expected_days == 7:
                assert "1 Woche" in countdown.state or "7 Tage" in countdown.state
            
            # Prüfe dass Text nicht leer ist
            assert len(countdown.state) > 0


@pytest.mark.asyncio
async def test_advent_sundays_calculation(hass: HomeAssistant, special_event_entry_factory):
    """
    Warum:
      Advent-Sonntage müssen korrekt rückwärts vom 24.12. berechnet werden.
    Wie:
      Prüfe alle 4 Advent-Sonntage für 2026.
    Erwartet:
      - 1. Advent: 29.11.2026 (4. Sonntag vor 24.12.)
      - 2. Advent: 06.12.2026 (3. Sonntag vor 24.12.)
      - 3. Advent: 13.12.2026 (2. Sonntag vor 24.12.)
      - 4. Advent: 20.12.2026 (Sonntag vor 24.12.)
    """
    advent_dates = [
        ("advent_1", "2026-11-29"),
        ("advent_2", "2026-12-06"),
        ("advent_3", "2026-12-13"),
        ("advent_4", "2026-12-20"),
    ]
    
    with with_time("2026-11-01 10:00:00+00:00"):
        for special_type, expected_date in advent_dates:
            entry = special_event_entry_factory(special_type, f"Test {special_type}")
            await setup_and_wait(hass, entry)
            
            entity_prefix = slug(f"Test {special_type}")
            next_date = get(hass, f"sensor.{entity_prefix}_next_date")
            
            assert next_date.state == expected_date, f"{special_type}: Expected {expected_date}, got {next_date.state}"


@pytest.mark.asyncio
async def test_easter_dependent_events(hass: HomeAssistant, special_event_entry_factory):
    """
    Warum:
      Ostern und davon abhängige Events (Pfingsten) müssen via Gauss-Algorithmus berechnet werden.
    Wie:
      Prüfe Ostern und Pfingsten für 2026 und 2027.
    Erwartet:
      - 2026: Ostern 05.04., Pfingsten 24.05. (49 Tage später)
      - 2027: Ostern 28.03., Pfingsten 16.05. (49 Tage später)
    """
    # Test für 2026
    with with_time("2026-03-01 10:00:00+00:00"):
        easter_entry = special_event_entry_factory("easter", "Ostern 2026")
        pentecost_entry = special_event_entry_factory("pentecost", "Pfingsten 2026")
        
        await setup_and_wait(hass, easter_entry)
        await setup_and_wait(hass, pentecost_entry)
        
        # Ostern 2026
        easter_date = get(hass, "sensor.ostern_2026_next_date")
        assert easter_date.state == "2026-04-05"
        
        # Pfingsten 2026 (49 Tage nach Ostern)
        pentecost_date = get(hass, "sensor.pfingsten_2026_next_date")
        assert pentecost_date.state == "2026-05-24"
    
    # Test für 2027 (nach den Events von 2026)
    with with_time("2026-12-01 10:00:00+00:00"):
        await hass.config_entries.async_reload(easter_entry.entry_id)
        await hass.config_entries.async_reload(pentecost_entry.entry_id)
        await hass.async_block_till_done()
        
        # Ostern 2027
        easter_date = get(hass, "sensor.ostern_2026_next_date")
        assert easter_date.state == "2027-03-28"
        
        # Pfingsten 2027
        pentecost_date = get(hass, "sensor.pfingsten_2026_next_date")
        assert pentecost_date.state == "2027-05-16"