"""Special Event sensor for WhenHub integration.

This module implements sensors for special holidays and astronomical events
(e.g., Christmas, Easter, Solstices). Special event sensors calculate dates
for fixed holidays and compute dates for moveable feasts like Easter.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry

from ..const import (
    CONF_SPECIAL_TYPE,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    EVENT_TYPE_SPECIAL,
    SPECIAL_SENSOR_TYPES,
    SPECIAL_EVENTS,
    TEXT_ZERO_DAYS,
)
from .base import BaseCountdownSensor

_LOGGER = logging.getLogger(__name__)


class SpecialEventSensor(BaseCountdownSensor):
    """Sensor for special holidays and astronomical events.
    
    Provides countdown calculations for fixed and calculated special events:
    - days_until: Integer days until the next occurrence
    - countdown_text: Human-readable countdown text
    - next_date: ISO date string of next occurrence
    
    Handles complex date calculations for moveable feasts (Easter-based holidays)
    and astronomical events (solstices, equinoxes).
    """

    def __init__(self, config_entry: ConfigEntry, event_data: dict, sensor_type: str) -> None:
        """Initialize the special event sensor.
        
        Args:
            config_entry: Home Assistant config entry for this integration
            event_data: Dictionary containing special event configuration
            sensor_type: Type of sensor to create (from SPECIAL_SENSOR_TYPES)
        """
        super().__init__(config_entry, event_data, sensor_type, SPECIAL_SENSOR_TYPES)
        
        # Get the special event type
        self._special_type = event_data.get(CONF_SPECIAL_TYPE, "christmas")
        self._special_info = SPECIAL_EVENTS.get(self._special_type, SPECIAL_EVENTS["christmas"])
        
        # Use consistent star icon for all special events (matches other event types)

    @property
    def native_value(self) -> str | int | float | None:
        """Return the current sensor value."""
        return self._safe_calculate(self._calculate_value)

    def _calculate_value(self) -> str | int | float | None:
        """Calculate the current sensor value based on sensor type."""
        today = date.today()
        
        if self._sensor_type == "days_until":
            next_date = self._get_next_event_date()
            return (next_date - today).days if next_date else 0
            
        elif self._sensor_type == "days_since_last":
            last_date = self._get_last_event_date()
            return (today - last_date).days if last_date else None
            
        elif self._sensor_type == "countdown_text":
            next_date = self._get_next_event_date()
            if next_date:
                days_until = (next_date - today).days
                if days_until == 0:
                    return TEXT_ZERO_DAYS
                else:
                    return self._format_countdown_text(next_date)
            return TEXT_ZERO_DAYS
                
        elif self._sensor_type == "next_date":
            next_date = self._get_next_event_date()
            return next_date.isoformat() if next_date else today.isoformat()
            
        elif self._sensor_type == "last_date":
            last_date = self._get_last_event_date()
            return last_date.isoformat() if last_date else None
        
        return None

    def _get_next_event_date(self) -> Optional[date]:
        """Calculate the next occurrence of this special event.
        
        Returns:
            Date of the next event occurrence, or None if calculation fails
        """
        today = date.today()
        current_year = today.year
        
        # Calculate this year's date
        this_year_date = self._calculate_event_date(current_year)
        
        # If this year's event hasn't happened yet, return it
        if this_year_date and this_year_date >= today:
            return this_year_date
        
        # Otherwise, calculate next year's date
        next_year_date = self._calculate_event_date(current_year + 1)
        return next_year_date

    def _get_last_event_date(self) -> Optional[date]:
        """Calculate the last occurrence of this special event.
        
        Returns:
            Date of the last event occurrence, or None if no past occurrence
        """
        today = date.today()
        current_year = today.year
        
        # Calculate this year's date
        this_year_date = self._calculate_event_date(current_year)
        
        # If this year's event already happened, return it
        if this_year_date and this_year_date < today:
            return this_year_date
        
        # Otherwise, calculate last year's date
        last_year_date = self._calculate_event_date(current_year - 1)
        return last_year_date

    def _calculate_event_date(self, year: int) -> Optional[date]:
        """Calculate the date of the special event for a given year.
        
        Args:
            year: Year to calculate the event date for
            
        Returns:
            Date of the event in the given year, or None if calculation fails
        """
        event_type = self._special_info.get("type", "fixed")
        
        if event_type == "fixed":
            # Fixed date events (Christmas, Halloween, etc.)
            month = self._special_info.get("month", 1)
            day = self._special_info.get("day", 1)
            try:
                return date(year, month, day)
            except ValueError:
                _LOGGER.error("Invalid date for special event %s: %d-%d-%d", 
                             self._special_type, year, month, day)
                return None
                
        elif event_type == "calculated":
            # Calculated events (Easter, Solstices, etc.)
            calculation = self._special_info.get("calculation", "")
            
            if calculation == "easter":
                return self._calculate_easter(year)
            elif calculation == "good_friday":
                easter = self._calculate_easter(year)
                return easter - timedelta(days=2) if easter else None
            elif calculation == "easter_monday":
                easter = self._calculate_easter(year)
                return easter + timedelta(days=1) if easter else None
            elif calculation == "carnival":
                easter = self._calculate_easter(year)
                return easter - timedelta(days=48) if easter else None
            elif calculation == "ash_wednesday":
                easter = self._calculate_easter(year)
                return easter - timedelta(days=46) if easter else None
            elif calculation == "ascension":
                easter = self._calculate_easter(year)
                return easter + timedelta(days=39) if easter else None
            elif calculation == "pentecost":
                easter = self._calculate_easter(year)
                return easter + timedelta(days=49) if easter else None
            elif calculation == "pentecost_monday":
                easter = self._calculate_easter(year)
                return easter + timedelta(days=50) if easter else None
            elif calculation == "mothers_day":
                return self._calculate_mothers_day(year)
            elif calculation.startswith("advent_"):
                return self._calculate_advent(year, calculation)
            elif calculation == "summer_solstice":
                return self._calculate_summer_solstice(year)
            elif calculation == "winter_solstice":
                return self._calculate_winter_solstice(year)
            elif calculation == "spring_equinox":
                return self._calculate_spring_equinox(year)
            elif calculation == "autumn_equinox":
                return self._calculate_autumn_equinox(year)
            else:
                _LOGGER.warning("Unknown calculation type: %s", calculation)
                return None
        
        return None

    def _calculate_easter(self, year: int) -> Optional[date]:
        """Calculate Easter Sunday using the Gauss algorithm.
        
        This algorithm calculates Western/Gregorian Easter.
        
        Args:
            year: Year to calculate Easter for
            
        Returns:
            Date of Easter Sunday in the given year
        """
        # Gauss Easter Algorithm
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
            _LOGGER.error("Failed to calculate Easter for year %d", year)
            return None

    def _calculate_mothers_day(self, year: int) -> Optional[date]:
        """Calculate Mother's Day (2nd Sunday in May).
        
        Args:
            year: Year to calculate Mother's Day for
            
        Returns:
            Date of Mother's Day in the given year
        """
        # Find first day of May
        first_may = date(year, 5, 1)
        
        # Find first Sunday in May
        days_until_sunday = (6 - first_may.weekday()) % 7
        first_sunday = first_may + timedelta(days=days_until_sunday)
        
        # Second Sunday is 7 days later
        second_sunday = first_sunday + timedelta(days=7)
        
        return second_sunday

    def _calculate_advent(self, year: int, advent_num: str) -> Optional[date]:
        """Calculate Advent Sunday dates.
        
        Args:
            year: Year to calculate Advent for
            advent_num: Which Advent Sunday (advent_1, advent_2, advent_3, advent_4)
            
        Returns:
            Date of the specified Advent Sunday
        """
        # Christmas Eve
        christmas = date(year, 12, 24)
        
        # Find the Sunday before Christmas (could be Christmas Eve itself)
        days_back = (christmas.weekday() + 1) % 7
        if days_back == 0:
            days_back = 7
        
        # 4th Advent is the last Sunday before or on Christmas Eve
        advent_4 = christmas - timedelta(days=days_back)
        
        # Calculate other Advents
        if advent_num == "advent_4":
            return advent_4
        elif advent_num == "advent_3":
            return advent_4 - timedelta(days=7)
        elif advent_num == "advent_2":
            return advent_4 - timedelta(days=14)
        elif advent_num == "advent_1":
            return advent_4 - timedelta(days=21)
        
        return None

    def _calculate_summer_solstice(self, year: int) -> date:
        """Calculate summer solstice date.
        
        Simplified calculation - actual date varies between June 20-22.
        For more accuracy, an astronomical library would be needed.
        
        Args:
            year: Year to calculate summer solstice for
            
        Returns:
            Approximate date of summer solstice
        """
        # Simplified: Summer solstice is usually June 21
        # In reality it varies between June 20-22
        if year % 4 == 0:
            return date(year, 6, 20)
        else:
            return date(year, 6, 21)

    def _calculate_winter_solstice(self, year: int) -> date:
        """Calculate winter solstice date.
        
        Simplified calculation - actual date varies between December 20-22.
        
        Args:
            year: Year to calculate winter solstice for
            
        Returns:
            Approximate date of winter solstice
        """
        # Simplified: Winter solstice is usually December 21
        # In reality it varies between December 20-22
        if (year - 1) % 4 == 0:
            return date(year, 12, 22)
        else:
            return date(year, 12, 21)

    def _calculate_spring_equinox(self, year: int) -> date:
        """Calculate spring equinox date.
        
        Simplified calculation - actual date is usually March 20 or 21.
        
        Args:
            year: Year to calculate spring equinox for
            
        Returns:
            Approximate date of spring equinox
        """
        # Simplified: Spring equinox is usually March 20
        # In reality it can be March 19-21
        if year % 4 == 0:
            return date(year, 3, 20)
        else:
            return date(year, 3, 20)

    def _calculate_autumn_equinox(self, year: int) -> date:
        """Calculate autumn equinox date.
        
        Simplified calculation - actual date is usually September 22 or 23.
        
        Args:
            year: Year to calculate autumn equinox for
            
        Returns:
            Approximate date of autumn equinox
        """
        # Simplified: Autumn equinox is usually September 23
        # In reality it can be September 22-24
        if year % 4 <= 1:
            return date(year, 9, 22)
        else:
            return date(year, 9, 23)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes for this sensor."""
        # Only countdown_text sensor gets detailed attributes
        if self._sensor_type == "countdown_text":
            attributes = self._get_base_attributes()
            attributes.update({
                "special_type": self._special_type,
                "special_name": self._special_info.get("name", "Unknown"),
            })
            
            # Add next event date
            next_date = self._get_next_event_date()
            if next_date:
                attributes["next_date"] = next_date.isoformat()
            
            # Add countdown breakdown
            attributes.update(self._get_countdown_attributes())
            
            return attributes
        
        # All other special sensors have no attributes
        return {}