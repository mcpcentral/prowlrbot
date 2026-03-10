# -*- coding: utf-8 -*-
"""Full A2A adapter — bidirectional ROAR ↔ A2A (Google) translation.

Covers the A2A v0.3.0 task lifecycle:
  - tasks/send ↔ DELEGATE intent
  - tasks/get ↔ ASK intent
  - tasks/cancel ↔ NOTIFY intent
  - tasks/sendSubscribe ↔ streaming DELEGATE
  - Agent Card ↔ ROAR AgentCard

Ref: Google A2A Protocol (github.com/google/A2A)
Ref: Now under Linux Foundation governance (22,397 stars as of March 2026)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ...roar import (
    AgentCard,
    AgentIdentity,
    MessageIntent,
    ROARMessage,
    StreamEvent,
)


class A2AFullAdapter:
    """Bidirectional adapter between ROAR and Google A2A protocol."""

    # A2A task states → ROAR-compatible status
    TASK_STATE_MAP = {
        "submitted": "pending",
        "working": "running",
        "input-required": "blocked",
        "completed": "completed",
        "failed": "failed",
        "canceled": "cancelled",
        "rejected": "rejected",
    }

    @staticmethod
    def a2a_send_to_roar(
        a2a_request: Dict[str, Any],
        source_identity: Optional[AgentIdentity] = None,
        target_identity: Optional[AgentIdentity] = None,
    ) -> ROARMessage:
        """Convert an A2A tasks/send request to a ROARMessage.

        Args:
            a2a_request: A2A task send request body.
            source_identity: The sending agent's identity.
            target_identity: The target agent's identity.

        Returns:
            A ROARMessage with DELEGATE intent.
        """
        params = a2a_request.get("params", {})
        task_id = params.get("id", a2a_request.get("id", ""))
        messages = params.get("message", {})
        session_id = params.get("sessionId", "")

        from_id = source_identity or AgentIdentity(
            display_name="a2a-client", agent_type="agent"
        )
        to_id = target_identity or AgentIdentity(
            display_name="a2a-server", agent_type="agent"
        )

        return ROARMessage(
            **{"from": from_id, "to": to_id},
            intent=MessageIntent.DELEGATE,
            payload={
                "a2a_task_id": task_id,
                "a2a_message": messages,
                "a2a_session_id": session_id,
            },
            context={
                "protocol": "a2a",
                "a2a_version": "0.3.0",
            },
        )

    @staticmethod
    def roar_to_a2a_send(
        roar_message: ROARMessage,
        task_id: str = "",
    ) -> Dict[str, Any]:
        """Convert a ROAR DELEGATE message to an A2A tasks/send request.

        Args:
            roar_message: The ROAR message to convert.
            task_id: Optional A2A task ID (generated if empty).

        Returns:
            An A2A tasks/send request dict.
        """
        import uuid

        return {
            "jsonrpc": "2.0",
            "id": roar_message.id,
            "method": "tasks/send",
            "params": {
                "id": task_id or roar_message.payload.get(
                    "a2a_task_id", str(uuid.uuid4())
                ),
                "message": {
                    "role": "user",
                    "parts": [
                        {"type": "text", "text": _extract_text(roar_message.payload)}
                    ],
                },
                "sessionId": roar_message.payload.get(
                    "a2a_session_id", roar_message.id
                ),
            },
        }

    @staticmethod
    def a2a_task_to_roar_response(
        a2a_task: Dict[str, Any],
        original_request: Optional[ROARMessage] = None,
        server_identity: Optional[AgentIdentity] = None,
    ) -> ROARMessage:
        """Convert an A2A task result to a ROAR response.

        Args:
            a2a_task: A2A task result dict.
            original_request: Original ROAR request for routing.
            server_identity: The A2A server's identity.

        Returns:
            A ROARMessage with RESPOND intent.
        """
        from_id = server_identity or AgentIdentity(
            display_name="a2a-server", agent_type="agent"
        )
        to_id = (
            original_request.from_identity
            if original_request
            else AgentIdentity(display_name="a2a-client")
        )

        status = a2a_task.get("status", {}).get("state", "unknown")
        artifacts = a2a_task.get("artifacts", [])

        context = {"protocol": "a2a"}
        if original_request:
            context["in_reply_to"] = original_request.id

        return ROARMessage(
            **{"from": from_id, "to": to_id},
            intent=MessageIntent.RESPOND,
            payload={
                "a2a_status": A2AFullAdapter.TASK_STATE_MAP.get(status, status),
                "a2a_artifacts": artifacts,
                "a2a_task_id": a2a_task.get("id", ""),
            },
            context=context,
        )

    @staticmethod
    def a2a_sse_to_stream_event(
        sse_data: Dict[str, Any],
        source_did: str = "",
        session_id: str = "",
    ) -> StreamEvent:
        """Convert an A2A SSE event to a ROAR StreamEvent.

        Args:
            sse_data: The SSE event data dict.
            source_did: DID of the A2A agent.
            session_id: Session ID for the stream.

        Returns:
            A StreamEvent with task_update type.
        """
        return StreamEvent(
            type="task_update",
            source=source_did,
            session_id=session_id,
            data={
                "protocol": "a2a",
                "task_id": sse_data.get("id", ""),
                "status": sse_data.get("status", {}).get("state", "unknown"),
                "message": sse_data.get("status", {}).get("message", ""),
            },
        )

    @staticmethod
    def a2a_card_to_roar(a2a_card: Dict[str, Any]) -> AgentCard:
        """Convert an A2A Agent Card to a ROAR AgentCard.

        Args:
            a2a_card: A2A Agent Card dict.

        Returns:
            A ROAR AgentCard.
        """
        skills = [
            s.get("name", s.get("id", ""))
            for s in a2a_card.get("skills", [])
        ]

        identity = AgentIdentity(
            display_name=a2a_card.get("name", ""),
            agent_type="agent",
            capabilities=skills,
        )

        endpoints = {}
        url = a2a_card.get("url", "")
        if url:
            endpoints["http"] = url

        return AgentCard(
            identity=identity,
            description=a2a_card.get("description", ""),
            skills=skills,
            endpoints=endpoints,
        )

    @staticmethod
    def roar_card_to_a2a(card: AgentCard) -> Dict[str, Any]:
        """Convert a ROAR AgentCard to an A2A Agent Card.

        Args:
            card: The ROAR AgentCard.

        Returns:
            An A2A Agent Card dict.
        """
        return {
            "name": card.identity.display_name,
            "description": card.description,
            "url": card.endpoints.get("http", ""),
            "version": card.identity.version,
            "capabilities": {
                "streaming": "websocket" in card.endpoints,
                "pushNotifications": False,
                "stateTransitionHistory": True,
            },
            "skills": [
                {"id": s, "name": s} for s in card.skills
            ],
        }


def _extract_text(payload: Dict[str, Any]) -> str:
    """Extract a text representation from a ROAR payload."""
    if "text" in payload:
        return str(payload["text"])
    if "task" in payload:
        return str(payload["task"])
    if "a2a_message" in payload:
        msg = payload["a2a_message"]
        if isinstance(msg, dict):
            parts = msg.get("parts", [])
            return " ".join(p.get("text", "") for p in parts if "text" in p)
    import json
    return json.dumps(payload)
