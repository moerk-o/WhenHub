#!/bin/bash
source .venv/bin/activate

echo "=== INDIVIDUAL TEST RESULTS ==="

# Basic Logic Tests
echo "1. test_basic_logic.py::test_special_events_structure"
python -m pytest tests/test_basic_logic.py::test_special_events_structure -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "2. test_basic_logic.py::test_date_calculations"
python -m pytest tests/test_basic_logic.py::test_date_calculations -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "3. test_basic_logic.py::test_countdown_text_formatting"
python -m pytest tests/test_basic_logic.py::test_countdown_text_formatting -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "4. test_basic_logic.py::test_leap_year_handling"
python -m pytest tests/test_basic_logic.py::test_leap_year_handling -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

# Binary Today Tests
echo "5. test_binary_today.py::test_trip_starts_today"
python -m pytest tests/test_binary_today.py::test_trip_starts_today -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "6. test_binary_today.py::test_trip_ends_today"
python -m pytest tests/test_binary_today.py::test_trip_ends_today -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "7. test_binary_today.py::test_milestone_is_today_true"
python -m pytest tests/test_binary_today.py::test_milestone_is_today_true -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "8. test_binary_today.py::test_milestone_is_today_false"
python -m pytest tests/test_binary_today.py::test_milestone_is_today_false -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "9. test_binary_today.py::test_anniversary_is_today"
python -m pytest tests/test_binary_today.py::test_anniversary_is_today -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "10. test_binary_today.py::test_special_christmas_is_today"
python -m pytest tests/test_binary_today.py::test_special_christmas_is_today -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "11. test_binary_today.py::test_special_christmas_not_today"
python -m pytest tests/test_binary_today.py::test_special_christmas_not_today -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

# Debug Path Test
echo "12. test_debug_path.py::test_debug_paths"
python -m pytest tests/test_debug_path.py::test_debug_paths -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

# Manifest Tests
echo "13. test_manifest_and_setup.py::test_trip_setup_creates_entities"
python -m pytest tests/test_manifest_and_setup.py::test_trip_setup_creates_entities -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "14. test_manifest_and_setup.py::test_milestone_setup_creates_entities"
python -m pytest tests/test_manifest_and_setup.py::test_milestone_setup_creates_entities -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "15. test_manifest_and_setup.py::test_anniversary_setup_creates_entities"
python -m pytest tests/test_manifest_and_setup.py::test_anniversary_setup_creates_entities -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "16. test_manifest_and_setup.py::test_special_setup_creates_entities"
python -m pytest tests/test_manifest_and_setup.py::test_special_setup_creates_entities -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

# Sensor Countdown Tests
echo "17. test_sensor_countdown.py::test_trip_countdown_future_18_days"
python -m pytest tests/test_sensor_countdown.py::test_trip_countdown_future_18_days -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "18. test_sensor_countdown.py::test_trip_active_during_trip"
python -m pytest tests/test_sensor_countdown.py::test_trip_active_during_trip -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "19. test_sensor_countdown.py::test_milestone_countdown_future"
python -m pytest tests/test_sensor_countdown.py::test_milestone_countdown_future -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "20. test_sensor_countdown.py::test_milestone_is_today"
python -m pytest tests/test_sensor_countdown.py::test_milestone_is_today -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "21. test_sensor_countdown.py::test_anniversary_next_occurrence"
python -m pytest tests/test_sensor_countdown.py::test_anniversary_next_occurrence -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "22. test_sensor_countdown.py::test_special_christmas_countdown"
python -m pytest tests/test_sensor_countdown.py::test_special_christmas_countdown -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

# Simple Setup Tests
echo "23. test_simple_setup.py::test_whenhub_integration_loads"
python -m pytest tests/test_simple_setup.py::test_whenhub_integration_loads -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "24. test_simple_setup.py::test_setup_component_minimal"
python -m pytest tests/test_simple_setup.py::test_setup_component_minimal -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"

echo "25. test_simple_setup.py::test_manual_config_entry_setup"
python -m pytest tests/test_simple_setup.py::test_manual_config_entry_setup -v --tb=no 2>/dev/null | grep -E "(PASSED|FAILED)" || echo "ERROR"