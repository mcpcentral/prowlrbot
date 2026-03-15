import { AgentIdentity, MessageIntent, ROARMessage } from "./types";
import { createMessage } from "./message";
import { createIdentity } from "./identity";

/**
 * Adapter for converting between ROAR messages and
 * Model Context Protocol (MCP) tool calls / results.
 *
 * Maps MCP tool calls to ROAR EXECUTE messages (matching Python's MCPAdapter).
 */
export class MCPAdapter {
  /**
   * Convert an MCP tool call to a ROAR EXECUTE message.
   *
   * @param toolName - The MCP tool name.
   * @param params - Tool parameters.
   * @param fromAgent - Identity of the calling agent.
   * @returns A ROAR message with EXECUTE intent.
   */
  static mcpToRoar(
    toolName: string,
    params: Record<string, unknown>,
    fromAgent: AgentIdentity,
  ): ROARMessage {
    const toolIdentity = createIdentity(toolName, { agentType: "tool" });
    return createMessage(fromAgent, toolIdentity, MessageIntent.EXECUTE, {
      action: toolName,
      params,
    });
  }

  /**
   * Convert a ROAR EXECUTE message back to MCP tool call format.
   */
  static roarToMcp(msg: ROARMessage): {
    tool: string;
    params: Record<string, unknown>;
  } {
    return {
      tool: (msg.payload.action as string) ?? "",
      params: (msg.payload.params as Record<string, unknown>) ?? {},
    };
  }

  /**
   * Convert an MCP tool result into a ROAR RESPOND message.
   */
  static fromMcpResult(
    result: {
      call_id?: string;
      content?: unknown;
      is_error?: boolean;
    },
    fromAgent: AgentIdentity,
    toAgent: AgentIdentity,
  ): ROARMessage {
    return createMessage(
      fromAgent,
      toAgent,
      MessageIntent.RESPOND,
      {
        call_id: result.call_id,
        result: result.content,
        is_error: result.is_error ?? false,
      },
      { in_reply_to: result.call_id },
    );
  }
}

/**
 * Adapter for converting between ROAR messages and
 * Agent-to-Agent (A2A) protocol tasks / results.
 *
 * Maps A2A tasks to ROAR DELEGATE messages (matching Python's A2AAdapter).
 */
export class A2AAdapter {
  /**
   * Convert an A2A task to a ROAR DELEGATE message.
   */
  static a2aTaskToRoar(
    task: Record<string, unknown>,
    fromAgent: AgentIdentity,
    toAgent: AgentIdentity,
  ): ROARMessage {
    return createMessage(fromAgent, toAgent, MessageIntent.DELEGATE, task, {
      protocol: "a2a",
    });
  }

  /**
   * Convert a ROAR DELEGATE message to A2A task format.
   */
  static roarToA2a(msg: ROARMessage): Record<string, unknown> {
    return {
      task_id: msg.id,
      from: msg.from_identity.did,
      to: msg.to_identity.did,
      payload: msg.payload,
    };
  }

  /**
   * Convert an A2A task result into a ROAR RESPOND message.
   */
  static fromA2aResult(
    result: {
      id?: string;
      status?: { state?: string; message?: unknown };
      artifacts?: Array<{
        parts?: Array<{ type?: string; text?: string }>;
      }>;
    },
    fromAgent: AgentIdentity,
    toAgent: AgentIdentity,
  ): ROARMessage {
    let content: unknown = result.status?.message;
    if (result.artifacts && result.artifacts.length > 0) {
      const parts = result.artifacts.flatMap((a) => a.parts ?? []);
      const texts = parts
        .filter((p) => p.type === "text")
        .map((p) => p.text)
        .join("\n");
      if (texts) {
        content = texts;
      }
    }

    return createMessage(
      fromAgent,
      toAgent,
      MessageIntent.RESPOND,
      {
        task_id: result.id,
        result: content,
        state: result.status?.state ?? "unknown",
      },
      { protocol: "a2a", in_reply_to: result.id },
    );
  }
}
