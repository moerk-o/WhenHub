"""Tests for the ImageEntity contract of WhenHubImage (issue #23).

`ImageEntity.state` is marked `@final` in HA Core and returns the ISO
timestamp of `image_last_updated`. WhenHubImage used to override `state` with
a fixed "idle" and never set `_attr_image_last_updated`. These tests pin the
corrected behaviour.
"""
from __future__ import annotations

import base64

import pytest
from freezegun import freeze_time
from homeassistant.components.image import ImageEntity
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whenhub.image import WhenHubImage

IMAGE_ENTITY_ID = "image.image_contract_event_image"

# 1x1 pixel, content is irrelevant — only the MIME handling is under test
PNG_BASE64 = base64.b64encode(b"fake_png_bytes").decode()


def create_trip_entry(**overrides) -> MockConfigEntry:
    """Create a trip config entry named 'Image Contract'."""
    data = {
        "event_type": "trip",
        "start_date": "2026-07-12",
        "end_date": "2026-07-26",
        "image_path": "",
    }
    data.update(overrides)
    return MockConfigEntry(
        domain="whenhub",
        title="Image Contract",
        data=data,
        unique_id="whenhub_image_contract",
        version=2,
    )


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Set up the integration with a single config entry."""
    assert await async_setup_component(hass, "whenhub", {})
    await hass.async_block_till_done()

    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


# ---------------------------------------------------------------------------
# state / image_last_updated
# ---------------------------------------------------------------------------

class TestImageEntityState:
    """The entity state must follow the ImageEntity contract."""

    def test_state_is_not_overridden(self):
        """WhenHubImage must not shadow the @final ImageEntity.state."""
        assert "state" not in WhenHubImage.__dict__
        assert WhenHubImage.state is ImageEntity.state

    @pytest.mark.asyncio
    async def test_state_is_iso_timestamp(self, hass: HomeAssistant):
        """The state is the ISO timestamp of image_last_updated, not 'idle'."""
        with freeze_time("2026-08-29 12:00:00+00:00"):
            await setup_entry(hass, create_trip_entry())

            state = hass.states.get(IMAGE_ENTITY_ID)

        assert state is not None
        assert state.state != "idle"
        assert state.state == "2026-08-29T12:00:00+00:00"

    @pytest.mark.asyncio
    async def test_image_last_updated_is_set(self, hass: HomeAssistant):
        """image_last_updated is set when the entity is created."""
        with freeze_time("2026-08-29 12:00:00+00:00"):
            await setup_entry(hass, create_trip_entry())

            entity = _get_image_entity(hass)

            assert entity.image_last_updated is not None
            assert entity.image_last_updated.isoformat() == "2026-08-29T12:00:00+00:00"
            assert entity.state == entity.image_last_updated.isoformat()

    @pytest.mark.asyncio
    async def test_timestamp_is_newer_after_reload_with_new_image(
        self, hass: HomeAssistant
    ):
        """A changed image via the options flow yields a newer timestamp."""
        entry = create_trip_entry()

        with freeze_time("2026-08-29 12:00:00+00:00") as frozen:
            await setup_entry(hass, entry)

            before = hass.states.get(IMAGE_ENTITY_ID).state
            assert before == "2026-08-29T12:00:00+00:00"

            frozen.move_to("2026-08-29 12:05:00+00:00")

            # Same path the options flow takes: update the entry, which
            # triggers a reload and recreates the image entity
            hass.config_entries.async_update_entry(
                entry,
                data={
                    **entry.data,
                    "image_data": PNG_BASE64,
                    "image_mime": "image/png",
                },
            )
            await hass.async_block_till_done()

            after = hass.states.get(IMAGE_ENTITY_ID).state

        assert after == "2026-08-29T12:05:00+00:00"
        assert after > before

    @pytest.mark.asyncio
    async def test_access_token_attribute_present(self, hass: HomeAssistant):
        """The @final state_attributes of ImageEntity still provide the token."""
        await setup_entry(hass, create_trip_entry())

        state = hass.states.get(IMAGE_ENTITY_ID)

        assert "access_token" in state.attributes
        # Own extra attributes are still merged in
        assert state.attributes["image_type"] == "system_defined"
        assert state.attributes["image_path"] == "default_svg"


# ---------------------------------------------------------------------------
# content_type
# ---------------------------------------------------------------------------

class TestContentType:
    """content_type is served through _attr_content_type (ImageEntity contract)."""

    def test_content_type_is_not_overridden(self):
        """WhenHubImage must not shadow the cached_property from Core."""
        assert "content_type" not in WhenHubImage.__dict__

    @pytest.mark.asyncio
    async def test_default_svg(self, hass: HomeAssistant):
        """Without a configured image the default SVG type is used."""
        await setup_entry(hass, create_trip_entry())

        assert _get_image_entity(hass).content_type == "image/svg+xml"

    @pytest.mark.asyncio
    async def test_uploaded_image_uses_stored_mime(self, hass: HomeAssistant):
        """An uploaded image uses the MIME type stored in the entry."""
        await setup_entry(
            hass,
            create_trip_entry(image_data=PNG_BASE64, image_mime="image/png"),
        )

        assert _get_image_entity(hass).content_type == "image/png"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("/local/images/trip.png", "image/png"),
            ("/local/images/trip.webp", "image/webp"),
            ("/local/images/trip.gif", "image/gif"),
            ("/local/images/trip.svg", "image/svg+xml"),
            ("/local/images/trip.jpg", "image/jpeg"),
        ],
    )
    async def test_path_extension(self, hass: HomeAssistant, path: str, expected: str):
        """The content type is detected from the file extension."""
        await setup_entry(hass, create_trip_entry(image_path=path))

        assert _get_image_entity(hass).content_type == expected

    @pytest.mark.asyncio
    async def test_upload_without_stored_mime_falls_back_to_jpeg(
        self, hass: HomeAssistant
    ):
        """Base64 data without a stored MIME type defaults to JPEG."""
        await setup_entry(hass, create_trip_entry(image_data=PNG_BASE64))

        assert _get_image_entity(hass).content_type == "image/jpeg"


def _get_image_entity(hass: HomeAssistant) -> WhenHubImage:
    """Return the WhenHubImage instance behind IMAGE_ENTITY_ID."""
    component = hass.data["image"]
    entity = component.get_entity(IMAGE_ENTITY_ID)
    assert entity is not None, "image entity not found"
    return entity
