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


class TestOptionsFlow:
    """Tests for options flow (reconfiguring existing entries)."""

    @pytest.mark.asyncio
    async def test_options_flow_trip_shows_form(self, hass: HomeAssistant, trip_config_entry):
        """Test that options flow for trip shows the correct form."""
        trip_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_config_entry.entry_id)
        await hass.async_block_till_done()

        # Start options flow
        result = await hass.config_entries.options.async_init(trip_config_entry.entry_id)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "trip_options"
        # Form should have the expected fields
        schema_keys = list(result["data_schema"].schema.keys())
        assert any("event_name" in str(k) for k in schema_keys)
        assert any("start_date" in str(k) for k in schema_keys)
        assert any("end_date" in str(k) for k in schema_keys)

    @pytest.mark.asyncio
    async def test_options_flow_trip_update(self, hass: HomeAssistant, trip_config_entry):
        """Test that trip options can be updated."""
        from datetime import date
        trip_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_config_entry.entry_id)
        await hass.async_block_till_done()

        # Start options flow
        result = await hass.config_entries.options.async_init(trip_config_entry.entry_id)

        # Update trip details
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "event_name": "Updated Trip Name",
                "start_date": date(2026, 9, 1),
                "end_date": date(2026, 9, 15),
                "image_path": "",
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        # Verify entry was updated
        assert trip_config_entry.data["event_name"] == "Updated Trip Name"

    @pytest.mark.asyncio
    async def test_options_flow_milestone_shows_form(self, hass: HomeAssistant, milestone_config_entry):
        """Test that options flow for milestone shows the correct form."""
        milestone_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone_config_entry.entry_id)
        await hass.async_block_till_done()

        # Start options flow
        result = await hass.config_entries.options.async_init(milestone_config_entry.entry_id)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "milestone_options"
        schema_keys = list(result["data_schema"].schema.keys())
        assert any("event_name" in str(k) for k in schema_keys)
        assert any("target_date" in str(k) for k in schema_keys)

    @pytest.mark.asyncio
    async def test_options_flow_milestone_update(self, hass: HomeAssistant, milestone_config_entry):
        """Test that milestone options can be updated."""
        from datetime import date
        milestone_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(milestone_config_entry.entry_id)
        await hass.async_block_till_done()

        # Start options flow
        result = await hass.config_entries.options.async_init(milestone_config_entry.entry_id)

        # Update milestone details
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "event_name": "Updated Milestone",
                "target_date": date(2026, 6, 30),
                "image_path": "",
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert milestone_config_entry.data["event_name"] == "Updated Milestone"

    @pytest.mark.asyncio
    async def test_options_flow_anniversary_shows_form(self, hass: HomeAssistant, anniversary_config_entry):
        """Test that options flow for anniversary shows the correct form."""
        anniversary_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_config_entry.entry_id)
        await hass.async_block_till_done()

        # Start options flow
        result = await hass.config_entries.options.async_init(anniversary_config_entry.entry_id)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "anniversary_options"
        schema_keys = list(result["data_schema"].schema.keys())
        assert any("event_name" in str(k) for k in schema_keys)
        assert any("target_date" in str(k) for k in schema_keys)

    @pytest.mark.asyncio
    async def test_options_flow_anniversary_update(self, hass: HomeAssistant, anniversary_config_entry):
        """Test that anniversary options can be updated."""
        from datetime import date
        anniversary_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(anniversary_config_entry.entry_id)
        await hass.async_block_till_done()

        # Start options flow
        result = await hass.config_entries.options.async_init(anniversary_config_entry.entry_id)

        # Update anniversary details
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "event_name": "Updated Anniversary",
                "target_date": date(2010, 6, 15),
                "image_path": "",
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert anniversary_config_entry.data["event_name"] == "Updated Anniversary"

    @pytest.mark.asyncio
    async def test_options_flow_special_shows_form(self, hass: HomeAssistant, special_config_entry):
        """Test that options flow for special event shows the correct form."""
        special_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(special_config_entry.entry_id)
        await hass.async_block_till_done()

        # Start options flow
        result = await hass.config_entries.options.async_init(special_config_entry.entry_id)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "special_options"
        schema_keys = list(result["data_schema"].schema.keys())
        assert any("event_name" in str(k) for k in schema_keys)

    @pytest.mark.asyncio
    async def test_options_flow_special_update(self, hass: HomeAssistant, special_config_entry):
        """Test that special event options can be updated."""
        special_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(special_config_entry.entry_id)
        await hass.async_block_till_done()

        # Start options flow
        result = await hass.config_entries.options.async_init(special_config_entry.entry_id)

        # Update special event details
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "event_name": "Updated Christmas",
                "image_path": "",
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert special_config_entry.data["event_name"] == "Updated Christmas"

    @pytest.mark.asyncio
    async def test_options_flow_dst_shows_form(self, hass: HomeAssistant, dst_eu_config_entry):
        """Test that options flow for DST event shows the correct form."""
        dst_eu_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(dst_eu_config_entry.entry_id)
        await hass.async_block_till_done()

        # Start options flow
        result = await hass.config_entries.options.async_init(dst_eu_config_entry.entry_id)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "dst_options"
        schema_keys = list(result["data_schema"].schema.keys())
        assert any("event_name" in str(k) for k in schema_keys)

    @pytest.mark.asyncio
    async def test_options_flow_dst_update(self, hass: HomeAssistant, dst_eu_config_entry):
        """Test that DST event options can be updated."""
        dst_eu_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(dst_eu_config_entry.entry_id)
        await hass.async_block_till_done()

        # Start options flow
        result = await hass.config_entries.options.async_init(dst_eu_config_entry.entry_id)

        # Update DST event details
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "event_name": "Updated DST Event",
                "dst_region": "eu",
                "dst_type": "next_change",
                "image_path": "",
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert dst_eu_config_entry.data["event_name"] == "Updated DST Event"

    @pytest.mark.asyncio
    async def test_options_flow_trip_invalid_dates(self, hass: HomeAssistant, trip_config_entry):
        """Test that trip options flow rejects invalid date range."""
        from datetime import date
        trip_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(trip_config_entry.entry_id)
        await hass.async_block_till_done()

        # Start options flow
        result = await hass.config_entries.options.async_init(trip_config_entry.entry_id)

        # Try to set end date before start date
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "event_name": "Invalid Trip",
                "start_date": date(2026, 9, 15),
                "end_date": date(2026, 9, 1),  # End before start
                "image_path": "",
            }
        )

        # Should show form again with error
        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_dates"
