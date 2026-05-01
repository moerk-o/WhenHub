"""DataUpdateCoordinator for WhenHub integration.

This module implements the central data update coordinator that manages
refreshing sensor data at regular intervals. All sensors subscribe to
this coordinator to receive updates efficiently.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue, async_delete_issue
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    CONF_START_DATE,
    CONF_END_DATE,
    CONF_TARGET_DATE,
    CONF_SPECIAL_TYPE,
    CONF_SPECIAL_CATEGORY,
    CONF_DST_TYPE,
    CONF_DST_REGION,
    CONF_NOTIFY_ON_EXPIRY,
    CONF_CP_END_TYPE,
    CONF_CP_UNTIL,
    CONF_EVENT_DATE_USE_ENTITY,
    CONF_EVENT_DATE_ENTITY_ID,
    CONF_START_DATE_USE_ENTITY,
    CONF_START_DATE_ENTITY_ID,
    CONF_END_DATE_USE_ENTITY,
    CONF_END_DATE_ENTITY_ID,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
    EVENT_TYPE_SPECIAL,
    SPECIAL_EVENTS,
    DST_REGIONS,
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
    next_dst_event,
    last_dst_event,
    is_dst_active,
    next_custom_pattern,
    last_custom_pattern,
    occurrence_count_custom_pattern,
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

        self._check_expiry_repair(today)

        return data

    def _parse_entity_date(self, state: Any) -> date | None:
        """Parse a date from an entity state object.

        Supports device_class 'date' (state is YYYY-MM-DD) and
        'timestamp' (state is ISO-8601 datetime, converted to local date).
        """
        device_class = state.attributes.get("device_class")
        if device_class == "timestamp":
            parsed = dt_util.parse_datetime(state.state)
            if parsed:
                return dt_util.as_local(parsed).date()
            return None
        # device_class == "date" or fallback
        try:
            return date.fromisoformat(state.state)
        except (ValueError, TypeError):
            return None

    def _resolve_date(
        self,
        date_key: str,
        use_entity_key: str,
        entity_id_key: str,
    ) -> date:
        """Resolve a date from manual config or a live entity state.

        Raises UpdateFailed when the entity source is configured but
        unavailable, unknown, or returns an unparseable value.
        Falls back to the manual date field when use_entity is False.
        """
        if self.event_data.get(use_entity_key):
            entity_id = self.event_data.get(entity_id_key)
            if not entity_id:
                raise UpdateFailed(
                    f"Entity date source enabled for '{date_key}' but no entity configured"
                )
            state = self.hass.states.get(entity_id)
            if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                raise UpdateFailed(
                    f"Date source entity '{entity_id}' is unavailable or unknown"
                )
            resolved = self._parse_entity_date(state)
            if resolved is None:
                raise UpdateFailed(
                    f"Cannot parse date from entity '{entity_id}' (state: {state.state!r})"
                )
            return resolved
        raw = self.event_data.get(date_key)
        if not raw:
            raise UpdateFailed(f"No date configured for '{date_key}'")
        return parse_date(raw)

    def _calculate_trip_data(self, today: date) -> dict[str, Any]:
        """Calculate all trip-related values.

        Args:
            today: Current date for calculations

        Returns:
            Dictionary with trip sensor values
        """
        start_date = self._resolve_date(
            CONF_START_DATE, CONF_START_DATE_USE_ENTITY, CONF_START_DATE_ENTITY_ID
        )
        end_date = self._resolve_date(
            CONF_END_DATE, CONF_END_DATE_USE_ENTITY, CONF_END_DATE_ENTITY_ID
        )

        # When at least one date comes from an entity, check order at runtime.
        # Manual-only trips are validated at config time so this can't happen there.
        if self.event_data.get(CONF_START_DATE_USE_ENTITY) or self.event_data.get(
            CONF_END_DATE_USE_ENTITY
        ):
            issue_id = f"date_order_{self.config_entry.entry_id}"
            if end_date < start_date:
                async_create_issue(
                    self.hass,
                    DOMAIN,
                    issue_id,
                    is_fixable=False,
                    severity=IssueSeverity.WARNING,
                    translation_key="date_order_invalid",
                    translation_placeholders={
                        "event_name": self.config_entry.title,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                )
                raise UpdateFailed(
                    f"Trip end date ({end_date}) is before start date ({start_date})"
                )
            async_delete_issue(self.hass, DOMAIN, issue_id)

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
        target_date = self._resolve_date(
            CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
        )

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
        original_date = self._resolve_date(
            CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
        )
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
        # Check if this is a DST or Custom Pattern event
        special_category = self.event_data.get(CONF_SPECIAL_CATEGORY)
        if special_category == "dst":
            return self._calculate_dst_data(today)
        if special_category == "custom_pattern":
            return self._calculate_custom_pattern_data(today)

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

    def _calculate_dst_data(self, today: date) -> dict[str, Any]:
        """Calculate all DST event-related values.

        Args:
            today: Current date for calculations

        Returns:
            Dictionary with DST event sensor values
        """
        dst_type = self.event_data.get(CONF_DST_TYPE, "next_change")
        dst_region = self.event_data.get(CONF_DST_REGION, "eu")
        region_info = DST_REGIONS.get(dst_region, DST_REGIONS["eu"])

        next_event = next_dst_event(region_info, dst_type, today)
        last_event = last_dst_event(region_info, dst_type, today)

        days_to_next = days_until(next_event, today) if next_event else 0
        countdown = countdown_breakdown(next_event, today) if next_event and days_to_next > 0 else {}

        return {
            "dst_type": dst_type,
            "dst_region": dst_region,
            "region_name": region_info.get("name", "Unknown"),
            # Datetime objects for sensors with device_class: timestamp
            "next_date": _date_to_datetime(next_event),
            "last_date": _date_to_datetime(last_event),
            "days_until": days_to_next,
            "days_since_last": (today - last_event).days if last_event else None,
            "countdown_text": format_countdown_text(next_event, today) if next_event and days_to_next > 0 else "0 Tage",
            "countdown_breakdown": countdown,
            # Binary sensor values
            "is_today": is_date_today(next_event, today) if next_event else False,
            "is_dst_active": is_dst_active(region_info, today),
        }

    def _calculate_custom_pattern_data(self, today: date) -> dict[str, Any]:
        """Calculate all custom pattern event values.

        Args:
            today: Current date for calculations

        Returns:
            Dictionary with custom pattern sensor values
        """
        next_event = next_custom_pattern(self.event_data, today)
        last_event = last_custom_pattern(self.event_data, today)
        occ_count = occurrence_count_custom_pattern(self.event_data, today)

        is_today_val = (next_event == today) if next_event else False

        # For display, show the next *future* occurrence (not today even when today is an
        # occurrence). This avoids next_date == last_date == today on occurrence days.
        if is_today_val:
            next_display = next_custom_pattern(self.event_data, today + timedelta(days=1))
        else:
            next_display = next_event

        days_to_next = days_until(next_display, today) if next_display else 0
        countdown = countdown_breakdown(next_display, today) if next_display and days_to_next > 0 else {}

        return {
            # Datetime objects for sensors with device_class: timestamp
            "next_date": _date_to_datetime(next_display),
            "last_date": _date_to_datetime(last_event),
            "days_until": days_to_next,
            "days_since_last": (today - last_event).days if last_event else None,
            "countdown_text": format_countdown_text(next_display, today) if next_display and days_to_next > 0 else "0 Tage",
            "countdown_breakdown": countdown,
            "occurrence_count": occ_count,
            # Binary sensor values
            "is_today": is_today_val,
        }

    def _check_expiry_repair(self, today: date) -> None:
        """Create or delete a Repairs issue based on event expiry state.

        Called on every coordinator update cycle. Idempotent — calling
        async_create_issue repeatedly with the same issue_id is safe in HA.
        """
        issue_id = f"expired_{self.config_entry.entry_id}"
        notify = self.event_data.get(CONF_NOTIFY_ON_EXPIRY, False)

        if not notify:
            # Clean up if the toggle was turned off after expiry was reported
            async_delete_issue(self.hass, DOMAIN, issue_id)
            return

        is_expired = False
        expiry_date = ""

        if self.event_type == EVENT_TYPE_TRIP:
            try:
                end_date = self._resolve_date(
                    CONF_END_DATE, CONF_END_DATE_USE_ENTITY, CONF_END_DATE_ENTITY_ID
                )
            except UpdateFailed:
                return  # Entity unavailable — skip expiry check
            if end_date is not None and end_date < today:
                is_expired = True
                expiry_date = end_date.isoformat()

        elif self.event_type == EVENT_TYPE_MILESTONE:
            try:
                target_date = self._resolve_date(
                    CONF_TARGET_DATE, CONF_EVENT_DATE_USE_ENTITY, CONF_EVENT_DATE_ENTITY_ID
                )
            except UpdateFailed:
                return  # Entity unavailable — skip expiry check
            if target_date is not None and target_date < today:
                is_expired = True
                expiry_date = target_date.isoformat()

        elif self.event_type == EVENT_TYPE_SPECIAL:
            special_category = self.event_data.get(CONF_SPECIAL_CATEGORY)
            if special_category == "custom_pattern":
                cp_end_type = self.event_data.get(CONF_CP_END_TYPE, "none")
                if cp_end_type != "none":
                    next_occurrence = next_custom_pattern(self.event_data, today)
                    if next_occurrence is None:
                        is_expired = True
                        until = self.event_data.get(CONF_CP_UNTIL)
                        if until:
                            expiry_date = until
                        else:
                            last = last_custom_pattern(self.event_data, today)
                            expiry_date = last.isoformat() if last else ""

        if is_expired:
            async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=True,
                severity=IssueSeverity.WARNING,
                translation_key="expired_event",
                translation_placeholders={
                    "event_name": self.config_entry.title,
                    "expiry_date": expiry_date,
                },
                data={
                    "entry_id": self.config_entry.entry_id,
                    "event_name": self.config_entry.title,
                    "expiry_date": expiry_date,
                },
            )
        else:
            async_delete_issue(self.hass, DOMAIN, issue_id)
