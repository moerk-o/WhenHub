"""Unit tests for FR09 Custom Pattern calculations.

Tests cover all frequency types (yearly, monthly, weekly, daily),
day rules (nth_weekday, last_weekday, fixed_day), end conditions
(none, until, count), EXDATE via rruleset, and occurrence counting.
"""
import pytest
from datetime import date
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.whenhub.calculations import (
    build_rrule_from_config,
    next_custom_pattern,
    last_custom_pattern,
    occurrence_count_custom_pattern,
    custom_pattern_occurrences,
)


# =============================================================================
# Helpers
# =============================================================================

def _cfg(**kwargs) -> dict:
    """Build a minimal config dict with sensible defaults."""
    defaults = {
        "cp_freq": "yearly",
        "cp_interval": 1,
        "cp_dtstart": "2020-01-01",
        "cp_day_rule": None,
        "cp_bymonth": None,
        "cp_byday_pos": None,
        "cp_byday_weekday": None,
        "cp_bymonthday": None,
        "cp_byday_list": [],
        "cp_end_type": "none",
        "cp_until": None,
        "cp_count": None,
        "cp_exdates": [],
    }
    defaults.update(kwargs)
    return defaults


# =============================================================================
# YEARLY — Nth Weekday
# =============================================================================

class TestYearlyNthWeekday:
    """FREQ=YEARLY;BYMONTH=11;BYDAY=+4TH — Thanksgiving (4th Thursday November)."""

    def _thanksgiving_cfg(self, dtstart="2020-01-01"):
        return _cfg(
            cp_freq="yearly",
            cp_dtstart=dtstart,
            cp_bymonth=11,
            cp_day_rule="nth_weekday",
            cp_byday_pos=4,
            cp_byday_weekday=3,  # Thursday
        )

    def test_next_from_before(self):
        # From early 2026, next Thanksgiving is 2026-11-26
        result = next_custom_pattern(self._thanksgiving_cfg(), date(2026, 1, 1))
        assert result == date(2026, 11, 26)

    def test_next_on_the_day(self):
        # On Thanksgiving itself, next = today
        result = next_custom_pattern(self._thanksgiving_cfg(), date(2026, 11, 26))
        assert result == date(2026, 11, 26)

    def test_next_day_after(self):
        # Day after Thanksgiving 2026 → next is Thanksgiving 2027 = 2027-11-25
        result = next_custom_pattern(self._thanksgiving_cfg(), date(2026, 11, 27))
        assert result == date(2027, 11, 25)

    def test_last_before(self):
        # From Jan 2026, last Thanksgiving was 2025-11-27
        result = last_custom_pattern(self._thanksgiving_cfg(), date(2026, 1, 1))
        assert result == date(2025, 11, 27)

    def test_last_on_the_day(self):
        result = last_custom_pattern(self._thanksgiving_cfg(), date(2026, 11, 26))
        assert result == date(2026, 11, 26)

    def test_occurrence_count(self):
        # dtstart 2020-01-01, today 2026-11-26 → occurrences: 2020,2021,2022,2023,2024,2025,2026 = 7
        result = occurrence_count_custom_pattern(self._thanksgiving_cfg(), date(2026, 11, 26))
        assert result == 7

    def test_occurrence_count_before_first(self):
        # Before first occurrence of 2020
        result = occurrence_count_custom_pattern(self._thanksgiving_cfg(), date(2020, 1, 1))
        assert result == 0

    def test_calendar_occurrences_in_year(self):
        cfg = self._thanksgiving_cfg()
        occurrences = custom_pattern_occurrences(cfg, date(2026, 1, 1), date(2026, 12, 31))
        assert occurrences == [date(2026, 11, 26)]

    def test_calendar_occurrences_multi_year(self):
        cfg = self._thanksgiving_cfg()
        occurrences = custom_pattern_occurrences(cfg, date(2025, 1, 1), date(2026, 12, 31))
        assert date(2025, 11, 27) in occurrences
        assert date(2026, 11, 26) in occurrences
        assert len(occurrences) == 2


# =============================================================================
# YEARLY — Last Weekday
# =============================================================================

class TestYearlyLastWeekday:
    """FREQ=YEARLY;BYMONTH=5;BYDAY=-1MO — Last Monday in May (Memorial Day)."""

    def _memorial_cfg(self):
        return _cfg(
            cp_freq="yearly",
            cp_dtstart="2020-01-01",
            cp_bymonth=5,
            cp_day_rule="last_weekday",
            cp_byday_weekday=0,  # Monday
        )

    def test_next_memorial_day_2026(self):
        # Last Monday in May 2026 = 2026-05-25
        result = next_custom_pattern(self._memorial_cfg(), date(2026, 1, 1))
        assert result == date(2026, 5, 25)

    def test_last_memorial_day(self):
        result = last_custom_pattern(self._memorial_cfg(), date(2026, 6, 1))
        assert result == date(2026, 5, 25)


# =============================================================================
# YEARLY — Fixed Day
# =============================================================================

class TestYearlyFixedDay:
    """FREQ=YEARLY;BYMONTH=12;BYMONTHDAY=24 — Christmas Eve."""

    def _christmas_cfg(self):
        return _cfg(
            cp_freq="yearly",
            cp_dtstart="2020-01-01",
            cp_bymonth=12,
            cp_day_rule="fixed_day",
            cp_bymonthday=24,
        )

    def test_next_christmas_eve(self):
        result = next_custom_pattern(self._christmas_cfg(), date(2026, 1, 1))
        assert result == date(2026, 12, 24)

    def test_next_christmas_eve_on_the_day(self):
        result = next_custom_pattern(self._christmas_cfg(), date(2026, 12, 24))
        assert result == date(2026, 12, 24)

    def test_occurrence_count_christmas(self):
        # dtstart 2020-01-01, today 2026-12-24 → 7 occurrences (2020..2026)
        result = occurrence_count_custom_pattern(self._christmas_cfg(), date(2026, 12, 24))
        assert result == 7


# =============================================================================
# MONTHLY — Nth Weekday
# =============================================================================

class TestMonthlyNthWeekday:
    """FREQ=MONTHLY;BYDAY=+1MO — First Monday of every month."""

    def _first_monday_cfg(self):
        return _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-01-01",
            cp_day_rule="nth_weekday",
            cp_byday_pos=1,
            cp_byday_weekday=0,  # Monday
        )

    def test_next_from_start_of_april(self):
        # First Monday in April 2026 = 2026-04-06
        result = next_custom_pattern(self._first_monday_cfg(), date(2026, 4, 1))
        assert result == date(2026, 4, 6)

    def test_next_after_first_monday(self):
        # After April 6 → first Monday in May 2026 = 2026-05-04
        result = next_custom_pattern(self._first_monday_cfg(), date(2026, 4, 7))
        assert result == date(2026, 5, 4)

    def test_last_first_monday(self):
        result = last_custom_pattern(self._first_monday_cfg(), date(2026, 4, 7))
        assert result == date(2026, 4, 6)

    def test_occurrence_count_monthly(self):
        # dtstart 2026-01-01, first occurrence Jan 5 2026
        # Up to and including Apr 6 2026: Jan, Feb, Mar, Apr = 4 occurrences
        cfg = self._first_monday_cfg()
        result = occurrence_count_custom_pattern(cfg, date(2026, 4, 6))
        assert result == 4

    def test_calendar_occurrences_quarter(self):
        cfg = self._first_monday_cfg()
        occurrences = custom_pattern_occurrences(cfg, date(2026, 1, 1), date(2026, 3, 31))
        # Jan 5, Feb 2, Mar 2
        assert date(2026, 1, 5) in occurrences
        assert date(2026, 2, 2) in occurrences
        assert date(2026, 3, 2) in occurrences
        assert len(occurrences) == 3


# =============================================================================
# MONTHLY — Last Weekday
# =============================================================================

class TestMonthlyLastWeekday:
    """FREQ=MONTHLY;BYDAY=-1FR — Last Friday of every month."""

    def _last_friday_cfg(self):
        return _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-01-01",
            cp_day_rule="last_weekday",
            cp_byday_weekday=4,  # Friday
        )

    def test_last_friday_april_2026(self):
        # Last Friday in April 2026 = 2026-04-24
        result = next_custom_pattern(self._last_friday_cfg(), date(2026, 4, 1))
        assert result == date(2026, 4, 24)


# =============================================================================
# MONTHLY — Fixed Day
# =============================================================================

class TestMonthlyFixedDay:
    """FREQ=MONTHLY;BYMONTHDAY=15 — 15th of every month."""

    def _fifteenth_cfg(self):
        return _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-01-01",
            cp_day_rule="fixed_day",
            cp_bymonthday=15,
        )

    def test_next_15th(self):
        result = next_custom_pattern(self._fifteenth_cfg(), date(2026, 4, 1))
        assert result == date(2026, 4, 15)

    def test_next_15th_after(self):
        result = next_custom_pattern(self._fifteenth_cfg(), date(2026, 4, 16))
        assert result == date(2026, 5, 15)


# =============================================================================
# WEEKLY
# =============================================================================

class TestWeekly:
    """FREQ=WEEKLY;BYDAY=MO,WE,FR — Every Monday, Wednesday, Friday."""

    def _mwf_cfg(self):
        return _cfg(
            cp_freq="weekly",
            cp_dtstart="2026-01-01",
            cp_byday_list=[0, 2, 4],  # Mo, We, Fr
        )

    def test_next_from_sunday(self):
        # Sunday 2026-04-05 → next is Monday 2026-04-06
        result = next_custom_pattern(self._mwf_cfg(), date(2026, 4, 5))
        assert result == date(2026, 4, 6)

    def test_next_from_monday(self):
        # Monday 2026-04-06 → next is today (inclusive)
        result = next_custom_pattern(self._mwf_cfg(), date(2026, 4, 6))
        assert result == date(2026, 4, 6)

    def test_next_from_tuesday(self):
        # Tuesday 2026-04-07 → next is Wednesday 2026-04-08
        result = next_custom_pattern(self._mwf_cfg(), date(2026, 4, 7))
        assert result == date(2026, 4, 8)

    def test_last_from_saturday(self):
        # Saturday 2026-04-11 → last occurrence was Friday 2026-04-10
        result = last_custom_pattern(self._mwf_cfg(), date(2026, 4, 11))
        assert result == date(2026, 4, 10)

    def test_single_weekday_weekly(self):
        """FREQ=WEEKLY;BYDAY=MO — Every Monday."""
        cfg = _cfg(
            cp_freq="weekly",
            cp_dtstart="2026-01-01",
            cp_byday_list=[0],  # Monday only
        )
        result = next_custom_pattern(cfg, date(2026, 4, 7))  # Tuesday
        assert result == date(2026, 4, 13)

    def test_occurrence_count_weekly_mwf(self):
        # dtstart 2026-01-01 (Thursday), first occurrence Mon 2026-01-05
        # Count Mo+We+Fr occurrences from Jan 1 to Apr 6 (Monday)
        # Jan: 5,7,9,12,14,16,19,21,23,26,28,30 = 12 (Mo+We+Fr in Jan = ~13)
        # Let's just check it's a reasonable number and includes today
        cfg = self._mwf_cfg()
        count = occurrence_count_custom_pattern(cfg, date(2026, 4, 6))
        assert count > 0
        # Verify Apr 6 (Monday) is counted
        count_before = occurrence_count_custom_pattern(cfg, date(2026, 4, 5))
        assert count == count_before + 1


# =============================================================================
# WEEKLY — With Interval
# =============================================================================

class TestWeeklyInterval:
    """FREQ=WEEKLY;INTERVAL=2;BYDAY=MO — Every other Monday."""

    def _biweekly_monday_cfg(self):
        return _cfg(
            cp_freq="weekly",
            cp_interval=2,
            cp_dtstart="2026-04-06",  # Monday April 6 = anchor
            cp_byday_list=[0],        # Monday
        )

    def test_first_occurrence_is_anchor(self):
        result = next_custom_pattern(self._biweekly_monday_cfg(), date(2026, 4, 6))
        assert result == date(2026, 4, 6)

    def test_next_biweekly_skips_one_monday(self):
        # After Apr 6, next biweekly Monday is Apr 20 (skips Apr 13)
        result = next_custom_pattern(self._biweekly_monday_cfg(), date(2026, 4, 7))
        assert result == date(2026, 4, 20)


# =============================================================================
# DAILY
# =============================================================================

class TestDaily:
    """FREQ=DAILY — Every day and every N days."""

    def test_daily_every_day_next(self):
        cfg = _cfg(cp_freq="daily", cp_interval=1, cp_dtstart="2026-04-01")
        result = next_custom_pattern(cfg, date(2026, 4, 6))
        assert result == date(2026, 4, 6)

    def test_daily_every_3_days(self):
        # Anchor 2026-04-01, +3 days: Apr 4, Apr 7, Apr 10...
        cfg = _cfg(cp_freq="daily", cp_interval=3, cp_dtstart="2026-04-01")
        result = next_custom_pattern(cfg, date(2026, 4, 5))
        assert result == date(2026, 4, 7)

    def test_daily_every_3_days_on_occurrence(self):
        cfg = _cfg(cp_freq="daily", cp_interval=3, cp_dtstart="2026-04-01")
        result = next_custom_pattern(cfg, date(2026, 4, 7))
        assert result == date(2026, 4, 7)

    def test_daily_occurrence_count(self):
        cfg = _cfg(cp_freq="daily", cp_interval=1, cp_dtstart="2026-04-01")
        # Apr 1 to Apr 6 = 6 days
        result = occurrence_count_custom_pattern(cfg, date(2026, 4, 6))
        assert result == 6


# =============================================================================
# End Conditions
# =============================================================================

class TestEndConditions:
    """Tests for UNTIL and COUNT end conditions."""

    def test_count_1_single_occurrence(self):
        """COUNT=1 behaves like a milestone — occurs exactly once."""
        cfg = _cfg(
            cp_freq="yearly",
            cp_dtstart="2026-01-01",
            cp_bymonth=3,
            cp_day_rule="nth_weekday",
            cp_byday_pos=1,
            cp_byday_weekday=1,  # First Tuesday in March
            cp_count=1,
        )
        result = next_custom_pattern(cfg, date(2026, 1, 1))
        assert result == date(2026, 3, 3)  # First Tuesday March 2026

        # After occurrence, rule is exhausted
        result_after = next_custom_pattern(cfg, date(2026, 3, 4))
        assert result_after is None

    def test_count_3_stops_after_3(self):
        cfg = _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-01-01",
            cp_day_rule="fixed_day",
            cp_bymonthday=1,
            cp_count=3,
        )
        # Occurrences: Jan 1, Feb 1, Mar 1
        assert next_custom_pattern(cfg, date(2026, 1, 1)) == date(2026, 1, 1)
        assert next_custom_pattern(cfg, date(2026, 2, 1)) == date(2026, 2, 1)
        assert next_custom_pattern(cfg, date(2026, 3, 1)) == date(2026, 3, 1)
        assert next_custom_pattern(cfg, date(2026, 3, 2)) is None  # exhausted

    def test_until_stops_at_date(self):
        cfg = _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-01-01",
            cp_day_rule="fixed_day",
            cp_bymonthday=15,
            cp_end_type="until",
            cp_until="2026-03-31",
        )
        # Occurrences: Jan 15, Feb 15, Mar 15
        assert next_custom_pattern(cfg, date(2026, 3, 15)) == date(2026, 3, 15)
        assert next_custom_pattern(cfg, date(2026, 3, 16)) is None

    def test_occurrence_count_with_count_limit(self):
        cfg = _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-01-01",
            cp_day_rule="fixed_day",
            cp_bymonthday=1,
            cp_count=3,
        )
        # On Mar 1: all 3 occurrences have fired
        assert occurrence_count_custom_pattern(cfg, date(2026, 3, 1)) == 3


# =============================================================================
# EXDATE (rruleset)
# =============================================================================

class TestExdate:
    """EXDATE excludes specific dates from occurrences."""

    def test_exdate_skips_occurrence(self):
        # Monthly on 1st, but Jan 1 2026 is excluded
        cfg = _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-01-01",
            cp_day_rule="fixed_day",
            cp_bymonthday=1,
            cp_exdates=["2026-01-01"],
        )
        # Jan 1 skipped → next from Jan 1 is Feb 1
        result = next_custom_pattern(cfg, date(2026, 1, 1))
        assert result == date(2026, 2, 1)

    def test_exdate_multiple(self):
        cfg = _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-01-01",
            cp_day_rule="fixed_day",
            cp_bymonthday=1,
            cp_exdates=["2026-01-01", "2026-02-01"],
        )
        result = next_custom_pattern(cfg, date(2026, 1, 1))
        assert result == date(2026, 3, 1)

    def test_exdate_not_matching_skips_nothing(self):
        cfg = _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-01-01",
            cp_day_rule="fixed_day",
            cp_bymonthday=1,
            cp_exdates=["2025-06-15"],  # Past date, not an occurrence
        )
        result = next_custom_pattern(cfg, date(2026, 1, 1))
        assert result == date(2026, 1, 1)

    def test_occurrence_count_with_exdate(self):
        # Monthly on 1st, Jan excluded → Feb 1 + Mar 1 = 2 in range Jan-Mar
        cfg = _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-01-01",
            cp_day_rule="fixed_day",
            cp_bymonthday=1,
            cp_exdates=["2026-01-01"],
        )
        result = occurrence_count_custom_pattern(cfg, date(2026, 3, 1))
        assert result == 2


# =============================================================================
# Calendar Occurrences
# =============================================================================

class TestCalendarOccurrences:
    """Tests for custom_pattern_occurrences() used by Calendar entity."""

    def test_empty_range(self):
        cfg = _cfg(
            cp_freq="yearly",
            cp_dtstart="2020-01-01",
            cp_bymonth=12,
            cp_day_rule="fixed_day",
            cp_bymonthday=24,
        )
        # Range within a year that has no occurrence
        result = custom_pattern_occurrences(cfg, date(2026, 1, 1), date(2026, 12, 23))
        assert result == []

    def test_includes_boundary_dates(self):
        cfg = _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-01-01",
            cp_day_rule="fixed_day",
            cp_bymonthday=1,
        )
        result = custom_pattern_occurrences(cfg, date(2026, 1, 1), date(2026, 3, 1))
        assert date(2026, 1, 1) in result
        assert date(2026, 3, 1) in result

    def test_daily_occurrences_in_week(self):
        cfg = _cfg(cp_freq="daily", cp_interval=1, cp_dtstart="2026-04-01")
        result = custom_pattern_occurrences(cfg, date(2026, 4, 6), date(2026, 4, 10))
        assert len(result) == 5
        assert result[0] == date(2026, 4, 6)
        assert result[-1] == date(2026, 4, 10)

    def test_weekly_occurrences_correct_days(self):
        cfg = _cfg(
            cp_freq="weekly",
            cp_dtstart="2026-01-01",
            cp_byday_list=[0, 4],  # Monday + Friday
        )
        result = custom_pattern_occurrences(cfg, date(2026, 4, 6), date(2026, 4, 12))
        # Mon Apr 6, Fri Apr 10
        assert date(2026, 4, 6) in result
        assert date(2026, 4, 10) in result
        assert len(result) == 2


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge cases: no past occurrences, exhausted rule, interval > 1."""

    def test_no_past_occurrence_returns_none(self):
        # dtstart in the future relative to today
        cfg = _cfg(
            cp_freq="yearly",
            cp_dtstart="2030-01-01",
            cp_bymonth=6,
            cp_day_rule="fixed_day",
            cp_bymonthday=15,
        )
        result = last_custom_pattern(cfg, date(2026, 4, 6))
        assert result is None

    def test_occurrence_count_zero_before_start(self):
        cfg = _cfg(
            cp_freq="monthly",
            cp_dtstart="2026-06-01",
            cp_day_rule="fixed_day",
            cp_bymonthday=1,
        )
        result = occurrence_count_custom_pattern(cfg, date(2026, 4, 6))
        assert result == 0

    def test_exhausted_count_rule_returns_none(self):
        cfg = _cfg(
            cp_freq="daily",
            cp_dtstart="2026-04-01",
            cp_interval=1,
            cp_count=3,
        )
        # Rule fires Apr 1, 2, 3 → exhausted after Apr 3
        assert next_custom_pattern(cfg, date(2026, 4, 4)) is None

    def test_yearly_interval_2(self):
        """FREQ=YEARLY;INTERVAL=2 — Every other year."""
        cfg = _cfg(
            cp_freq="yearly",
            cp_interval=2,
            cp_dtstart="2020-01-01",
            cp_bymonth=6,
            cp_day_rule="fixed_day",
            cp_bymonthday=1,
        )
        # Should fire 2020, 2022, 2024, 2026 (not 2021, 2023, 2025)
        result = next_custom_pattern(cfg, date(2025, 6, 2))
        assert result == date(2026, 6, 1)
