# -*- coding: utf-8 -*-
"""Tests for environment variable masking."""

from prowlrbot.app.routers.envs import mask_env_value


def test_mask_short_value():
    assert mask_env_value("abc") == "***"


def test_mask_long_value():
    result = mask_env_value("sk-ant-api03-abcdef123456")
    assert result.startswith("sk-a")
    assert result.endswith("***")
    assert "abcdef" not in result


def test_mask_empty_value():
    assert mask_env_value("") == ""


def test_mask_medium_value():
    result = mask_env_value("12345678")
    assert result.startswith("1234")
    assert result.endswith("***")
