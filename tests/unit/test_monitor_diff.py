# -*- coding: utf-8 -*-
"""Tests for prowlrbot.monitor.diff."""
from prowlrbot.monitor.diff import diff_text, has_changed


class TestHasChanged:
    def test_none_old_is_changed(self):
        assert has_changed(None, "new content") is True

    def test_same_content(self):
        assert has_changed("hello", "hello") is False

    def test_different_content(self):
        assert has_changed("hello", "world") is True

    def test_none_old_none_new(self):
        assert has_changed(None, None) is True

    def test_empty_to_content(self):
        assert has_changed("", "something") is True

    def test_content_to_empty(self):
        assert has_changed("something", "") is True


class TestDiffText:
    def test_first_run(self):
        result = diff_text(None, "new content")
        assert result.changed is True
        assert result.summary == "Initial content captured"
        assert result.unified_diff == ""

    def test_no_change(self):
        result = diff_text("same", "same")
        assert result.changed is False
        assert result.summary == "No changes"

    def test_change_detected(self):
        result = diff_text("line1\nline2\n", "line1\nline3\n")
        assert result.changed is True
        assert "added" in result.summary
        assert "removed" in result.summary
        assert result.unified_diff != ""

    def test_addition_only(self):
        result = diff_text("line1\n", "line1\nline2\n")
        assert result.changed is True
        assert "1 line(s) added" in result.summary

    def test_removal_only(self):
        result = diff_text("line1\nline2\n", "line1\n")
        assert result.changed is True
        assert "1 line(s) removed" in result.summary
