"""Tests for registry sync trust tier assignment."""
from prowlrbot.marketplace.registry import CATEGORY_DIR_MAP


def test_specs_in_category_dir_map():
    """specs directory should be mapped."""
    assert "specs" in CATEGORY_DIR_MAP
    assert CATEGORY_DIR_MAP["specs"] == "specs"


def test_all_categories_mapped():
    expected = {"skills", "agents", "prompts", "mcp-servers", "themes", "workflows", "specs", "consumer"}
    assert set(CATEGORY_DIR_MAP.keys()) == expected
