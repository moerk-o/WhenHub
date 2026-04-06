"""Tests for the 9 Custom Pattern example configurations shown in README.md.

Each test verifies that the pattern produces the expected next-occurrence date
for 2026, using the exact configuration documented in the README.
"""
import pytest
from datetime import date
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.whenhub.calculations import next_custom_pattern


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
# Example 1 — Early May Bank Holiday (UK)
# 1st Monday in May — 2026: May 4
# =============================================================================

def test_early_may_bank_holiday_2026():
    cfg = _cfg(
        cp_freq="yearly",
        cp_bymonth=5,
        cp_day_rule="nth_weekday",
        cp_byday_pos=1,
        cp_byday_weekday=0,  # Monday
    )
    result = next_custom_pattern(cfg, date(2026, 1, 1))
    assert result == date(2026, 5, 4), f"Expected 2026-05-04, got {result}"


# =============================================================================
# Example 2 — Mother's Day (DE/AT/CH/UK and many others)
# 2nd Sunday in May — 2026: May 10
# =============================================================================

def test_mothers_day_2026():
    cfg = _cfg(
        cp_freq="yearly",
        cp_bymonth=5,
        cp_day_rule="nth_weekday",
        cp_byday_pos=2,
        cp_byday_weekday=6,  # Sunday
    )
    result = next_custom_pattern(cfg, date(2026, 1, 1))
    assert result == date(2026, 5, 10), f"Expected 2026-05-10, got {result}"


# =============================================================================
# Example 3 — Memorial Day (US)
# Last Monday in May — 2026: May 25
# =============================================================================

def test_memorial_day_2026():
    cfg = _cfg(
        cp_freq="yearly",
        cp_bymonth=5,
        cp_day_rule="last_weekday",
        cp_byday_weekday=0,  # Monday
    )
    result = next_custom_pattern(cfg, date(2026, 1, 1))
    assert result == date(2026, 5, 25), f"Expected 2026-05-25, got {result}"


# =============================================================================
# Example 4 — Tag der Deutschen Einheit (DE)
# Fixed date: 3rd October — 2026: October 3
# =============================================================================

def test_tag_der_deutschen_einheit_2026():
    cfg = _cfg(
        cp_freq="yearly",
        cp_bymonth=10,
        cp_day_rule="fixed_day",
        cp_bymonthday=3,
    )
    result = next_custom_pattern(cfg, date(2026, 1, 1))
    assert result == date(2026, 10, 3), f"Expected 2026-10-03, got {result}"


# =============================================================================
# Example 5 — Väterdag (Sweden)
# 2nd Sunday in November — 2026: November 8
# =============================================================================

def test_vaterdag_2026():
    cfg = _cfg(
        cp_freq="yearly",
        cp_bymonth=11,
        cp_day_rule="nth_weekday",
        cp_byday_pos=2,
        cp_byday_weekday=6,  # Sunday
    )
    result = next_custom_pattern(cfg, date(2026, 1, 1))
    assert result == date(2026, 11, 8), f"Expected 2026-11-08, got {result}"


# =============================================================================
# Example 6 — Thanksgiving (US)
# 4th Thursday in November — 2026: November 26
# =============================================================================

def test_thanksgiving_2026():
    cfg = _cfg(
        cp_freq="yearly",
        cp_bymonth=11,
        cp_day_rule="nth_weekday",
        cp_byday_pos=4,
        cp_byday_weekday=3,  # Thursday
    )
    result = next_custom_pattern(cfg, date(2026, 1, 1))
    assert result == date(2026, 11, 26), f"Expected 2026-11-26, got {result}"


# =============================================================================
# Example 7 — Your team meeting
# Every Monday — next Monday from Sunday Apr 5 is Apr 6
# =============================================================================

def test_team_meeting_every_monday():
    cfg = _cfg(
        cp_freq="weekly",
        cp_interval=1,
        cp_dtstart="2024-01-01",  # Monday anchor
        cp_byday_list=[0],  # Monday
    )
    # Apr 5, 2026 is a Sunday — next occurrence is Monday Apr 6
    result = next_custom_pattern(cfg, date(2026, 4, 5))
    assert result == date(2026, 4, 6), f"Expected 2026-04-06, got {result}"


# =============================================================================
# Example 8 — Medication reminder
# Every 3 days, starting Apr 1, 2026
# Occurrences: Apr 1, Apr 4, Apr 7, Apr 10, ...
# =============================================================================

def test_medication_reminder_every_3_days():
    cfg = _cfg(
        cp_freq="daily",
        cp_interval=3,
        cp_dtstart="2026-04-01",
    )
    # From Apr 5 (between Apr 4 and Apr 7) → next is Apr 7
    result = next_custom_pattern(cfg, date(2026, 4, 5))
    assert result == date(2026, 4, 7), f"Expected 2026-04-07, got {result}"


# =============================================================================
# Example 9 — Quarterly review
# First Monday of every 3rd month, starting Jan 2026
# Occurrences: Jan 5, Apr 6, Jul 6, Oct 5, ...
# =============================================================================

def test_quarterly_review_first_monday():
    cfg = _cfg(
        cp_freq="monthly",
        cp_interval=3,
        cp_dtstart="2026-01-01",
        cp_day_rule="nth_weekday",
        cp_byday_pos=1,
        cp_byday_weekday=0,  # Monday
    )
    # From Apr 7 (Apr 6 already passed) → next is Jul 6
    result = next_custom_pattern(cfg, date(2026, 4, 7))
    assert result == date(2026, 7, 6), f"Expected 2026-07-06, got {result}"
