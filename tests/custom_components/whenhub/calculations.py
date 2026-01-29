"""Pure calculation functions for WhenHub integration.

This module contains all date calculation logic separated from Home Assistant
integration code. Functions here are pure Python with no HA dependencies,
making them easy to test and reuse.

All functions take explicit date parameters rather than using date.today()
internally, which makes them deterministic and testable with freezegun.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional


# =============================================================================
# Date Parsing
# =============================================================================

def parse_date(date_str: str | date) -> date:
    """Parse date string in ISO format or return existing date object.

    Args:
        date_str: Either an ISO date string (YYYY-MM-DD) or a date object

    Returns:
        A date object

    Raises:
        ValueError: If date_str is a malformed string
    """
    if isinstance(date_str, str):
        return date.fromisoformat(date_str)
    return date_str


# =============================================================================
# Basic Date Calculations
# =============================================================================

def days_until(target_date: date, today: date) -> int:
    """Calculate days from today until target date.

    Args:
        target_date: The target date to count to
        today: The reference date (usually today)

    Returns:
        Number of days (negative if target is in the past)
    """
    return (target_date - today).days


def days_between(start_date: date, end_date: date) -> int:
    """Calculate total days between two dates (inclusive).

    Args:
        start_date: Start of the period
        end_date: End of the period

    Returns:
        Number of days including both start and end date
    """
    return (end_date - start_date).days + 1


# =============================================================================
# Trip Calculations
# =============================================================================

def trip_left_days(start_date: date, end_date: date, today: date) -> int:
    """Calculate remaining days in an active trip.

    Args:
        start_date: Trip start date
        end_date: Trip end date
        today: Current date

    Returns:
        Days remaining (including today) if trip is active, 0 otherwise
    """
    if start_date <= today <= end_date:
        return (end_date - today).days + 1
    return 0


def trip_left_percent(start_date: date, end_date: date, today: date) -> float:
    """Calculate percentage of trip remaining.

    Args:
        start_date: Trip start date
        end_date: Trip end date
        today: Current date

    Returns:
        Percentage remaining (100.0 before trip, 0.0 after trip)
    """
    total_days = (end_date - start_date).days
    if total_days == 0:
        # Single day trip
        if today < start_date:
            return 100.0
        elif today > end_date:
            return 0.0
        else:
            return 100.0  # On the day itself

    if today < start_date:
        return 100.0
    elif today > end_date:
        return 0.0
    else:
        passed_days = (today - start_date).days
        remaining_percent = 100.0 - ((passed_days / total_days) * 100.0)
        return round(remaining_percent, 1)


def is_trip_active(start_date: date, end_date: date, today: date) -> bool:
    """Check if trip is currently active.

    Args:
        start_date: Trip start date
        end_date: Trip end date
        today: Current date

    Returns:
        True if today is within the trip period (inclusive)
    """
    return start_date <= today <= end_date


def is_date_today(target_date: date, today: date) -> bool:
    """Check if target date is today.

    Args:
        target_date: Date to check
        today: Current date

    Returns:
        True if dates match
    """
    return target_date == today


# =============================================================================
# Countdown Text Formatting
# =============================================================================

def countdown_breakdown(target_date: date, today: date) -> dict[str, int]:
    """Break down days until target into years, months, weeks, days.

    Uses approximations (365 days/year, 30 days/month) for simplicity.

    Args:
        target_date: The date to count down to
        today: Current date

    Returns:
        Dictionary with years, months, weeks, days breakdown
    """
    if target_date <= today:
        return {"years": 0, "months": 0, "weeks": 0, "days": 0}

    total_days = (target_date - today).days

    years = total_days // 365
    remaining = total_days - (years * 365)

    months = remaining // 30
    remaining = remaining - (months * 30)

    weeks = remaining // 7
    days = remaining % 7

    return {
        "years": years,
        "months": months,
        "weeks": weeks,
        "days": days
    }


def format_countdown_text(target_date: date, today: date) -> str:
    """Format countdown into human-readable German text.

    Note: German output is intentional - see prompt.md for rationale
    (sensor state values cannot be translated by Home Assistant).

    Args:
        target_date: The date to count down to
        today: Current date

    Returns:
        German string like "2 Jahre, 3 Monate, 1 Woche, 4 Tage"
        or "0 Tage" if target has passed
    """
    breakdown = countdown_breakdown(target_date, today)

    if all(v == 0 for v in breakdown.values()):
        return "0 Tage"

    parts = []
    if breakdown["years"] > 0:
        parts.append(f"{breakdown['years']} Jahr{'e' if breakdown['years'] > 1 else ''}")
    if breakdown["months"] > 0:
        parts.append(f"{breakdown['months']} Monat{'e' if breakdown['months'] > 1 else ''}")
    if breakdown["weeks"] > 0:
        parts.append(f"{breakdown['weeks']} Woche{'n' if breakdown['weeks'] > 1 else ''}")
    if breakdown["days"] > 0:
        parts.append(f"{breakdown['days']} Tag{'e' if breakdown['days'] > 1 else ''}")

    return ", ".join(parts) if parts else "0 Tage"


# =============================================================================
# Anniversary Calculations
# =============================================================================

def anniversary_for_year(original_date: date, target_year: int) -> date:
    """Get anniversary date for a specific year, handling leap years.

    Handles February 29th birthdays in non-leap years by using Feb 28.

    Args:
        original_date: The original event date (e.g., birth date)
        target_year: Year to calculate anniversary for

    Returns:
        Anniversary date for the target year

    Example:
        anniversary_for_year(date(2020, 2, 29), 2021) -> date(2021, 2, 28)
    """
    try:
        return original_date.replace(year=target_year)
    except ValueError:
        # Feb 29 in non-leap year -> use Feb 28
        return date(target_year, 2, 28)


def next_anniversary(original_date: date, today: date) -> date:
    """Calculate the next occurrence of an anniversary.

    Args:
        original_date: The original event date
        today: Current date

    Returns:
        Date of the next anniversary
    """
    this_year = anniversary_for_year(original_date, today.year)
    if this_year >= today:
        return this_year
    return anniversary_for_year(original_date, today.year + 1)


def last_anniversary(original_date: date, today: date) -> Optional[date]:
    """Calculate the most recent past anniversary.

    Args:
        original_date: The original event date
        today: Current date

    Returns:
        Date of last anniversary, or None if original is in the future
    """
    if original_date > today:
        return None

    this_year = anniversary_for_year(original_date, today.year)
    if this_year <= today:
        return this_year
    return anniversary_for_year(original_date, today.year - 1)


def anniversary_count(original_date: date, today: date) -> int:
    """Count total anniversary occurrences including today if applicable.

    Args:
        original_date: The original event date
        today: Current date

    Returns:
        Number of occurrences (0 if original is in the future)
    """
    if original_date > today:
        return 0

    years_passed = today.year - original_date.year
    this_year = anniversary_for_year(original_date, today.year)

    if this_year > today:
        years_passed -= 1

    return max(1, years_passed + 1)


# =============================================================================
# Special Event Calculations (Easter, Advent)
# =============================================================================

def calculate_easter(year: int) -> Optional[date]:
    """Calculate Easter Sunday using the Gauss algorithm.

    Calculates Western/Gregorian Easter.

    Args:
        year: Year to calculate Easter for

    Returns:
        Date of Easter Sunday, or None on calculation error
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451

    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1

    try:
        return date(year, month, day)
    except ValueError:
        return None


def calculate_pentecost(year: int) -> Optional[date]:
    """Calculate Pentecost Sunday (49 days after Easter).

    Args:
        year: Year to calculate Pentecost for

    Returns:
        Date of Pentecost Sunday, or None if Easter calculation fails
    """
    easter = calculate_easter(year)
    if easter:
        return easter + timedelta(days=49)
    return None


def calculate_advent(year: int, advent_num: int) -> Optional[date]:
    """Calculate Advent Sunday date.

    Args:
        year: Year to calculate Advent for
        advent_num: Which Advent (1, 2, 3, or 4)

    Returns:
        Date of the specified Advent Sunday
    """
    if advent_num not in (1, 2, 3, 4):
        return None

    # Christmas Eve
    christmas = date(year, 12, 24)

    # Find the Sunday before Christmas
    days_back = (christmas.weekday() + 1) % 7
    if days_back == 0:
        days_back = 7

    # 4th Advent is the last Sunday before or on Christmas Eve
    advent_4 = christmas - timedelta(days=days_back)

    # Calculate requested Advent
    weeks_before_4th = 4 - advent_num
    return advent_4 - timedelta(days=weeks_before_4th * 7)


def calculate_special_event_date(special_info: dict, year: int) -> Optional[date]:
    """Calculate date for a special event in a given year.

    Args:
        special_info: Event definition dict with type, month/day or calculation
        year: Year to calculate for

    Returns:
        Date of the event, or None if calculation fails
    """
    event_type = special_info.get("type", "fixed")

    if event_type == "fixed":
        month = special_info.get("month", 1)
        day = special_info.get("day", 1)
        try:
            return date(year, month, day)
        except ValueError:
            return None

    elif event_type == "calculated":
        calculation = special_info.get("calculation", "")

        if calculation == "easter":
            return calculate_easter(year)
        elif calculation == "pentecost":
            return calculate_pentecost(year)
        elif calculation.startswith("advent_"):
            try:
                advent_num = int(calculation.split("_")[1])
                return calculate_advent(year, advent_num)
            except (ValueError, IndexError):
                return None

    return None


def next_special_event(special_info: dict, today: date) -> Optional[date]:
    """Calculate next occurrence of a special event.

    Args:
        special_info: Event definition dict
        today: Current date

    Returns:
        Date of next occurrence
    """
    this_year = calculate_special_event_date(special_info, today.year)

    if this_year and this_year >= today:
        return this_year

    return calculate_special_event_date(special_info, today.year + 1)


def last_special_event(special_info: dict, today: date) -> Optional[date]:
    """Calculate last occurrence of a special event.

    Args:
        special_info: Event definition dict
        today: Current date

    Returns:
        Date of last occurrence
    """
    this_year = calculate_special_event_date(special_info, today.year)

    if this_year and this_year < today:
        return this_year

    return calculate_special_event_date(special_info, today.year - 1)


# =============================================================================
# DST (Daylight Saving Time) Calculations
# =============================================================================

def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> Optional[date]:
    """Calculate the nth occurrence of a weekday in a month.

    Args:
        year: Year to calculate for
        month: Month (1-12)
        weekday: Weekday (0=Monday, 6=Sunday)
        n: Which occurrence (1=first, 2=second, etc.)

    Returns:
        Date of the nth weekday, or None if n is too large for the month

    Example:
        nth_weekday_of_month(2026, 3, 6, 2)  # 2nd Sunday in March 2026
        -> date(2026, 3, 8)
    """
    # First day of the month
    first_day = date(year, month, 1)

    # Weekday of the first day (0=Monday, 6=Sunday)
    first_weekday = first_day.weekday()

    # Days until the first desired weekday
    days_until_first = (weekday - first_weekday) % 7

    # Date of the first desired weekday
    first_occurrence = first_day + timedelta(days=days_until_first)

    # nth occurrence (n-1 weeks after the first)
    result = first_occurrence + timedelta(weeks=n - 1)

    # Check if still in the same month
    if result.month != month:
        return None

    return result


def last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    """Calculate the last occurrence of a weekday in a month.

    Args:
        year: Year to calculate for
        month: Month (1-12)
        weekday: Weekday (0=Monday, 6=Sunday)

    Returns:
        Date of the last weekday in the month

    Example:
        last_weekday_of_month(2026, 10, 6)  # Last Sunday in October 2026
        -> date(2026, 10, 25)
    """
    # Last day of the month
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # Weekday of the last day
    last_weekday = last_day.weekday()

    # Days back to the desired weekday
    days_back = (last_weekday - weekday) % 7

    return last_day - timedelta(days=days_back)


def calculate_dst_date(region_info: dict, dst_type: str, year: int) -> Optional[date]:
    """Calculate DST transition date for a region and type.

    Args:
        region_info: Region definition dict with summer/winter rules
        dst_type: "summer" or "winter"
        year: Year to calculate for

    Returns:
        Date of the DST transition, or None on error

    Example:
        calculate_dst_date(DST_REGIONS["eu"], "summer", 2026)
        -> date(2026, 3, 29)  # Last Sunday in March 2026
    """
    if dst_type not in ("summer", "winter"):
        return None

    rule_info = region_info.get(dst_type)
    if not rule_info:
        return None

    rule = rule_info.get("rule")
    weekday = rule_info.get("weekday", 6)  # Default: Sunday
    month = rule_info.get("month")

    if not month:
        return None

    if rule == "last":
        return last_weekday_of_month(year, month, weekday)
    elif rule == "nth":
        n = rule_info.get("n", 1)
        return nth_weekday_of_month(year, month, weekday, n)

    return None


def next_dst_event(
    region_info: dict,
    dst_type: str,
    today: date
) -> Optional[date]:
    """Calculate next DST event date.

    Args:
        region_info: Region definition dict
        dst_type: "next_change", "next_summer", or "next_winter"
        today: Current date

    Returns:
        Date of the next DST event
    """
    if dst_type == "next_summer":
        # Next summer time
        this_year = calculate_dst_date(region_info, "summer", today.year)
        if this_year and this_year >= today:
            return this_year
        return calculate_dst_date(region_info, "summer", today.year + 1)

    elif dst_type == "next_winter":
        # Next winter time
        this_year = calculate_dst_date(region_info, "winter", today.year)
        if this_year and this_year >= today:
            return this_year
        return calculate_dst_date(region_info, "winter", today.year + 1)

    elif dst_type == "next_change":
        # Next change (either summer or winter)
        next_summer = next_dst_event(region_info, "next_summer", today)
        next_winter = next_dst_event(region_info, "next_winter", today)

        if next_summer and next_winter:
            return min(next_summer, next_winter)
        return next_summer or next_winter

    return None


def last_dst_event(
    region_info: dict,
    dst_type: str,
    today: date
) -> Optional[date]:
    """Calculate last DST event date.

    On the transition day itself, the new time is already active,
    so the transition day counts as "already happened".

    Args:
        region_info: Region definition dict
        dst_type: "next_change", "next_summer", or "next_winter"
        today: Current date

    Returns:
        Date of the last DST event
    """
    if dst_type == "next_summer":
        # Last summer time (includes today if transition day)
        this_year = calculate_dst_date(region_info, "summer", today.year)
        if this_year and this_year <= today:
            return this_year
        return calculate_dst_date(region_info, "summer", today.year - 1)

    elif dst_type == "next_winter":
        # Last winter time (includes today if transition day)
        this_year = calculate_dst_date(region_info, "winter", today.year)
        if this_year and this_year <= today:
            return this_year
        return calculate_dst_date(region_info, "winter", today.year - 1)

    elif dst_type == "next_change":
        # Last change (either summer or winter)
        last_summer = last_dst_event(region_info, "next_summer", today)
        last_winter = last_dst_event(region_info, "next_winter", today)

        if last_summer and last_winter:
            return max(last_summer, last_winter)
        return last_summer or last_winter

    return None


def is_dst_active(region_info: dict, today: date) -> bool:
    """Check if daylight saving time is currently active.

    Determines whether we are currently in summer time (DST) or
    winter time (standard time) by comparing the most recent
    summer and winter transitions.

    Args:
        region_info: Region definition dict
        today: Current date

    Returns:
        True if summer time (DST) is currently active,
        False if winter time (standard time) is active

    Example:
        # EU, June 1st 2026 (between March and October)
        is_dst_active(DST_REGIONS["eu"], date(2026, 6, 1))
        -> True  # Summer time active

        # EU, December 1st 2026 (after October)
        is_dst_active(DST_REGIONS["eu"], date(2026, 12, 1))
        -> False  # Winter time active
    """
    # Last summer time transition
    last_summer = last_dst_event(region_info, "next_summer", today)
    # Last winter time transition
    last_winter = last_dst_event(region_info, "next_winter", today)

    # If no events found
    if last_summer is None and last_winter is None:
        return False
    if last_summer is None:
        return False  # Only winter time known -> winter time active
    if last_winter is None:
        return True   # Only summer time known -> summer time active

    # The more recent event determines the current state
    # If summer time was last -> summer time active
    # If winter time was last -> winter time active
    return last_summer > last_winter
