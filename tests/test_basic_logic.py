"""Basic logic tests that work without Home Assistant."""
import pytest
from freezegun import freeze_time
from datetime import date, timedelta
import sys
import os

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import our modules directly
from custom_components.whenhub.const import SPECIAL_EVENTS


def test_special_events_structure():
    """Test that special events are properly defined."""
    assert "christmas_eve" in SPECIAL_EVENTS
    assert SPECIAL_EVENTS["christmas_eve"]["name"] == "Heilig Abend"
    assert SPECIAL_EVENTS["christmas_eve"]["month"] == 12
    assert SPECIAL_EVENTS["christmas_eve"]["day"] == 24
    
    # Test Easter is calculated type
    assert SPECIAL_EVENTS["easter"]["type"] == "calculated"
    assert SPECIAL_EVENTS["easter"]["calculation"] == "easter"


def test_date_calculations():
    """Test basic date calculation logic."""
    # Test days until calculation
    with freeze_time("2026-12-01"):
        today = date(2026, 12, 1)
        christmas = date(2026, 12, 24)
        days_until = (christmas - today).days
        assert days_until == 23
        
    # Test anniversary year calculation  
    with freeze_time("2026-05-20"):
        original_date = date(2010, 5, 20)
        today = date(2026, 5, 20)
        years_passed = today.year - original_date.year
        assert years_passed == 16


def test_countdown_text_formatting():
    """Test German countdown text formatting logic."""
    # This would normally be in the sensor module
    def format_countdown(days: int) -> str:
        if days <= 0:
            return "0 Tage"
        elif days == 1:
            return "1 Tag"
        else:
            return f"{days} Tage"
    
    assert format_countdown(0) == "0 Tage"
    assert format_countdown(1) == "1 Tag"
    assert format_countdown(5) == "5 Tage"
    assert format_countdown(-5) == "0 Tage"


def test_leap_year_handling():
    """Test leap year date handling."""
    # Test leap year detection
    assert date(2024, 2, 29)  # Should not raise - 2024 is leap year
    
    # Non-leap year should use Feb 28
    with pytest.raises(ValueError):
        date(2023, 2, 29)  # Should raise - 2023 is not leap year
        
    # Anniversary on Feb 29 in non-leap year
    original = date(2020, 2, 29)  # Leap year
    
    # Calculate next anniversary in non-leap year
    def get_anniversary_date(original_date: date, target_year: int) -> date:
        try:
            return date(target_year, original_date.month, original_date.day)
        except ValueError:
            # Feb 29 in non-leap year -> use Feb 28
            if original_date.month == 2 and original_date.day == 29:
                return date(target_year, 2, 28)
            raise
    
    assert get_anniversary_date(original, 2023) == date(2023, 2, 28)
    assert get_anniversary_date(original, 2024) == date(2024, 2, 29)


if __name__ == "__main__":
    # Run tests directly without pytest
    print("Running basic logic tests...")
    
    test_special_events_structure()
    print("✓ Special events structure")
    
    test_date_calculations()
    print("✓ Date calculations")
    
    test_countdown_text_formatting()
    print("✓ Countdown text formatting")
    
    test_leap_year_handling()
    print("✓ Leap year handling")
    
    print("\nAll basic tests passed! ✅")