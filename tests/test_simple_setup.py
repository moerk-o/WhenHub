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
    """Test manual config entry setup."""
    from custom_components.whenhub import async_setup_entry
    
    # Add the entry to hass
    trip_config_entry.add_to_hass(hass)
    
    # Try to setup directly
    result = await async_setup_entry(hass, trip_config_entry)
    await hass.async_block_till_done()
    
    assert result is True
    print("✅ Direct config entry setup works")