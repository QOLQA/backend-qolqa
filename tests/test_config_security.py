"""
Security tests for application configuration.

Covers the production guard on ``secret_key``:
- the default / weak development key must never boot a production instance
- the key must be masked in ``repr()`` / ``str()`` so it cannot leak into logs
"""
import pytest
from pydantic import ValidationError

from config.settings import Settings


STRONG_SECRET_KEY = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
DEFAULT_DEV_SECRET_KEY = "dev-secret-key-CHANGE-THIS-IN-PRODUCTION-min-32-characters"


def build_settings(**kwargs) -> Settings:
    """Build a Settings instance with the required fields already satisfied.

    ``database_url`` and ``type_db`` are the required fields behind the
    ``DATABASE_URL`` / ``TYPE_DB`` environment variables. ``BaseSettings`` is
    configured with ``extra='forbid'``, so the field names — not the env var
    names — must be used as init kwargs.
    """
    return Settings(
        database_url="mongodb://localhost:27017/test_db",
        type_db="mongo",
        **kwargs,
    )


@pytest.mark.unit
class TestSecretKeyProductionGuard:
    """The production guard must actually fire."""

    @pytest.mark.parametrize(
        "weak_key",
        [
            DEFAULT_DEV_SECRET_KEY,
            "change-this-secret-key",
            "secret",
            "secret-key",
        ],
    )
    def test_production_rejects_weak_secret_keys(self, weak_key):
        """Known default/weak keys are rejected when environment is production."""
        with pytest.raises(ValidationError):
            build_settings(environment="production", secret_key=weak_key)

    def test_production_rejects_default_secret_key_when_not_provided(self):
        """Even the implicit default is rejected in production."""
        with pytest.raises(ValidationError):
            build_settings(environment="production")

    def test_production_accepts_strong_secret_key(self):
        """A strong, explicitly provided key boots a production instance."""
        settings = build_settings(environment="production", secret_key=STRONG_SECRET_KEY)

        assert settings.environment == "production"
        assert settings.secret_key.get_secret_value() == STRONG_SECRET_KEY

    def test_production_accepts_strong_secret_key_from_env(self, monkeypatch):
        """SECRET_KEY coming from the environment is validated the same way."""
        monkeypatch.setenv("SECRET_KEY", STRONG_SECRET_KEY)

        settings = build_settings(environment="production")

        assert settings.secret_key.get_secret_value() == STRONG_SECRET_KEY

    def test_development_accepts_default_secret_key(self):
        """The default development key is still valid outside production."""
        settings = build_settings(environment="development")

        assert settings.environment == "development"
        assert settings.secret_key.get_secret_value() == DEFAULT_DEV_SECRET_KEY

    def test_short_secret_key_is_rejected_in_every_environment(self):
        """The minimum length constraint is enforced regardless of environment."""
        with pytest.raises(ValidationError):
            build_settings(environment="development", secret_key="too-short")


@pytest.mark.unit
class TestSecretKeyIsNotLeaked:
    """The secret key must never show up in a printed settings object."""

    def test_repr_masks_secret_key(self):
        settings = build_settings(environment="development", secret_key=STRONG_SECRET_KEY)

        assert STRONG_SECRET_KEY not in repr(settings)
        assert STRONG_SECRET_KEY not in str(settings)

    def test_str_masks_secret_key(self):
        settings = build_settings(environment="production", secret_key=STRONG_SECRET_KEY)

        rendered = str(settings)

        assert STRONG_SECRET_KEY not in rendered
        assert "**********" in rendered

    def test_secret_value_is_still_readable_explicitly(self):
        """Masking must not break legitimate consumers."""
        settings = build_settings(environment="development", secret_key=STRONG_SECRET_KEY)

        assert settings.secret_key.get_secret_value() == STRONG_SECRET_KEY
