# -*- coding: utf-8 -*-
"""Tests for ProviderDetector — env var scanning."""

import os
from unittest.mock import patch

from prowlrbot.providers.detector import ProviderDetector
from prowlrbot.providers.models import ProviderDefinition


# Test fixtures: fake provider definitions with env_var set
_FAKE_ANTHROPIC = ProviderDefinition(
    id="anthropic",
    name="Anthropic",
    default_base_url="https://api.anthropic.com/v1",
    env_var="ANTHROPIC_API_KEY",
    api_key_prefix="sk-ant-",
    cost_tier="premium",
    health_check_endpoint="/v1/models",
)

_FAKE_OPENAI = ProviderDefinition(
    id="openai",
    name="OpenAI",
    default_base_url="https://api.openai.com/v1",
    env_var="OPENAI_API_KEY",
    api_key_prefix="sk-",
    cost_tier="premium",
    health_check_endpoint="/v1/models",
)

_FAKE_GROQ = ProviderDefinition(
    id="groq",
    name="Groq",
    default_base_url="https://api.groq.com/openai/v1",
    env_var="GROQ_API_KEY",
    api_key_prefix="gsk_",
    cost_tier="low",
    health_check_endpoint="/openai/v1/models",
)

_FAKE_OLLAMA = ProviderDefinition(
    id="ollama",
    name="Ollama",
    default_base_url="http://localhost:11434/v1",
    env_var="",
    url_based_detection=True,
    is_local=True,
    cost_tier="free",
)

_TEST_PROVIDERS = [_FAKE_ANTHROPIC, _FAKE_OPENAI, _FAKE_GROQ, _FAKE_OLLAMA]


def test_detects_provider_by_env_var():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"}, clear=False):
        detector = ProviderDetector(providers=_TEST_PROVIDERS)
        detected = detector.scan_env_vars()
        ids = [p.id for p in detected]
        assert "anthropic" in ids
        assert "openai" not in ids  # not set


def test_detects_multiple_providers():
    env = {
        "ANTHROPIC_API_KEY": "sk-ant-test",
        "GROQ_API_KEY": "gsk_testkey",
    }
    with patch.dict(os.environ, env, clear=False):
        detector = ProviderDetector(providers=_TEST_PROVIDERS)
        detected = detector.scan_env_vars()
        ids = [p.id for p in detected]
        assert "anthropic" in ids
        assert "groq" in ids


def test_no_providers_when_no_env_vars():
    with patch.dict(os.environ, {}, clear=True):
        detector = ProviderDetector(providers=_TEST_PROVIDERS)
        detected = detector.scan_env_vars()
        # Should not include cloud providers
        cloud = [p for p in detected if not p.is_local]
        assert len(cloud) == 0


def test_skips_url_based_local_providers():
    """Ollama (url_based_detection=True, is_local=True) should not appear in env scan."""
    with patch.dict(os.environ, {}, clear=True):
        detector = ProviderDetector(providers=_TEST_PROVIDERS)
        detected = detector.scan_env_vars()
        ids = [p.id for p in detected]
        assert "ollama" not in ids


def test_skips_providers_without_env_var():
    """Providers with empty env_var are skipped."""
    no_env = ProviderDefinition(id="noenv", name="No Env", env_var="")
    detector = ProviderDetector(providers=[no_env])
    with patch.dict(os.environ, {}, clear=True):
        detected = detector.scan_env_vars()
        assert len(detected) == 0
