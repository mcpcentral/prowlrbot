# -*- coding: utf-8 -*-
"""SQLite-backed autonomy controller.

Evaluates whether an agent action should be approved, escalated, or
blocked based on the agent's configured ``AutonomyPolicy``.
"""

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from prowlrbot.constant import WORKING_DIR

from .models import (
    ActionDecision,
    AutonomyLevel,
    AutonomyPolicy,
    EscalationEvent,
    EscalationReason,
)

logger = logging.getLogger(__name__)

AUTONOMY_DB_PATH = WORKING_DIR / "autonomy.db"


class AutonomyController:
    """Graduated autonomy controller backed by SQLite.

    Each request should create its own controller instance to avoid
    threading issues with SQLite.  WAL mode is enabled so readers do
    not block writers.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else AUTONOMY_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _create_tables(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS policies (
                agent_id                TEXT PRIMARY KEY,
                level                   TEXT NOT NULL DEFAULT 'watch',
                max_cost_per_action     REAL NOT NULL DEFAULT 0.10,
                max_actions_per_hour    INTEGER NOT NULL DEFAULT 10,
                allowed_tools           TEXT NOT NULL DEFAULT '[]',
                blocked_tools           TEXT NOT NULL DEFAULT '[]',
                require_approval_for    TEXT NOT NULL DEFAULT '[]',
                escalation_contacts     TEXT NOT NULL DEFAULT '[]',
                updated_at              REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS escalations (
                id          TEXT PRIMARY KEY,
                agent_id    TEXT NOT NULL,
                reason      TEXT NOT NULL,
                action      TEXT NOT NULL,
                context     TEXT NOT NULL DEFAULT '{}',
                resolved    INTEGER NOT NULL DEFAULT 0,
                created_at  REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_escalations_agent
                ON escalations (agent_id);
        """,
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()

    # ------------------------------------------------------------------
    # Policy CRUD
    # ------------------------------------------------------------------

    def set_policy(self, policy: AutonomyPolicy) -> AutonomyPolicy:
        """Create or update an autonomy policy for an agent."""
        policy.updated_at = time.time()
        self._conn.execute(
            """
            INSERT INTO policies (
                agent_id, level, max_cost_per_action, max_actions_per_hour,
                allowed_tools, blocked_tools, require_approval_for,
                escalation_contacts, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET
                level = excluded.level,
                max_cost_per_action = excluded.max_cost_per_action,
                max_actions_per_hour = excluded.max_actions_per_hour,
                allowed_tools = excluded.allowed_tools,
                blocked_tools = excluded.blocked_tools,
                require_approval_for = excluded.require_approval_for,
                escalation_contacts = excluded.escalation_contacts,
                updated_at = excluded.updated_at
            """,
            (
                policy.agent_id,
                policy.level.value,
                policy.max_cost_per_action,
                policy.max_actions_per_hour,
                json.dumps(policy.allowed_tools),
                json.dumps(policy.blocked_tools),
                json.dumps(policy.require_approval_for),
                json.dumps(policy.escalation_contacts),
                policy.updated_at,
            ),
        )
        self._conn.commit()
        logger.info(
            "Autonomy policy set for agent %s (level=%s)",
            policy.agent_id,
            policy.level,
        )
        return policy

    def get_policy(self, agent_id: str) -> Optional[AutonomyPolicy]:
        """Return the autonomy policy for *agent_id*, or ``None``."""
        row = self._conn.execute(
            "SELECT * FROM policies WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_policy(row)

    def list_policies(self) -> List[AutonomyPolicy]:
        """Return all stored autonomy policies."""
        rows = self._conn.execute(
            "SELECT * FROM policies ORDER BY agent_id",
        ).fetchall()
        return [self._row_to_policy(r) for r in rows]

    def delete_policy(self, agent_id: str) -> bool:
        """Delete the policy for *agent_id*.  Returns ``True`` if a row
        was actually removed."""
        cur = self._conn.execute(
            "DELETE FROM policies WHERE agent_id = ?",
            (agent_id,),
        )
        self._conn.commit()
        deleted = cur.rowcount > 0
        if deleted:
            logger.info("Autonomy policy deleted for agent %s", agent_id)
        return deleted

    # ------------------------------------------------------------------
    # Action evaluation
    # ------------------------------------------------------------------

    def evaluate_action(
        self,
        agent_id: str,
        action: str,
        tool_name: str,
        estimated_cost: float = 0.0,
    ) -> ActionDecision:
        """Decide whether *action* using *tool_name* should be approved.

        The decision depends on the agent's ``AutonomyLevel``:

        - **WATCH** -- always escalate; nothing is auto-approved.
        - **GUIDE** -- approve if the tool is known (not novel) and cost
          is within threshold; otherwise escalate.
        - **DELEGATE** -- approve unless the tool is blocked or cost /
          rate thresholds are exceeded.
        - **AUTONOMOUS** -- approve everything except explicitly blocked
          tools.

        Regardless of level, tools listed in ``blocked_tools`` are
        always denied and tools in ``require_approval_for`` always
        trigger escalation.
        """
        policy = self.get_policy(agent_id)
        if policy is None:
            # No policy means default WATCH behaviour.
            return self._escalate(
                action,
                "No autonomy policy configured for agent",
            )

        # --- universal blocks ---
        if tool_name in policy.blocked_tools:
            return ActionDecision(
                action=action,
                approved=False,
                reason=f"Tool '{tool_name}' is explicitly blocked",
                escalated=False,
            )

        # --- universal approval-required tools ---
        if tool_name in policy.require_approval_for:
            return self._escalate(
                action,
                f"Tool '{tool_name}' always requires approval",
            )

        # --- allowed_tools whitelist (empty = all allowed) ---
        if policy.allowed_tools and tool_name not in policy.allowed_tools:
            return self._escalate(
                action,
                f"Tool '{tool_name}' is not in the allowed tools list",
            )

        # --- per-level logic ---
        level = policy.level

        if level == AutonomyLevel.WATCH:
            return self._escalate(
                action,
                "WATCH mode: all actions require approval",
            )

        if level == AutonomyLevel.GUIDE:
            if estimated_cost > policy.max_cost_per_action:
                return self._escalate(
                    action,
                    f"Estimated cost ${estimated_cost:.2f} exceeds "
                    f"limit ${policy.max_cost_per_action:.2f}",
                )
            # In GUIDE mode, routine (known) tools are approved.
            return ActionDecision(
                action=action,
                approved=True,
                reason="GUIDE mode: routine tool approved",
                escalated=False,
            )

        if level == AutonomyLevel.DELEGATE:
            if estimated_cost > policy.max_cost_per_action:
                return self._escalate(
                    action,
                    f"Estimated cost ${estimated_cost:.2f} exceeds "
                    f"limit ${policy.max_cost_per_action:.2f}",
                )
            return ActionDecision(
                action=action,
                approved=True,
                reason="DELEGATE mode: action approved within thresholds",
                escalated=False,
            )

        # AUTONOMOUS
        return ActionDecision(
            action=action,
            approved=True,
            reason="AUTONOMOUS mode: action approved",
            escalated=False,
        )

    # ------------------------------------------------------------------
    # Escalation CRUD
    # ------------------------------------------------------------------

    def record_escalation(self, event: EscalationEvent) -> EscalationEvent:
        """Persist an escalation event."""
        self._conn.execute(
            """
            INSERT INTO escalations (id, agent_id, reason, action, context, resolved, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.agent_id,
                event.reason.value,
                event.action,
                json.dumps(event.context),
                int(event.resolved),
                event.created_at,
            ),
        )
        self._conn.commit()
        logger.info(
            "Escalation recorded: id=%s agent=%s reason=%s",
            event.id,
            event.agent_id,
            event.reason,
        )
        return event

    def list_escalations(
        self,
        agent_id: str,
        resolved: Optional[bool] = None,
    ) -> List[EscalationEvent]:
        """List escalation events for *agent_id*.

        If *resolved* is provided, filter by resolution status.
        """
        if resolved is None:
            rows = self._conn.execute(
                "SELECT * FROM escalations WHERE agent_id = ? ORDER BY created_at DESC",
                (agent_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM escalations WHERE agent_id = ? AND resolved = ? "
                "ORDER BY created_at DESC",
                (agent_id, int(resolved)),
            ).fetchall()
        return [self._row_to_escalation(r) for r in rows]

    def resolve_escalation(self, escalation_id: str) -> bool:
        """Mark an escalation as resolved.  Returns ``True`` if a row
        was actually updated."""
        cur = self._conn.execute(
            "UPDATE escalations SET resolved = 1 WHERE id = ? AND resolved = 0",
            (escalation_id,),
        )
        self._conn.commit()
        resolved = cur.rowcount > 0
        if resolved:
            logger.info("Escalation resolved: id=%s", escalation_id)
        return resolved

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _escalate(action: str, reason: str) -> ActionDecision:
        return ActionDecision(
            action=action,
            approved=False,
            reason=reason,
            escalated=True,
        )

    @staticmethod
    def _row_to_policy(row: sqlite3.Row) -> AutonomyPolicy:
        return AutonomyPolicy(
            agent_id=row["agent_id"],
            level=AutonomyLevel(row["level"]),
            max_cost_per_action=row["max_cost_per_action"],
            max_actions_per_hour=row["max_actions_per_hour"],
            allowed_tools=json.loads(row["allowed_tools"]),
            blocked_tools=json.loads(row["blocked_tools"]),
            require_approval_for=json.loads(row["require_approval_for"]),
            escalation_contacts=json.loads(row["escalation_contacts"]),
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_escalation(row: sqlite3.Row) -> EscalationEvent:
        return EscalationEvent(
            id=row["id"],
            agent_id=row["agent_id"],
            reason=EscalationReason(row["reason"]),
            action=row["action"],
            context=json.loads(row["context"]),
            resolved=bool(row["resolved"]),
            created_at=row["created_at"],
        )
