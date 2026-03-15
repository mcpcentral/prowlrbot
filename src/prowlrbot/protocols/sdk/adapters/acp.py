# -*- coding: utf-8 -*-
"""ACP Adapter — translate between ACP (IBM/BeeAI Agent Communication Protocol) and ROAR.

ACP is a session-based HTTP protocol for IDE-to-agent communication.
It defines sessions, messages, and responses but has no identity, signing,
or federation layer. ROAR provides all three.

Mapping:
  ACP session start   → ROARMessage(intent=NOTIFY, payload={"event": "session.start"})
  ACP message (user)  → ROARMessage(intent=ASK)
  ACP message (agent) → ROARMessage(intent=RESPOND)
  ACP session end     → ROARMessage(intent=NOTIFY, payload={"event": "session.end"})

Ref: https://agentcommunicationprotocol.dev/
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from ...roar import AgentIdentity, MessageIntent, ROARMessage


class ACPAdapter:
    """Translate between ACP sessions/messages and ROAR messages."""

    # ── ACP → ROAR ──────────────────────────────────────────────────────────

    @staticmethod
    def acp_message_to_roar(
        acp_message: Dict[str, Any],
        from_agent: AgentIdentity,
        to_agent: AgentIdentity,
        session_id: str = "",
    ) -> ROARMessage:
        """Translate an ACP message dict to a ROARMessage.

        ACP message format::

            {"role": "user" | "assistant", "content": str | list, "attachments": [...]}

        Intent is derived from role:
          "user" → ASK (user is requesting something from the agent)
          "assistant" → RESPOND (agent is replying)
        """
        role = acp_message.get("role", "user")
        content = acp_message.get("content", "")
        attachments = acp_message.get("attachments", [])

        intent = MessageIntent.ASK if role == "user" else MessageIntent.RESPOND

        payload: Dict[str, Any] = {"content": content}
        if attachments:
            payload["attachments"] = attachments

        context: Dict[str, Any] = {"protocol": "acp"}
        if session_id:
            context["session_id"] = session_id

        return ROARMessage(
            **{"from": from_agent, "to": to_agent},
            intent=intent,
            payload=payload,
            context=context,
        )

    @staticmethod
    def acp_session_event_to_roar(
        event: str,  # "start" | "end"
        from_agent: AgentIdentity,
        to_agent: AgentIdentity,
        session_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ROARMessage:
        """Translate an ACP session lifecycle event (start/end) to a ROARMessage."""
        return ROARMessage(
            **{"from": from_agent, "to": to_agent},
            intent=MessageIntent.NOTIFY,
            payload={"event": f"session.{event}", **(metadata or {})},
            context={"protocol": "acp", "session_id": session_id},
        )

    # ── ROAR → ACP ──────────────────────────────────────────────────────────

    @staticmethod
    def roar_to_acp_message(msg: ROARMessage) -> Dict[str, Any]:
        """Translate a ROARMessage to an ACP message dict.

        Maps intent to ACP role:
          RESPOND → "assistant"
          ASK     → "user" (agent requesting human input)
          UPDATE  → "assistant" with progress metadata
          NOTIFY  → "assistant" with event metadata
          *       → "assistant"
        """
        intent_to_role = {
            MessageIntent.RESPOND: "assistant",
            MessageIntent.ASK: "user",
            MessageIntent.UPDATE: "assistant",
            MessageIntent.NOTIFY: "assistant",
        }
        role = intent_to_role.get(msg.intent, "assistant")
        content = msg.payload.get("content") or msg.payload.get("result") or msg.payload

        acp: Dict[str, Any] = {"role": role, "content": content}
        if "attachments" in msg.payload:
            acp["attachments"] = msg.payload["attachments"]
        return acp

    @staticmethod
    def roar_to_acp_run(msg: ROARMessage, run_id: str = "") -> Dict[str, Any]:
        """Translate a ROARMessage to an ACP run response (richer format)."""
        return {
            "run_id": run_id or msg.id,
            "session_id": msg.context.get("session_id", ""),
            "status": "completed"
            if msg.intent == MessageIntent.RESPOND
            else "in_progress",
            "output": ACPAdapter.roar_to_acp_message(msg),
            "metadata": {
                "roar_intent": msg.intent,
                "roar_message_id": msg.id,
                "from_did": msg.from_identity.did,
                "timestamp": msg.timestamp,
            },
            "created_at": time.time(),
        }

    # ── Agent Card ↔ ACP Agent ───────────────────────────────────────────────

    @staticmethod
    def well_known_agent_to_card(
        well_known: Dict[str, Any],
        endpoint: str = "",
    ) -> Dict[str, Any]:
        """Convert an ACP /.well-known/agent.json to a ROAR AgentCard dict.

        Returns a dict suitable for constructing an AgentCard + AgentIdentity.
        """
        name = well_known.get("name", "unknown-agent")
        description = well_known.get("description", "")
        skills: List[str] = [
            s.get("name", "") for s in well_known.get("skills", []) if s.get("name")
        ]

        return {
            "identity": {
                "did": "",  # auto-generated
                "display_name": name,
                "agent_type": "agent",
                "capabilities": skills,
                "version": well_known.get("version", "1.0"),
                "public_key": None,
            },
            "description": description,
            "skills": skills,
            "channels": well_known.get("supportedModes", []),
            "endpoints": {"http": endpoint or well_known.get("url", "")},
            "declared_capabilities": [],
            "metadata": {"protocol": "acp", "original": well_known},
        }
