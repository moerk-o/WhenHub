"""Tests for image upload file-type validation (fix for issue #12).

Tests _process_image_upload and _apply_image_changes to verify that
unsupported file extensions are rejected with 'image_upload_failed'.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from custom_components.whenhub.config_flow import (
    _process_image_upload,
    _apply_image_changes,
)
from custom_components.whenhub.const import CONF_IMAGE_UPLOAD, CONF_IMAGE_DELETE, CONF_IMAGE_MIME


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_hass():
    return MagicMock()


def _mock_upload(suffix: str, content: bytes = b"fake_image_data", size: int | None = None):
    """Context manager that simulates process_uploaded_file returning a path."""
    fake_path = MagicMock(spec=Path)
    fake_path.suffix = suffix
    fake_path.read_bytes.return_value = content
    # Default size: len(content) — small enough to pass the 5 MB limit
    fake_path.stat.return_value.st_size = size if size is not None else len(content)

    @contextmanager
    def _ctx(hass, upload_id):
        yield fake_path

    return patch(
        "custom_components.whenhub.config_flow.process_uploaded_file",
        side_effect=_ctx,
    )


# ---------------------------------------------------------------------------
# _process_image_upload
# ---------------------------------------------------------------------------

class TestProcessImageUpload:
    """Unit tests for _process_image_upload()."""

    def test_no_upload_returns_triple_none(self):
        """When no upload_id is in user_input, return (None, None, None)."""
        result = _process_image_upload(_fake_hass(), {})
        assert result == (None, None, None)

    def test_no_upload_key_missing(self):
        """Missing CONF_IMAGE_UPLOAD key → (None, None, None)."""
        result = _process_image_upload(_fake_hass(), {"other_key": "value"})
        assert result == (None, None, None)

    def test_valid_jpg_accepted(self):
        """JPEG file upload returns (base64_data, 'image/jpeg', None)."""
        with _mock_upload(".jpg", b"jpeg_bytes"):
            data, mime, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert data is not None
        assert mime == "image/jpeg"
        assert error is None

    def test_valid_jpeg_accepted(self):
        """.jpeg extension also maps to image/jpeg."""
        with _mock_upload(".jpeg"):
            data, mime, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert mime == "image/jpeg"
        assert error is None

    def test_valid_png_accepted(self):
        """.png returns image/png."""
        with _mock_upload(".png"):
            data, mime, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert mime == "image/png"
        assert error is None

    def test_valid_webp_accepted(self):
        """.webp returns image/webp."""
        with _mock_upload(".webp"):
            data, mime, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert mime == "image/webp"
        assert error is None

    def test_valid_gif_accepted(self):
        """.gif returns image/gif."""
        with _mock_upload(".gif"):
            data, mime, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert mime == "image/gif"
        assert error is None

    def test_pdf_rejected(self):
        """PDF files return (None, None, 'image_upload_failed')."""
        with _mock_upload(".pdf"):
            data, mime, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert data is None
        assert mime is None
        assert error == "image_upload_failed"

    def test_exe_rejected(self):
        """Executable files return error."""
        with _mock_upload(".exe"):
            data, mime, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert error == "image_upload_failed"

    def test_txt_rejected(self):
        """Text files return error."""
        with _mock_upload(".txt"):
            _, _, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert error == "image_upload_failed"

    def test_no_extension_rejected(self):
        """Files without extension return error."""
        with _mock_upload(""):
            _, _, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert error == "image_upload_failed"

    def test_uppercase_extension_accepted(self):
        """Extension check is case-insensitive (.JPG should be accepted)."""
        with _mock_upload(".JPG"):
            data, mime, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert error is None
        assert mime == "image/jpeg"

    def test_base64_data_is_returned(self):
        """Successful upload returns base64-encoded content."""
        import base64
        content = b"hello image bytes"
        with _mock_upload(".png", content):
            data, mime, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert data == base64.b64encode(content).decode()

    def test_file_too_large_rejected(self):
        """Files exceeding 5 MB return 'image_too_large' error."""
        from custom_components.whenhub.config_flow import _MAX_IMAGE_SIZE_BYTES

        fake_path = MagicMock(spec=Path)
        fake_path.suffix = ".jpg"
        fake_path.stat.return_value.st_size = _MAX_IMAGE_SIZE_BYTES + 1

        @contextmanager
        def _ctx(hass, upload_id):
            yield fake_path

        with patch(
            "custom_components.whenhub.config_flow.process_uploaded_file",
            side_effect=_ctx,
        ):
            data, mime, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert data is None
        assert mime is None
        assert error == "image_too_large"

    def test_file_exactly_at_limit_accepted(self):
        """File exactly at 5 MB limit is accepted."""
        from custom_components.whenhub.config_flow import _MAX_IMAGE_SIZE_BYTES
        import base64

        content = b"x" * _MAX_IMAGE_SIZE_BYTES
        fake_path = MagicMock(spec=Path)
        fake_path.suffix = ".png"
        fake_path.stat.return_value.st_size = _MAX_IMAGE_SIZE_BYTES
        fake_path.read_bytes.return_value = content

        @contextmanager
        def _ctx(hass, upload_id):
            yield fake_path

        with patch(
            "custom_components.whenhub.config_flow.process_uploaded_file",
            side_effect=_ctx,
        ):
            data, mime, error = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert error is None
        assert mime == "image/png"

    def test_exception_returns_triple_none(self):
        """If process_uploaded_file raises, return (None, None, None) — not an error."""
        with patch(
            "custom_components.whenhub.config_flow.process_uploaded_file",
            side_effect=OSError("disk error"),
        ):
            result = _process_image_upload(
                _fake_hass(), {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert result == (None, None, None)


# ---------------------------------------------------------------------------
# _apply_image_changes
# ---------------------------------------------------------------------------

class TestApplyImageChanges:
    """Unit tests for _apply_image_changes()."""

    def test_no_upload_returns_none(self):
        """No upload provided → no error, new_data unchanged."""
        new_data = {}
        error = _apply_image_changes(_fake_hass(), new_data, {})
        assert error is None

    def test_valid_upload_stores_data(self):
        """Valid upload stores image_data and image_mime, returns None."""
        new_data = {}
        with _mock_upload(".jpg", b"img"):
            error = _apply_image_changes(
                _fake_hass(), new_data, {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert error is None
        assert "image_data" in new_data
        assert new_data[CONF_IMAGE_MIME] == "image/jpeg"

    def test_invalid_upload_returns_error_key(self):
        """Invalid file type → returns 'image_upload_failed', does not store data."""
        new_data = {}
        with _mock_upload(".pdf"):
            error = _apply_image_changes(
                _fake_hass(), new_data, {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert error == "image_upload_failed"
        assert "image_data" not in new_data

    def test_invalid_upload_does_not_corrupt_existing_image(self):
        """When validation fails, existing image_data is NOT overwritten."""
        new_data = {"image_data": "old_data", CONF_IMAGE_MIME: "image/png"}
        with _mock_upload(".exe"):
            error = _apply_image_changes(
                _fake_hass(), new_data, {CONF_IMAGE_UPLOAD: "upload123"}
            )
        assert error == "image_upload_failed"
        assert new_data["image_data"] == "old_data"

    def test_image_delete_clears_data(self):
        """CONF_IMAGE_DELETE flag clears existing image, returns None."""
        new_data = {"image_data": "some_data", CONF_IMAGE_MIME: "image/jpg"}
        error = _apply_image_changes(
            _fake_hass(), new_data, {CONF_IMAGE_DELETE: True}
        )
        assert error is None
        assert new_data["image_data"] is None
        assert new_data[CONF_IMAGE_MIME] is None

    def test_upload_key_removed_from_new_data(self):
        """CONF_IMAGE_UPLOAD key is always removed from new_data."""
        new_data = {CONF_IMAGE_UPLOAD: "some_id"}
        with _mock_upload(".png"):
            _apply_image_changes(
                _fake_hass(), new_data, {CONF_IMAGE_UPLOAD: "some_id"}
            )
        assert CONF_IMAGE_UPLOAD not in new_data

    def test_upload_key_removed_even_on_error(self):
        """CONF_IMAGE_UPLOAD is removed from new_data even when validation fails."""
        new_data = {CONF_IMAGE_UPLOAD: "some_id"}
        with _mock_upload(".pdf"):
            _apply_image_changes(
                _fake_hass(), new_data, {CONF_IMAGE_UPLOAD: "some_id"}
            )
        assert CONF_IMAGE_UPLOAD not in new_data
