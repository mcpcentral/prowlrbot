# -*- coding: utf-8 -*-
"""Tests for monitor alert routing to channels."""

from __future__ import annotations

import pytest

from prowlrbot.monitor.alert_router import AlertRouter


class TestAlertRouterBasicRouting:
    def test_route_critical_to_multiple_channels(self):
        router = AlertRouter(
            rules={
                "critical": ["discord", "telegram"],
                "warning": ["discord"],
                "info": [],
            },
        )
        channels = router.route("critical", "Site down: example.com")
        assert "discord" in channels
        assert "telegram" in channels

    def test_route_warning_to_single_channel(self):
        router = AlertRouter(
            rules={
                "critical": ["discord", "telegram"],
                "warning": ["discord"],
                "info": [],
            },
        )
        channels = router.route("warning", "Content changed on example.com")
        assert channels == ["discord"]

    def test_route_info_to_no_channels(self):
        router = AlertRouter(
            rules={
                "critical": ["discord", "telegram"],
                "warning": ["discord"],
                "info": [],
            },
        )
        channels = router.route("info", "Check completed successfully")
        assert channels == []

    def test_route_unknown_severity_returns_empty(self):
        router = AlertRouter(rules={"critical": ["discord"]})
        channels = router.route("debug", "Some debug message")
        assert channels == []

    def test_default_rules_route_to_console(self):
        router = AlertRouter()
        for severity in ("critical", "warning", "info"):
            channels = router.route(severity, "Test message")
            assert channels == ["console"]


class TestAlertRouterQuietHours:
    def test_quiet_hours_suppresses_non_critical(self):
        router = AlertRouter(
            rules={"warning": ["discord"], "critical": ["discord"]},
            quiet_hours=(22, 7),
        )
        # Hour 2 is within quiet hours (22:00 - 06:59)
        channels = router.route("warning", "Minor change", force_hour=2)
        assert channels == []

    def test_quiet_hours_allows_critical(self):
        router = AlertRouter(
            rules={"warning": ["discord"], "critical": ["discord"]},
            quiet_hours=(22, 7),
        )
        channels = router.route("critical", "Site down", force_hour=2)
        assert "discord" in channels

    def test_quiet_hours_outside_window_allows_all(self):
        router = AlertRouter(
            rules={"warning": ["discord"], "critical": ["discord"]},
            quiet_hours=(22, 7),
        )
        # Hour 12 is outside quiet hours
        channels = router.route("warning", "Content changed", force_hour=12)
        assert channels == ["discord"]

    def test_quiet_hours_at_boundary_start(self):
        router = AlertRouter(
            rules={"warning": ["discord"]},
            quiet_hours=(22, 7),
        )
        # Hour 22 is the start of quiet hours
        channels = router.route("warning", "Change", force_hour=22)
        assert channels == []

    def test_quiet_hours_at_boundary_end(self):
        router = AlertRouter(
            rules={"warning": ["discord"]},
            quiet_hours=(22, 7),
        )
        # Hour 7 is NOT in quiet hours (end is exclusive)
        channels = router.route("warning", "Change", force_hour=7)
        assert channels == ["discord"]

    def test_quiet_hours_non_wrapping(self):
        """Test quiet hours that don't wrap midnight (e.g. 9am to 5pm)."""
        router = AlertRouter(
            rules={"warning": ["discord"]},
            quiet_hours=(9, 17),
        )
        # Hour 12 is within 9-17
        channels = router.route("warning", "Change", force_hour=12)
        assert channels == []
        # Hour 20 is outside
        channels = router.route("warning", "Change", force_hour=20)
        assert channels == ["discord"]

    def test_no_quiet_hours_allows_all(self):
        router = AlertRouter(
            rules={"warning": ["discord"]},
            quiet_hours=None,
        )
        channels = router.route("warning", "Change", force_hour=3)
        assert channels == ["discord"]


class TestAlertRouterMutation:
    def test_update_rules(self):
        router = AlertRouter(rules={"critical": ["discord"]})
        router.update_rules({"critical": ["telegram", "slack"]})
        channels = router.route("critical", "Test")
        assert set(channels) == {"telegram", "slack"}

    def test_set_quiet_hours(self):
        router = AlertRouter(rules={"warning": ["discord"]})
        assert router.quiet_hours is None

        router.set_quiet_hours((23, 6))
        assert router.quiet_hours == (23, 6)
        channels = router.route("warning", "Change", force_hour=1)
        assert channels == []

    def test_rules_property_returns_copy(self):
        router = AlertRouter(rules={"critical": ["discord"]})
        rules_copy = router.rules
        rules_copy["critical"].append("telegram")
        # Original should not be modified
        assert router.route("critical", "Test") == ["discord"]
