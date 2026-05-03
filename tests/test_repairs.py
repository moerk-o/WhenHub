"""Tests for FR13: Expiry notification via HA Repairs.

Tests the _check_expiry_repair() logic in WhenHubCoordinator using mocked
HA repairs functions and lightweight stubs — no HA runtime required.
"""
from __future__ import annotations

import sys
import os
from datetime import date
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from custom_components.whenhub.const import (
    DOMAIN,
    CONF_NOTIFY_ON_EXPIRY,
    CONF_START_DATE,
    CONF_END_DATE,
    CONF_TARGET_DATE,
    CONF_CP_END_TYPE,
    CONF_CP_UNTIL,
    CONF_CP_DTSTART,
    CONF_CP_FREQ,
    CONF_CP_INTERVAL,
    CONF_CP_DAY_RULE,
    CONF_CP_BYDAY_LIST,
    CONF_SPECIAL_CATEGORY,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
    EVENT_TYPE_SPECIAL,
)


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class _FakeHass:
    """Minimal hass stub — repairs functions are patched at module level."""


class _FakeConfigEntry:
    def __init__(self, entry_id="test_id", title="Test Event"):
        self.entry_id = entry_id
        self.title = title


def _make_coordinator(event_type: str, event_data: dict):
    """Create a WhenHubCoordinator instance bypassing __init__."""
    from custom_components.whenhub.coordinator import WhenHubCoordinator

    coord = object.__new__(WhenHubCoordinator)
    coord.hass = _FakeHass()
    coord.config_entry = _FakeConfigEntry()
    coord.event_type = event_type
    coord.event_data = event_data
    return coord


# ---------------------------------------------------------------------------
# Helper: patch both repairs functions and return mocks
# ---------------------------------------------------------------------------

PATCH_CREATE = "custom_components.whenhub.coordinator.async_create_issue"
PATCH_DELETE = "custom_components.whenhub.coordinator.async_delete_issue"


# ---------------------------------------------------------------------------
# Trip expiry tests
# ---------------------------------------------------------------------------

class TestTripExpiry:
    """_check_expiry_repair for EVENT_TYPE_TRIP."""

    def test_no_action_when_toggle_off(self):
        """With notify_on_expiry=False, only delete is called (cleanup)."""
        data = {
            CONF_END_DATE: "2020-01-01",  # past
            CONF_NOTIFY_ON_EXPIRY: False,
        }
        coord = _make_coordinator(EVENT_TYPE_TRIP, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_create.assert_not_called()
        mock_delete.assert_called_once_with(
            coord.hass, DOMAIN, f"expired_{coord.config_entry.entry_id}"
        )

    def test_create_issue_when_trip_expired(self):
        """Issue created when end_date is in the past and toggle is on."""
        data = {
            CONF_END_DATE: "2024-12-31",
            CONF_NOTIFY_ON_EXPIRY: True,
        }
        coord = _make_coordinator(EVENT_TYPE_TRIP, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_delete.assert_not_called()
        mock_create.assert_called_once()
        kwargs = mock_create.call_args
        assert kwargs[0][0] is coord.hass
        assert kwargs[0][1] == DOMAIN
        assert kwargs[0][2] == f"expired_{coord.config_entry.entry_id}"
        assert kwargs[1]["is_fixable"] is True
        assert kwargs[1]["translation_key"] == "expired_event"
        assert kwargs[1]["data"]["expiry_date"] == "2024-12-31"
        assert kwargs[1]["data"]["entry_id"] == coord.config_entry.entry_id

    def test_delete_issue_when_trip_not_yet_expired(self):
        """Issue deleted when end_date is today or in the future."""
        data = {
            CONF_END_DATE: "2026-05-01",  # today — not expired
            CONF_NOTIFY_ON_EXPIRY: True,
        }
        coord = _make_coordinator(EVENT_TYPE_TRIP, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_create.assert_not_called()
        mock_delete.assert_called_once()

    def test_delete_issue_when_trip_future(self):
        """Issue deleted when end_date is clearly in the future."""
        data = {
            CONF_END_DATE: "2028-01-01",
            CONF_NOTIFY_ON_EXPIRY: True,
        }
        coord = _make_coordinator(EVENT_TYPE_TRIP, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_create.assert_not_called()
        mock_delete.assert_called_once()

    def test_expired_day_after_end_date(self):
        """Trip is expired the day after end_date."""
        data = {
            CONF_END_DATE: "2026-04-30",
            CONF_NOTIFY_ON_EXPIRY: True,
        }
        coord = _make_coordinator(EVENT_TYPE_TRIP, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE):
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_create.assert_called_once()


# ---------------------------------------------------------------------------
# Milestone expiry tests
# ---------------------------------------------------------------------------

class TestMilestoneExpiry:
    """_check_expiry_repair for EVENT_TYPE_MILESTONE."""

    def test_create_issue_when_milestone_expired(self):
        """Issue created when target_date is in the past and toggle is on."""
        data = {
            CONF_TARGET_DATE: "2023-06-15",
            CONF_NOTIFY_ON_EXPIRY: True,
        }
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_delete.assert_not_called()
        mock_create.assert_called_once()
        assert mock_create.call_args[1]["data"]["expiry_date"] == "2023-06-15"

    def test_delete_issue_when_milestone_not_expired(self):
        """Issue deleted when target_date is today or future."""
        data = {
            CONF_TARGET_DATE: "2026-05-01",  # today
            CONF_NOTIFY_ON_EXPIRY: True,
        }
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_create.assert_not_called()
        mock_delete.assert_called_once()

    def test_no_action_when_toggle_off_milestone(self):
        """With notify_on_expiry=False, only cleanup delete is called."""
        data = {
            CONF_TARGET_DATE: "2020-01-01",  # past
            CONF_NOTIFY_ON_EXPIRY: False,
        }
        coord = _make_coordinator(EVENT_TYPE_MILESTONE, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_create.assert_not_called()
        mock_delete.assert_called_once()


# ---------------------------------------------------------------------------
# Anniversary — should never trigger expiry
# ---------------------------------------------------------------------------

class TestAnniversaryNoExpiry:
    """Anniversary events are recurring — never expire."""

    def test_no_issue_created_for_anniversary(self):
        """Anniversary events ignore the expiry check entirely."""
        data = {
            CONF_TARGET_DATE: "2000-01-01",
            CONF_NOTIFY_ON_EXPIRY: True,
        }
        coord = _make_coordinator(EVENT_TYPE_ANNIVERSARY, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        # notify=True but anniversary — neither branch sets is_expired → delete called
        mock_create.assert_not_called()
        mock_delete.assert_called_once()


# ---------------------------------------------------------------------------
# Custom Pattern expiry tests
# ---------------------------------------------------------------------------

def _cp_weekly_data(end_type: str, cp_until: str | None = None, cp_count: int | None = None) -> dict:
    """Create minimal custom pattern event data for a weekly Monday pattern."""
    return {
        "event_type": EVENT_TYPE_SPECIAL,
        CONF_SPECIAL_CATEGORY: "custom_pattern",
        CONF_CP_FREQ: "weekly",
        CONF_CP_INTERVAL: 1,
        CONF_CP_DTSTART: "2020-01-06",  # Monday
        CONF_CP_DAY_RULE: "fixed_day",
        CONF_CP_BYDAY_LIST: [0],          # Monday
        CONF_CP_END_TYPE: end_type,
        CONF_CP_UNTIL: cp_until,
        "cp_count": cp_count,
        "cp_bymonth": None,
        "cp_byday_pos": None,
        "cp_byday_weekday": None,
        "cp_bymonthday": None,
        "cp_exdates": [],
        CONF_NOTIFY_ON_EXPIRY: True,
    }


class TestCustomPatternExpiry:
    """_check_expiry_repair for custom pattern events."""

    def test_no_expiry_for_open_ended_pattern(self):
        """Pattern with cp_end_type='none' never expires."""
        data = _cp_weekly_data(end_type="none")
        coord = _make_coordinator(EVENT_TYPE_SPECIAL, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_create.assert_not_called()
        mock_delete.assert_called_once()

    def test_create_issue_when_until_date_passed(self):
        """Issue created when cp_until is in the past and no future occurrence."""
        # Weekly on Monday, ended 2024-01-01 — no future occurrences in 2026
        data = _cp_weekly_data(end_type="until", cp_until="2024-01-01")
        coord = _make_coordinator(EVENT_TYPE_SPECIAL, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_create.assert_called_once()
        assert mock_create.call_args[1]["translation_key"] == "expired_event"
        # expiry_date should be the cp_until date
        assert mock_create.call_args[1]["data"]["expiry_date"] == "2024-01-01"

    def test_create_issue_when_count_exhausted(self):
        """Issue created when all occurrences are consumed."""
        # 3 occurrences starting 2020-01-06 (weekly Monday)
        # occurrences: 2020-01-06, 2020-01-13, 2020-01-20 — all past
        data = _cp_weekly_data(end_type="count", cp_count=3)
        coord = _make_coordinator(EVENT_TYPE_SPECIAL, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_create.assert_called_once()

    def test_no_issue_when_pattern_has_future_occurrences(self):
        """No issue when cp_until is in the future."""
        data = _cp_weekly_data(end_type="until", cp_until="2030-01-01")
        coord = _make_coordinator(EVENT_TYPE_SPECIAL, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_create.assert_not_called()
        mock_delete.assert_called_once()

    def test_toggle_off_does_not_create_issue_for_cp(self):
        """Toggle off: no issue created even for expired CP."""
        data = _cp_weekly_data(end_type="until", cp_until="2024-01-01")
        data[CONF_NOTIFY_ON_EXPIRY] = False
        coord = _make_coordinator(EVENT_TYPE_SPECIAL, data)

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        mock_create.assert_not_called()
        mock_delete.assert_called_once()


# ---------------------------------------------------------------------------
# Issue ID stability
# ---------------------------------------------------------------------------

class TestIssueId:
    """Issue ID is stable and matches entry_id."""

    def test_issue_id_uses_entry_id(self):
        """issue_id is always 'expired_{entry_id}'."""
        data = {CONF_END_DATE: "2020-01-01", CONF_NOTIFY_ON_EXPIRY: True}
        coord = _make_coordinator(EVENT_TYPE_TRIP, data)
        coord.config_entry = _FakeConfigEntry(entry_id="abc123")

        with patch(PATCH_CREATE) as mock_create, patch(PATCH_DELETE):
            coord._check_expiry_repair(date(2026, 5, 1))

        assert mock_create.call_args[0][2] == "expired_abc123"

    def test_delete_uses_same_issue_id(self):
        """Delete call also uses 'expired_{entry_id}'."""
        data = {CONF_END_DATE: "2028-01-01", CONF_NOTIFY_ON_EXPIRY: True}
        coord = _make_coordinator(EVENT_TYPE_TRIP, data)
        coord.config_entry = _FakeConfigEntry(entry_id="xyz999")

        with patch(PATCH_CREATE), patch(PATCH_DELETE) as mock_delete:
            coord._check_expiry_repair(date(2026, 5, 1))

        assert mock_delete.call_args[0][2] == "expired_xyz999"
