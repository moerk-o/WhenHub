"""Simple integration setup test to verify the test framework works."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

@pytest.mark.asyncio
async def test_whenhub_integration_loads(hass: HomeAssistant):
    """Test that we can at least import the integration."""
    # Try to import our integration directly
    try:
        from custom_components.whenhub import async_setup_entry
        from custom_components.whenhub.const import DOMAIN
        print(f"✅ Integration import works, domain: {DOMAIN}")
        assert DOMAIN == "whenhub"
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        pytest.fail(f"Cannot import integration: {e}")

@pytest.mark.asyncio
async def test_setup_component_minimal(hass: HomeAssistant):
    """Test minimal component setup without config entry."""
    # Just try to load the component
    assert await async_setup_component(hass, "whenhub", {})
    await hass.async_block_till_done()
    
    # Check if it's loaded
    assert "whenhub" in hass.config.components
    print("✅ Component loaded into Home Assistant")

@pytest.mark.asyncio  
async def test_manual_config_entry_setup(hass: HomeAssistant, trip_config_entry):
    """Test manual config entry setup using proper Home Assistant flow."""
    # Add the entry to hass
    trip_config_entry.add_to_hass(hass)
    
    # Use the proper Home Assistant setup flow
    assert await hass.config_entries.async_setup(trip_config_entry.entry_id)
    await hass.async_block_till_done()
    
    # Verify the entry is loaded
    from homeassistant.config_entries import ConfigEntryState
    assert trip_config_entry.state == ConfigEntryState.LOADED
    
    # Verify entities were created
    assert hass.states.get("sensor.danemark_2026_days_until_start") is not None
    print("✅ Config entry setup through Home Assistant flow works")