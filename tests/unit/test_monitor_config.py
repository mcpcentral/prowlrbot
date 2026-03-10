# -*- coding: utf-8 -*-
"""Tests for prowlrbot.monitor.config."""
import pytest

from prowlrbot.monitor.config import (
    APIMonitorConfig,
    MonitorConfig,
    WebMonitorConfig,
    parse_interval,
    parse_monitor_configs,
)


class TestParseInterval:
    def test_seconds(self):
        assert parse_interval("30s") == 30

    def test_minutes(self):
        assert parse_interval("5m") == 300

    def test_hours(self):
        assert parse_interval("1h") == 3600

    def test_days(self):
        assert parse_interval("2d") == 172800

    def test_case_insensitive(self):
        assert parse_interval("5M") == 300

    def test_whitespace(self):
        assert parse_interval("  10s  ") == 10

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid interval"):
            parse_interval("abc")

    def test_no_unit(self):
        with pytest.raises(ValueError):
            parse_interval("100")

    def test_empty(self):
        with pytest.raises(ValueError):
            parse_interval("")


class TestMonitorConfig:
    def test_basic(self):
        config = MonitorConfig(name="test", interval="5m")
        assert config.interval_seconds == 300
        assert config.enabled is True

    def test_invalid_interval_rejected(self):
        with pytest.raises(ValueError):
            MonitorConfig(name="test", interval="bad")


class TestWebMonitorConfig:
    def test_web_monitor_config(self):
        config = WebMonitorConfig(
            name="test-monitor",
            url="https://example.com",
            interval="5m",
            css_selector="h1",
        )
        assert config.interval_seconds == 300
        assert config.type == "web"
        assert config.url == "https://example.com"
        assert config.css_selector == "h1"

    def test_defaults(self):
        config = WebMonitorConfig(name="x", url="https://example.com")
        assert config.interval == "5m"
        assert config.headers == {}
        assert config.css_selector is None


class TestAPIMonitorConfig:
    def test_api_config(self):
        config = APIMonitorConfig(
            name="api-check",
            url="https://api.example.com/status",
            interval="1h",
            method="POST",
            expected_status=201,
            json_path="data.status",
        )
        assert config.interval_seconds == 3600
        assert config.type == "api"
        assert config.method == "POST"

    def test_defaults(self):
        config = APIMonitorConfig(name="x", url="https://api.example.com")
        assert config.method == "GET"
        assert config.expected_status == 200


class TestParseMonitorConfigs:
    def test_parse_web(self):
        configs = parse_monitor_configs([
            {"name": "w", "type": "web", "url": "https://example.com"}
        ])
        assert len(configs) == 1
        assert isinstance(configs[0], WebMonitorConfig)

    def test_parse_api(self):
        configs = parse_monitor_configs([
            {"name": "a", "type": "api", "url": "https://api.example.com"}
        ])
        assert len(configs) == 1
        assert isinstance(configs[0], APIMonitorConfig)

    def test_default_type_is_web(self):
        configs = parse_monitor_configs([
            {"name": "d", "url": "https://example.com"}
        ])
        assert isinstance(configs[0], WebMonitorConfig)
