"""Unit tests for password hashing, JWT tokens, and config validation."""

from jose import jwt

import config
from auth.security import hash_password, verify_password, create_access_token


def test_password_hash_and_verify():
    hashed = hash_password("password123")
    # The hash must not equal the raw password.
    assert hashed != "password123"
    # Correct password verifies, wrong one does not.
    assert verify_password("password123", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token_roundtrip():
    token = create_access_token(42)
    payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    assert payload["sub"] == "42"
    assert "exp" in payload


def test_config_validate_flags_insecure_production(monkeypatch):
    monkeypatch.setattr(config, "ENVIRONMENT", "production")
    monkeypatch.setattr(config, "GOOGLE_API_KEY", None)
    monkeypatch.setattr(config, "JWT_SECRET", config._DEV_JWT_SECRET)

    errors, warnings = config.validate()

    assert any("GOOGLE_API_KEY" in e for e in errors)
    assert any("JWT_SECRET" in e for e in errors)
