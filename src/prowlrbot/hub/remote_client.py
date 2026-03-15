# -*- coding: utf-8 -*-
"""ProwlrHub Remote Client — connects to the HTTP bridge from another machine.

When PROWLR_HUB_URL is set, the MCP server uses this client instead of
direct SQLite access. This enables WSL ↔ Mac war room coordination.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RemoteWarRoom:
    """HTTP client for the ProwlrHub bridge.

    Drop-in replacement for direct engine calls when running on a remote machine.
    Uses only stdlib (urllib) — no external dependencies needed.
    Sends Bearer auth token (PROWLR_HUB_SECRET) and X-Session-Token for
    agent identity verification.
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._agent_id: Optional[str] = None
        self._session_id: Optional[str] = None
        self._auth_token: Optional[str] = (
            os.environ.get("PROWLR_HUB_SECRET", "") or None
        )

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
    ) -> Dict:
        """Make an HTTP request to the bridge."""
        url = f"{self._base_url}{path}"
        body = json.dumps(data).encode() if data else None
        headers: Dict[str, str] = {}
        if body:
            headers["Content-Type"] = "application/json"
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Token"] = self._session_id
        req = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.URLError as e:
            logger.error("Bridge request failed: %s %s — %s", method, url, e)
            return {"error": str(e)}

    def _get(self, path: str) -> Dict:
        return self._request("GET", path)

    def _post(self, path: str, data: Dict) -> Dict:
        return self._request("POST", path, data)

    # --- Agent lifecycle ---

    def register(self, name: str, capabilities: List[str]) -> Dict:
        result = self._post(
            "/register",
            {"name": name, "capabilities": capabilities},
        )
        if "agent_id" in result:
            self._agent_id = result["agent_id"]
        if "session_id" in result:
            self._session_id = result["session_id"]
        return result

    def heartbeat(self) -> None:
        if self._agent_id:
            self._post(f"/heartbeat/{self._agent_id}", {})

    @property
    def agent_id(self) -> Optional[str]:
        return self._agent_id

    # --- Mission board ---

    def get_mission_board(self, status: str = "") -> List[Dict]:
        params = f"?status={status}" if status else ""
        result = self._get(f"/board{params}")
        return result.get("tasks", [])

    def claim_task(
        self,
        title: str = "",
        task_id: str = "",
        file_scopes: List[str] = None,
        description: str = "",
        priority: str = "normal",
    ) -> Dict:
        return self._post(
            f"/claim/{self._agent_id}",
            {
                "title": title,
                "task_id": task_id,
                "file_scopes": file_scopes or [],
                "description": description,
                "priority": priority,
            },
        )

    def update_task(self, task_id: str, progress_note: str) -> Dict:
        return self._post(
            f"/update/{self._agent_id}",
            {
                "task_id": task_id,
                "progress_note": progress_note,
            },
        )

    def complete_task(self, task_id: str, summary: str = "") -> Dict:
        return self._post(
            f"/complete/{self._agent_id}",
            {
                "task_id": task_id,
                "summary": summary,
            },
        )

    def fail_task(self, task_id: str, reason: str = "") -> Dict:
        return self._post(
            f"/fail/{self._agent_id}",
            {
                "task_id": task_id,
                "reason": reason,
            },
        )

    # --- File locking ---

    def lock_file(self, path: str) -> Dict:
        return self._post(f"/lock/{self._agent_id}", {"path": path})

    def unlock_file(self, path: str) -> Dict:
        return self._post(f"/unlock/{self._agent_id}", {"path": path})

    def check_conflicts(self, paths: List[str]) -> List[Dict]:
        result = self._post("/conflicts", {"paths": paths})
        return result.get("conflicts", [])

    # --- Agents & communication ---

    def get_agents(self) -> List[Dict]:
        result = self._get("/agents")
        return result.get("agents", [])

    def broadcast_status(self, message: str) -> None:
        self._post(f"/broadcast/{self._agent_id}", {"message": message})

    def share_finding(self, key: str, value: str) -> None:
        self._post(f"/findings/{self._agent_id}", {"key": key, "value": value})

    def get_shared_context(self, key: str = "") -> List[Dict]:
        params = f"?key={key}" if key else ""
        result = self._get(f"/context{params}")
        return result.get("context", [])

    def get_events(self, limit: int = 20, event_type: str = "") -> List[Dict]:
        params = f"?limit={limit}"
        if event_type:
            params += f"&event_type={event_type}"
        result = self._get(f"/events{params}")
        return result.get("events", [])

    # --- Health ---

    def health(self) -> Dict:
        return self._get("/health")
