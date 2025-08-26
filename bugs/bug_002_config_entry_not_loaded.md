# Bug #002: Config Entry Not Loaded - Manual Setup API Test Failure

## Summary
Direct call to `async_setup_entry()` fails because the config entry is not in the LOADED state when called manually in tests.

## Severity
Low - Only affects direct API testing, not actual integration functionality

## Discovery
Found during pytest test suite execution on 2025-08-26 while testing the integration's internal API.

## Root Cause
In `tests/test_simple_setup.py::test_manual_config_entry_setup`, line 39:
```python
result = await async_setup_entry(hass, trip_config_entry)
```

The test attempts to call `async_setup_entry()` directly, but Home Assistant requires the config entry to be in `ConfigEntryState.LOADED` state before forwarding platform setups.

## Affected Tests
1. `tests/test_simple_setup.py::test_manual_config_entry_setup`

## Error Message
```
homeassistant.config_entries.OperationNotAllowed: The config entry 'Mock Title' (whenhub) 
with entry_id '01K3K1DYM6RCE4EVRPBDH3Q932' cannot forward setup for 
[<Platform.SENSOR: 'sensor'>, <Platform.IMAGE: 'image'>, <Platform.BINARY_SENSOR: 'binary_sensor'>] 
because it is in state ConfigEntryState.NOT_LOADED, but needs to be in the ConfigEntryState.LOADED state
```

## Reproduction Steps
1. Set up test environment
2. Run the specific test:
```bash
source .venv/bin/activate
python -m pytest tests/test_simple_setup.py::test_manual_config_entry_setup -v
```

## Expected Behavior
The test should properly set up the config entry through Home Assistant's normal flow rather than calling the internal API directly.

## Proposed Fix
Option 1: Remove the test (recommended)
- This test is testing Home Assistant's internal API behavior, not the integration itself

Option 2: Fix the test to use proper setup flow:
```python
@pytest.mark.asyncio
async def test_manual_config_entry_setup(hass: HomeAssistant, trip_config_entry):
    """Test manual config entry setup."""
    trip_config_entry.add_to_hass(hass)
    
    # Use the proper Home Assistant setup flow
    assert await hass.config_entries.async_setup(trip_config_entry.entry_id)
    await hass.async_block_till_done()
    
    # Verify the entry is loaded
    assert trip_config_entry.state == ConfigEntryState.LOADED
```

## Test Verification
After fix:
```bash
python -m pytest tests/test_simple_setup.py::test_manual_config_entry_setup -v
```

## Impact
- 1 test failing (4% of test suite)
- No impact on actual integration functionality
- Only affects direct API testing scenario