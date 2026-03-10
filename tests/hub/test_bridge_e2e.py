# -*- coding: utf-8 -*-
"""End-to-end tests for ProwlrHub HTTP bridge + remote client."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestBridgeE2E(unittest.TestCase):
    """Test the HTTP bridge with the remote client."""

    PORT = 18099

    @classmethod
    def setUpClass(cls):
        """Start bridge server as a subprocess."""
        cls._tmpdir = tempfile.mkdtemp()
        cls._db_path = os.path.join(cls._tmpdir, "test_bridge.db")

        env = os.environ.copy()
        env["PROWLR_HUB_DB"] = cls._db_path
        env["PROWLR_BRIDGE_HOST"] = "127.0.0.1"
        env["PROWLR_BRIDGE_PORT"] = str(cls.PORT)
        env["PYTHONPATH"] = os.path.join(os.path.dirname(__file__), "..", "..", "src")

        cls._proc = subprocess.Popen(
            [sys.executable, "-m", "prowlrbot.hub.bridge"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        from prowlrbot.hub.remote_client import RemoteWarRoom
        cls._client = RemoteWarRoom(f"http://127.0.0.1:{cls.PORT}")

        for _ in range(40):
            try:
                health = cls._client.health()
                if health.get("status") == "ok":
                    break
            except Exception:
                pass
            time.sleep(0.25)
        else:
            cls._proc.kill()
            out, err = cls._proc.communicate(timeout=3)
            raise RuntimeError(
                f"Bridge server did not start.\nstdout: {out.decode()[:500]}\nstderr: {err.decode()[:500]}"
            )

    @classmethod
    def tearDownClass(cls):
        cls._proc.kill()
        cls._proc.wait(timeout=3)
        import shutil
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_01_health(self):
        result = self._client.health()
        assert result["status"] == "ok"

    def test_02_register(self):
        result = self._client.register("test-agent-1", ["code", "review"])
        assert "agent_id" in result
        assert self._client.agent_id is not None

    def test_03_get_agents(self):
        agents = self._client.get_agents()
        assert len(agents) >= 1
        names = [a["name"] for a in agents]
        assert "test-agent-1" in names

    def test_04_mission_board_empty(self):
        tasks = self._client.get_mission_board()
        assert isinstance(tasks, list)

    def test_05_claim_new_task(self):
        result = self._client.claim_task(
            title="Test task from bridge",
            file_scopes=["src/test.py"],
            description="Testing bridge E2E",
            priority="normal",
        )
        assert result.get("success") is True
        assert "lock_token" in result

    def test_06_check_mission_board_has_task(self):
        tasks = self._client.get_mission_board()
        titles = [t.get("title") for t in tasks]
        assert "Test task from bridge" in titles

    def test_07_share_finding(self):
        self._client.share_finding("bridge-test", "Bridge E2E works")

    def test_08_get_shared_context(self):
        ctx = self._client.get_shared_context("bridge-test")
        assert len(ctx) >= 1
        assert ctx[0]["value"] == "Bridge E2E works"

    def test_09_broadcast(self):
        self._client.broadcast_status("Testing bridge connectivity")

    def test_10_get_events(self):
        events = self._client.get_events(limit=5)
        assert isinstance(events, list)
        assert len(events) >= 1

    def test_11_check_conflicts(self):
        conflicts = self._client.check_conflicts(["src/test.py"])
        assert isinstance(conflicts, list)
        assert len(conflicts) >= 1

    def test_12_lock_unlock(self):
        result = self._client.lock_file("src/extra.py")
        assert result.get("success") is True

        result = self._client.unlock_file("src/extra.py")
        assert result.get("ok") is True


if __name__ == "__main__":
    unittest.main()
