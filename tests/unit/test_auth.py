# -*- coding: utf-8 -*-
"""Tests for API authentication."""

import pytest

from prowlrbot.app.auth import (
    generate_api_token,
    verify_api_token,
    hash_token,
    AuthConfig,
)


def test_generate_api_token_returns_string():
    token = generate_api_token()
    assert isinstance(token, str)
    assert len(token) >= 32


def test_verify_valid_token():
    token = generate_api_token()
    hashed = hash_token(token)
    assert verify_api_token(token, hashed) is True


def test_verify_invalid_token():
    token = generate_api_token()
    hashed = hash_token(token)
    assert verify_api_token("wrong-token", hashed) is False


def test_verify_empty_token():
    assert verify_api_token("", hash_token("real")) is False


def test_auth_config_defaults():
    config = AuthConfig()
    assert config.enabled is True
    assert config.token_hash == ""


def test_auth_config_disabled_allows_all():
    config = AuthConfig(enabled=False)
    assert config.enabled is False
