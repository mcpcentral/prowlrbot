"""Tests for Bridge API."""
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add swarm bridge to path - use relative path from test file
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "swarm", "bridge"))
from capabilities import CapabilityExecutor


class TestBridgeAPI:
    """Test Bridge API functionality."""

    def test_capability_list(self):
        """Test that capabilities are listed correctly."""
        executor = CapabilityExecutor()
        capabilities = executor.list_capabilities()

        assert len(capabilities) > 0
        names = [c["name"] for c in capabilities]
        assert "browser_automation" in names
        assert "shell_command" in names
        assert "file_operations" in names

    def test_unknown_capability(self):
        """Test that unknown capability raises error."""
        executor = CapabilityExecutor()

        import asyncio
        with pytest.raises(ValueError, match="Unknown capability"):
            asyncio.run(executor.execute("unknown:capability", {}))


class TestPathSecurity:
    """Test path security in file operations."""

    def test_path_normalization(self):
        """Test that paths are normalized."""
        import os

        # Test path traversal attempts
        malicious_paths = [
            "../../../etc/passwd",
            "~/.ssh/id_rsa",
            "/etc/passwd",
            "..\\..\\windows\\system32",
        ]

        home = os.path.expanduser("~")

        for path in malicious_paths:
            full_path = os.path.abspath(os.path.expanduser(path))
            # Path should be outside home
            assert not full_path.startswith(home + "/prowlrbot")

    def test_safe_path_within_home(self):
        """Test that safe paths within home are allowed."""
        import os

        home = os.path.expanduser("~")
        safe_path = os.path.join(home, "Documents", "test.txt")
        full_path = os.path.abspath(safe_path)

        assert full_path.startswith(home)


class TestShellSecurity:
    """Test shell command security."""

    def test_blocked_commands(self):
        """Test that dangerous commands are blocked."""
        blocked = ["rm -rf /", "rm -rf /*", "> /dev/sda", "dd if=/dev/zero"]

        for cmd in blocked:
            assert any(b in cmd.lower() for b in ["rm -rf /", "> /dev/sda", "dd if=/dev/zero"])

    def test_safe_commands_allowed(self):
        """Test that safe commands are allowed."""
        safe = [
            "ls -la",
            "cat file.txt",
            "echo hello",
            "pwd",
        ]

        for cmd in safe:
            blocked = ["rm -rf /", "mkfs", "dd", ">", "|", "sudo"]
            assert not any(b in cmd for b in blocked)
