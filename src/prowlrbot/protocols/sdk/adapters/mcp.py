# -*- coding: utf-8 -*-
"""Full MCP adapter — bidirectional ROAR ↔ MCP translation.

Covers the full MCP tool lifecycle:
  - tools/list ↔ DISCOVER intent
  - tools/call ↔ EXECUTE intent
  - Tool results ↔ RESPOND intent
  - resources/list, prompts/list ↔ DISCOVER with capability filter

Ref: MCP Specification (modelcontextprotocol.io)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ...roar import AgentIdentity, MessageIntent, ROARMessage


class MCPFullAdapter:
    """Bidirectional adapter between ROAR messages and MCP JSON-RPC.

    MCP uses JSON-RPC 2.0 over stdio or HTTP. This adapter maps
    ROAR intents to MCP methods and vice versa.
    """

    # MCP method → ROAR intent mapping
    METHOD_TO_INTENT = {
        "tools/list": MessageIntent.DISCOVER,
        "tools/call": MessageIntent.EXECUTE,
        "resources/list": MessageIntent.DISCOVER,
        "resources/read": MessageIntent.EXECUTE,
        "prompts/list": MessageIntent.DISCOVER,
        "prompts/get": MessageIntent.EXECUTE,
        "completion/complete": MessageIntent.ASK,
        "initialize": MessageIntent.DISCOVER,
    }

    # ROAR intent → MCP method (default mapping)
    INTENT_TO_METHOD = {
        MessageIntent.DISCOVER: "tools/list",
        MessageIntent.EXECUTE: "tools/call",
        MessageIntent.RESPOND: None,  # MCP responses are JSON-RPC results
    }

    @staticmethod
    def mcp_to_roar(
        mcp_message: Dict[str, Any],
        source_identity: Optional[AgentIdentity] = None,
        target_identity: Optional[AgentIdentity] = None,
    ) -> ROARMessage:
        """Convert an MCP JSON-RPC request to a ROARMessage.

        Args:
            mcp_message: MCP JSON-RPC message dict.
            source_identity: Identity of the MCP client.
            target_identity: Identity of the MCP server.

        Returns:
            A ROARMessage with the mapped intent and payload.
        """
        method = mcp_message.get("method", "")
        params = mcp_message.get("params", {})
        msg_id = mcp_message.get("id", "")

        intent = MCPFullAdapter.METHOD_TO_INTENT.get(
            method, MessageIntent.EXECUTE
        )

        from_id = source_identity or AgentIdentity(
            display_name="mcp-client", agent_type="tool"
        )
        to_id = target_identity or AgentIdentity(
            display_name="mcp-server", agent_type="tool"
        )

        return ROARMessage(
            **{"from": from_id, "to": to_id},
            intent=intent,
            payload={
                "mcp_method": method,
                "mcp_params": params,
                "mcp_id": msg_id,
            },
            context={"protocol": "mcp", "jsonrpc_id": msg_id},
        )

    @staticmethod
    def roar_to_mcp(
        roar_message: ROARMessage,
        method_override: str = "",
    ) -> Dict[str, Any]:
        """Convert a ROARMessage to an MCP JSON-RPC request.

        Args:
            roar_message: The ROAR message to convert.
            method_override: Force a specific MCP method.

        Returns:
            An MCP JSON-RPC 2.0 request dict.
        """
        method = method_override or roar_message.payload.get(
            "mcp_method",
            MCPFullAdapter.INTENT_TO_METHOD.get(
                roar_message.intent, "tools/call"
            ),
        )

        params = roar_message.payload.get("mcp_params", roar_message.payload)

        return {
            "jsonrpc": "2.0",
            "id": roar_message.context.get("jsonrpc_id", roar_message.id),
            "method": method,
            "params": params,
        }

    @staticmethod
    def mcp_result_to_roar(
        result: Dict[str, Any],
        original_request: Optional[ROARMessage] = None,
        server_identity: Optional[AgentIdentity] = None,
    ) -> ROARMessage:
        """Convert an MCP JSON-RPC result to a ROARMessage response.

        Args:
            result: The MCP result dict.
            original_request: The original ROAR request (for reply routing).
            server_identity: Identity of the MCP server.

        Returns:
            A ROARMessage with RESPOND intent carrying the MCP result.
        """
        from_id = server_identity or AgentIdentity(
            display_name="mcp-server", agent_type="tool"
        )
        to_id = (
            original_request.from_identity
            if original_request
            else AgentIdentity(display_name="mcp-client", agent_type="tool")
        )

        is_error = "error" in result
        payload = {
            "mcp_result": result.get("result", result.get("error", {})),
            "mcp_is_error": is_error,
        }

        context = {"protocol": "mcp"}
        if original_request:
            context["in_reply_to"] = original_request.id

        return ROARMessage(
            **{"from": from_id, "to": to_id},
            intent=MessageIntent.RESPOND,
            payload=payload,
            context=context,
        )

    @staticmethod
    def roar_to_mcp_result(
        roar_response: ROARMessage,
    ) -> Dict[str, Any]:
        """Convert a ROAR response back to MCP JSON-RPC result format."""
        jsonrpc_id = roar_response.context.get("jsonrpc_id", roar_response.id)

        if roar_response.payload.get("mcp_is_error"):
            return {
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "error": roar_response.payload.get("mcp_result", {}),
            }

        return {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": roar_response.payload.get("mcp_result", roar_response.payload),
        }
