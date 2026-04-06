"""Config flow for WhenHub integration."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol
from datetime import date

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import (
    DateSelector,
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
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WhenHub."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._event_type: str | None = None
        self._special_category: str | None = None
        self._calendar_data: dict = {}

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
            return self.async_create_entry(title="Trip", data=user_input)

        return await self._show_trip_form(user_input, errors)

    async def _show_trip_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show trip configuration form."""
        data_schema = vol.Schema({
            vol.Required(CONF_START_DATE, default=date.today().isoformat() if user_input is None else user_input.get(CONF_START_DATE, date.today().isoformat())): DateSelector(),
            vol.Required(CONF_END_DATE, default=date.today().isoformat() if user_input is None else user_input.get(CONF_END_DATE, date.today().isoformat())): DateSelector(),
            vol.Optional(CONF_IMAGE_PATH, default="" if user_input is None else user_input.get(CONF_IMAGE_PATH, "")): str,
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
        return self.async_create_entry(title="Milestone", data=user_input)

    async def _show_milestone_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show milestone configuration form."""
        data_schema = vol.Schema({
            vol.Required(CONF_TARGET_DATE, default=date.today().isoformat() if user_input is None else user_input.get(CONF_TARGET_DATE, date.today().isoformat())): DateSelector(),
            vol.Optional(CONF_IMAGE_PATH, default="" if user_input is None else user_input.get(CONF_IMAGE_PATH, "")): str,
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
        return self.async_create_entry(title="Anniversary", data=user_input)

    async def _show_anniversary_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show anniversary configuration form."""
        data_schema = vol.Schema({
            vol.Required(CONF_TARGET_DATE, default=date.today().isoformat() if user_input is None else user_input.get(CONF_TARGET_DATE, date.today().isoformat())): DateSelector(),
            vol.Optional(CONF_IMAGE_PATH, default="" if user_input is None else user_input.get(CONF_IMAGE_PATH, "")): str,
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
        return self.async_create_entry(title="Special Event", data=user_input)

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

        data_schema = vol.Schema({
            vol.Required(CONF_SPECIAL_TYPE, default=default_special_type): SelectSelector(
                SelectSelectorConfig(
                    options=special_options,
                    translation_key="special_type",
                )
            ),
            vol.Optional(CONF_IMAGE_PATH, default="" if user_input is None else user_input.get(CONF_IMAGE_PATH, "")): str,
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
        return self.async_create_entry(title="DST Event", data=user_input)

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
            vol.Optional(CONF_IMAGE_PATH, default="" if user_input is None else user_input.get(CONF_IMAGE_PATH, "")): str,
        })

        return self.async_show_form(
            step_id="dst_event",
            data_schema=data_schema,
            errors=errors or {},
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

                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=new_data,
                )

                self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
                return self.async_create_entry(title="", data={})

        current_data = user_input if user_input is not None else self.config_entry.data
        data_schema = vol.Schema({
            vol.Required(CONF_START_DATE, default=current_data.get(CONF_START_DATE, date.today().isoformat())): DateSelector(),
            vol.Required(CONF_END_DATE, default=current_data.get(CONF_END_DATE, date.today().isoformat())): DateSelector(),
            vol.Optional(CONF_IMAGE_PATH, default=current_data.get(CONF_IMAGE_PATH, "")): str,
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

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )

            self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
            return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data
        data_schema = vol.Schema({
            vol.Required(CONF_TARGET_DATE, default=current_data.get(CONF_TARGET_DATE, date.today().isoformat())): DateSelector(),
            vol.Optional(CONF_IMAGE_PATH, default=current_data.get(CONF_IMAGE_PATH, "")): str,
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

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )

            self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
            return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data
        data_schema = vol.Schema({
            vol.Required(CONF_TARGET_DATE, default=current_data.get(CONF_TARGET_DATE, date.today().isoformat())): DateSelector(),
            vol.Optional(CONF_IMAGE_PATH, default=current_data.get(CONF_IMAGE_PATH, "")): str,
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

        data_schema = vol.Schema({
            vol.Required(CONF_SPECIAL_TYPE, default=current_special_type): SelectSelector(
                SelectSelectorConfig(
                    options=special_options,
                    translation_key="special_type",
                )
            ),
            vol.Optional(CONF_IMAGE_PATH, default=current_data.get(CONF_IMAGE_PATH, "")): str,
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

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )

            self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
            return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data
        region_options = list(DST_REGIONS.keys())
        dst_type_options = list(DST_EVENT_TYPES.keys())

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
            vol.Optional(CONF_IMAGE_PATH, default=current_data.get(CONF_IMAGE_PATH, "")): str,
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
