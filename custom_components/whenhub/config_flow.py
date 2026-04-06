"""Config flow for WhenHub integration."""
from __future__ import annotations

import base64
import json
import logging
import pathlib
from typing import Any
import voluptuous as vol
from datetime import date

from homeassistant import config_entries
from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import (
    BooleanSelector,
    DateSelector,
    FileSelector,
    FileSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    SelectOptionDict,
)

from .const import (
    DOMAIN,
    EVENT_TYPES,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
    EVENT_TYPE_SPECIAL,
    CONF_EVENT_TYPE,
    CONF_START_DATE,
    CONF_END_DATE,
    CONF_TARGET_DATE,
    CONF_SPECIAL_TYPE,
    CONF_SPECIAL_CATEGORY,
    CONF_DST_TYPE,
    CONF_DST_REGION,
    CONF_IMAGE_PATH,
    CONF_IMAGE_UPLOAD,
    CONF_IMAGE_MIME,
    CONF_IMAGE_DELETE,
    SPECIAL_EVENTS,
    SPECIAL_EVENT_CATEGORIES,
    DST_EVENT_TYPES,
    DST_REGIONS,
    TIMEZONE_TO_DST_REGION,
    CONF_ENTRY_TYPE,
    ENTRY_TYPE_CALENDAR,
    CONF_CALENDAR_SCOPE,
    CONF_CALENDAR_TYPES,
    CONF_CALENDAR_EVENT_IDS,
    CONF_CP_FREQ,
    CONF_CP_INTERVAL,
    CONF_CP_DTSTART,
    CONF_CP_DAY_RULE,
    CONF_CP_BYMONTH,
    CONF_CP_BYDAY_POS,
    CONF_CP_BYDAY_WEEKDAY,
    CONF_CP_BYMONTHDAY,
    CONF_CP_BYDAY_LIST,
    CONF_CP_END_TYPE,
    CONF_CP_UNTIL,
    CONF_CP_COUNT,
)

_LOGGER = logging.getLogger(__name__)

_IMAGE_MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _process_image_upload(hass: HomeAssistant, user_input: dict) -> tuple[str | None, str | None]:
    """Process an uploaded image file from a FileSelector field.

    Returns (base64_data, mime_type) if an upload was provided, (None, None) otherwise.
    """
    upload_id = user_input.get(CONF_IMAGE_UPLOAD)
    if not upload_id:
        return None, None
    try:
        with process_uploaded_file(hass, upload_id) as path:
            image_bytes = path.read_bytes()
            image_data = base64.b64encode(image_bytes).decode()
            image_mime = _IMAGE_MIME_MAP.get(path.suffix.lower(), "image/jpeg")
            return image_data, image_mime
    except Exception as err:
        _LOGGER.warning("Failed to process uploaded image: %s", err)
        return None, None


def _apply_image_changes(hass: HomeAssistant, new_data: dict, user_input: dict) -> None:
    """Apply image upload / delete choices from user_input to new_data (in-place).

    - If 'image_delete' is checked: clears image_data, image_mime, image_path.
    - Else if a file was uploaded: stores base64 data and MIME type.
    - Else: leaves existing image_data / image_mime untouched.
    Always removes the temporary UI-only keys from new_data.
    """
    if user_input.get(CONF_IMAGE_DELETE):
        new_data["image_data"] = None
        new_data[CONF_IMAGE_MIME] = None
        new_data[CONF_IMAGE_PATH] = ""
    else:
        image_data, image_mime = _process_image_upload(hass, user_input)
        if image_data:
            new_data["image_data"] = image_data
            new_data[CONF_IMAGE_MIME] = image_mime
    new_data.pop(CONF_IMAGE_UPLOAD, None)
    new_data.pop(CONF_IMAGE_DELETE, None)


def _schema_image(current: dict, show_delete: bool = False) -> dict:
    """Return voluptuous field dict for the image section (upload + path + optional delete).

    Intended to be spread into a larger vol.Schema dict.
    """
    fields: dict = {
        vol.Optional(CONF_IMAGE_UPLOAD): FileSelector(
            FileSelectorConfig(accept=".jpg,.jpeg,.png,.webp,.gif")
        ),
        vol.Optional(CONF_IMAGE_PATH, default=current.get(CONF_IMAGE_PATH, "")): str,
    }
    if show_delete:
        fields[vol.Optional(CONF_IMAGE_DELETE, default=False)] = BooleanSelector()
    return fields


# ── Custom Pattern schema helpers ─────────────────────────────────────────────
# These module-level functions build voluptuous schemas for each CP step.
# Both ConfigFlow and OptionsFlowHandler call them with a `current` dict that
# provides default values (empty dict for new entries, entry.data for edits).

def _schema_cp_freq(current: dict) -> vol.Schema:
    """Schema for step cp_freq: frequency, anchor date, interval."""
    return vol.Schema({
        vol.Required(CONF_CP_FREQ, default=current.get(CONF_CP_FREQ, "yearly")): SelectSelector(
            SelectSelectorConfig(
                options=["yearly", "monthly", "weekly", "daily"],
                translation_key="cp_freq",
            )
        ),
        vol.Required(CONF_CP_DTSTART, default=current.get(CONF_CP_DTSTART, date.today().isoformat())): DateSelector(),
        vol.Required(CONF_CP_INTERVAL, default=int(current.get(CONF_CP_INTERVAL, 1))): NumberSelector(
            NumberSelectorConfig(min=1, max=99, step=1, mode="box")
        ),
    })


def _schema_cp_yearly(current: dict) -> vol.Schema:
    """Schema for step cp_yearly: target month + day rule."""
    return vol.Schema({
        vol.Required(CONF_CP_BYMONTH, default=str(current.get(CONF_CP_BYMONTH, 1))): SelectSelector(
            SelectSelectorConfig(
                options=[str(i) for i in range(1, 13)],
                translation_key="cp_bymonth",
            )
        ),
        vol.Required(CONF_CP_DAY_RULE, default=current.get(CONF_CP_DAY_RULE, "nth_weekday")): SelectSelector(
            SelectSelectorConfig(
                options=["nth_weekday", "last_weekday", "fixed_day"],
                translation_key="cp_day_rule",
            )
        ),
    })


def _schema_cp_monthly(current: dict) -> vol.Schema:
    """Schema for step cp_monthly: day rule."""
    return vol.Schema({
        vol.Required(CONF_CP_DAY_RULE, default=current.get(CONF_CP_DAY_RULE, "nth_weekday")): SelectSelector(
            SelectSelectorConfig(
                options=["nth_weekday", "last_weekday", "fixed_day"],
                translation_key="cp_day_rule",
            )
        ),
    })


def _schema_cp_weekday_nth(current: dict) -> vol.Schema:
    """Schema for step cp_weekday_nth: position (1st/2nd/…) + weekday."""
    return vol.Schema({
        vol.Required(CONF_CP_BYDAY_POS, default=str(current.get(CONF_CP_BYDAY_POS, 1))): SelectSelector(
            SelectSelectorConfig(
                options=["1", "2", "3", "4"],
                translation_key="cp_byday_pos",
            )
        ),
        vol.Required(CONF_CP_BYDAY_WEEKDAY, default=str(current.get(CONF_CP_BYDAY_WEEKDAY, 0))): SelectSelector(
            SelectSelectorConfig(
                options=["0", "1", "2", "3", "4", "5", "6"],
                translation_key="cp_byday_weekday",
            )
        ),
    })


def _schema_cp_weekday_last(current: dict) -> vol.Schema:
    """Schema for step cp_weekday_last: last occurrence of weekday."""
    return vol.Schema({
        vol.Required(CONF_CP_BYDAY_WEEKDAY, default=str(current.get(CONF_CP_BYDAY_WEEKDAY, 0))): SelectSelector(
            SelectSelectorConfig(
                options=["0", "1", "2", "3", "4", "5", "6"],
                translation_key="cp_byday_weekday",
            )
        ),
    })


def _schema_cp_fixed_day(current: dict) -> vol.Schema:
    """Schema for step cp_fixed_day: fixed day-of-month number."""
    return vol.Schema({
        vol.Required(CONF_CP_BYMONTHDAY, default=int(current.get(CONF_CP_BYMONTHDAY, 1))): NumberSelector(
            NumberSelectorConfig(min=1, max=31, step=1, mode="box")
        ),
    })


def _schema_cp_weekly(current: dict) -> vol.Schema:
    """Schema for step cp_weekly: set of weekdays."""
    raw = current.get(CONF_CP_BYDAY_LIST, [0])
    default_list = [str(d) for d in raw] if isinstance(raw, list) else ["0"]
    return vol.Schema({
        vol.Required(CONF_CP_BYDAY_LIST, default=default_list): SelectSelector(
            SelectSelectorConfig(
                options=["0", "1", "2", "3", "4", "5", "6"],
                multiple=True,
                translation_key="cp_byday_weekday",
            )
        ),
    })


def _schema_cp_end(current: dict) -> vol.Schema:
    """Schema for step cp_end: end condition type."""
    return vol.Schema({
        vol.Required(CONF_CP_END_TYPE, default=current.get(CONF_CP_END_TYPE, "none")): SelectSelector(
            SelectSelectorConfig(
                options=["none", "until", "count"],
                translation_key="cp_end_type",
            )
        ),
    })


def _schema_cp_end_until(current: dict) -> vol.Schema:
    """Schema for step cp_end_until: repeat-until date."""
    return vol.Schema({
        vol.Required(CONF_CP_UNTIL, default=current.get(CONF_CP_UNTIL, date.today().isoformat())): DateSelector(),
    })


def _schema_cp_end_count(current: dict) -> vol.Schema:
    """Schema for step cp_end_count: maximum number of occurrences."""
    return vol.Schema({
        vol.Required(CONF_CP_COUNT, default=int(current.get(CONF_CP_COUNT, 10))): NumberSelector(
            NumberSelectorConfig(min=1, max=9999, step=1, mode="box")
        ),
    })


def _schema_cp_image(current: dict, show_delete: bool = False) -> vol.Schema:
    """Schema for the final cp_image step: optional image upload and/or path."""
    return vol.Schema(_schema_image(current, show_delete=show_delete))


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WhenHub."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._event_type: str | None = None
        self._special_category: str | None = None
        self._calendar_data: dict = {}
        self._cp_data: dict = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - event type selection."""
        if user_input is None:
            return await self._show_event_type_form()

        self._event_type = user_input[CONF_EVENT_TYPE]

        if self._event_type == ENTRY_TYPE_CALENDAR:
            return await self.async_step_calendar()
        elif self._event_type == EVENT_TYPE_TRIP:
            return await self.async_step_trip()
        elif self._event_type == EVENT_TYPE_MILESTONE:
            return await self.async_step_milestone()
        elif self._event_type == EVENT_TYPE_ANNIVERSARY:
            return await self.async_step_anniversary()
        elif self._event_type == EVENT_TYPE_SPECIAL:
            return await self.async_step_special_category()

    async def _show_event_type_form(self) -> FlowResult:
        """Show event type selection form."""
        event_type_options = list(EVENT_TYPES.keys()) + [ENTRY_TYPE_CALENDAR]

        data_schema = vol.Schema({
            vol.Required(CONF_EVENT_TYPE): SelectSelector(
                SelectSelectorConfig(
                    options=event_type_options,
                    translation_key="event_type",
                )
            )
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    def _suggest_calendar_name(self) -> str:
        """Return a localized, auto-incremented calendar name suggestion."""
        lang = self.hass.config.language or ""
        base = "WhenHub Kalender" if lang.startswith("de") else "WhenHub Calendar"
        existing = {
            e.title
            for e in self.hass.config_entries.async_entries(DOMAIN)
            if e.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR
        }
        if base not in existing:
            return base
        counter = 2
        while f"{base} {counter}" in existing:
            counter += 1
        return f"{base} {counter}"

    def _suggest_event_name(self, base: str) -> str:
        """Return an auto-incremented event name suggestion."""
        existing = {
            e.title
            for e in self.hass.config_entries.async_entries(DOMAIN)
        }
        if base not in existing:
            return base
        counter = 2
        while f"{base} {counter}" in existing:
            counter += 1
        return f"{base} {counter}"

    def _get_translated_selector_option(self, selector: str, key: str) -> str:
        """Look up a translated selector option from the translation file."""
        lang = (self.hass.config.language or "en").split("-")[0]
        translations_dir = pathlib.Path(__file__).parent / "translations"
        for try_lang in [lang, "en"]:
            trans_file = translations_dir / f"{try_lang}.json"
            if trans_file.exists():
                try:
                    data = json.loads(trans_file.read_text(encoding="utf-8"))
                    name = (
                        data.get("selector", {})
                        .get(selector, {})
                        .get("options", {})
                        .get(key, "")
                    )
                    if name:
                        return name
                except Exception:
                    pass
        return key.replace("_", " ").title()

    async def async_step_calendar(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle calendar scope selection."""
        if user_input is None:
            return self.async_show_form(
                step_id="calendar",
                data_schema=vol.Schema({
                    vol.Required(CONF_CALENDAR_SCOPE, default="all"): SelectSelector(
                        SelectSelectorConfig(
                            options=["all", "by_type", "specific"],
                            translation_key="calendar_scope",
                        )
                    )
                }),
            )

        self._calendar_data = {
            CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
            CONF_CALENDAR_SCOPE: user_input[CONF_CALENDAR_SCOPE],
        }
        scope = user_input[CONF_CALENDAR_SCOPE]
        if scope == "by_type":
            return await self.async_step_calendar_by_type()
        if scope == "specific":
            return await self.async_step_calendar_specific()
        return self.async_create_entry(
            title=self._suggest_calendar_name(),
            data=self._calendar_data,
        )

    async def async_step_calendar_by_type(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle calendar type filter selection."""
        if user_input is None:
            return self.async_show_form(
                step_id="calendar_by_type",
                data_schema=vol.Schema({
                    vol.Required(CONF_CALENDAR_TYPES, default=list(EVENT_TYPES.keys())): SelectSelector(
                        SelectSelectorConfig(
                            options=list(EVENT_TYPES.keys()),
                            multiple=True,
                            translation_key="event_type",
                        )
                    )
                }),
            )

        self._calendar_data[CONF_CALENDAR_TYPES] = user_input[CONF_CALENDAR_TYPES]
        return self.async_create_entry(
            title=self._suggest_calendar_name(),
            data=self._calendar_data,
        )

    async def async_step_calendar_specific(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle specific event selection for calendar."""
        event_entries = [
            e for e in self.hass.config_entries.async_entries(DOMAIN)
            if e.data.get(CONF_ENTRY_TYPE) != ENTRY_TYPE_CALENDAR
        ]
        options = [
            SelectOptionDict(value=e.entry_id, label=e.title)
            for e in event_entries
        ]

        if user_input is None:
            return self.async_show_form(
                step_id="calendar_specific",
                data_schema=vol.Schema({
                    vol.Required(CONF_CALENDAR_EVENT_IDS): SelectSelector(
                        SelectSelectorConfig(options=options, multiple=True)
                    )
                }),
            )

        self._calendar_data[CONF_CALENDAR_EVENT_IDS] = user_input[CONF_CALENDAR_EVENT_IDS]
        return self.async_create_entry(
            title=self._suggest_calendar_name(),
            data=self._calendar_data,
        )

    async def async_step_trip(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle trip configuration."""
        if user_input is None:
            return await self._show_trip_form()

        errors = {}

        start_date = user_input[CONF_START_DATE]
        end_date = user_input[CONF_END_DATE]

        if start_date >= end_date:
            errors["base"] = "invalid_dates"

        if not errors:
            user_input[CONF_EVENT_TYPE] = self._event_type
            image_data, image_mime = _process_image_upload(self.hass, user_input)
            if image_data:
                user_input["image_data"] = image_data
                user_input[CONF_IMAGE_MIME] = image_mime
            user_input.pop(CONF_IMAGE_UPLOAD, None)
            return self.async_create_entry(title=self._suggest_event_name("Trip"), data=user_input)

        return await self._show_trip_form(user_input, errors)

    async def _show_trip_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show trip configuration form."""
        current = user_input or {}
        data_schema = vol.Schema({
            vol.Required(CONF_START_DATE, default=current.get(CONF_START_DATE, date.today().isoformat())): DateSelector(),
            vol.Required(CONF_END_DATE, default=current.get(CONF_END_DATE, date.today().isoformat())): DateSelector(),
            **_schema_image(current),
        })

        return self.async_show_form(
            step_id="trip",
            data_schema=data_schema,
            errors=errors or {},
        )

    async def async_step_milestone(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle milestone configuration."""
        if user_input is None:
            return await self._show_milestone_form()

        user_input[CONF_EVENT_TYPE] = self._event_type
        image_data, image_mime = _process_image_upload(self.hass, user_input)
        if image_data:
            user_input["image_data"] = image_data
            user_input[CONF_IMAGE_MIME] = image_mime
        user_input.pop(CONF_IMAGE_UPLOAD, None)
        return self.async_create_entry(title=self._suggest_event_name("Milestone"), data=user_input)

    async def _show_milestone_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show milestone configuration form."""
        current = user_input or {}
        data_schema = vol.Schema({
            vol.Required(CONF_TARGET_DATE, default=current.get(CONF_TARGET_DATE, date.today().isoformat())): DateSelector(),
            **_schema_image(current),
        })

        return self.async_show_form(
            step_id="milestone",
            data_schema=data_schema,
            errors=errors or {},
        )

    async def async_step_anniversary(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle anniversary configuration."""
        if user_input is None:
            return await self._show_anniversary_form()

        user_input[CONF_EVENT_TYPE] = self._event_type
        image_data, image_mime = _process_image_upload(self.hass, user_input)
        if image_data:
            user_input["image_data"] = image_data
            user_input[CONF_IMAGE_MIME] = image_mime
        user_input.pop(CONF_IMAGE_UPLOAD, None)
        return self.async_create_entry(title=self._suggest_event_name("Anniversary"), data=user_input)

    async def _show_anniversary_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show anniversary configuration form."""
        current = user_input or {}
        data_schema = vol.Schema({
            vol.Required(CONF_TARGET_DATE, default=current.get(CONF_TARGET_DATE, date.today().isoformat())): DateSelector(),
            **_schema_image(current),
        })

        return self.async_show_form(
            step_id="anniversary",
            data_schema=data_schema,
            errors=errors or {},
        )

    async def async_step_special_category(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle special event category selection."""
        if user_input is None:
            return await self._show_special_category_form()

        self._special_category = user_input[CONF_SPECIAL_CATEGORY]

        if self._special_category == "dst":
            return await self.async_step_dst_event()
        if self._special_category == "custom_pattern":
            return await self.async_step_cp_freq()

        return await self.async_step_special_event()

    async def _show_special_category_form(self) -> FlowResult:
        """Show special event category selection form."""
        category_options = list(SPECIAL_EVENT_CATEGORIES.keys())

        data_schema = vol.Schema({
            vol.Required(CONF_SPECIAL_CATEGORY): SelectSelector(
                SelectSelectorConfig(
                    options=category_options,
                    translation_key="special_category",
                )
            )
        })

        return self.async_show_form(
            step_id="special_category",
            data_schema=data_schema,
        )

    async def async_step_special_event(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle special event selection and configuration."""
        if user_input is None:
            return await self._show_special_event_form()

        user_input[CONF_EVENT_TYPE] = self._event_type
        user_input[CONF_SPECIAL_CATEGORY] = self._special_category
        image_data, image_mime = _process_image_upload(self.hass, user_input)
        if image_data:
            user_input["image_data"] = image_data
            user_input[CONF_IMAGE_MIME] = image_mime
        user_input.pop(CONF_IMAGE_UPLOAD, None)
        special_type = user_input.get(CONF_SPECIAL_TYPE, "special_event")
        base_name = self._get_translated_selector_option("special_type", special_type)
        return self.async_create_entry(title=self._suggest_event_name(base_name), data=user_input)

    async def _show_special_event_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show special event selection and configuration form."""
        filtered_events = {
            key: info for key, info in SPECIAL_EVENTS.items()
            if info.get("category") == self._special_category
        }

        special_options = list(filtered_events.keys())
        default_special_type = special_options[0] if special_options else ""
        if user_input is not None:
            default_special_type = user_input.get(CONF_SPECIAL_TYPE, default_special_type)

        current = user_input or {}
        data_schema = vol.Schema({
            vol.Required(CONF_SPECIAL_TYPE, default=default_special_type): SelectSelector(
                SelectSelectorConfig(
                    options=special_options,
                    translation_key="special_type",
                )
            ),
            **_schema_image(current),
        })

        return self.async_show_form(
            step_id="special_event",
            data_schema=data_schema,
            errors=errors or {},
        )

    async def async_step_dst_event(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle DST event configuration."""
        if user_input is None:
            return await self._show_dst_event_form()

        user_input[CONF_EVENT_TYPE] = self._event_type
        user_input[CONF_SPECIAL_CATEGORY] = self._special_category
        image_data, image_mime = _process_image_upload(self.hass, user_input)
        if image_data:
            user_input["image_data"] = image_data
            user_input[CONF_IMAGE_MIME] = image_mime
        user_input.pop(CONF_IMAGE_UPLOAD, None)
        return self.async_create_entry(title=self._suggest_event_name("DST Event"), data=user_input)

    async def _show_dst_event_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show DST event configuration form."""
        region_options = list(DST_REGIONS.keys())
        dst_type_options = list(DST_EVENT_TYPES.keys())

        default_region = None
        tz_name = self.hass.config.time_zone
        if tz_name:
            for tz_prefix, region in TIMEZONE_TO_DST_REGION.items():
                if tz_name.startswith(tz_prefix) or tz_name == tz_prefix:
                    default_region = region
                    break

        if default_region is None:
            default_region = "eu"

        default_dst_type = "next_change"

        current = user_input or {}
        if user_input is not None:
            default_region = user_input.get(CONF_DST_REGION, default_region)
            default_dst_type = user_input.get(CONF_DST_TYPE, default_dst_type)

        data_schema = vol.Schema({
            vol.Required(CONF_DST_REGION, default=default_region): SelectSelector(
                SelectSelectorConfig(
                    options=region_options,
                    translation_key="dst_region",
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_DST_TYPE, default=default_dst_type): SelectSelector(
                SelectSelectorConfig(
                    options=dst_type_options,
                    translation_key="dst_type",
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            **_schema_image(current),
        })

        return self.async_show_form(
            step_id="dst_event",
            data_schema=data_schema,
            errors=errors or {},
        )

    # ── Custom Pattern steps ──────────────────────────────────────────────────

    async def async_step_cp_freq(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: frequency, anchor date, interval."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_freq",
                data_schema=_schema_cp_freq(self._cp_data),
            )
        self._cp_data[CONF_CP_FREQ] = user_input[CONF_CP_FREQ]
        self._cp_data[CONF_CP_DTSTART] = user_input[CONF_CP_DTSTART]
        self._cp_data[CONF_CP_INTERVAL] = int(user_input[CONF_CP_INTERVAL])

        freq = user_input[CONF_CP_FREQ]
        if freq == "yearly":
            return await self.async_step_cp_yearly()
        if freq == "monthly":
            return await self.async_step_cp_monthly()
        if freq == "weekly":
            return await self.async_step_cp_weekly()
        # daily: no further config needed beyond end condition
        return await self.async_step_cp_end()

    async def async_step_cp_yearly(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2a (yearly): which month + day rule."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_yearly",
                data_schema=_schema_cp_yearly(self._cp_data),
            )
        self._cp_data[CONF_CP_BYMONTH] = int(user_input[CONF_CP_BYMONTH])
        self._cp_data[CONF_CP_DAY_RULE] = user_input[CONF_CP_DAY_RULE]
        return await self._cp_branch_day_rule(user_input[CONF_CP_DAY_RULE])

    async def async_step_cp_monthly(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2b (monthly): day rule."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_monthly",
                data_schema=_schema_cp_monthly(self._cp_data),
            )
        self._cp_data[CONF_CP_DAY_RULE] = user_input[CONF_CP_DAY_RULE]
        return await self._cp_branch_day_rule(user_input[CONF_CP_DAY_RULE])

    async def _cp_branch_day_rule(self, day_rule: str) -> FlowResult:
        """Route to the correct day-rule detail step."""
        if day_rule == "nth_weekday":
            return await self.async_step_cp_weekday_nth()
        if day_rule == "last_weekday":
            return await self.async_step_cp_weekday_last()
        return await self.async_step_cp_fixed_day()

    async def async_step_cp_weekday_nth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 3a: Nth weekday — position + weekday."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_weekday_nth",
                data_schema=_schema_cp_weekday_nth(self._cp_data),
            )
        self._cp_data[CONF_CP_BYDAY_POS] = int(user_input[CONF_CP_BYDAY_POS])
        self._cp_data[CONF_CP_BYDAY_WEEKDAY] = int(user_input[CONF_CP_BYDAY_WEEKDAY])
        return await self.async_step_cp_end()

    async def async_step_cp_weekday_last(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 3b: Last weekday of period."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_weekday_last",
                data_schema=_schema_cp_weekday_last(self._cp_data),
            )
        self._cp_data[CONF_CP_BYDAY_WEEKDAY] = int(user_input[CONF_CP_BYDAY_WEEKDAY])
        return await self.async_step_cp_end()

    async def async_step_cp_fixed_day(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 3c: Fixed day of month."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_fixed_day",
                data_schema=_schema_cp_fixed_day(self._cp_data),
            )
        self._cp_data[CONF_CP_BYMONTHDAY] = int(user_input[CONF_CP_BYMONTHDAY])
        return await self.async_step_cp_end()

    async def async_step_cp_weekly(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2c (weekly): weekday selection."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_weekly",
                data_schema=_schema_cp_weekly(self._cp_data),
            )
        self._cp_data[CONF_CP_BYDAY_LIST] = [int(d) for d in user_input[CONF_CP_BYDAY_LIST]]
        return await self.async_step_cp_end()

    async def async_step_cp_end(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Final step: end condition (none / until / count)."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_end",
                data_schema=_schema_cp_end(self._cp_data),
            )
        self._cp_data[CONF_CP_END_TYPE] = user_input[CONF_CP_END_TYPE]
        end_type = user_input[CONF_CP_END_TYPE]
        if end_type == "until":
            return await self.async_step_cp_end_until()
        if end_type == "count":
            return await self.async_step_cp_end_count()
        return await self.async_step_cp_image()

    async def async_step_cp_end_until(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """End detail: repeat until a specific date."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_end_until",
                data_schema=_schema_cp_end_until(self._cp_data),
            )
        self._cp_data[CONF_CP_UNTIL] = user_input[CONF_CP_UNTIL]
        return await self.async_step_cp_image()

    async def async_step_cp_end_count(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """End detail: limited number of occurrences."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_end_count",
                data_schema=_schema_cp_end_count(self._cp_data),
            )
        self._cp_data[CONF_CP_COUNT] = int(user_input[CONF_CP_COUNT])
        return await self.async_step_cp_image()

    async def async_step_cp_image(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Final step: optional image upload and/or path."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_image",
                data_schema=_schema_cp_image(self._cp_data),
            )
        self._cp_data[CONF_IMAGE_PATH] = user_input.get(CONF_IMAGE_PATH, "")
        if user_input.get(CONF_IMAGE_UPLOAD):
            self._cp_data[CONF_IMAGE_UPLOAD] = user_input[CONF_IMAGE_UPLOAD]
        return self._cp_create_entry()

    def _cp_create_entry(self) -> FlowResult:
        """Assemble entry data and create the config entry."""
        image_data, image_mime = _process_image_upload(self.hass, self._cp_data)
        data = {
            CONF_EVENT_TYPE: self._event_type,
            CONF_SPECIAL_CATEGORY: "custom_pattern",
        }
        data.update(self._cp_data)
        if image_data:
            data["image_data"] = image_data
            data[CONF_IMAGE_MIME] = image_mime
        data.pop(CONF_IMAGE_UPLOAD, None)
        freq = self._cp_data.get(CONF_CP_FREQ, "monthly")
        base_name = f"{freq.capitalize()} Pattern"
        return self.async_create_entry(
            title=self._suggest_event_name(base_name),
            data=data,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for WhenHub.

    Note: config_entry is automatically provided by the OptionsFlow base class
    as a read-only property. Do not override __init__ to set it manually.
    """

    def __init__(self) -> None:
        """Initialize the options flow."""
        self._calendar_data: dict = {}
        self._cp_data: dict = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if self.config_entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_CALENDAR:
            return await self.async_step_calendar_options(user_input)

        event_type = self.config_entry.data.get(CONF_EVENT_TYPE, EVENT_TYPE_TRIP)

        if event_type == EVENT_TYPE_TRIP:
            return await self.async_step_trip_options(user_input)
        elif event_type == EVENT_TYPE_MILESTONE:
            return await self.async_step_milestone_options(user_input)
        elif event_type == EVENT_TYPE_ANNIVERSARY:
            return await self.async_step_anniversary_options(user_input)
        elif event_type == EVENT_TYPE_SPECIAL:
            special_category = self.config_entry.data.get(CONF_SPECIAL_CATEGORY)
            if special_category == "dst":
                return await self.async_step_dst_options(user_input)
            if special_category == "custom_pattern":
                if not self._cp_data:
                    self._cp_data = dict(self.config_entry.data)
                return await self.async_step_cp_freq(user_input)
            return await self.async_step_special_options(user_input)

    async def async_step_trip_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle trip options."""
        errors = {}

        if user_input is not None:
            start_date = user_input[CONF_START_DATE]
            end_date = user_input[CONF_END_DATE]

            if start_date >= end_date:
                errors["base"] = "invalid_dates"

            if not errors:
                user_input[CONF_EVENT_TYPE] = self.config_entry.data[CONF_EVENT_TYPE]

                new_data = dict(self.config_entry.data)
                new_data.update(user_input)
                _apply_image_changes(self.hass, new_data, user_input)

                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=new_data,
                )

                self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
                return self.async_create_entry(title="", data={})

        current_data = user_input if user_input is not None else self.config_entry.data
        has_image = bool(self.config_entry.data.get("image_data") or self.config_entry.data.get(CONF_IMAGE_PATH))
        data_schema = vol.Schema({
            vol.Required(CONF_START_DATE, default=current_data.get(CONF_START_DATE, date.today().isoformat())): DateSelector(),
            vol.Required(CONF_END_DATE, default=current_data.get(CONF_END_DATE, date.today().isoformat())): DateSelector(),
            **_schema_image(self.config_entry.data, show_delete=has_image),
        })

        return self.async_show_form(
            step_id="trip_options",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_milestone_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle milestone options."""
        if user_input is not None:
            user_input[CONF_EVENT_TYPE] = self.config_entry.data[CONF_EVENT_TYPE]

            new_data = dict(self.config_entry.data)
            new_data.update(user_input)
            _apply_image_changes(self.hass, new_data, user_input)

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )

            self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
            return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data
        has_image = bool(current_data.get("image_data") or current_data.get(CONF_IMAGE_PATH))
        data_schema = vol.Schema({
            vol.Required(CONF_TARGET_DATE, default=current_data.get(CONF_TARGET_DATE, date.today().isoformat())): DateSelector(),
            **_schema_image(current_data, show_delete=has_image),
        })

        return self.async_show_form(
            step_id="milestone_options",
            data_schema=data_schema,
        )

    async def async_step_anniversary_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle anniversary options."""
        if user_input is not None:
            user_input[CONF_EVENT_TYPE] = self.config_entry.data[CONF_EVENT_TYPE]

            new_data = dict(self.config_entry.data)
            new_data.update(user_input)
            _apply_image_changes(self.hass, new_data, user_input)

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )

            self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
            return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data
        has_image = bool(current_data.get("image_data") or current_data.get(CONF_IMAGE_PATH))
        data_schema = vol.Schema({
            vol.Required(CONF_TARGET_DATE, default=current_data.get(CONF_TARGET_DATE, date.today().isoformat())): DateSelector(),
            **_schema_image(current_data, show_delete=has_image),
        })

        return self.async_show_form(
            step_id="anniversary_options",
            data_schema=data_schema,
        )

    async def async_step_special_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle special event options."""
        if user_input is not None:
            user_input[CONF_EVENT_TYPE] = self.config_entry.data[CONF_EVENT_TYPE]

            new_data = dict(self.config_entry.data)
            new_data.update(user_input)
            _apply_image_changes(self.hass, new_data, user_input)

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )

            self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
            return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data

        current_category = current_data.get(CONF_SPECIAL_CATEGORY)
        current_special_type = current_data.get(CONF_SPECIAL_TYPE, "christmas_eve")

        if not current_category:
            for event_key, event_info in SPECIAL_EVENTS.items():
                if event_key == current_special_type:
                    current_category = event_info.get("category", "traditional")
                    break
            if not current_category:
                current_category = "traditional"

        filtered_events = {
            key: info for key, info in SPECIAL_EVENTS.items()
            if info.get("category") == current_category
        }

        special_options = list(filtered_events.keys())
        has_image = bool(current_data.get("image_data") or current_data.get(CONF_IMAGE_PATH))

        data_schema = vol.Schema({
            vol.Required(CONF_SPECIAL_TYPE, default=current_special_type): SelectSelector(
                SelectSelectorConfig(
                    options=special_options,
                    translation_key="special_type",
                )
            ),
            **_schema_image(current_data, show_delete=has_image),
        })

        return self.async_show_form(
            step_id="special_options",
            data_schema=data_schema,
        )

    async def async_step_dst_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle DST event options."""
        if user_input is not None:
            user_input[CONF_EVENT_TYPE] = self.config_entry.data[CONF_EVENT_TYPE]
            user_input[CONF_SPECIAL_CATEGORY] = self.config_entry.data.get(CONF_SPECIAL_CATEGORY, "dst")

            new_data = dict(self.config_entry.data)
            new_data.update(user_input)
            _apply_image_changes(self.hass, new_data, user_input)

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )

            self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
            return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data
        region_options = list(DST_REGIONS.keys())
        dst_type_options = list(DST_EVENT_TYPES.keys())
        has_image = bool(current_data.get("image_data") or current_data.get(CONF_IMAGE_PATH))

        data_schema = vol.Schema({
            vol.Required(CONF_DST_REGION, default=current_data.get(CONF_DST_REGION, "eu")): SelectSelector(
                SelectSelectorConfig(
                    options=region_options,
                    translation_key="dst_region",
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_DST_TYPE, default=current_data.get(CONF_DST_TYPE, "next_change")): SelectSelector(
                SelectSelectorConfig(
                    options=dst_type_options,
                    translation_key="dst_type",
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            **_schema_image(current_data, show_delete=has_image),
        })

        return self.async_show_form(
            step_id="dst_options",
            data_schema=data_schema,
        )

    async def async_step_calendar_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle calendar scope change."""
        if user_input is None:
            current_scope = self.config_entry.data.get(CONF_CALENDAR_SCOPE, "all")
            return self.async_show_form(
                step_id="calendar_options",
                data_schema=vol.Schema({
                    vol.Required(CONF_CALENDAR_SCOPE, default=current_scope): SelectSelector(
                        SelectSelectorConfig(
                            options=["all", "by_type", "specific"],
                            translation_key="calendar_scope",
                        )
                    )
                }),
            )

        self._calendar_data = {
            CONF_ENTRY_TYPE: ENTRY_TYPE_CALENDAR,
            CONF_CALENDAR_SCOPE: user_input[CONF_CALENDAR_SCOPE],
        }
        scope = user_input[CONF_CALENDAR_SCOPE]
        if scope == "by_type":
            return await self.async_step_calendar_by_type_options()
        if scope == "specific":
            return await self.async_step_calendar_specific_options()

        return self._save_calendar_options()

    async def async_step_calendar_by_type_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle calendar type filter change."""
        if user_input is None:
            current_types = self.config_entry.data.get(CONF_CALENDAR_TYPES, list(EVENT_TYPES.keys()))
            return self.async_show_form(
                step_id="calendar_by_type_options",
                data_schema=vol.Schema({
                    vol.Required(CONF_CALENDAR_TYPES, default=current_types): SelectSelector(
                        SelectSelectorConfig(
                            options=list(EVENT_TYPES.keys()),
                            multiple=True,
                            translation_key="event_type",
                        )
                    )
                }),
            )

        self._calendar_data[CONF_CALENDAR_TYPES] = user_input[CONF_CALENDAR_TYPES]
        return self._save_calendar_options()

    async def async_step_calendar_specific_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle specific event selection change."""
        event_entries = [
            e for e in self.hass.config_entries.async_entries(DOMAIN)
            if e.data.get(CONF_ENTRY_TYPE) != ENTRY_TYPE_CALENDAR
        ]
        options = [
            SelectOptionDict(value=e.entry_id, label=e.title)
            for e in event_entries
        ]

        if user_input is None:
            current_ids = self.config_entry.data.get(CONF_CALENDAR_EVENT_IDS, [])
            return self.async_show_form(
                step_id="calendar_specific_options",
                data_schema=vol.Schema({
                    vol.Required(CONF_CALENDAR_EVENT_IDS, default=current_ids): SelectSelector(
                        SelectSelectorConfig(options=options, multiple=True)
                    )
                }),
            )

        self._calendar_data[CONF_CALENDAR_EVENT_IDS] = user_input[CONF_CALENDAR_EVENT_IDS]
        return self._save_calendar_options()

    def _save_calendar_options(self) -> FlowResult:
        """Save updated calendar configuration and close options flow."""
        new_data = dict(self.config_entry.data)
        new_data.update(self._calendar_data)
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=new_data,
        )
        return self.async_create_entry(title="", data={})

    # ── Custom Pattern options steps ──────────────────────────────────────────
    # Step methods reuse the same step_ids and schema helpers as ConfigFlow.
    # self._cp_data is pre-populated from config_entry.data in async_step_init.

    async def async_step_cp_freq(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: frequency, anchor date, interval."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_freq",
                data_schema=_schema_cp_freq(self._cp_data),
            )
        self._cp_data[CONF_CP_FREQ] = user_input[CONF_CP_FREQ]
        self._cp_data[CONF_CP_DTSTART] = user_input[CONF_CP_DTSTART]
        self._cp_data[CONF_CP_INTERVAL] = int(user_input[CONF_CP_INTERVAL])

        freq = user_input[CONF_CP_FREQ]
        if freq == "yearly":
            return await self.async_step_cp_yearly()
        if freq == "monthly":
            return await self.async_step_cp_monthly()
        if freq == "weekly":
            return await self.async_step_cp_weekly()
        return await self.async_step_cp_end()

    async def async_step_cp_yearly(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2a (yearly): which month + day rule."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_yearly",
                data_schema=_schema_cp_yearly(self._cp_data),
            )
        self._cp_data[CONF_CP_BYMONTH] = int(user_input[CONF_CP_BYMONTH])
        self._cp_data[CONF_CP_DAY_RULE] = user_input[CONF_CP_DAY_RULE]
        return await self._cp_branch_day_rule(user_input[CONF_CP_DAY_RULE])

    async def async_step_cp_monthly(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2b (monthly): day rule."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_monthly",
                data_schema=_schema_cp_monthly(self._cp_data),
            )
        self._cp_data[CONF_CP_DAY_RULE] = user_input[CONF_CP_DAY_RULE]
        return await self._cp_branch_day_rule(user_input[CONF_CP_DAY_RULE])

    async def _cp_branch_day_rule(self, day_rule: str) -> FlowResult:
        """Route to the correct day-rule detail step."""
        if day_rule == "nth_weekday":
            return await self.async_step_cp_weekday_nth()
        if day_rule == "last_weekday":
            return await self.async_step_cp_weekday_last()
        return await self.async_step_cp_fixed_day()

    async def async_step_cp_weekday_nth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 3a: Nth weekday — position + weekday."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_weekday_nth",
                data_schema=_schema_cp_weekday_nth(self._cp_data),
            )
        self._cp_data[CONF_CP_BYDAY_POS] = int(user_input[CONF_CP_BYDAY_POS])
        self._cp_data[CONF_CP_BYDAY_WEEKDAY] = int(user_input[CONF_CP_BYDAY_WEEKDAY])
        return await self.async_step_cp_end()

    async def async_step_cp_weekday_last(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 3b: Last weekday of period."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_weekday_last",
                data_schema=_schema_cp_weekday_last(self._cp_data),
            )
        self._cp_data[CONF_CP_BYDAY_WEEKDAY] = int(user_input[CONF_CP_BYDAY_WEEKDAY])
        return await self.async_step_cp_end()

    async def async_step_cp_fixed_day(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 3c: Fixed day of month."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_fixed_day",
                data_schema=_schema_cp_fixed_day(self._cp_data),
            )
        self._cp_data[CONF_CP_BYMONTHDAY] = int(user_input[CONF_CP_BYMONTHDAY])
        return await self.async_step_cp_end()

    async def async_step_cp_weekly(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2c (weekly): weekday selection."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_weekly",
                data_schema=_schema_cp_weekly(self._cp_data),
            )
        self._cp_data[CONF_CP_BYDAY_LIST] = [int(d) for d in user_input[CONF_CP_BYDAY_LIST]]
        return await self.async_step_cp_end()

    async def async_step_cp_end(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Final step: end condition (none / until / count)."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_end",
                data_schema=_schema_cp_end(self._cp_data),
            )
        self._cp_data[CONF_CP_END_TYPE] = user_input[CONF_CP_END_TYPE]
        end_type = user_input[CONF_CP_END_TYPE]
        if end_type == "until":
            return await self.async_step_cp_end_until()
        if end_type == "count":
            return await self.async_step_cp_end_count()
        return await self.async_step_cp_image()

    async def async_step_cp_end_until(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """End detail: repeat until a specific date."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_end_until",
                data_schema=_schema_cp_end_until(self._cp_data),
            )
        self._cp_data[CONF_CP_UNTIL] = user_input[CONF_CP_UNTIL]
        return await self.async_step_cp_image()

    async def async_step_cp_end_count(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """End detail: limited number of occurrences."""
        if user_input is None:
            return self.async_show_form(
                step_id="cp_end_count",
                data_schema=_schema_cp_end_count(self._cp_data),
            )
        self._cp_data[CONF_CP_COUNT] = int(user_input[CONF_CP_COUNT])
        return await self.async_step_cp_image()

    async def async_step_cp_image(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Final step: optional image upload and/or path."""
        current_data = self.config_entry.data
        has_image = bool(current_data.get("image_data") or current_data.get(CONF_IMAGE_PATH))
        if user_input is None:
            return self.async_show_form(
                step_id="cp_image",
                data_schema=_schema_cp_image(
                    {**current_data, **self._cp_data}, show_delete=has_image
                ),
            )
        self._cp_data[CONF_IMAGE_PATH] = user_input.get(CONF_IMAGE_PATH, "")
        if user_input.get(CONF_IMAGE_UPLOAD):
            self._cp_data[CONF_IMAGE_UPLOAD] = user_input[CONF_IMAGE_UPLOAD]
        if user_input.get(CONF_IMAGE_DELETE):
            self._cp_data[CONF_IMAGE_DELETE] = True
        return self._cp_save_options()

    def _cp_save_options(self) -> FlowResult:
        """Merge updated CP fields into the config entry and close options flow."""
        new_data = dict(self.config_entry.data)
        new_data.update(self._cp_data)
        # Ensure fixed keys are always present
        new_data[CONF_EVENT_TYPE] = self.config_entry.data[CONF_EVENT_TYPE]
        new_data[CONF_SPECIAL_CATEGORY] = "custom_pattern"
        _apply_image_changes(self.hass, new_data, self._cp_data)

        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=new_data,
        )
        self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
        return self.async_create_entry(title="", data={})
