"""Image platform for WhenHub integration.

This module implements image entities that display visual representations
for WhenHub events. Images can be user-provided (file paths or base64 data)
or auto-generated SVG graphics based on event type.
"""
from __future__ import annotations

import logging
import os
import base64
from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    EVENT_TYPES,
    EVENT_TYPE_TRIP,
    EVENT_TYPE_MILESTONE,
    EVENT_TYPE_ANNIVERSARY,
    CONF_EVENT_TYPE,
    CONF_EVENT_NAME,
    CONF_IMAGE_PATH,
)
from .sensors.base import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WhenHub image based on a config entry.
    
    Creates a single image entity for each WhenHub event that can display
    user-provided images or auto-generated event type graphics.
    
    Args:
        hass: Home Assistant instance
        config_entry: Config entry for this WhenHub integration instance
        async_add_entities: Callback to add entities to Home Assistant
    """
    event_data = hass.data[DOMAIN][config_entry.entry_id]
    
    # Always create one image entity per event
    image_entity = WhenHubImage(hass, config_entry, event_data)
    async_add_entities([image_entity])


class WhenHubImage(ImageEntity):
    """Image entity for WhenHub events.
    
    Displays visual representations of events with fallback hierarchy:
    1. User-uploaded base64 image data
    2. User-provided file path (/local/ or absolute paths)
    3. Auto-generated SVG based on event type (Trip=blue airplane, etc.)
    
    Handles common image formats (JPEG, PNG, WebP, GIF, SVG) and provides
    appropriate content-type headers for browser compatibility.
    """

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, event_data: dict) -> None:
        """Initialize the image entity.
        
        Args:
            hass: Home Assistant instance
            config_entry: Config entry for this integration instance
            event_data: Event configuration containing image settings
        """
        super().__init__(hass)
        
        self._config_entry = config_entry
        self._event_data = event_data
        self._attr_name = f"{event_data[CONF_EVENT_NAME]} Image"
        self._attr_unique_id = f"{config_entry.entry_id}_image"
        
        # Extract image configuration
        self._image_path = event_data.get(CONF_IMAGE_PATH)
        self._image_data = event_data.get("image_data")  # Base64 encoded image data

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity.
        
        Groups this image entity with other entities from the same WhenHub event.
        """
        return get_device_info(self._config_entry, self._event_data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes describing the image source.
        
        Provides metadata about where the image comes from for debugging
        and automation purposes.
        
        Returns:
            Dictionary with image_type and image_path information
        """
        attributes = {}
        
        # Determine and report image source type
        if self._image_data:
            # Base64 uploaded image
            attributes["image_type"] = "user_defined"
            attributes["image_path"] = "base64_data"
        elif self._image_path:
            # User provided file path
            attributes["image_type"] = "user_defined"
            attributes["image_path"] = self._image_path
        else:
            # Default system-generated SVG
            attributes["image_type"] = "system_defined"
            attributes["image_path"] = "default_svg"
        
        return attributes

    async def async_image(self) -> bytes | None:
        """Return bytes of the image to display.
        
        Implements the fallback hierarchy for image loading with comprehensive
        error handling to ensure the integration remains functional even with
        invalid image configurations.
        
        Returns:
            Image data as bytes, or auto-generated SVG on failure
        """
        try:
            # Priority 1: Try uploaded base64 image data
            if self._image_data:
                try:
                    return base64.b64decode(self._image_data)
                except Exception as err:
                    _LOGGER.warning("Error decoding Base64 image for %s: %s", 
                                   self._event_data[CONF_EVENT_NAME], err)
            
            # Priority 2: Try user-provided file path
            if self._image_path:
                image_bytes = self._load_image_from_path(self._image_path)
                if image_bytes:
                    return image_bytes
            
            # Priority 3: Return default auto-generated SVG
            return self._get_default_image()
                
        except Exception as err:
            _LOGGER.warning("Error loading image for %s: %s", 
                           self._event_data[CONF_EVENT_NAME], err)
            return self._get_default_image()

    def _load_image_from_path(self, path: str) -> bytes | None:
        """Load image from file system path.
        
        Supports both Home Assistant /local/ paths (mapped to www directory)
        and absolute file system paths with appropriate security considerations.
        
        Args:
            path: File path to load image from
            
        Returns:
            Image data as bytes, or None if loading fails
        """
        try:
            # Handle Home Assistant /local/ paths (www directory)
            if path.startswith("/local/"):
                local_path = path.replace("/local/", "")
                file_path = os.path.join(self.hass.config.config_dir, "www", local_path)
                
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        return f.read()
                else:
                    _LOGGER.warning("Image file not found: %s", file_path)
            
            # Handle absolute file system paths
            elif os.path.exists(path):
                with open(path, "rb") as f:
                    return f.read()
            else:
                _LOGGER.warning("Image file not found at path: %s", path)
                
        except Exception as err:
            _LOGGER.warning("Error loading image from path %s: %s", path, err)
        
        return None

    def _get_default_image(self) -> bytes:
        """Generate a default SVG image based on event type.
        
        Creates colored SVG graphics with appropriate icons for each event type:
        - Trip: Blue background with airplane icon
        - Milestone: Red background with flag icon  
        - Anniversary: Pink background with heart icon
        
        Returns:
            SVG image data as UTF-8 encoded bytes
        """
        # Get event type for appropriate styling
        event_type = self._event_data.get(CONF_EVENT_TYPE, EVENT_TYPE_TRIP)
        
        # Define event-specific colors and icons
        if event_type == EVENT_TYPE_TRIP:
            color = "#4a90e2"  # Blue for travel/trips
            icon_path = "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"  # Airplane-style icon
        elif event_type == EVENT_TYPE_MILESTONE:
            color = "#e74c3c"  # Red for important milestones
            icon_path = "M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z"  # Flag icon
        elif event_type == EVENT_TYPE_ANNIVERSARY:
            color = "#e91e63"  # Pink for celebrations/love
            icon_path = "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"  # Heart icon
        else:
            # Fallback for unknown event types
            color = "#4a90e2"  # Default blue
            icon_path = "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
        
        # Generate 400x300 SVG with centered icon
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="{color}"/>
  <g transform="translate(200,150) scale(8,8) translate(-12,-12)">
    <path d="{icon_path}" fill="white" fill-opacity="0.8"/>
  </g>
</svg>'''
        return svg_content.encode('utf-8')

    @property
    def state(self) -> str:
        """Return the state of the image entity.
        
        Image entities in Home Assistant use 'idle' state when ready to serve images.
        """
        return "idle"

    @property  
    def content_type(self) -> str:
        """Return the MIME content type for the image.
        
        Detects content type based on file extension or defaults to appropriate
        types for different image sources.
        
        Returns:
            MIME type string for HTTP Content-Type header
        """
        # Default SVG content type for auto-generated images
        if not self._image_path and not self._image_data:
            return "image/svg+xml"
        
        # Detect content type from file extension for user images
        if self._image_path:
            lower_path = self._image_path.lower()
            if lower_path.endswith('.png'):
                return "image/png"
            elif lower_path.endswith('.webp'):
                return "image/webp"
            elif lower_path.endswith('.gif'):
                return "image/gif"
            elif lower_path.endswith('.svg'):
                return "image/svg+xml"
        
        # Default to JPEG for base64 data and unknown extensions
        return "image/jpeg"