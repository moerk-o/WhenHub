"""Tests for WhenHub config flow."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.whenhub.const import DOMAIN


class TestConfigFlowUserStep:
    """Tests for the initial user step of config flow."""

    @pytest.mark.asyncio
    async def test_user_step_shows_event_type_form(self, hass: HomeAssistant):
        """Test that user step shows event type selection form."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        # Form should have event_type field
        assert "event_type" in result["data_schema"].schema

    @pytest.mark.asyncio
    async def test_user_step_trip_routes_to_trip_step(self, hass: HomeAssistant):
        """Test that selecting trip event type routes to trip configuration."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"event_type": "trip"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "trip"

    @pytest.mark.asyncio
    async def test_user_step_milestone_routes_to_milestone_step(self, hass: HomeAssistant):
        """Test that selecting milestone event type routes to milestone configuration."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"event_type": "milestone"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "milestone"

    @pytest.mark.asyncio
    async def test_user_step_special_routes_to_category_step(self, hass: HomeAssistant):
        """Test that selecting special event type routes to category selection."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"event_type": "special"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "special_category"


class TestConfigFlowSpecialEvents:
    """Tests for special event configuration in config flow."""

    @pytest.mark.asyncio
    async def test_special_category_dst_routes_to_dst_step(self, hass: HomeAssistant):
        """Test that selecting DST category routes to DST configuration."""
        # Start flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        # Select special event type
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"event_type": "special"}
        )
        # Select DST category
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"special_category": "dst"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "dst_event"

    @pytest.mark.asyncio
    async def test_special_category_traditional_routes_to_special_step(self, hass: HomeAssistant):
        """Test that selecting traditional category routes to special event selection."""
        # Start flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        # Select special event type
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"event_type": "special"}
        )
        # Select traditional category
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"special_category": "traditional"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "special_event"


class TestConfigFlowCompleteFlow:
    """Tests for complete config flow from start to finish."""

    @pytest.mark.asyncio
    async def test_complete_trip_flow(self, hass: HomeAssistant):
        """Test complete trip event creation flow."""
        # Start flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        # Select trip event type
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"event_type": "trip"}
        )
        # Fill trip details
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "event_name": "Test Trip",
                "start_date": "2026-08-01",
                "end_date": "2026-08-15",
                "image_path": "",
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Test Trip"
        assert result["data"]["event_type"] == "trip"
        assert result["data"]["start_date"] == "2026-08-01"
        assert result["data"]["end_date"] == "2026-08-15"

    @pytest.mark.asyncio
    async def test_complete_milestone_flow(self, hass: HomeAssistant):
        """Test complete milestone event creation flow."""
        # Start flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        # Select milestone event type
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"event_type": "milestone"}
        )
        # Fill milestone details
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "event_name": "Test Milestone",
                "target_date": "2026-12-31",
                "image_path": "",
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Test Milestone"
        assert result["data"]["event_type"] == "milestone"
        assert result["data"]["target_date"] == "2026-12-31"
