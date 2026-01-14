"""
Tests for configuration validation.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_secret_key_required_in_production():
    """Test that SECRET_KEY is required in production environment."""
    with patch.dict(os.environ, {"ENVIRONMENT": "production", "SECRET_KEY": ""}, clear=True):
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_message = str(exc_info.value)
        assert "SECRET_KEY environment variable must be set in production" in error_message


def test_secret_key_auto_generated_in_development():
    """Test that SECRET_KEY is auto-generated in development if not set."""
    # Clear any existing SECRET_KEY
    env_vars = {
        "ENVIRONMENT": "development",
        "DATABASE_URL": "postgresql+asyncpg://postgres@localhost:5432/test_db",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings()

        # Should have auto-generated key
        assert settings.secret_key is not None
        assert len(settings.secret_key) >= 32


def test_secret_key_minimum_length_validation():
    """Test that SECRET_KEY must be at least 32 characters."""
    env_vars = {
        "ENVIRONMENT": "development",
        "SECRET_KEY": "short",  # Too short
        "DATABASE_URL": "postgresql+asyncpg://postgres@localhost:5432/test_db",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_message = str(exc_info.value)
        assert "must be at least 32 characters long" in error_message


def test_secret_key_accepts_valid_key():
    """Test that a valid SECRET_KEY is accepted."""
    valid_key = "a" * 32  # 32 characters minimum

    env_vars = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": valid_key,
        "DATABASE_URL": "postgresql+asyncpg://postgres@localhost:5432/test_db",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings()

        assert settings.secret_key == valid_key
        assert len(settings.secret_key) >= 32


def test_secret_key_accepts_urlsafe_token():
    """Test that a urlsafe token (recommended format) is accepted."""
    import secrets

    secure_key = secrets.token_urlsafe(32)  # Generates ~43 character string

    env_vars = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": secure_key,
        "DATABASE_URL": "postgresql+asyncpg://postgres@localhost:5432/test_db",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings()

        assert settings.secret_key == secure_key
        assert len(settings.secret_key) >= 32


def test_development_with_explicit_key():
    """Test that explicitly set SECRET_KEY is used even in development."""
    explicit_key = "my-explicit-dev-key-that-is-long-enough-32chars"

    env_vars = {
        "ENVIRONMENT": "development",
        "SECRET_KEY": explicit_key,
        "DATABASE_URL": "postgresql+asyncpg://postgres@localhost:5432/test_db",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings()

        # Should use explicit key, not auto-generate
        assert settings.secret_key == explicit_key
