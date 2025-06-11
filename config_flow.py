"""Config flow for WhenHub integration - INTERNATIONALIZED VERSION."""
from __future__ import annotations

import logging
import uuid
from typing import Any
import voluptuous as vol
from datetime import date

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    EVENT_TYPES,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    CONF_START_DATE,
    CONF_END_DATE,
    CONF_TARGET_DATE,
    CONF_IMAGE_PATH,
    CONF_IMAGE_UPLOAD,
    CONF_WEBSITE_URL,
    CONF_NOTES,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WhenHub - INTERNATIONALIZED VERSION."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._event_type: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - event type selection.""" 
        if user_input is None:
            return await self._show_event_type_form()

        self._event_type = user_input[CONF_EVENT_TYPE]
        
        # Route to appropriate event-specific step
        if self._event_type == EVENT_TYPE_TRIP:
            return await self.async_step_trip()
        elif self._event_type == EVENT_TYPE_MILESTONE:
            return await self.async_step_milestone()
        elif self._event_type == EVENT_TYPE_ANNIVERSARY:
            return await self.async_step_anniversary()

    async def _show_event_type_form(self) -> FlowResult:
        """Show event type selection form - INTERNATIONALIZED."""
        # MIGRATION: Remove hard-coded descriptions - these come from translations now
        event_type_options = {
            event_type: info['name'] for event_type, info in EVENT_TYPES.items()
        }
        
        data_schema = vol.Schema({
            vol.Required(CONF_EVENT_TYPE): vol.In(event_type_options)
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            # MIGRATION: Removed hard-coded description_placeholders - now in translations
        )

    async def async_step_trip(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle trip configuration - INTERNATIONALIZED."""
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
        """Show trip configuration form - INTERNATIONALIZED."""
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
            # MIGRATION: Removed hard-coded description_placeholders - now in translations
        )

    async def async_step_milestone(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle milestone configuration - INTERNATIONALIZED."""
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
        """Show milestone configuration form - INTERNATIONALIZED."""
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
            # MIGRATION: Removed hard-coded description_placeholders - now in translations
        )

    async def async_step_anniversary(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle anniversary configuration - INTERNATIONALIZED.""" 
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
        """Show anniversary configuration form - INTERNATIONALIZED."""
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
            # MIGRATION: Removed hard-coded description_placeholders - now in translations
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for WhenHub - INTERNATIONALIZED VERSION."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options - INTERNATIONALIZED."""
        # Get the event type from existing config
        event_type = self.config_entry.data.get(CONF_EVENT_TYPE, EVENT_TYPE_TRIP)
        
        # Route to appropriate options step based on event type
        if event_type == EVENT_TYPE_TRIP:
            return await self.async_step_trip_options(user_input)
        elif event_type == EVENT_TYPE_MILESTONE:
            return await self.async_step_milestone_options(user_input)
        elif event_type == EVENT_TYPE_ANNIVERSARY:
            return await self.async_step_anniversary_options(user_input)

    async def async_step_trip_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle trip options - INTERNATIONALIZED."""
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
            # MIGRATION: Removed hard-coded description_placeholders - now in translations
        )

    async def async_step_milestone_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle milestone options - INTERNATIONALIZED."""
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
            # MIGRATION: Removed hard-coded description_placeholders - now in translations
        )

    async def async_step_anniversary_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle anniversary options - INTERNATIONALIZED."""
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
            # MIGRATION: Removed hard-coded description_placeholders - now in translations
        )