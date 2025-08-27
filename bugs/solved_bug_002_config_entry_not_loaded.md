# Bug #002: Config Entry Not Loaded - Manual Setup API Test Failure

## Status: ✅ FIXED (2025-08-26)

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

## Fix Applied
Changed test to use proper Home Assistant setup flow:
```python
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
# Result: 1 passed
```

## Impact
- 1 test now passing (previously failed)
- Test suite achieves 100% success rate (25/25 tests passing)
- Test properly validates integration setup flow