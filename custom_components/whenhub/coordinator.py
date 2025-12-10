"""DataUpdateCoordinator for WhenHub integration.

This module implements the central data update coordinator that manages
refreshing sensor data at regular intervals. All sensors subscribe to
this coordinator to receive updates efficiently.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    CONF_START_DATE,
    CONF_END_DATE,
    CONF_TARGET_DATE,
    CONF_SPECIAL_TYPE,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
    EVENT_TYPE_SPECIAL,
    SPECIAL_EVENTS,
)
from .calculations import (
    parse_date,
    days_until,
    days_between,
    trip_left_days,
    trip_left_percent,
    is_trip_active,
    is_date_today,
    countdown_breakdown,
    format_countdown_text,
    next_anniversary,
    last_anniversary,
    anniversary_count,
    next_special_event,
    last_special_event,
)

_LOGGER = logging.getLogger(__name__)

# Update interval - once per hour is sufficient for date-based calculations
# Sensors will still show correct values since calculations use date.today()
UPDATE_INTERVAL = timedelta(hours=1)


def _date_to_datetime(d: date | None) -> datetime | None:
    """Convert a date to a timezone-aware datetime at start of day.

    Args:
        d: Date to convert, or None

    Returns:
        Timezone-aware datetime at midnight local time, or None if input is None
    """
    if d is None:
        return None
    return dt_util.start_of_local_day(d)


class WhenHubCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for WhenHub event data.

    This coordinator centralizes all data fetching and calculation for WhenHub
    sensors. It calculates all relevant values for an event (days until, countdown
    text, etc.) and provides them to subscribing entities.

    Benefits:
    - Single point of calculation reduces redundant date operations
    - Consistent data across all sensors for the same event
    - Efficient Home Assistant integration with automatic refresh
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        event_data: dict[str, Any],
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            config_entry: Config entry for this WhenHub integration instance
            event_data: Dictionary containing event configuration
        """
        self.config_entry = config_entry
        self.event_data = event_data
        self.event_type = event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_TRIP)
        self.event_name = event_data.get(CONF_EVENT_NAME, "Unknown Event")

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and calculate all event data.

        This method is called by the coordinator at the configured interval.
        It calculates all values needed by sensors for this event type.

        Returns:
            Dictionary with all calculated values for the event
        """
        today = date.today()
        data: dict[str, Any] = {
            "today": today.isoformat(),
            "event_type": self.event_type,
            "event_name": self.event_name,
        }

        if self.event_type == EVENT_TYPE_TRIP:
            data.update(self._calculate_trip_data(today))
        elif self.event_type == EVENT_TYPE_MILESTONE:
            data.update(self._calculate_milestone_data(today))
        elif self.event_type == EVENT_TYPE_ANNIVERSARY:
            data.update(self._calculate_anniversary_data(today))
        elif self.event_type == EVENT_TYPE_SPECIAL:
            data.update(self._calculate_special_data(today))

        return data

    def _calculate_trip_data(self, today: date) -> dict[str, Any]:
        """Calculate all trip-related values.

        Args:
            today: Current date for calculations

        Returns:
            Dictionary with trip sensor values
        """
        start_date = parse_date(self.event_data[CONF_START_DATE])
        end_date = parse_date(self.event_data[CONF_END_DATE])

        days_to_start = days_until(start_date, today)
        countdown = countdown_breakdown(start_date, today) if today < start_date else {}

        return {
            # Datetime objects for sensors with device_class: timestamp
            "start_date": _date_to_datetime(start_date),
            "end_date": _date_to_datetime(end_date),
            "days_until": days_to_start,
            "days_until_end": days_until(end_date, today),
            "countdown_text": format_countdown_text(start_date, today) if today <= start_date else "0 Tage",
            "countdown_breakdown": countdown,
            "trip_left_days": trip_left_days(start_date, end_date, today),
            "trip_left_percent": trip_left_percent(start_date, end_date, today),
            "total_days": days_between(start_date, end_date),
            # Binary sensor values
            "trip_starts_today": is_date_today(start_date, today),
            "trip_active_today": is_trip_active(start_date, end_date, today),
            "trip_ends_today": is_date_today(end_date, today),
        }

    def _calculate_milestone_data(self, today: date) -> dict[str, Any]:
        """Calculate all milestone-related values.

        Args:
            today: Current date for calculations

        Returns:
            Dictionary with milestone sensor values
        """
        target_date = parse_date(self.event_data[CONF_TARGET_DATE])

        countdown = countdown_breakdown(target_date, today) if today < target_date else {}

        return {
            # Datetime object for sensors with device_class: timestamp
            "target_date": _date_to_datetime(target_date),
            "days_until": days_until(target_date, today),
            "countdown_text": format_countdown_text(target_date, today) if today < target_date else "0 Tage",
            "countdown_breakdown": countdown,
            # Binary sensor values
            "is_today": is_date_today(target_date, today),
        }

    def _calculate_anniversary_data(self, today: date) -> dict[str, Any]:
        """Calculate all anniversary-related values.

        Args:
            today: Current date for calculations

        Returns:
            Dictionary with anniversary sensor values
        """
        original_date = parse_date(self.event_data[CONF_TARGET_DATE])
        next_ann = next_anniversary(original_date, today)
        last_ann = last_anniversary(original_date, today)

        days_to_next = days_until(next_ann, today)
        countdown = countdown_breakdown(next_ann, today) if days_to_next > 0 else {}

        return {
            # Datetime objects for sensors with device_class: timestamp
            "original_date": _date_to_datetime(original_date),
            "next_anniversary": _date_to_datetime(next_ann),
            "last_anniversary": _date_to_datetime(last_ann),
            "days_until_next": days_to_next,
            "days_since_last": (today - last_ann).days if last_ann else None,
            "countdown_text": format_countdown_text(next_ann, today) if days_to_next > 0 else "0 Tage",
            "countdown_breakdown": countdown,
            "occurrences_count": anniversary_count(original_date, today),
            "years_on_next": next_ann.year - original_date.year,
            # Binary sensor values
            "is_today": is_date_today(next_ann, today),
        }

    def _calculate_special_data(self, today: date) -> dict[str, Any]:
        """Calculate all special event-related values.

        Args:
            today: Current date for calculations

        Returns:
            Dictionary with special event sensor values
        """
        special_type = self.event_data.get(CONF_SPECIAL_TYPE, "christmas_eve")
        special_info = SPECIAL_EVENTS.get(special_type, SPECIAL_EVENTS["christmas_eve"])

        next_event = next_special_event(special_info, today)
        last_event = last_special_event(special_info, today)

        days_to_next = days_until(next_event, today) if next_event else 0
        countdown = countdown_breakdown(next_event, today) if next_event and days_to_next > 0 else {}

        return {
            "special_type": special_type,
            "special_name": special_info.get("name", "Unknown"),
            # Datetime objects for sensors with device_class: timestamp
            "next_date": _date_to_datetime(next_event if next_event else today),
            "last_date": _date_to_datetime(last_event),
            "days_until": days_to_next,
            "days_since_last": (today - last_event).days if last_event else None,
            "countdown_text": format_countdown_text(next_event, today) if next_event and days_to_next > 0 else "0 Tage",
            "countdown_breakdown": countdown,
            # Binary sensor values
            "is_today": is_date_today(next_event, today) if next_event else False,
        }
