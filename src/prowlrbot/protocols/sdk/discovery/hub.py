# -*- coding: utf-8 -*-
"""Hub HTTP API client for federated agent discovery.

A Discovery Hub is a centralized (or federated) registry where agents
publish their cards and discover others. Multiple hubs can gossip
with each other for cross-network discovery.

The Hub API follows a simple REST pattern:
  - POST /agents      — Register an agent card
  - GET  /agents/:did — Look up by DID
  - GET  /agents?q=   — Search by capability
  - DELETE /agents/:did — Unregister
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...roar import AgentCard, AgentIdentity, DiscoveryEntry

logger = logging.getLogger(__name__)


@dataclass
class HubConfig:
    """Configuration for connecting to a Discovery Hub.

    Attributes:
        url: Base URL of the hub (e.g. "https://hub.example.com").
        api_key: Optional API key for authentication.
        timeout_ms: Request timeout in milliseconds.
    """

    url: str
    api_key: str = ""
    timeout_ms: int = 10000


class HubClient:
    """Client for interacting with a ROAR Discovery Hub.

    Usage::

        hub = HubClient(HubConfig(url="https://hub.example.com"))

        # Register
        await hub.register(my_card)

        # Discover
        agents = await hub.search("code-review")

        # Look up
        entry = await hub.lookup("did:roar:agent:planner-abc12345")
    """

    def __init__(self, config: HubConfig) -> None:
        self._config = config
        self._url = config.url.rstrip("/")

    async def register(self, card: AgentCard) -> Dict[str, Any]:
        """Register an agent card with the hub.

        Args:
            card: The agent card to register.

        Returns:
            The hub's response dict.

        Raises:
            ConnectionError: If the hub is unreachable.
        """
        import httpx

        headers = self._headers()
        payload = {
            "did": card.identity.did,
            "display_name": card.identity.display_name,
            "agent_type": card.identity.agent_type,
            "description": card.description,
            "skills": card.skills,
            "channels": card.channels,
            "endpoints": card.endpoints,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self._config.timeout_ms / 1000
            ) as client:
                resp = await client.post(
                    f"{self._url}/agents",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            raise ConnectionError(f"Hub register failed: {exc}") from exc

    async def lookup(self, did: str) -> Optional[DiscoveryEntry]:
        """Look up an agent by DID.

        Args:
            did: The agent's DID.

        Returns:
            A DiscoveryEntry if found, None otherwise.
        """
        import httpx

        try:
            async with httpx.AsyncClient(
                timeout=self._config.timeout_ms / 1000
            ) as client:
                resp = await client.get(
                    f"{self._url}/agents/{did}",
                    headers=self._headers(),
                )
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                data = resp.json()
                return self._parse_entry(data)
        except ConnectionError:
            raise
        except Exception as exc:
            logger.warning("Hub lookup failed for %s: %s", did, exc)
            return None

    async def search(self, query: str) -> List[DiscoveryEntry]:
        """Search for agents by capability or keyword.

        Args:
            query: Search query string.

        Returns:
            List of matching discovery entries.
        """
        import httpx

        try:
            async with httpx.AsyncClient(
                timeout=self._config.timeout_ms / 1000
            ) as client:
                resp = await client.get(
                    f"{self._url}/agents",
                    params={"q": query},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                return [
                    self._parse_entry(item)
                    for item in data.get("agents", [])
                    if item
                ]
        except Exception as exc:
            logger.warning("Hub search failed for '%s': %s", query, exc)
            return []

    async def unregister(self, did: str) -> bool:
        """Remove an agent from the hub.

        Args:
            did: The agent's DID.

        Returns:
            True if successfully removed.
        """
        import httpx

        try:
            async with httpx.AsyncClient(
                timeout=self._config.timeout_ms / 1000
            ) as client:
                resp = await client.delete(
                    f"{self._url}/agents/{did}",
                    headers=self._headers(),
                )
                return resp.status_code in (200, 204)
        except Exception:
            return False

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        return headers

    @staticmethod
    def _parse_entry(data: Dict[str, Any]) -> DiscoveryEntry:
        """Parse a hub response into a DiscoveryEntry."""
        identity = AgentIdentity(
            did=data.get("did", ""),
            display_name=data.get("display_name", ""),
            agent_type=data.get("agent_type", "agent"),
        )
        card = AgentCard(
            identity=identity,
            description=data.get("description", ""),
            skills=data.get("skills", []),
            channels=data.get("channels", []),
            endpoints=data.get("endpoints", {}),
        )
        return DiscoveryEntry(agent_card=card)
