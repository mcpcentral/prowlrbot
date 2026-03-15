# -*- coding: utf-8 -*-
"""JSON file-based storage for webhook rules.

Single-machine, no cross-process lock. Atomic write via tmp-then-replace.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import WebhookFile, WebhookRule

logger = logging.getLogger(__name__)

_FILENAME = "webhooks.json"


class WebhookStore:
    """CRUD operations for webhook rules stored in a JSON file."""

    def __init__(self, base_dir: Path) -> None:
        self._path = base_dir.expanduser().resolve() / _FILENAME

    @property
    def path(self) -> Path:
        return self._path

    # ------------------------------------------------------------------
    # Low-level I/O
    # ------------------------------------------------------------------

    async def _load(self) -> WebhookFile:
        if not self._path.exists():
            return WebhookFile(version=1, rules=[])
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return WebhookFile.model_validate(data)

    async def _save(self, wf: WebhookFile) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        payload = wf.model_dump(mode="json")
        tmp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(self._path)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def list_rules(self) -> list[WebhookRule]:
        """Return all webhook rules."""
        wf = await self._load()
        return wf.rules

    async def get_rule(self, rule_id: str) -> Optional[WebhookRule]:
        """Return a single rule by id, or None."""
        wf = await self._load()
        for rule in wf.rules:
            if rule.id == rule_id:
                return rule
        return None

    async def create_rule(self, rule: WebhookRule) -> WebhookRule:
        """Append a new rule. The caller must set ``rule.id``."""
        wf = await self._load()
        # Guard against duplicate ids.
        existing_ids = {r.id for r in wf.rules}
        if rule.id in existing_ids:
            raise ValueError(f"rule id already exists: {rule.id}")
        wf.rules.append(rule)
        await self._save(wf)
        logger.info("webhook rule created: %s (%s)", rule.id, rule.name)
        return rule

    async def update_rule(self, rule: WebhookRule) -> Optional[WebhookRule]:
        """Replace a rule by id. Returns updated rule or None if not found."""
        wf = await self._load()
        for idx, existing in enumerate(wf.rules):
            if existing.id == rule.id:
                rule = rule.model_copy(
                    update={"updated_at": datetime.now(timezone.utc)},
                )
                wf.rules[idx] = rule
                await self._save(wf)
                logger.info(
                    "webhook rule updated: %s (%s)",
                    rule.id,
                    rule.name,
                )
                return rule
        return None

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule by id. Returns True if found and deleted."""
        wf = await self._load()
        before = len(wf.rules)
        wf.rules = [r for r in wf.rules if r.id != rule_id]
        if len(wf.rules) == before:
            return False
        await self._save(wf)
        logger.info("webhook rule deleted: %s", rule_id)
        return True

    async def toggle_enabled(
        self,
        rule_id: str,
        enabled: bool,
    ) -> Optional[WebhookRule]:
        """Toggle the enabled flag on a rule. Returns updated rule or None."""
        wf = await self._load()
        for idx, existing in enumerate(wf.rules):
            if existing.id == rule_id:
                wf.rules[idx] = existing.model_copy(
                    update={
                        "enabled": enabled,
                        "updated_at": datetime.now(timezone.utc),
                    },
                )
                await self._save(wf)
                logger.info(
                    "webhook rule %s: %s",
                    "enabled" if enabled else "disabled",
                    rule_id,
                )
                return wf.rules[idx]
        return None

    async def record_trigger(self, rule_id: str) -> None:
        """Bump trigger_count and set last_triggered_at for a rule."""
        wf = await self._load()
        for idx, existing in enumerate(wf.rules):
            if existing.id == rule_id:
                wf.rules[idx] = existing.model_copy(
                    update={
                        "last_triggered_at": datetime.now(timezone.utc),
                        "trigger_count": existing.trigger_count + 1,
                    },
                )
                await self._save(wf)
                return
