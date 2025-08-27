"""Gemeinsame Test-Helfer für WhenHub Integration Tests."""
from contextlib import contextmanager
from freezegun import freeze_time
from typing import List, Optional
from homeassistant.core import HomeAssistant


async def setup_and_wait(hass: HomeAssistant, config_entry) -> bool:
    """
    Entry hinzufügen, Setup ausführen und auf Completion warten.
    
    Args:
        hass: Home Assistant Instanz
        config_entry: Die Config Entry zum Setup
        
    Returns:
        bool: True wenn Setup erfolgreich
    """
    config_entry.add_to_hass(hass)
    success = await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return success


def assert_entities_exist(hass: HomeAssistant, entity_ids: List[str]) -> None:
    """
    Prüft die Existenz erwarteter Entitäten mit klaren Fehlermeldungen.
    
    Args:
        hass: Home Assistant Instanz  
        entity_ids: Liste der erwarteten Entity IDs
        
    Raises:
        AssertionError: Wenn eine Entity fehlt
    """
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state is not None, f"Expected entity missing: {entity_id}"


def get(hass: HomeAssistant, entity_id: str) -> Optional[object]:
    """
    State-Getter mit klarer Fehlermeldung.
    
    Args:
        hass: Home Assistant Instanz
        entity_id: Die Entity ID
        
    Returns:
        State object oder None
        
    Raises:
        AssertionError: Wenn Entity nicht existiert
    """
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity not found: {entity_id}"
    return state


def slug(name: str) -> str:
    """
    Vereinheitlicht erwartete Entity-Namen (wie die Integration es tut).
    Konvertiert zu lowercase und ersetzt Spaces/Sonderzeichen mit Underscore.
    
    Args:
        name: Der Event-Name
        
    Returns:
        str: Slug-Version des Namens
    """
    import re
    # Lowercase, replace spaces and special chars with underscore
    slug_name = name.lower()
    slug_name = re.sub(r'[^a-z0-9]+', '_', slug_name)
    slug_name = slug_name.strip('_')
    return slug_name


@contextmanager
def with_time(dtstr: str):
    """
    Kontextmanager um freezegun.freeze_time für deterministisches Testing.
    
    Args:
        dtstr: ISO datetime string mit Timezone (z.B. "2026-07-26 10:00:00+00:00")
        
    Usage:
        with with_time("2026-07-26 10:00:00+00:00"):
            # Code der zu dieser Zeit ausgeführt wird
    """
    with freeze_time(dtstr):
        yield