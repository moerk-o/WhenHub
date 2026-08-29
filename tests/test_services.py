"""Tests for FR15: the create_event / update_event / delete_event services.

Covered:
- happy path of every service for every event type it supports
- every error condition from the concept
- the response structure of all three services, including ``changed: {}``
- the reload after update_event (a sensor shows the new value)
- delete_event removing entry, device, entities and an open expiry issue
"""
from __future__ import annotations

from typing import Any

import pytest
from freezegun import freeze_time
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whenhub.const import (
    DOMAIN,
    SERVICE_CREATE_EVENT,
    SERVICE_DELETE_EVENT,
    SERVICE_UPDATE_EVENT,
)

# All tests run on a fixed date so sensor values are deterministic
NOW = "2026-05-01 12:00:00+00:00"

DATE_ENTITY = "sensor.holiday_start"
TIMESTAMP_ENTITY = "sensor.next_appointment"
PLAIN_ENTITY = "sensor.without_device_class"


# =============================================================================
# Fixtures and helpers
# =============================================================================


@pytest.fixture
async def whenhub(hass: HomeAssistant) -> None:
    """Load the integration so the services are registered."""
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()


@pytest.fixture
def date_entities(hass: HomeAssistant) -> None:
    """Provide entities that may and may not serve as a date source."""
    hass.states.async_set(DATE_ENTITY, "2026-09-01", {"device_class": "date"})
    hass.states.async_set(
        TIMESTAMP_ENTITY, "2026-10-05T08:00:00+00:00", {"device_class": "timestamp"}
    )
    hass.states.async_set(PLAIN_ENTITY, "2026-09-01", {})


async def _create(hass: HomeAssistant, **fields: Any) -> dict[str, Any]:
    """Call create_event and return its response."""
    return await hass.services.async_call(
        DOMAIN, SERVICE_CREATE_EVENT, fields, blocking=True, return_response=True
    )


async def _update(hass: HomeAssistant, device_id: str, **fields: Any) -> dict[str, Any]:
    """Call update_event for a device and return its response."""
    return await hass.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_EVENT,
        {"device_id": device_id, **fields},
        blocking=True,
        return_response=True,
    )


async def _delete(hass: HomeAssistant, device_id: str) -> dict[str, Any]:
    """Call delete_event for a device and return its response."""
    return await hass.services.async_call(
        DOMAIN,
        SERVICE_DELETE_EVENT,
        {"device_id": device_id},
        blocking=True,
        return_response=True,
    )


def _entry_data(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Return the stored data of a config entry."""
    return dict(hass.config_entries.async_get_entry(entry_id).data)


async def _add_entry(hass: HomeAssistant, title: str, data: dict) -> MockConfigEntry:
    """Add and set up a config entry that the services cannot create."""
    entry = MockConfigEntry(domain=DOMAIN, data=data, title=title, version=2)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _device_id(hass: HomeAssistant, entry_id: str) -> str:
    """Return the device ID of a WhenHub config entry."""
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, entry_id)})
    return device.id


# =============================================================================
# Registration
# =============================================================================


@freeze_time(NOW)
class TestServiceRegistration:
    """The services exist once and support optional responses."""

    async def test_all_three_services_registered(self, hass: HomeAssistant, whenhub):
        """async_setup registers exactly the three event services."""
        services = hass.services.async_services()[DOMAIN]
        assert sorted(services) == [
            SERVICE_CREATE_EVENT,
            SERVICE_DELETE_EVENT,
            SERVICE_UPDATE_EVENT,
        ]

    async def test_services_support_optional_response(
        self, hass: HomeAssistant, whenhub
    ):
        """All three services can be called with or without a response."""
        for service in (SERVICE_CREATE_EVENT, SERVICE_UPDATE_EVENT, SERVICE_DELETE_EVENT):
            assert (
                hass.services.async_services()[DOMAIN][service].supports_response
                is SupportsResponse.OPTIONAL
            )

    async def test_call_without_response_variable(self, hass: HomeAssistant, whenhub):
        """A call that does not ask for a response returns None and still works."""
        result = await hass.services.async_call(
            DOMAIN,
            SERVICE_CREATE_EVENT,
            {"event_type": "milestone", "name": "Silent", "target_date": "2026-06-01"},
            blocking=True,
        )
        assert result is None
        assert hass.states.get("sensor.silent_days_until") is not None


# =============================================================================
# create_event — happy paths
# =============================================================================


@freeze_time(NOW)
class TestCreateEvent:
    """One happy path per event type the service supports."""

    async def test_create_trip(self, hass: HomeAssistant, whenhub):
        """A trip is created with both dates and its sensors appear."""
        response = await _create(
            hass,
            event_type="trip",
            name="Denmark",
            start_date="2026-07-12",
            end_date="2026-07-26",
        )

        assert response["name"] == "Denmark"
        assert response["event_type"] == "trip"
        data = _entry_data(hass, response["entry_id"])
        assert data["event_type"] == "trip"
        assert data["start_date"] == "2026-07-12"
        assert data["end_date"] == "2026-07-26"
        assert data["start_date_use_entity"] is False
        assert hass.states.get("sensor.denmark_days_until").state == "72"

    async def test_create_milestone(self, hass: HomeAssistant, whenhub):
        """A milestone is created from a single target date."""
        response = await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        assert _entry_data(hass, response["entry_id"])["target_date"] == "2026-06-01"
        assert hass.states.get("sensor.deadline_days_until").state == "31"

    async def test_create_anniversary(self, hass: HomeAssistant, whenhub):
        """An anniversary keeps its original date and counts occurrences."""
        response = await _create(
            hass, event_type="anniversary", name="Birthday", target_date="1983-04-17"
        )

        assert _entry_data(hass, response["entry_id"])["target_date"] == "1983-04-17"
        # The count includes the original date, so 1983 through 2026 is 44
        assert hass.states.get("sensor.birthday_occurrences_count").state == "44"

    async def test_create_special_event(self, hass: HomeAssistant, whenhub):
        """A special event derives its category from the holiday."""
        response = await _create(
            hass, event_type="special", name="Easter", special_type="easter"
        )

        data = _entry_data(hass, response["entry_id"])
        assert data["event_type"] == "special"
        assert data["special_type"] == "easter"
        assert data["special_category"] == "traditional"
        assert hass.states.get("sensor.easter_days_until") is not None

    async def test_create_special_event_calendar_category(
        self, hass: HomeAssistant, whenhub
    ):
        """A calendar holiday gets the calendar category, not traditional."""
        response = await _create(
            hass, event_type="special", name="New Year", special_type="new_year"
        )

        assert _entry_data(hass, response["entry_id"])["special_category"] == "calendar"

    async def test_create_dst_event(self, hass: HomeAssistant, whenhub):
        """A DST event is stored as special with the dst category."""
        response = await _create(
            hass, event_type="dst", name="Clock change", dst_region="usa"
        )

        assert response["event_type"] == "dst"
        data = _entry_data(hass, response["entry_id"])
        assert data["event_type"] == "special"
        assert data["special_category"] == "dst"
        assert data["dst_region"] == "usa"
        assert data["dst_type"] == "next_change"

    async def test_create_dst_event_with_explicit_type(
        self, hass: HomeAssistant, whenhub
    ):
        """dst_type overrides the default."""
        response = await _create(
            hass,
            event_type="dst",
            name="Summer time",
            dst_region="eu",
            dst_type="next_summer",
        )

        assert _entry_data(hass, response["entry_id"])["dst_type"] == "next_summer"

    async def test_create_with_optional_fields(self, hass: HomeAssistant, whenhub):
        """Image path, URL, memo and the expiry toggle are stored."""
        response = await _create(
            hass,
            event_type="milestone",
            name="Move",
            target_date="2026-06-01",
            image_path="/local/whenhub/move.png",
            url="https://example.com/move",
            memo="Keys at noon",
            notify_on_expiry=True,
        )

        data = _entry_data(hass, response["entry_id"])
        assert data["image_path"] == "/local/whenhub/move.png"
        assert data["url"] == "https://example.com/move"
        assert data["memo"] == "Keys at noon"
        assert data["notify_on_expiry"] is True
        assert hass.states.get("sensor.move_url").state == "https://example.com/move"

    async def test_create_normalizes_the_date(self, hass: HomeAssistant, whenhub):
        """A compact ISO date is stored in the canonical YYYY-MM-DD form."""
        response = await _create(
            hass, event_type="milestone", name="Compact", target_date="20260601"
        )

        assert _entry_data(hass, response["entry_id"])["target_date"] == "2026-06-01"

    async def test_create_returns_device_id(self, hass: HomeAssistant, whenhub):
        """The response points at the device that was created."""
        response = await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        device = dr.async_get(hass).async_get(response["device_id"])
        assert device.name == "Deadline"
        assert device.identifiers == {(DOMAIN, response["entry_id"])}


@freeze_time(NOW)
class TestCreateEventWithEntitySource:
    """Dates that come from another entity instead of a fixed value."""

    async def test_trip_start_from_entity(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """The start date entity is stored and switched on."""
        response = await _create(
            hass,
            event_type="trip",
            name="Flexible",
            start_date_entity=DATE_ENTITY,
            end_date="2026-09-20",
        )

        data = _entry_data(hass, response["entry_id"])
        assert data["start_date_use_entity"] is True
        assert data["start_date_entity_id"] == DATE_ENTITY
        assert data["end_date_use_entity"] is False
        assert hass.states.get("sensor.flexible_days_until").state == "123"

    async def test_milestone_from_timestamp_entity(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """A timestamp entity is accepted as a date source."""
        response = await _create(
            hass,
            event_type="milestone",
            name="Appointment",
            target_date_entity=TIMESTAMP_ENTITY,
        )

        data = _entry_data(hass, response["entry_id"])
        assert data["event_date_use_entity"] is True
        assert data["event_date_entity_id"] == TIMESTAMP_ENTITY

    async def test_entity_source_stores_placeholder_date(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """A fixed date is kept as a placeholder so the calendar can read it."""
        response = await _create(
            hass,
            event_type="milestone",
            name="Appointment",
            target_date_entity=DATE_ENTITY,
        )

        assert _entry_data(hass, response["entry_id"])["target_date"] == "2026-05-01"

    async def test_unavailable_entity_leaves_entry_in_retry(
        self, hass: HomeAssistant, whenhub
    ):
        """An entity without a usable value defers setup, so there is no device yet."""
        hass.states.async_set("sensor.not_ready", "unknown", {"device_class": "date"})

        response = await _create(
            hass,
            event_type="milestone",
            name="Later",
            target_date_entity="sensor.not_ready",
        )

        assert response["device_id"] is None
        entry = hass.config_entries.async_get_entry(response["entry_id"])
        assert entry.state is ConfigEntryState.SETUP_RETRY


# =============================================================================
# create_event — errors
# =============================================================================


@freeze_time(NOW)
class TestCreateEventErrors:
    """Every rejected create_event call from the concept."""

    async def test_duplicate_name_is_rejected(self, hass: HomeAssistant, whenhub):
        """A name that is already taken fails instead of creating a second event."""
        await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        with pytest.raises(ServiceValidationError) as err:
            await _create(
                hass, event_type="milestone", name="Deadline", target_date="2026-07-01"
            )

        assert err.value.translation_key == "name_exists"
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    async def test_auto_rename_appends_a_number(self, hass: HomeAssistant, whenhub):
        """With auto_rename the second event becomes 'Deadline 2'."""
        await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        response = await _create(
            hass,
            event_type="milestone",
            name="Deadline",
            target_date="2026-07-01",
            auto_rename=True,
        )

        assert response["name"] == "Deadline 2"
        assert hass.config_entries.async_get_entry(response["entry_id"]).title == "Deadline 2"

    async def test_end_date_before_start_date(self, hass: HomeAssistant, whenhub):
        """A trip that ends before it starts is rejected."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(
                hass,
                event_type="trip",
                name="Backwards",
                start_date="2026-07-26",
                end_date="2026-07-12",
            )

        assert err.value.translation_key == "invalid_dates"
        assert hass.config_entries.async_entries(DOMAIN) == []

    async def test_end_date_equals_start_date(self, hass: HomeAssistant, whenhub):
        """A single-day trip is rejected, exactly as in the config flow."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(
                hass,
                event_type="trip",
                name="One day",
                start_date="2026-07-12",
                end_date="2026-07-12",
            )

        assert err.value.translation_key == "invalid_dates"

    async def test_invalid_date_format(self, hass: HomeAssistant, whenhub):
        """A date that is not ISO formatted is rejected."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(
                hass, event_type="milestone", name="German", target_date="01.06.2026"
            )

        assert err.value.translation_key == "invalid_date_format"

    async def test_missing_date_for_milestone(self, hass: HomeAssistant, whenhub):
        """A milestone without a date is rejected."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(hass, event_type="milestone", name="Nameless")

        assert err.value.translation_key == "missing_field"

    async def test_missing_end_date_for_trip(self, hass: HomeAssistant, whenhub):
        """A trip needs both dates."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(
                hass, event_type="trip", name="Half", start_date="2026-07-12"
            )

        assert err.value.translation_key == "missing_field"

    async def test_missing_special_type(self, hass: HomeAssistant, whenhub):
        """A special event needs a holiday."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(hass, event_type="special", name="Which one")

        assert err.value.translation_key == "missing_field"

    async def test_missing_dst_region(self, hass: HomeAssistant, whenhub):
        """A DST event needs a region."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(hass, event_type="dst", name="Where")

        assert err.value.translation_key == "missing_field"

    async def test_date_and_entity_together(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """A field takes either a fixed date or an entity, not both."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(
                hass,
                event_type="milestone",
                name="Both",
                target_date="2026-06-01",
                target_date_entity=DATE_ENTITY,
            )

        assert err.value.translation_key == "date_and_entity"

    async def test_field_of_another_event_type(self, hass: HomeAssistant, whenhub):
        """A trip field on a milestone is rejected."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(
                hass,
                event_type="milestone",
                name="Confused",
                target_date="2026-06-01",
                start_date="2026-06-01",
            )

        assert err.value.translation_key == "field_not_allowed"

    async def test_special_type_on_a_trip(self, hass: HomeAssistant, whenhub):
        """A holiday cannot be set on a trip."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(
                hass,
                event_type="trip",
                name="Confused",
                start_date="2026-07-12",
                end_date="2026-07-26",
                special_type="easter",
            )

        assert err.value.translation_key == "field_not_allowed"

    async def test_notify_on_expiry_for_anniversary(self, hass: HomeAssistant, whenhub):
        """An anniversary never expires, so the toggle is rejected."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(
                hass,
                event_type="anniversary",
                name="Birthday",
                target_date="1983-04-17",
                notify_on_expiry=True,
            )

        assert err.value.translation_key == "notify_not_supported"

    async def test_notify_on_expiry_false_for_anniversary(
        self, hass: HomeAssistant, whenhub
    ):
        """``notify_on_expiry: false`` is accepted for every type (no-op)."""
        created = await _create(
            hass,
            event_type="anniversary",
            name="Birthday",
            target_date="1983-04-17",
            notify_on_expiry=False,
        )

        entry = hass.config_entries.async_get_entry(created["entry_id"])
        assert entry.data["notify_on_expiry"] is False

    async def test_unknown_date_entity(self, hass: HomeAssistant, whenhub):
        """An entity that does not exist is rejected."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(
                hass,
                event_type="milestone",
                name="Ghost",
                target_date_entity="sensor.does_not_exist",
            )

        assert err.value.translation_key == "entity_not_found"

    async def test_entity_with_wrong_device_class(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """A date source needs device class date or timestamp."""
        with pytest.raises(ServiceValidationError) as err:
            await _create(
                hass,
                event_type="milestone",
                name="Wrong class",
                target_date_entity=PLAIN_ENTITY,
            )

        assert err.value.translation_key == "entity_wrong_device_class"


# =============================================================================
# update_event
# =============================================================================


@freeze_time(NOW)
class TestUpdateEvent:
    """Changing an existing event."""

    async def test_update_reloads_the_entry(self, hass: HomeAssistant, whenhub):
        """The sensor shows the new value when the blocking call returns."""
        created = await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )
        assert hass.states.get("sensor.deadline_days_until").state == "31"

        await _update(hass, created["device_id"], target_date="2026-06-10")

        assert hass.states.get("sensor.deadline_days_until").state == "40"

    async def test_response_lists_only_changed_fields(
        self, hass: HomeAssistant, whenhub
    ):
        """changed carries the old and new value of each touched field."""
        created = await _create(
            hass,
            event_type="milestone",
            name="Deadline",
            target_date="2026-06-01",
            memo="old note",
        )

        response = await _update(
            hass, created["device_id"], target_date="2026-06-10", memo="new note"
        )

        assert response["device_id"] == created["device_id"]
        assert response["name"] == "Deadline"
        assert response["changed"] == {
            "target_date": {"old": "2026-06-01", "new": "2026-06-10"},
            "memo": {"old": "old note", "new": "new note"},
        }

    async def test_unchanged_value_is_a_noop(self, hass: HomeAssistant, whenhub):
        """Writing the same value again changes nothing."""
        created = await _create(
            hass,
            event_type="milestone",
            name="Deadline",
            target_date="2026-06-01",
            memo="note",
        )

        response = await _update(
            hass, created["device_id"], target_date="2026-06-01", memo="note"
        )

        assert response["changed"] == {}

    async def test_call_without_any_field_is_a_noop(self, hass: HomeAssistant, whenhub):
        """A call that passes only the device is a no-op."""
        created = await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        response = await _update(hass, created["device_id"])

        assert response["changed"] == {}

    async def test_update_trip_dates(self, hass: HomeAssistant, whenhub):
        """Both trip dates can be changed in one call."""
        created = await _create(
            hass,
            event_type="trip",
            name="Denmark",
            start_date="2026-07-12",
            end_date="2026-07-26",
        )

        response = await _update(
            hass,
            created["device_id"],
            start_date="2026-08-01",
            end_date="2026-08-10",
        )

        assert set(response["changed"]) == {"start_date", "end_date"}
        data = _entry_data(hass, created["entry_id"])
        assert data["start_date"] == "2026-08-01"
        assert data["end_date"] == "2026-08-10"

    async def test_rename_event(self, hass: HomeAssistant, whenhub):
        """A rename updates the entry title and the device name."""
        created = await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        response = await _update(hass, created["device_id"], name="Final deadline")

        assert response["name"] == "Final deadline"
        assert response["changed"]["name"] == {
            "old": "Deadline",
            "new": "Final deadline",
        }
        assert hass.config_entries.async_get_entry(created["entry_id"]).title == (
            "Final deadline"
        )
        assert dr.async_get(hass).async_get(created["device_id"]).name == (
            "Final deadline"
        )

    async def test_rename_to_the_same_name_is_a_noop(
        self, hass: HomeAssistant, whenhub
    ):
        """Passing the current name changes nothing."""
        created = await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        response = await _update(hass, created["device_id"], name="Deadline")

        assert response["changed"] == {}

    async def test_switch_to_entity_source(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """Switching a fixed date to an entity needs no protection parameter."""
        created = await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        response = await _update(
            hass, created["device_id"], target_date_entity=DATE_ENTITY
        )

        assert response["changed"] == {
            "target_date": {"old": "2026-06-01", "new": None},
            "target_date_entity": {"old": None, "new": DATE_ENTITY},
        }
        data = _entry_data(hass, created["entry_id"])
        assert data["event_date_use_entity"] is True
        assert data["event_date_entity_id"] == DATE_ENTITY

    async def test_replace_date_source(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """replace_date_source detaches the entity and stores a fixed date."""
        created = await _create(
            hass,
            event_type="milestone",
            name="Deadline",
            target_date_entity=DATE_ENTITY,
        )

        response = await _update(
            hass,
            created["device_id"],
            target_date="2026-06-01",
            replace_date_source=True,
        )

        assert response["changed"] == {
            "target_date": {"old": None, "new": "2026-06-01"},
            "target_date_entity": {"old": DATE_ENTITY, "new": None},
        }
        data = _entry_data(hass, created["entry_id"])
        assert data["event_date_use_entity"] is False
        assert "event_date_entity_id" not in data
        assert hass.states.get("sensor.deadline_days_until").state == "31"

    async def test_switch_entity_source_to_another_entity(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """Only the entity key changes when swapping one source for another."""
        created = await _create(
            hass,
            event_type="milestone",
            name="Deadline",
            target_date_entity=DATE_ENTITY,
        )

        response = await _update(
            hass, created["device_id"], target_date_entity=TIMESTAMP_ENTITY
        )

        assert response["changed"] == {
            "target_date_entity": {"old": DATE_ENTITY, "new": TIMESTAMP_ENTITY}
        }

    async def test_clear_url_and_memo(self, hass: HomeAssistant, whenhub):
        """An empty string removes the URL and memo sensors."""
        created = await _create(
            hass,
            event_type="milestone",
            name="Deadline",
            target_date="2026-06-01",
            url="https://example.com",
            memo="note",
        )
        assert hass.states.get("sensor.deadline_url") is not None

        await _update(hass, created["device_id"], url="", memo="")

        assert hass.states.get("sensor.deadline_url") is None
        assert hass.states.get("sensor.deadline_memo") is None

    async def test_update_special_type_updates_the_category(
        self, hass: HomeAssistant, whenhub
    ):
        """Switching to a holiday of another category updates the category too."""
        created = await _create(
            hass, event_type="special", name="Holiday", special_type="easter"
        )

        response = await _update(hass, created["device_id"], special_type="new_year")

        assert response["changed"]["special_type"] == {
            "old": "easter",
            "new": "new_year",
        }
        assert _entry_data(hass, created["entry_id"])["special_category"] == "calendar"

    async def test_update_dst_fields(self, hass: HomeAssistant, whenhub):
        """Region and change type of a DST event can be updated."""
        created = await _create(
            hass, event_type="dst", name="Clock change", dst_region="eu"
        )

        response = await _update(
            hass, created["device_id"], dst_region="usa", dst_type="next_winter"
        )

        assert set(response["changed"]) == {"dst_region", "dst_type"}
        data = _entry_data(hass, created["entry_id"])
        assert data["dst_region"] == "usa"
        assert data["dst_type"] == "next_winter"

    async def test_update_anniversary(self, hass: HomeAssistant, whenhub):
        """An anniversary date can be corrected."""
        created = await _create(
            hass, event_type="anniversary", name="Birthday", target_date="1983-04-17"
        )

        await _update(hass, created["device_id"], target_date="1984-04-17")

        assert hass.states.get("sensor.birthday_occurrences_count").state == "43"

    async def test_update_custom_pattern_generic_fields(
        self, hass: HomeAssistant, whenhub
    ):
        """Custom pattern events accept the generic fields."""
        entry = await _add_entry(
            hass,
            "Cleaning day",
            {
                "event_type": "special",
                "special_category": "custom_pattern",
                "cp_freq": "monthly",
                "cp_dtstart": "2026-01-01",
                "cp_interval": 1,
                "cp_day_rule": "fixed_day",
                "cp_bymonthday": 15,
                "cp_end_type": "none",
            },
        )

        response = await _update(
            hass, _device_id(hass, entry.entry_id), memo="Bring gloves"
        )

        assert response["changed"] == {"memo": {"old": None, "new": "Bring gloves"}}
        assert hass.states.get("sensor.cleaning_day_memo").state == "Bring gloves"

    async def test_notify_on_expiry_for_custom_pattern_with_end(
        self, hass: HomeAssistant, whenhub
    ):
        """A custom pattern with an end condition can expire and accepts the toggle."""
        entry = await _add_entry(
            hass,
            "Course",
            {
                "event_type": "special",
                "special_category": "custom_pattern",
                "cp_freq": "weekly",
                "cp_dtstart": "2026-01-05",
                "cp_interval": 1,
                "cp_byday_list": [0],
                "cp_end_type": "count",
                "cp_count": 5,
            },
        )

        response = await _update(
            hass, _device_id(hass, entry.entry_id), notify_on_expiry=True
        )

        assert response["changed"]["notify_on_expiry"] == {"old": None, "new": True}


# =============================================================================
# update_event — errors
# =============================================================================


@freeze_time(NOW)
class TestUpdateEventErrors:
    """Every rejected update_event call from the concept."""

    async def test_unknown_device(self, hass: HomeAssistant, whenhub):
        """An unknown device ID is rejected."""
        with pytest.raises(ServiceValidationError) as err:
            await _update(hass, "does-not-exist", memo="x")

        assert err.value.translation_key == "device_not_found"

    async def test_device_of_another_integration(self, hass: HomeAssistant, whenhub):
        """A device that does not belong to WhenHub is rejected."""
        other = MockConfigEntry(domain="demo", data={}, title="Other")
        other.add_to_hass(hass)
        device = dr.async_get(hass).async_get_or_create(
            config_entry_id=other.entry_id, identifiers={("demo", "thing")}
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(hass, device.id, memo="x")

        assert err.value.translation_key == "device_not_whenhub"

    async def test_calendar_device(self, hass: HomeAssistant, whenhub):
        """A WhenHub calendar is not an event and cannot be updated."""
        entry = await _add_entry(
            hass,
            "WhenHub Calendar",
            {"entry_type": "calendar", "calendar_scope": "all"},
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(hass, _device_id(hass, entry.entry_id), memo="x")

        assert err.value.translation_key == "calendar_not_supported"

    async def test_fixed_date_while_entity_source_active(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """A fixed date does not silently replace an entity source."""
        created = await _create(
            hass,
            event_type="milestone",
            name="Deadline",
            target_date_entity=DATE_ENTITY,
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(hass, created["device_id"], target_date="2026-06-01")

        assert err.value.translation_key == "date_source_active"
        assert _entry_data(hass, created["entry_id"])["event_date_use_entity"] is True

    async def test_date_and_entity_together(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """A field takes either a fixed date or an entity, not both."""
        created = await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(
                hass,
                created["device_id"],
                target_date="2026-07-01",
                target_date_entity=DATE_ENTITY,
            )

        assert err.value.translation_key == "date_and_entity"

    async def test_field_of_another_event_type(self, hass: HomeAssistant, whenhub):
        """A milestone field on a trip is rejected."""
        created = await _create(
            hass,
            event_type="trip",
            name="Denmark",
            start_date="2026-07-12",
            end_date="2026-07-26",
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(hass, created["device_id"], target_date="2026-06-01")

        assert err.value.translation_key == "field_not_allowed"

    async def test_dst_field_on_a_custom_pattern(self, hass: HomeAssistant, whenhub):
        """Custom pattern events accept no type-specific fields at all."""
        entry = await _add_entry(
            hass,
            "Cleaning day",
            {
                "event_type": "special",
                "special_category": "custom_pattern",
                "cp_freq": "monthly",
                "cp_dtstart": "2026-01-01",
                "cp_interval": 1,
                "cp_day_rule": "fixed_day",
                "cp_bymonthday": 15,
                "cp_end_type": "none",
            },
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(hass, _device_id(hass, entry.entry_id), special_type="easter")

        assert err.value.translation_key == "field_not_allowed"

    async def test_notify_on_expiry_for_anniversary(self, hass: HomeAssistant, whenhub):
        """An anniversary never expires, so the toggle is rejected."""
        created = await _create(
            hass, event_type="anniversary", name="Birthday", target_date="1983-04-17"
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(hass, created["device_id"], notify_on_expiry=True)

        assert err.value.translation_key == "notify_not_supported"

    async def test_notify_on_expiry_false_for_anniversary_is_noop(
        self, hass: HomeAssistant, whenhub
    ):
        """``notify_on_expiry: false`` on a type that cannot expire changes nothing."""
        created = await _create(
            hass, event_type="anniversary", name="Birthday", target_date="1983-04-17"
        )

        response = await _update(hass, created["device_id"], notify_on_expiry=False)

        assert response["changed"] == {}

    async def test_notify_on_expiry_for_endless_custom_pattern(
        self, hass: HomeAssistant, whenhub
    ):
        """A pattern without an end condition can never expire."""
        entry = await _add_entry(
            hass,
            "Cleaning day",
            {
                "event_type": "special",
                "special_category": "custom_pattern",
                "cp_freq": "monthly",
                "cp_dtstart": "2026-01-01",
                "cp_interval": 1,
                "cp_day_rule": "fixed_day",
                "cp_bymonthday": 15,
                "cp_end_type": "none",
            },
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(
                hass, _device_id(hass, entry.entry_id), notify_on_expiry=True
            )

        assert err.value.translation_key == "notify_not_supported"

    async def test_end_date_before_start_date(self, hass: HomeAssistant, whenhub):
        """An update may not move the end date before the start date."""
        created = await _create(
            hass,
            event_type="trip",
            name="Denmark",
            start_date="2026-07-12",
            end_date="2026-07-26",
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(hass, created["device_id"], end_date="2026-07-01")

        assert err.value.translation_key == "invalid_dates"
        assert _entry_data(hass, created["entry_id"])["end_date"] == "2026-07-26"

    async def test_date_order_is_not_checked_against_an_entity_source(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """With an entity as start date the order is left to the coordinator."""
        created = await _create(
            hass,
            event_type="trip",
            name="Flexible",
            start_date_entity=DATE_ENTITY,
            end_date="2026-09-20",
        )

        response = await _update(hass, created["device_id"], end_date="2026-09-25")

        assert response["changed"]["end_date"]["new"] == "2026-09-25"

    async def test_invalid_date_format(self, hass: HomeAssistant, whenhub):
        """A date that is not ISO formatted is rejected."""
        created = await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(hass, created["device_id"], target_date="01.06.2026")

        assert err.value.translation_key == "invalid_date_format"

    async def test_entity_with_wrong_device_class(
        self, hass: HomeAssistant, whenhub, date_entities
    ):
        """A date source needs device class date or timestamp."""
        created = await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(hass, created["device_id"], target_date_entity=PLAIN_ENTITY)

        assert err.value.translation_key == "entity_wrong_device_class"

    async def test_rename_to_an_existing_name(self, hass: HomeAssistant, whenhub):
        """A rename may not collide with another event."""
        await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )
        second = await _create(
            hass, event_type="milestone", name="Other", target_date="2026-07-01"
        )

        with pytest.raises(ServiceValidationError) as err:
            await _update(hass, second["device_id"], name="Deadline")

        assert err.value.translation_key == "name_exists"
        assert hass.config_entries.async_get_entry(second["entry_id"]).title == "Other"


# =============================================================================
# delete_event
# =============================================================================


@freeze_time(NOW)
class TestDeleteEvent:
    """Removing an event."""

    async def test_delete_removes_entry_device_and_entities(
        self, hass: HomeAssistant, whenhub
    ):
        """Nothing of the event is left behind."""
        created = await _create(
            hass,
            event_type="trip",
            name="Denmark",
            start_date="2026-07-12",
            end_date="2026-07-26",
        )
        entry_id = created["entry_id"]
        assert hass.states.get("sensor.denmark_days_until") is not None

        await _delete(hass, created["device_id"])

        assert hass.config_entries.async_get_entry(entry_id) is None
        assert dr.async_get(hass).async_get(created["device_id"]) is None
        assert (
            er.async_entries_for_config_entry(er.async_get(hass), entry_id) == []
        )
        assert hass.states.get("sensor.denmark_days_until") is None

    async def test_delete_response_lists_removed_entities(
        self, hass: HomeAssistant, whenhub
    ):
        """The response names every entity that disappeared."""
        created = await _create(
            hass, event_type="milestone", name="Deadline", target_date="2026-06-01"
        )

        response = await _delete(hass, created["device_id"])

        assert response["device_id"] == created["device_id"]
        assert response["entry_id"] == created["entry_id"]
        assert response["name"] == "Deadline"
        assert response["event_type"] == "milestone"
        assert response["removed_entities"] == [
            "binary_sensor.deadline_is_today",
            "image.deadline_event_image",
            "sensor.deadline_days_until",
            "sensor.deadline_event_date",
        ]

    async def test_delete_removes_open_expiry_issue(
        self, hass: HomeAssistant, whenhub
    ):
        """An expiry repair for the deleted event is gone as well."""
        created = await _create(
            hass,
            event_type="milestone",
            name="Long gone",
            target_date="2020-01-01",
            notify_on_expiry=True,
        )
        await hass.async_block_till_done()
        issue_id = f"expired_{created['entry_id']}"
        assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is not None

        await _delete(hass, created["device_id"])

        assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None

    async def test_delete_custom_pattern_event(self, hass: HomeAssistant, whenhub):
        """Custom pattern events can be deleted even though they cannot be created."""
        entry = await _add_entry(
            hass,
            "Cleaning day",
            {
                "event_type": "special",
                "special_category": "custom_pattern",
                "cp_freq": "monthly",
                "cp_dtstart": "2026-01-01",
                "cp_interval": 1,
                "cp_day_rule": "fixed_day",
                "cp_bymonthday": 15,
                "cp_end_type": "none",
            },
        )

        response = await _delete(hass, _device_id(hass, entry.entry_id))

        assert response["event_type"] == "custom_pattern"
        assert hass.config_entries.async_get_entry(entry.entry_id) is None

    async def test_delete_dst_event(self, hass: HomeAssistant, whenhub):
        """A DST event reports its service event type, not the stored one."""
        created = await _create(
            hass, event_type="dst", name="Clock change", dst_region="eu"
        )

        response = await _delete(hass, created["device_id"])

        assert response["event_type"] == "dst"

    async def test_delete_unknown_device(self, hass: HomeAssistant, whenhub):
        """An unknown device ID is rejected."""
        with pytest.raises(ServiceValidationError) as err:
            await _delete(hass, "does-not-exist")

        assert err.value.translation_key == "device_not_found"

    async def test_delete_calendar_device(self, hass: HomeAssistant, whenhub):
        """A WhenHub calendar cannot be deleted through the event services."""
        entry = await _add_entry(
            hass,
            "WhenHub Calendar",
            {"entry_type": "calendar", "calendar_scope": "all"},
        )

        with pytest.raises(ServiceValidationError) as err:
            await _delete(hass, _device_id(hass, entry.entry_id))

        assert err.value.translation_key == "calendar_not_supported"
        assert hass.config_entries.async_get_entry(entry.entry_id) is not None
