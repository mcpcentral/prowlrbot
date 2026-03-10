# -*- coding: utf-8 -*-
"""Tests for file I/O path restrictions."""

from pathlib import Path
from unittest.mock import patch

from prowlrbot.agents.tools.file_io import validate_file_path


def test_allows_working_dir_path(tmp_path):
    with patch("prowlrbot.agents.tools.file_io.WORKING_DIR", tmp_path):
        assert validate_file_path(str(tmp_path / "test.txt")) is True


def test_blocks_etc_passwd():
    assert validate_file_path("/etc/passwd") is False


def test_blocks_ssh_keys():
    assert validate_file_path(str(Path.home() / ".ssh" / "id_rsa")) is False


def test_blocks_secret_dir():
    assert validate_file_path(str(Path.home() / ".prowlrbot.secret" / "envs.json")) is False


def test_blocks_path_traversal(tmp_path):
    with patch("prowlrbot.agents.tools.file_io.WORKING_DIR", tmp_path):
        assert validate_file_path(str(tmp_path / ".." / ".." / "etc" / "passwd")) is False


def test_allows_tmp_path():
    assert validate_file_path("/tmp/prowlrbot_output.txt") is True


def test_blocks_dev_null():
    assert validate_file_path("/dev/sda") is False
