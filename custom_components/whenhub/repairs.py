"""HA Repairs integration for WhenHub — expired event notifications.

When an event expires and the user has opted in via CONF_NOTIFY_ON_EXPIRY,
a Repairs issue is created. The fix flow offers to remove the config entry.
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Return the repair flow for a WhenHub issue."""
    return WhenHubRepairsFlow(issue_id, data)


class WhenHubRepairsFlow(RepairsFlow):
    """Repair flow for an expired WhenHub event.

    Presents a confirmation step with a warning about dashboards/automations,
    then removes the config entry on confirmation.
    """

    def __init__(
        self,
        issue_id: str,
        data: dict[str, str | int | float | None] | None,
    ) -> None:
        """Initialize the repair flow."""
        self._issue_id = issue_id
        self._data = data or {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Entry point — forward to confirm step."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show confirmation form, then remove the entry on submit."""
        if user_input is not None:
            entry_id = self._data.get("entry_id")
            if entry_id:
                entry = self.hass.config_entries.async_get_entry(entry_id)
                if entry:
                    await self.hass.config_entries.async_remove(entry_id)
                    _LOGGER.info(
                        "WhenHub: removed expired event entry %s via Repairs fix flow",
                        entry_id,
                    )
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "event_name": self._data.get("event_name", ""),
                "expiry_date": self._data.get("expiry_date", ""),
            },
        )
