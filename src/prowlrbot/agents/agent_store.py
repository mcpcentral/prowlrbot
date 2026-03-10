# -*- coding: utf-8 -*-
"""Persistent storage for agent configurations."""

import json
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

from prowlrbot.agents.agent_config import AgentConfig


class AgentStore:
    """File-based agent configuration store."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _agent_path(self, agent_id: str) -> Path:
        # Sanitize ID to prevent path traversal
        safe_id = "".join(c for c in agent_id if c.isalnum() or c in "-_")
        return self.base_dir / f"{safe_id}.json"

    def create(self, config: AgentConfig) -> str:
        """Create a new agent and return its ID."""
        agent_id = str(uuid.uuid4())[:8]
        path = self._agent_path(agent_id)
        path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
        return agent_id

    def get(self, agent_id: str) -> Optional[AgentConfig]:
        """Get an agent config by ID."""
        path = self._agent_path(agent_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return AgentConfig(**data)
        except (json.JSONDecodeError, ValueError):
            return None

    def list(self) -> List[Tuple[str, AgentConfig]]:
        """List all agent configs."""
        agents = []
        for path in sorted(self.base_dir.glob("*.json")):
            agent_id = path.stem
            config = self.get(agent_id)
            if config:
                agents.append((agent_id, config))
        return agents

    def update(self, agent_id: str, config: AgentConfig) -> bool:
        """Update an existing agent config."""
        path = self._agent_path(agent_id)
        if not path.exists():
            return False
        path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
        return True

    def delete(self, agent_id: str) -> bool:
        """Delete an agent config."""
        path = self._agent_path(agent_id)
        if not path.exists():
            return False
        path.unlink()
        return True
