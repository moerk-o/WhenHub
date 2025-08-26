# WhenHub Integration - Bug Tracking

## Overview
This directory contains documented bugs found in the WhenHub Home Assistant integration during testing setup on 2025-08-26.

## Bug List

| Bug # | Title | Severity | Status | Tests Affected |
|-------|-------|----------|--------|----------------|
| 001 | [Special Events KeyError - Missing 'christmas' Key](bug_001_special_events_keyerror.md) | High | Open | 4 |
| 002 | [Config Entry Not Loaded - Manual Setup API Test Failure](bug_002_config_entry_not_loaded.md) | Low | Open | 1 |

## Test Suite Status
- **Total Tests:** 25
- **Passing:** 20 (80%)
- **Failing:** 5 (20%)

## Bug Categories

### Integration Bugs (Critical)
- Bug #001: Prevents entire Special Events feature from functioning

### Test Infrastructure Issues (Non-Critical)
- Bug #002: Only affects API testing, not actual functionality

## Testing Environment
- Home Assistant: 2025.1.4
- Python: 3.12.3
- pytest-homeassistant-custom-component: 0.13.205
- Platform: WSL2 Linux

## How to Run Tests
```bash
# All tests except known failures
python -m pytest -v -k "not (special or manual_config_entry)"

# Specific bug reproduction
python -m pytest tests/test_binary_today.py::test_special_christmas_is_today -v
```