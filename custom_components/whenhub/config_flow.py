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
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import (
    DOMAIN,
    EVENT_TYPES,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
    EVENT_TYPE_SPECIAL,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    CONF_START_DATE,
    CONF_END_DATE,
    CONF_TARGET_DATE,
    CONF_SPECIAL_TYPE,
    CONF_SPECIAL_CATEGORY,
    CONF_IMAGE_PATH,
    CONF_IMAGE_UPLOAD,
    CONF_WEBSITE_URL,
    CONF_NOTES,
    SPECIAL_EVENTS,
    SPECIAL_EVENT_CATEGORIES,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WhenHub."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._event_type: str | None = None
        self._special_category: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - event type selection.""" 
        if user_input is None:
            return await self._show_event_type_form()

        self._event_type = user_input[CONF_EVENT_TYPE]
        
        # Route to the appropriate event-specific step
        if self._event_type == EVENT_TYPE_TRIP:
            return await self.async_step_trip()
        elif self._event_type == EVENT_TYPE_MILESTONE:
            return await self.async_step_milestone()
        elif self._event_type == EVENT_TYPE_ANNIVERSARY:
            return await self.async_step_anniversary()
        elif self._event_type == EVENT_TYPE_SPECIAL:
            return await self.async_step_special_category()

    async def _show_event_type_form(self) -> FlowResult:
        """Show event type selection form."""
        # Use simple string list for options - labels come from translation_key
        # See: https://developers.home-assistant.io/docs/internationalization/core/#selector
        event_type_options = list(EVENT_TYPES.keys())

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

    async def async_step_trip(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle trip configuration."""
        if user_input is None:
            return await self._show_trip_form()

        errors = {}

        # Validate dates for trip
        try:
            start_date = user_input[CONF_START_DATE]
            end_date = user_input[CONF_END_DATE]
            
            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)
                
            if start_date >= end_date:
                errors["base"] = "invalid_dates"
        except ValueError:
            errors["base"] = "invalid_date_format"

        if not errors:
            # Add event type to data
            user_input[CONF_EVENT_TYPE] = self._event_type
            
            # Create unique ID
            event_name = user_input[CONF_EVENT_NAME]
            await self.async_set_unique_id(f"{DOMAIN}_{event_name.lower().replace(' ', '_')}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=event_name,
                data=user_input,
            )

        return await self._show_trip_form(user_input, errors)

    async def _show_trip_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show trip configuration form."""
        data_schema = vol.Schema({
            vol.Required(CONF_EVENT_NAME, default="" if user_input is None else user_input.get(CONF_EVENT_NAME, "")): str,
            vol.Required(CONF_START_DATE, default=date.today().isoformat() if user_input is None else user_input.get(CONF_START_DATE, date.today().isoformat())): str,
            vol.Required(CONF_END_DATE, default="" if user_input is None else user_input.get(CONF_END_DATE, "")): str,
            vol.Optional(CONF_IMAGE_PATH, default="" if user_input is None else user_input.get(CONF_IMAGE_PATH, "")): str,
            vol.Optional(CONF_WEBSITE_URL, default="" if user_input is None else user_input.get(CONF_WEBSITE_URL, "")): str,
            vol.Optional(CONF_NOTES, default="" if user_input is None else user_input.get(CONF_NOTES, "")): str,
        })

        return self.async_show_form(
            step_id="trip",
            data_schema=data_schema,
            errors=errors or {},
            description_placeholders={
                "event_name": "z.B. Dänemarkurlaub 2025",
                "start_date": "Format: YYYY-MM-DD",
                "end_date": "Format: YYYY-MM-DD", 
                "image_path": "z.B. /local/images/event.jpg (optional)",
                "website_url": "URL zur Unterkunft (optional)",
                "notes": "Zusätzliche Notizen (optional)",
            },
        )

    async def async_step_milestone(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle milestone configuration."""
        if user_input is None:
            return await self._show_milestone_form()

        errors = {}

        # Validate date for milestone
        try:
            target_date = user_input[CONF_TARGET_DATE]
            if isinstance(target_date, str):
                target_date = date.fromisoformat(target_date)
        except ValueError:
            errors["base"] = "invalid_date_format"

        if not errors:
            # Add event type to data
            user_input[CONF_EVENT_TYPE] = self._event_type
            
            # Create unique ID
            event_name = user_input[CONF_EVENT_NAME]
            await self.async_set_unique_id(f"{DOMAIN}_{event_name.lower().replace(' ', '_')}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=event_name,
                data=user_input,
            )

        return await self._show_milestone_form(user_input, errors)

    async def _show_milestone_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show milestone configuration form."""
        data_schema = vol.Schema({
            vol.Required(CONF_EVENT_NAME, default="" if user_input is None else user_input.get(CONF_EVENT_NAME, "")): str,
            vol.Required(CONF_TARGET_DATE, default=date.today().isoformat() if user_input is None else user_input.get(CONF_TARGET_DATE, date.today().isoformat())): str,
            vol.Optional(CONF_IMAGE_PATH, default="" if user_input is None else user_input.get(CONF_IMAGE_PATH, "")): str,
            vol.Optional(CONF_WEBSITE_URL, default="" if user_input is None else user_input.get(CONF_WEBSITE_URL, "")): str,
            vol.Optional(CONF_NOTES, default="" if user_input is None else user_input.get(CONF_NOTES, "")): str,
        })

        return self.async_show_form(
            step_id="milestone",
            data_schema=data_schema,
            errors=errors or {},
            description_placeholders={
                "event_name": "z.B. Geburtstag Max oder Projektabgabe",
                "target_date": "Format: YYYY-MM-DD",
                "image_path": "z.B. /local/images/event.jpg (optional)",
                "website_url": "Relevante URL (optional)",
                "notes": "Zusätzliche Notizen (optional)",
            },
        )

    async def async_step_anniversary(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle anniversary configuration.""" 
        if user_input is None:
            return await self._show_anniversary_form()

        errors = {}

        # Validate date for anniversary
        try:
            target_date = user_input[CONF_TARGET_DATE]
            if isinstance(target_date, str):
                target_date = date.fromisoformat(target_date)
        except ValueError:
            errors["base"] = "invalid_date_format"

        if not errors:
            # Add event type to data
            user_input[CONF_EVENT_TYPE] = self._event_type
            
            # Create unique ID
            event_name = user_input[CONF_EVENT_NAME]
            await self.async_set_unique_id(f"{DOMAIN}_{event_name.lower().replace(' ', '_')}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=event_name,
                data=user_input,
            )

        return await self._show_anniversary_form(user_input, errors)

    async def _show_anniversary_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show anniversary configuration form."""
        data_schema = vol.Schema({
            vol.Required(CONF_EVENT_NAME, default="" if user_input is None else user_input.get(CONF_EVENT_NAME, "")): str,
            vol.Required(CONF_TARGET_DATE, default=date.today().isoformat() if user_input is None else user_input.get(CONF_TARGET_DATE, date.today().isoformat())): str,
            vol.Optional(CONF_IMAGE_PATH, default="" if user_input is None else user_input.get(CONF_IMAGE_PATH, "")): str,
            vol.Optional(CONF_WEBSITE_URL, default="" if user_input is None else user_input.get(CONF_WEBSITE_URL, "")): str,
            vol.Optional(CONF_NOTES, default="" if user_input is None else user_input.get(CONF_NOTES, "")): str,
        })

        return self.async_show_form(
            step_id="anniversary",
            data_schema=data_schema,
            errors=errors or {},
            description_placeholders={
                "event_name": "z.B. Hochzeitstag oder Firmenjubiläum",
                "target_date": "Ursprüngliches Datum (YYYY-MM-DD)",
                "image_path": "z.B. /local/images/event.jpg (optional)",
                "website_url": "Relevante URL (optional)",
                "notes": "Zusätzliche Notizen (optional)",
            },
        )

    async def async_step_special_category(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle special event category selection."""
        if user_input is None:
            return await self._show_special_category_form()

        self._special_category = user_input[CONF_SPECIAL_CATEGORY]
        return await self.async_step_special_event()

    async def _show_special_category_form(self) -> FlowResult:
        """Show special event category selection form."""
        # Use simple string list for options - labels come from translation_key
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

        # Add event type and category to data
        user_input[CONF_EVENT_TYPE] = self._event_type
        user_input[CONF_SPECIAL_CATEGORY] = self._special_category
        
        # Create unique ID
        event_name = user_input[CONF_EVENT_NAME]
        await self.async_set_unique_id(f"{DOMAIN}_{event_name.lower().replace(' ', '_')}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=event_name,
            data=user_input,
        )

    async def _show_special_event_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show special event selection and configuration form."""
        # Filter events by selected category
        filtered_events = {
            key: info for key, info in SPECIAL_EVENTS.items()
            if info.get("category") == self._special_category
        }

        # Use simple string list for options - labels come from translation_key
        special_options = list(filtered_events.keys())

        # Get default value
        default_special_type = special_options[0] if special_options else ""
        if user_input is not None:
            default_special_type = user_input.get(CONF_SPECIAL_TYPE, default_special_type)

        data_schema = vol.Schema({
            vol.Required(CONF_EVENT_NAME, default="" if user_input is None else user_input.get(CONF_EVENT_NAME, "")): str,
            vol.Required(CONF_SPECIAL_TYPE, default=default_special_type): SelectSelector(
                SelectSelectorConfig(
                    options=special_options,
                    translation_key="special_type",
                )
            ),
            vol.Optional(CONF_IMAGE_PATH, default="" if user_input is None else user_input.get(CONF_IMAGE_PATH, "")): str,
            vol.Optional(CONF_WEBSITE_URL, default="" if user_input is None else user_input.get(CONF_WEBSITE_URL, "")): str,
            vol.Optional(CONF_NOTES, default="" if user_input is None else user_input.get(CONF_NOTES, "")): str,
        })

        return self.async_show_form(
            step_id="special_event",
            data_schema=data_schema,
            errors=errors or {},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for WhenHub."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        # Get the event type from existing config
        event_type = self.config_entry.data.get(CONF_EVENT_TYPE, EVENT_TYPE_TRIP)
        
        # Route to appropriate options step based on event type
        if event_type == EVENT_TYPE_TRIP:
            return await self.async_step_trip_options(user_input)
        elif event_type == EVENT_TYPE_MILESTONE:
            return await self.async_step_milestone_options(user_input)
        elif event_type == EVENT_TYPE_ANNIVERSARY:
            return await self.async_step_anniversary_options(user_input)
        elif event_type == EVENT_TYPE_SPECIAL:
            return await self.async_step_special_options(user_input)

    async def async_step_trip_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle trip options."""
        if user_input is not None:
            errors = {}
            try:
                start_date = user_input[CONF_START_DATE]
                end_date = user_input[CONF_END_DATE]
                
                if isinstance(start_date, str):
                    start_date = date.fromisoformat(start_date)
                if isinstance(end_date, str):
                    end_date = date.fromisoformat(end_date)
                    
                if start_date >= end_date:
                    errors["base"] = "invalid_dates"
            except ValueError:
                errors["base"] = "invalid_date_format"

            if not errors:
                # Keep original event type
                user_input[CONF_EVENT_TYPE] = self.config_entry.data[CONF_EVENT_TYPE]
                
                # Update the config entry
                new_data = dict(self.config_entry.data)
                new_data.update(user_input)
                
                self.hass.config_entries.async_update_entry(
                    self.config_entry, 
                    data=new_data,
                    title=user_input[CONF_EVENT_NAME]
                )
                
                self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
                return self.async_create_entry(title="", data={})

        # Show current trip data
        current_data = self.config_entry.data
        data_schema = vol.Schema({
            vol.Required(CONF_EVENT_NAME, default=current_data.get(CONF_EVENT_NAME, "")): str,
            vol.Required(CONF_START_DATE, default=current_data.get(CONF_START_DATE, date.today().isoformat())): str,
            vol.Required(CONF_END_DATE, default=current_data.get(CONF_END_DATE, "")): str,
            vol.Optional(CONF_IMAGE_PATH, default=current_data.get(CONF_IMAGE_PATH, "")): str,
            vol.Optional(CONF_WEBSITE_URL, default=current_data.get(CONF_WEBSITE_URL, "")): str,
            vol.Optional(CONF_NOTES, default=current_data.get(CONF_NOTES, "")): str,
        })

        return self.async_show_form(
            step_id="trip_options",
            data_schema=data_schema,
        )

    async def async_step_milestone_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle milestone options."""
        if user_input is not None:
            errors = {}
            try:
                target_date = user_input[CONF_TARGET_DATE]
                if isinstance(target_date, str):
                    date.fromisoformat(target_date)
            except ValueError:
                errors["base"] = "invalid_date_format"

            if not errors:
                user_input[CONF_EVENT_TYPE] = self.config_entry.data[CONF_EVENT_TYPE]
                
                new_data = dict(self.config_entry.data)
                new_data.update(user_input)
                
                self.hass.config_entries.async_update_entry(
                    self.config_entry, 
                    data=new_data,
                    title=user_input[CONF_EVENT_NAME]
                )
                
                self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
                return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data
        data_schema = vol.Schema({
            vol.Required(CONF_EVENT_NAME, default=current_data.get(CONF_EVENT_NAME, "")): str,
            vol.Required(CONF_TARGET_DATE, default=current_data.get(CONF_TARGET_DATE, date.today().isoformat())): str,
            vol.Optional(CONF_IMAGE_PATH, default=current_data.get(CONF_IMAGE_PATH, "")): str,
            vol.Optional(CONF_WEBSITE_URL, default=current_data.get(CONF_WEBSITE_URL, "")): str,
            vol.Optional(CONF_NOTES, default=current_data.get(CONF_NOTES, "")): str,
        })

        return self.async_show_form(
            step_id="milestone_options",
            data_schema=data_schema,
            description_placeholders={
                "event_name": "z.B. Geburtstag Max oder Projektabgabe",
                "target_date": "Format: YYYY-MM-DD",
                "image_path": "z.B. /local/images/event.jpg (optional)",
                "website_url": "Relevante URL (optional)",
                "notes": "Zusätzliche Notizen (optional)",
            },
        )

    async def async_step_anniversary_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle anniversary options."""
        if user_input is not None:
            errors = {}
            try:
                target_date = user_input[CONF_TARGET_DATE]
                if isinstance(target_date, str):
                    date.fromisoformat(target_date)
            except ValueError:
                errors["base"] = "invalid_date_format"

            if not errors:
                user_input[CONF_EVENT_TYPE] = self.config_entry.data[CONF_EVENT_TYPE]
                
                new_data = dict(self.config_entry.data)
                new_data.update(user_input)
                
                self.hass.config_entries.async_update_entry(
                    self.config_entry, 
                    data=new_data,
                    title=user_input[CONF_EVENT_NAME]
                )
                
                self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
                return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data
        data_schema = vol.Schema({
            vol.Required(CONF_EVENT_NAME, default=current_data.get(CONF_EVENT_NAME, "")): str,
            vol.Required(CONF_TARGET_DATE, default=current_data.get(CONF_TARGET_DATE, date.today().isoformat())): str,
            vol.Optional(CONF_IMAGE_PATH, default=current_data.get(CONF_IMAGE_PATH, "")): str,
            vol.Optional(CONF_WEBSITE_URL, default=current_data.get(CONF_WEBSITE_URL, "")): str,
            vol.Optional(CONF_NOTES, default=current_data.get(CONF_NOTES, "")): str,
        })

        return self.async_show_form(
            step_id="anniversary_options",
            data_schema=data_schema,
            description_placeholders={
                "event_name": "z.B. Hochzeitstag oder Firmenjubiläum",
                "target_date": "Ursprüngliches Datum (YYYY-MM-DD)",
                "image_path": "z.B. /local/images/event.jpg (optional)",
                "website_url": "Relevante URL (optional)",
                "notes": "Zusätzliche Notizen (optional)",
            },
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
                title=user_input[CONF_EVENT_NAME]
            )

            self.hass.data[DOMAIN][self.config_entry.entry_id] = new_data
            return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data

        # Get current category or determine from existing special_type
        current_category = current_data.get(CONF_SPECIAL_CATEGORY)
        current_special_type = current_data.get(CONF_SPECIAL_TYPE, "christmas_eve")

        # If no category is saved, try to determine it from the special_type
        if not current_category:
            for event_key, event_info in SPECIAL_EVENTS.items():
                if event_key == current_special_type:
                    current_category = event_info.get("category", "traditional")
                    break
            if not current_category:
                current_category = "traditional"

        # Filter events by current category
        filtered_events = {
            key: info for key, info in SPECIAL_EVENTS.items()
            if info.get("category") == current_category
        }

        # Use simple string list for options - labels come from translation_key
        special_options = list(filtered_events.keys())

        data_schema = vol.Schema({
            vol.Required(CONF_EVENT_NAME, default=current_data.get(CONF_EVENT_NAME, "")): str,
            vol.Required(CONF_SPECIAL_TYPE, default=current_special_type): SelectSelector(
                SelectSelectorConfig(
                    options=special_options,
                    translation_key="special_type",
                )
            ),
            vol.Optional(CONF_IMAGE_PATH, default=current_data.get(CONF_IMAGE_PATH, "")): str,
            vol.Optional(CONF_WEBSITE_URL, default=current_data.get(CONF_WEBSITE_URL, "")): str,
            vol.Optional(CONF_NOTES, default=current_data.get(CONF_NOTES, "")): str,
        })

        return self.async_show_form(
            step_id="special_options",
            data_schema=data_schema,
        )