# -*- coding: utf-8 -*-
"""Tests for provider detection fields on ProviderDefinition."""

from prowlrbot.providers.models import ProviderDefinition


def test_provider_definition_has_detection_fields():
    p = ProviderDefinition(
        id="test",
        name="Test Provider",
        default_base_url="https://api.test.com/v1",
        env_var="TEST_API_KEY",
        api_key_prefix="sk-",
        is_local=False,
        url_based_detection=False,
        cost_tier="standard",
        health_check_endpoint="/v1/models",
    )
    assert p.env_var == "TEST_API_KEY"
    assert p.cost_tier == "standard"
    assert p.url_based_detection is False
    assert p.health_check_endpoint == "/v1/models"


def test_provider_definition_detection_defaults():
    """Detection fields should have sensible defaults for backward compat."""
    p = ProviderDefinition(id="minimal", name="Minimal")
    assert p.env_var == ""
    assert p.url_based_detection is False
    assert p.cost_tier == "standard"
    assert p.health_check_endpoint == ""
