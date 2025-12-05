"""
Tests for configuration module (ADR-011, ADR-071).

Tests validate that settings are properly loaded from environment variables.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import Settings, get_settings


class TestSettings:
    """Tests for Settings configuration class."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.flask_env == "development"
            assert settings.debug is False
            assert settings.host == "0.0.0.0"
            assert settings.port == 5000
            assert settings.db_name == "anthropic_data"
            assert settings.log_level == "INFO"

    def test_secret_key_generated_if_not_set(self) -> None:
        """Test that secret key is auto-generated if not provided."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.secret_key is not None
            assert len(settings.secret_key) == 64  # hex string of 32 bytes

    def test_secret_key_from_env(self) -> None:
        """Test loading secret key from environment variable."""
        with patch.dict(os.environ, {"SECRET_KEY": "my-custom-secret"}, clear=True):
            settings = Settings()
            assert settings.secret_key == "my-custom-secret"

    def test_mongo_uri_from_env(self) -> None:
        """Test loading MongoDB URI from environment."""
        test_uri = "mongodb://user:pass@localhost:27017/"
        with patch.dict(os.environ, {"MONGO_URI": test_uri}, clear=True):
            settings = Settings()
            assert settings.mongo_uri == test_uri

    def test_flask_env_normalization(self) -> None:
        """Test that flask_env is normalized to lowercase."""
        with patch.dict(os.environ, {"FLASK_ENV": "PRODUCTION"}, clear=True):
            settings = Settings()
            assert settings.flask_env == "production"

    def test_is_production_property(self) -> None:
        """Test is_production property."""
        with patch.dict(os.environ, {"FLASK_ENV": "production"}, clear=True):
            settings = Settings()
            assert settings.is_production is True
            assert settings.is_development is False
            assert settings.is_testing is False

    def test_is_development_property(self) -> None:
        """Test is_development property."""
        with patch.dict(os.environ, {"FLASK_ENV": "development"}, clear=True):
            settings = Settings()
            assert settings.is_development is True
            assert settings.is_production is False

    def test_is_testing_property(self) -> None:
        """Test is_testing property."""
        with patch.dict(os.environ, {"FLASK_ENV": "testing"}, clear=True):
            settings = Settings()
            assert settings.is_testing is True
            assert settings.is_production is False

    def test_port_validation_min(self) -> None:
        """Test that port must be at least 1."""
        with patch.dict(os.environ, {"PORT": "0"}, clear=True):
            with pytest.raises(ValueError):
                Settings()

    def test_port_validation_max(self) -> None:
        """Test that port must be at most 65535."""
        with patch.dict(os.environ, {"PORT": "70000"}, clear=True):
            with pytest.raises(ValueError):
                Settings()

    def test_max_content_length_from_env(self) -> None:
        """Test loading max content length from environment."""
        with patch.dict(os.environ, {"MAX_CONTENT_LENGTH": "104857600"}, clear=True):
            settings = Settings()
            assert settings.max_content_length == 104857600  # 100MB

    def test_log_level_validation(self) -> None:
        """Test that log level must be valid."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True):
            settings = Settings()
            assert settings.log_level == "DEBUG"

    def test_log_format_options(self) -> None:
        """Test log format options."""
        with patch.dict(os.environ, {"LOG_FORMAT": "json"}, clear=True):
            settings = Settings()
            assert settings.log_format == "json"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings_instance(self) -> None:
        """Test that get_settings returns a Settings instance."""
        # Clear cache first
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self) -> None:
        """Test that get_settings returns cached instance."""
        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

