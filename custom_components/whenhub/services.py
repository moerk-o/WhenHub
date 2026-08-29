"""Services for creating, updating and deleting WhenHub events (FR15).

Three services are registered once in `async_setup` (not per config entry):

- `whenhub.create_event` — runs the config flow import step, which applies the
  same name and date validation as the user flow.
- `whenhub.update_event` — addressed by `device_id`; writes the config entry and
  reloads it so entities show the new values when the call returns.
- `whenhub.delete_event` — addressed by `device_id`; removes the config entry
  including its device, entities and any open expiry Repairs issue.

All three use `SupportsResponse.OPTIONAL`, so they can be called from a dashboard
button or an automation without a `response_variable`. Every rejected call raises
`ServiceValidationError` with a `translation_key` from the `exceptions` block of
the translation files.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .config_flow import existing_event_names, validate_trip_date_order
from .const import (
    ATTR_AUTO_RENAME,
    ATTR_CHANGED,
    ATTR_DEVICE_ID,
    ATTR_END_DATE_ENTITY,
    ATTR_ENTRY_ID,
    ATTR_NAME,
    ATTR_REMOVED_ENTITIES,
    ATTR_REPLACE_DATE_SOURCE,
    ATTR_START_DATE_ENTITY,
    ATTR_TARGET_DATE_ENTITY,
    CONF_CP_END_TYPE,
    CONF_DST_REGION,
    CONF_DST_TYPE,
    CONF_END_DATE,
    CONF_END_DATE_ENTITY_ID,
    CONF_END_DATE_USE_ENTITY,
    CONF_ENTRY_TYPE,
    CONF_EVENT_DATE_ENTITY_ID,
    CONF_EVENT_DATE_USE_ENTITY,
    CONF_EVENT_TYPE,
    CONF_IMAGE_PATH,
    CONF_MEMO,
    CONF_NOTIFY_ON_EXPIRY,
    CONF_SPECIAL_CATEGORY,
    CONF_SPECIAL_TYPE,
    CONF_START_DATE,
    CONF_START_DATE_ENTITY_ID,
    CONF_START_DATE_USE_ENTITY,
    CONF_TARGET_DATE,
    CONF_URL,
    DATE_SOURCE_DEVICE_CLASSES,
    DEFAULT_DST_TYPE,
    DOMAIN,
    DST_EVENT_TYPES,
    DST_REGIONS,
    ENTRY_TYPE_CALENDAR,
    EVENT_TYPE_ANNIVERSARY,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_SPECIAL,
    EVENT_TYPE_TRIP,
    SERVICE_CREATE_EVENT,
    SERVICE_DELETE_EVENT,
    SERVICE_EVENT_TYPE_DST,
    SERVICE_EVENT_TYPES,
    SERVICE_UPDATE_EVENT,
    SPECIAL_CATEGORY_CUSTOM_PATTERN,
    SPECIAL_CATEGORY_DST,
    SPECIAL_EVENTS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class _DateField:
    """One date field of an event, with its fixed and entity-sourced storage keys.

    `date_key` is both the service parameter name and the config entry key.
    """

    date_key: str
    entity_key: str
    use_entity_key: str
    entity_id_key: str


_TRIP_START = _DateField(
    CONF_START_DATE,
    ATTR_START_DATE_ENTITY,
    CONF_START_DATE_USE_ENTITY,
    CONF_START_DATE_ENTITY_ID,
)
_TRIP_END = _DateField(
    CONF_END_DATE,
    ATTR_END_DATE_ENTITY,
    CONF_END_DATE_USE_ENTITY,
    CONF_END_DATE_ENTITY_ID,
)
_TARGET = _DateField(
    CONF_TARGET_DATE,
    ATTR_TARGET_DATE_ENTITY,
    CONF_EVENT_DATE_USE_ENTITY,
    CONF_EVENT_DATE_ENTITY_ID,
)

# Date fields per service event type
_DATE_FIELDS: dict[str, tuple[_DateField, ...]] = {
    EVENT_TYPE_TRIP: (_TRIP_START, _TRIP_END),
    EVENT_TYPE_MILESTONE: (_TARGET,),
    EVENT_TYPE_ANNIVERSARY: (_TARGET,),
}

# Type-specific service parameters per service event type. Everything not listed
# for the event type at hand is rejected with "field_not_allowed".
_TYPE_FIELDS: dict[str, tuple[str, ...]] = {
    EVENT_TYPE_TRIP: (
        CONF_START_DATE,
        CONF_END_DATE,
        ATTR_START_DATE_ENTITY,
        ATTR_END_DATE_ENTITY,
    ),
    EVENT_TYPE_MILESTONE: (CONF_TARGET_DATE, ATTR_TARGET_DATE_ENTITY),
    EVENT_TYPE_ANNIVERSARY: (CONF_TARGET_DATE, ATTR_TARGET_DATE_ENTITY),
    EVENT_TYPE_SPECIAL: (CONF_SPECIAL_TYPE,),
    SERVICE_EVENT_TYPE_DST: (CONF_DST_REGION, CONF_DST_TYPE),
    SPECIAL_CATEGORY_CUSTOM_PATTERN: (),
}

# Stable order so a call with several wrong fields always reports the same one
_ALL_TYPE_FIELDS: tuple[str, ...] = (
    CONF_START_DATE,
    CONF_END_DATE,
    ATTR_START_DATE_ENTITY,
    ATTR_END_DATE_ENTITY,
    CONF_TARGET_DATE,
    ATTR_TARGET_DATE_ENTITY,
    CONF_SPECIAL_TYPE,
    CONF_DST_REGION,
    CONF_DST_TYPE,
)

# Parameters that every event type accepts
_GENERIC_FIELDS: tuple[str, ...] = (CONF_IMAGE_PATH, CONF_URL, CONF_MEMO)

# Event types whose events can expire, and therefore support notify_on_expiry
_NOTIFY_CREATE_TYPES = (EVENT_TYPE_TRIP, EVENT_TYPE_MILESTONE)

# Parameters handled by _apply_date_field rather than copied straight through
_DATE_PARAMETERS: frozenset[str] = frozenset(
    key
    for field in (_TRIP_START, _TRIP_END, _TARGET)
    for key in (field.date_key, field.entity_key)
)


_DATE_FIELD_SCHEMA = {
    vol.Optional(CONF_START_DATE): cv.string,
    vol.Optional(CONF_END_DATE): cv.string,
    vol.Optional(CONF_TARGET_DATE): cv.string,
    vol.Optional(ATTR_START_DATE_ENTITY): cv.entity_id,
    vol.Optional(ATTR_END_DATE_ENTITY): cv.entity_id,
    vol.Optional(ATTR_TARGET_DATE_ENTITY): cv.entity_id,
}

_COMMON_FIELD_SCHEMA = {
    vol.Optional(CONF_SPECIAL_TYPE): vol.In(list(SPECIAL_EVENTS)),
    vol.Optional(CONF_DST_REGION): vol.In(list(DST_REGIONS)),
    vol.Optional(CONF_DST_TYPE): vol.In(list(DST_EVENT_TYPES)),
    vol.Optional(CONF_IMAGE_PATH): cv.string,
    vol.Optional(CONF_URL): cv.string,
    vol.Optional(CONF_MEMO): cv.string,
    vol.Optional(CONF_NOTIFY_ON_EXPIRY): cv.boolean,
}

CREATE_EVENT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EVENT_TYPE): vol.In(SERVICE_EVENT_TYPES),
        vol.Required(ATTR_NAME): cv.string,
        vol.Optional(ATTR_AUTO_RENAME, default=False): cv.boolean,
        **_DATE_FIELD_SCHEMA,
        **_COMMON_FIELD_SCHEMA,
    }
)

UPDATE_EVENT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Optional(ATTR_NAME): cv.string,
        vol.Optional(ATTR_REPLACE_DATE_SOURCE, default=False): cv.boolean,
        **_DATE_FIELD_SCHEMA,
        **_COMMON_FIELD_SCHEMA,
    }
)

DELETE_EVENT_SCHEMA = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string})


def _error(key: str, **placeholders: str) -> ServiceValidationError:
    """Build a ServiceValidationError translated via the exceptions block."""
    return ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key=key,
        translation_placeholders=placeholders,
    )


def _validate_date(value: str, field: str) -> str:
    """Return the date normalized to YYYY-MM-DD, or raise for a bad value.

    Normalizing matters because trip dates are compared as strings and stored
    dates are read back by the calendar entity and the options flow.
    """
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as err:
        raise _error("invalid_date_format", value=value, field=field) from err


def _validate_date_entity(hass: HomeAssistant, entity_id: str) -> None:
    """Check that an entity exists and can serve as a date source.

    Mirrors the entity picker in the config flow, which offers only entities
    with device class 'date' or 'timestamp'.
    """
    state = hass.states.get(entity_id)
    if state is None:
        raise _error("entity_not_found", entity_id=entity_id)
    if state.attributes.get("device_class") not in DATE_SOURCE_DEVICE_CLASSES:
        raise _error("entity_wrong_device_class", entity_id=entity_id)


def _service_event_type(entry_data: dict[str, Any]) -> str:
    """Return the event type in service vocabulary.

    DST and custom pattern events are stored as 'special' with a category; the
    services address them as their own types.
    """
    event_type = entry_data.get(CONF_EVENT_TYPE, EVENT_TYPE_TRIP)
    if event_type == EVENT_TYPE_SPECIAL:
        category = entry_data.get(CONF_SPECIAL_CATEGORY)
        if category == SPECIAL_CATEGORY_DST:
            return SERVICE_EVENT_TYPE_DST
        if category == SPECIAL_CATEGORY_CUSTOM_PATTERN:
            return SPECIAL_CATEGORY_CUSTOM_PATTERN
    return event_type


def _resolve_entry(hass: HomeAssistant, device_id: str) -> ConfigEntry:
    """Return the WhenHub event config entry behind a device ID."""
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        raise _error("device_not_found", device_id=device_id)

    for entry_id in device.config_entries:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is not None and entry.domain == DOMAIN:
            if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
                raise _error("calendar_not_supported", device_id=device_id)
            return entry

    raise _error("device_not_whenhub", device_id=device_id)


def _check_type_fields(data: dict[str, Any], event_type: str) -> None:
    """Reject parameters that do not belong to this event type."""
    allowed = _TYPE_FIELDS.get(event_type, ())
    for field in _ALL_TYPE_FIELDS:
        if field not in allowed and field in data:
            raise _error("field_not_allowed", field=field, event_type=event_type)


def _check_notify_supported(
    data: dict[str, Any], event_type: str, supported: tuple[str, ...]
) -> None:
    """Reject enabling notify_on_expiry for event types that cannot expire.

    Passing ``notify_on_expiry: false`` is accepted for every type so that a
    generic script can always send the parameter; only ``true`` is an error.
    """
    if data.get(CONF_NOTIFY_ON_EXPIRY) and event_type not in supported:
        raise _error("notify_not_supported", event_type=event_type)


def _required(data: dict[str, Any], field: str, event_type: str) -> Any:
    """Return a required parameter or raise a translated error."""
    if field not in data:
        raise _error("missing_field", field=field, event_type=event_type)
    return data[field]


def _new_date_source(
    hass: HomeAssistant,
    data: dict[str, Any],
    field: _DateField,
    event_type: str,
) -> dict[str, Any]:
    """Return the config entry keys for one date field of a new event."""
    has_date = field.date_key in data
    has_entity = field.entity_key in data

    if has_date and has_entity:
        raise _error(
            "date_and_entity", field=field.date_key, entity_field=field.entity_key
        )

    if has_entity:
        entity_id = data[field.entity_key]
        _validate_date_entity(hass, entity_id)
        # A fixed date is stored as a placeholder even when the entity provides
        # the value: the calendar entity reads the key directly, and the options
        # flow pre-fills it when the entity source is switched off again.
        return {
            field.date_key: date.today().isoformat(),
            field.use_entity_key: True,
            field.entity_id_key: entity_id,
        }

    if not has_date:
        raise _error("missing_field", field=field.date_key, event_type=event_type)

    return {
        field.date_key: _validate_date(data[field.date_key], field.date_key),
        field.use_entity_key: False,
    }


def _build_event_data(
    hass: HomeAssistant, data: dict[str, Any], event_type: str
) -> dict[str, Any]:
    """Assemble the config entry data for a new event."""
    entry_data: dict[str, Any] = {
        CONF_EVENT_TYPE: (
            EVENT_TYPE_SPECIAL if event_type == SERVICE_EVENT_TYPE_DST else event_type
        )
    }

    for field in _DATE_FIELDS.get(event_type, ()):
        entry_data.update(_new_date_source(hass, data, field, event_type))

    if event_type == EVENT_TYPE_SPECIAL:
        special_type = _required(data, CONF_SPECIAL_TYPE, event_type)
        entry_data[CONF_SPECIAL_TYPE] = special_type
        entry_data[CONF_SPECIAL_CATEGORY] = SPECIAL_EVENTS[special_type]["category"]
    elif event_type == SERVICE_EVENT_TYPE_DST:
        entry_data[CONF_SPECIAL_CATEGORY] = SPECIAL_CATEGORY_DST
        entry_data[CONF_DST_REGION] = _required(data, CONF_DST_REGION, event_type)
        entry_data[CONF_DST_TYPE] = data.get(CONF_DST_TYPE, DEFAULT_DST_TYPE)

    for field in _GENERIC_FIELDS:
        entry_data[field] = data.get(field, "")
    entry_data[CONF_NOTIFY_ON_EXPIRY] = data.get(CONF_NOTIFY_ON_EXPIRY, False)

    return entry_data


def _notify_types_for_update(entry_data: dict[str, Any]) -> tuple[str, ...]:
    """Return the event types that accept notify_on_expiry in update_event.

    Custom pattern events only expire when an end condition is configured —
    the same rule the options flow applies.
    """
    if entry_data.get(CONF_CP_END_TYPE, "none") != "none":
        return (*_NOTIFY_CREATE_TYPES, SPECIAL_CATEGORY_CUSTOM_PATTERN)
    return _NOTIFY_CREATE_TYPES


def _apply_date_field(
    hass: HomeAssistant,
    entry_data: dict[str, Any],
    new_data: dict[str, Any],
    changed: dict[str, dict[str, Any]],
    data: dict[str, Any],
    field: _DateField,
    replace_date_source: bool,
) -> None:
    """Apply one date field of an update call to `new_data` and `changed`."""
    has_date = field.date_key in data
    has_entity = field.entity_key in data

    if not has_date and not has_entity:
        return
    if has_date and has_entity:
        raise _error(
            "date_and_entity", field=field.date_key, entity_field=field.entity_key
        )

    from_entity = bool(entry_data.get(field.use_entity_key))
    old_date = None if from_entity else entry_data.get(field.date_key)
    old_entity = entry_data.get(field.entity_id_key) if from_entity else None

    if has_entity:
        new_entity = data[field.entity_key]
        _validate_date_entity(hass, new_entity)
        new_data[field.use_entity_key] = True
        new_data[field.entity_id_key] = new_entity
        new_date = None
    else:
        if from_entity and not replace_date_source:
            raise _error(
                "date_source_active", field=field.date_key, entity_id=old_entity or ""
            )
        new_date = _validate_date(data[field.date_key], field.date_key)
        new_data[field.date_key] = new_date
        new_data[field.use_entity_key] = False
        new_data.pop(field.entity_id_key, None)
        new_entity = None

    if new_date != old_date:
        changed[field.date_key] = {"old": old_date, "new": new_date}
    if new_entity != old_entity:
        changed[field.entity_key] = {"old": old_entity, "new": new_entity}


def _check_trip_date_order(new_data: dict[str, Any]) -> None:
    """Reject an update that would leave a trip's end before its start.

    Only fixed dates are checked; an entity-sourced date can change at any time
    and is validated by the coordinator on every refresh.
    """
    from_entity_start = new_data.get(CONF_START_DATE_USE_ENTITY)
    from_entity_end = new_data.get(CONF_END_DATE_USE_ENTITY)
    start = "" if from_entity_start else new_data.get(CONF_START_DATE, "")
    end = "" if from_entity_end else new_data.get(CONF_END_DATE, "")
    if start and end and (error := validate_trip_date_order(start, end)):
        raise _error(error)


async def _async_create_event(call: ServiceCall) -> ServiceResponse:
    """Handle whenhub.create_event."""
    hass = call.hass
    data = call.data
    event_type: str = data[CONF_EVENT_TYPE]

    _check_type_fields(data, event_type)
    _check_notify_supported(data, event_type, _NOTIFY_CREATE_TYPES)

    entry_data = _build_event_data(hass, data, event_type)
    entry_data[ATTR_NAME] = data[ATTR_NAME]
    entry_data[ATTR_AUTO_RENAME] = data[ATTR_AUTO_RENAME]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=entry_data
    )
    if result["type"] is FlowResultType.ABORT:
        raise _error(result["reason"], name=data[ATTR_NAME])

    entry: ConfigEntry = result["result"]
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, entry.entry_id)})

    _LOGGER.info("WhenHub event created via service: %s (%s)", entry.title, event_type)

    return {
        ATTR_DEVICE_ID: device.id if device else None,
        ATTR_ENTRY_ID: entry.entry_id,
        ATTR_NAME: entry.title,
        CONF_EVENT_TYPE: event_type,
    }


async def _async_update_event(call: ServiceCall) -> ServiceResponse:
    """Handle whenhub.update_event."""
    hass = call.hass
    data = call.data
    device_id: str = data[ATTR_DEVICE_ID]

    entry = _resolve_entry(hass, device_id)
    entry_data = dict(entry.data)
    event_type = _service_event_type(entry_data)

    _check_type_fields(data, event_type)
    notify_types = _notify_types_for_update(entry_data)
    _check_notify_supported(data, event_type, notify_types)

    new_data = dict(entry_data)
    changed: dict[str, dict[str, Any]] = {}

    for field in _DATE_FIELDS.get(event_type, ()):
        _apply_date_field(
            hass,
            entry_data,
            new_data,
            changed,
            data,
            field,
            data[ATTR_REPLACE_DATE_SOURCE],
        )

    if event_type == EVENT_TYPE_TRIP:
        _check_trip_date_order(new_data)

    for field in (
        *_TYPE_FIELDS.get(event_type, ()),
        *_GENERIC_FIELDS,
        CONF_NOTIFY_ON_EXPIRY,
    ):
        if field in _DATE_PARAMETERS or field not in data:
            continue
        if field == CONF_NOTIFY_ON_EXPIRY and event_type not in notify_types:
            continue  # ``false`` on a type that cannot expire is a no-op
        if (new_value := data[field]) != entry_data.get(field):
            changed[field] = {"old": entry_data.get(field), "new": new_value}
            new_data[field] = new_value

    if event_type == EVENT_TYPE_SPECIAL and CONF_SPECIAL_TYPE in changed:
        new_data[CONF_SPECIAL_CATEGORY] = SPECIAL_EVENTS[data[CONF_SPECIAL_TYPE]][
            "category"
        ]

    title = entry.title
    if (new_name := data.get(ATTR_NAME, title)) != title:
        if new_name in existing_event_names(hass, ignore_entry_id=entry.entry_id):
            raise _error("name_exists", name=new_name)
        changed[ATTR_NAME] = {"old": title, "new": new_name}
        title = new_name

    if changed:
        hass.config_entries.async_update_entry(entry, data=new_data, title=title)
        await hass.config_entries.async_reload(entry.entry_id)
        _LOGGER.info(
            "WhenHub event updated via service: %s (%s)",
            title,
            ", ".join(sorted(changed)),
        )

    return {
        ATTR_DEVICE_ID: device_id,
        ATTR_NAME: title,
        ATTR_CHANGED: changed,
    }


async def _async_delete_event(call: ServiceCall) -> ServiceResponse:
    """Handle whenhub.delete_event."""
    hass = call.hass
    device_id: str = call.data[ATTR_DEVICE_ID]

    entry = _resolve_entry(hass, device_id)
    entity_registry = er.async_get(hass)

    # Read the entities before removing the entry — unloading clears them from
    # the registry, so afterwards the list would always be empty.
    response: dict[str, Any] = {
        ATTR_DEVICE_ID: device_id,
        ATTR_ENTRY_ID: entry.entry_id,
        ATTR_NAME: entry.title,
        CONF_EVENT_TYPE: _service_event_type(dict(entry.data)),
        ATTR_REMOVED_ENTITIES: sorted(
            entity.entity_id
            for entity in er.async_entries_for_config_entry(
                entity_registry, entry.entry_id
            )
        ),
    }

    await hass.config_entries.async_remove(entry.entry_id)
    _LOGGER.info("WhenHub event deleted via service: %s", response[ATTR_NAME])

    return response


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the WhenHub services once for the integration."""
    for service, handler, schema in (
        (SERVICE_CREATE_EVENT, _async_create_event, CREATE_EVENT_SCHEMA),
        (SERVICE_UPDATE_EVENT, _async_update_event, UPDATE_EVENT_SCHEMA),
        (SERVICE_DELETE_EVENT, _async_delete_event, DELETE_EVENT_SCHEMA),
    ):
        hass.services.async_register(
            DOMAIN,
            service,
            handler,
            schema=schema,
            supports_response=SupportsResponse.OPTIONAL,
        )
