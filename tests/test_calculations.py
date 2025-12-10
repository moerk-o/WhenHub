"""Unit tests for calculations.py - pure Python date calculation functions.

These tests verify the calculation logic in isolation, without Home Assistant
dependencies. Uses freezegun to control the current date for deterministic tests.
"""
import pytest
from datetime import date
import sys
import os

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.whenhub.calculations import (
    parse_date,
    days_until,
    days_between,
    trip_left_days,
    trip_left_percent,
    is_trip_active,
    is_date_today,
    countdown_breakdown,
    format_countdown_text,
    anniversary_for_year,
    next_anniversary,
    last_anniversary,
    anniversary_count,
    calculate_easter,
    calculate_pentecost,
    calculate_advent,
    calculate_special_event_date,
    next_special_event,
    last_special_event,
)


class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_iso_string(self):
        """Test parsing ISO date string."""
        result = parse_date("2025-06-15")
        assert result == date(2025, 6, 15)

    def test_parse_date_object(self):
        """Test passing date object returns same object."""
        input_date = date(2025, 6, 15)
        result = parse_date(input_date)
        assert result == input_date

    def test_parse_invalid_string_raises(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError):
            parse_date("invalid-date")

    def test_parse_partial_date_raises(self):
        """Test that partial date raises ValueError."""
        with pytest.raises(ValueError):
            parse_date("2025-06")


class TestDaysUntil:
    """Tests for days_until function."""

    def test_future_date(self):
        """Test days until future date."""
        today = date(2025, 6, 1)
        target = date(2025, 6, 10)
        assert days_until(target, today) == 9

    def test_past_date(self):
        """Test days until past date returns negative."""
        today = date(2025, 6, 10)
        target = date(2025, 6, 1)
        assert days_until(target, today) == -9

    def test_same_date(self):
        """Test days until same date is zero."""
        today = date(2025, 6, 1)
        assert days_until(today, today) == 0


class TestDaysBetween:
    """Tests for days_between function."""

    def test_multi_day_range(self):
        """Test days between includes both start and end."""
        start = date(2025, 6, 1)
        end = date(2025, 6, 10)
        assert days_between(start, end) == 10

    def test_single_day(self):
        """Test same start and end is 1 day."""
        day = date(2025, 6, 1)
        assert days_between(day, day) == 1


class TestTripCalculations:
    """Tests for trip-related calculations."""

    def test_trip_left_days_before_trip(self):
        """Test days left before trip starts."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        today = date(2025, 6, 5)
        assert trip_left_days(start, end, today) == 0

    def test_trip_left_days_during_trip(self):
        """Test days left during active trip."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        today = date(2025, 6, 15)
        assert trip_left_days(start, end, today) == 6  # 15-20 inclusive

    def test_trip_left_days_on_last_day(self):
        """Test days left on last day of trip."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        today = date(2025, 6, 20)
        assert trip_left_days(start, end, today) == 1

    def test_trip_left_days_after_trip(self):
        """Test days left after trip ends."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        today = date(2025, 6, 25)
        assert trip_left_days(start, end, today) == 0

    def test_trip_left_percent_before_trip(self):
        """Test percent left before trip is 100%."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        today = date(2025, 6, 5)
        assert trip_left_percent(start, end, today) == 100.0

    def test_trip_left_percent_after_trip(self):
        """Test percent left after trip is 0%."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        today = date(2025, 6, 25)
        assert trip_left_percent(start, end, today) == 0.0

    def test_trip_left_percent_during_trip(self):
        """Test percent left during trip."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        today = date(2025, 6, 15)  # 5 days in, 5 to go
        result = trip_left_percent(start, end, today)
        assert 40 < result < 60  # Approximately 50%

    def test_trip_left_percent_single_day(self):
        """Test percent for single day trip."""
        day = date(2025, 6, 10)
        assert trip_left_percent(day, day, date(2025, 6, 9)) == 100.0
        assert trip_left_percent(day, day, date(2025, 6, 10)) == 100.0
        assert trip_left_percent(day, day, date(2025, 6, 11)) == 0.0

    def test_is_trip_active_before(self):
        """Test trip not active before start."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        today = date(2025, 6, 5)
        assert is_trip_active(start, end, today) is False

    def test_is_trip_active_during(self):
        """Test trip active during period."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        today = date(2025, 6, 15)
        assert is_trip_active(start, end, today) is True

    def test_is_trip_active_on_start(self):
        """Test trip active on start date."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        assert is_trip_active(start, end, start) is True

    def test_is_trip_active_on_end(self):
        """Test trip active on end date."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        assert is_trip_active(start, end, end) is True

    def test_is_trip_active_after(self):
        """Test trip not active after end."""
        start = date(2025, 6, 10)
        end = date(2025, 6, 20)
        today = date(2025, 6, 25)
        assert is_trip_active(start, end, today) is False


class TestIsDateToday:
    """Tests for is_date_today function."""

    def test_same_date(self):
        """Test same date returns True."""
        day = date(2025, 6, 15)
        assert is_date_today(day, day) is True

    def test_different_date(self):
        """Test different date returns False."""
        target = date(2025, 6, 15)
        today = date(2025, 6, 16)
        assert is_date_today(target, today) is False


class TestCountdownBreakdown:
    """Tests for countdown_breakdown function."""

    def test_past_date_returns_zeros(self):
        """Test past date returns all zeros."""
        target = date(2025, 6, 1)
        today = date(2025, 6, 15)
        result = countdown_breakdown(target, today)
        assert result == {"years": 0, "months": 0, "weeks": 0, "days": 0}

    def test_same_date_returns_zeros(self):
        """Test same date returns all zeros."""
        day = date(2025, 6, 15)
        result = countdown_breakdown(day, day)
        assert result == {"years": 0, "months": 0, "weeks": 0, "days": 0}

    def test_few_days(self):
        """Test a few days breakdown."""
        today = date(2025, 6, 1)
        target = date(2025, 6, 5)
        result = countdown_breakdown(target, today)
        assert result["days"] == 4
        assert result["weeks"] == 0
        assert result["months"] == 0
        assert result["years"] == 0

    def test_weeks_and_days(self):
        """Test weeks and days breakdown."""
        today = date(2025, 6, 1)
        target = date(2025, 6, 20)  # 19 days = 2 weeks + 5 days
        result = countdown_breakdown(target, today)
        assert result["weeks"] == 2
        assert result["days"] == 5

    def test_year_plus(self):
        """Test over a year breakdown."""
        today = date(2025, 1, 1)
        target = date(2026, 7, 15)  # About 1.5 years
        result = countdown_breakdown(target, today)
        assert result["years"] >= 1


class TestFormatCountdownText:
    """Tests for format_countdown_text function."""

    def test_past_date_returns_zero(self):
        """Test past date returns '0 Tage'."""
        target = date(2025, 6, 1)
        today = date(2025, 6, 15)
        assert format_countdown_text(target, today) == "0 Tage"

    def test_same_date_returns_zero(self):
        """Test same date returns '0 Tage'."""
        day = date(2025, 6, 15)
        assert format_countdown_text(day, day) == "0 Tage"

    def test_singular_day(self):
        """Test singular 'Tag'."""
        today = date(2025, 6, 1)
        target = date(2025, 6, 2)
        result = format_countdown_text(target, today)
        assert "1 Tag" in result

    def test_plural_days(self):
        """Test plural 'Tage'."""
        today = date(2025, 6, 1)
        target = date(2025, 6, 5)
        result = format_countdown_text(target, today)
        assert "4 Tage" in result

    def test_singular_week(self):
        """Test singular 'Woche'."""
        today = date(2025, 6, 1)
        target = date(2025, 6, 8)  # 7 days = 1 week
        result = format_countdown_text(target, today)
        assert "1 Woche" in result

    def test_singular_month(self):
        """Test singular 'Monat'."""
        today = date(2025, 6, 1)
        target = date(2025, 7, 1)  # 30 days = 1 month
        result = format_countdown_text(target, today)
        assert "1 Monat" in result

    def test_singular_year(self):
        """Test singular 'Jahr'."""
        today = date(2025, 1, 1)
        target = date(2026, 1, 1)  # 365 days = 1 year
        result = format_countdown_text(target, today)
        assert "1 Jahr" in result

    def test_complex_countdown(self):
        """Test complex countdown with multiple components."""
        today = date(2025, 1, 1)
        target = date(2027, 5, 15)  # About 2 years, 4 months, etc.
        result = format_countdown_text(target, today)
        assert "Jahre" in result  # Plural


class TestAnniversaryForYear:
    """Tests for anniversary_for_year function."""

    def test_normal_date(self):
        """Test normal date anniversary."""
        original = date(2000, 6, 15)
        result = anniversary_for_year(original, 2025)
        assert result == date(2025, 6, 15)

    def test_leap_year_birthday_in_leap_year(self):
        """Test Feb 29 birthday in leap year."""
        original = date(2000, 2, 29)
        result = anniversary_for_year(original, 2024)  # 2024 is leap year
        assert result == date(2024, 2, 29)

    def test_leap_year_birthday_in_non_leap_year(self):
        """Test Feb 29 birthday in non-leap year falls back to Feb 28."""
        original = date(2000, 2, 29)
        result = anniversary_for_year(original, 2025)  # 2025 is not leap year
        assert result == date(2025, 2, 28)


class TestNextAnniversary:
    """Tests for next_anniversary function."""

    def test_anniversary_this_year_future(self):
        """Test anniversary later this year."""
        original = date(2000, 12, 25)
        today = date(2025, 6, 15)
        result = next_anniversary(original, today)
        assert result == date(2025, 12, 25)

    def test_anniversary_this_year_past(self):
        """Test anniversary already passed this year."""
        original = date(2000, 3, 15)
        today = date(2025, 6, 15)
        result = next_anniversary(original, today)
        assert result == date(2026, 3, 15)

    def test_anniversary_today(self):
        """Test anniversary is today."""
        original = date(2000, 6, 15)
        today = date(2025, 6, 15)
        result = next_anniversary(original, today)
        assert result == date(2025, 6, 15)


class TestLastAnniversary:
    """Tests for last_anniversary function."""

    def test_original_in_future(self):
        """Test original date in future returns None."""
        original = date(2030, 6, 15)
        today = date(2025, 6, 15)
        result = last_anniversary(original, today)
        assert result is None

    def test_anniversary_this_year_passed(self):
        """Test anniversary passed this year."""
        original = date(2000, 3, 15)
        today = date(2025, 6, 15)
        result = last_anniversary(original, today)
        assert result == date(2025, 3, 15)

    def test_anniversary_today(self):
        """Test anniversary is today returns today."""
        original = date(2000, 6, 15)
        today = date(2025, 6, 15)
        result = last_anniversary(original, today)
        assert result == date(2025, 6, 15)

    def test_anniversary_not_yet_this_year(self):
        """Test anniversary not yet this year returns last year."""
        original = date(2000, 12, 25)
        today = date(2025, 6, 15)
        result = last_anniversary(original, today)
        assert result == date(2024, 12, 25)


class TestAnniversaryCount:
    """Tests for anniversary_count function."""

    def test_future_original(self):
        """Test future original date returns 0."""
        original = date(2030, 6, 15)
        today = date(2025, 6, 15)
        assert anniversary_count(original, today) == 0

    def test_first_year(self):
        """Test first occurrence counts as 1."""
        original = date(2025, 1, 1)
        today = date(2025, 6, 15)
        assert anniversary_count(original, today) == 1

    def test_multi_year(self):
        """Test multiple years count correctly."""
        original = date(2020, 6, 15)
        today = date(2025, 6, 15)  # 5th anniversary
        assert anniversary_count(original, today) == 6  # Original + 5 anniversaries


class TestEasterCalculation:
    """Tests for calculate_easter function."""

    def test_easter_2025(self):
        """Test Easter 2025."""
        result = calculate_easter(2025)
        assert result == date(2025, 4, 20)

    def test_easter_2026(self):
        """Test Easter 2026."""
        result = calculate_easter(2026)
        assert result == date(2026, 4, 5)

    def test_easter_2027(self):
        """Test Easter 2027."""
        result = calculate_easter(2027)
        assert result == date(2027, 3, 28)


class TestPentecostCalculation:
    """Tests for calculate_pentecost function."""

    def test_pentecost_2025(self):
        """Test Pentecost 2025 is 49 days after Easter."""
        result = calculate_pentecost(2025)
        easter = calculate_easter(2025)
        assert result == date(2025, 6, 8)
        assert (result - easter).days == 49


class TestAdventCalculation:
    """Tests for calculate_advent function."""

    def test_advent_4_2025(self):
        """Test 4th Advent 2025."""
        result = calculate_advent(2025, 4)
        assert result == date(2025, 12, 21)

    def test_advent_1_2025(self):
        """Test 1st Advent 2025."""
        result = calculate_advent(2025, 1)
        assert result == date(2025, 11, 30)

    def test_invalid_advent_number(self):
        """Test invalid Advent number returns None."""
        assert calculate_advent(2025, 0) is None
        assert calculate_advent(2025, 5) is None


class TestSpecialEventDate:
    """Tests for calculate_special_event_date function."""

    def test_fixed_event(self):
        """Test fixed date event."""
        info = {"type": "fixed", "month": 12, "day": 24}
        result = calculate_special_event_date(info, 2025)
        assert result == date(2025, 12, 24)

    def test_calculated_easter(self):
        """Test calculated Easter event."""
        info = {"type": "calculated", "calculation": "easter"}
        result = calculate_special_event_date(info, 2025)
        assert result == date(2025, 4, 20)

    def test_calculated_pentecost(self):
        """Test calculated Pentecost event."""
        info = {"type": "calculated", "calculation": "pentecost"}
        result = calculate_special_event_date(info, 2025)
        assert result == date(2025, 6, 8)

    def test_calculated_advent(self):
        """Test calculated Advent event."""
        info = {"type": "calculated", "calculation": "advent_1"}
        result = calculate_special_event_date(info, 2025)
        assert result == date(2025, 11, 30)


class TestNextSpecialEvent:
    """Tests for next_special_event function."""

    def test_event_later_this_year(self):
        """Test event later this year."""
        info = {"type": "fixed", "month": 12, "day": 24}
        today = date(2025, 6, 15)
        result = next_special_event(info, today)
        assert result == date(2025, 12, 24)

    def test_event_already_passed(self):
        """Test event already passed this year."""
        info = {"type": "fixed", "month": 1, "day": 1}
        today = date(2025, 6, 15)
        result = next_special_event(info, today)
        assert result == date(2026, 1, 1)

    def test_event_today(self):
        """Test event is today."""
        info = {"type": "fixed", "month": 6, "day": 15}
        today = date(2025, 6, 15)
        result = next_special_event(info, today)
        assert result == date(2025, 6, 15)


class TestLastSpecialEvent:
    """Tests for last_special_event function."""

    def test_event_earlier_this_year(self):
        """Test event earlier this year."""
        info = {"type": "fixed", "month": 1, "day": 1}
        today = date(2025, 6, 15)
        result = last_special_event(info, today)
        assert result == date(2025, 1, 1)

    def test_event_not_yet_this_year(self):
        """Test event not yet this year."""
        info = {"type": "fixed", "month": 12, "day": 24}
        today = date(2025, 6, 15)
        result = last_special_event(info, today)
        assert result == date(2024, 12, 24)
