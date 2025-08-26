# Bug #001: Special Events KeyError - Missing 'christmas' Key

## Status: ✅ FIXED (2025-08-26)

## Summary
The Special Events sensor crashes when trying to access a non-existent 'christmas' key in the SPECIAL_EVENTS dictionary, causing all Special Event tests to fail.

## Severity
High - Complete feature failure for Special Events

## Discovery
Found during pytest test suite execution on 2025-08-26 while setting up comprehensive testing infrastructure for WhenHub integration.

## Root Cause
In `custom_components/whenhub/sensors/special.py`, lines 52-53:
```python
self._special_type = event_data.get(CONF_SPECIAL_TYPE, "christmas")
self._special_info = SPECIAL_EVENTS.get(self._special_type, SPECIAL_EVENTS["christmas"])
```

The fallback attempts to access `SPECIAL_EVENTS["christmas"]`, but the dictionary only contains:
- `christmas_eve`
- `christmas_day`
- Other special events

No key named `"christmas"` exists.

## Affected Tests
1. `tests/test_binary_today.py::test_special_christmas_is_today`
2. `tests/test_binary_today.py::test_special_christmas_not_today`
3. `tests/test_manifest_and_setup.py::test_special_setup_creates_entities`
4. `tests/test_sensor_countdown.py::test_special_christmas_countdown`

## Error Message
```
ERROR    custom_components.whenhub.sensor:sensor.py:79 Error setting up sensors for Weihnachts-Countdown: 'christmas'
ERROR    custom_components.whenhub.binary_sensor:binary_sensor.py:91 Error setting up binary sensors for Weihnachts-Countdown: 'christmas'
```

## Fix Applied
Changed default and fallback from "christmas" to "christmas_eve" in:
- `custom_components/whenhub/sensors/special.py` (line 52-53)
- `custom_components/whenhub/binary_sensor.py` (line 442-443)

## Test Verification
After fix, all 4 Special Event tests pass:
```bash
python -m pytest -k "special" -v
# Result: 5 passed (includes test_special_events_structure)
```

## Impact
- 4 tests now passing (previously failed)
- Special Events feature fully functional
- Test success rate increased from 80% to 96%