# ROAR Protocol Specification v1.0

**Real-time Open Agent Runtime**

## Overview

ROAR is a five-layer protocol for agent identity, discovery, communication, and streaming. It provides a single unified format for all agent interactions while maintaining backward compatibility with MCP, A2A, and ACP.

### Architecture

```
Layer 5: Stream    — Real-time event streaming (SSE, WebSocket)
Layer 4: Exchange  — Message format, signing, verification
Layer 3: Connect   — Transport negotiation (stdio, HTTP, WS, gRPC)
Layer 2: Discovery — Directory service, capability search, federation
Layer 1: Identity  — W3C DID-based agent identity, capability declaration
```

Each layer builds on the one below it. An implementation may use only the lower layers (e.g. Identity + Discovery) without requiring the upper layers.

## Layer 1 — Identity

Agents identify themselves using W3C Decentralized Identifiers (DIDs) with the `did:roar:` method. Each agent has an `AgentIdentity` containing a DID, display name, type, capabilities list, and version. An `AgentCard` extends identity with a description, skills, channels, endpoints, and declared capabilities (`AgentCapability`).

See [ROAR-IDENTITY.md](ROAR-IDENTITY.md) for the full specification.

## Layer 2 — Discovery

The `AgentDirectory` provides in-memory agent registration, lookup by DID, and capability-based search. Federation across multiple directories is supported by propagating `DiscoveryEntry` records that include the originating hub URL and timestamps.

See [ROAR-DISCOVERY.md](ROAR-DISCOVERY.md) for the full specification.

## Layer 3 — Connect

ROAR supports four transport types: `stdio`, `http`, `websocket`, and `grpc`. A `ConnectionConfig` specifies the transport, URL, authentication method (`hmac`, `jwt`, `mtls`, `none`), shared secret, and timeout. Transport negotiation uses the endpoints declared in an agent's card.

See [ROAR-CONNECT.md](ROAR-CONNECT.md) for the full specification.

## Layer 4 — Exchange

All communication uses a single `ROARMessage` format with fields for protocol version, message ID, sender, receiver, intent, payload, context, auth, and timestamp. Seven intent types cover all interaction patterns: `execute`, `delegate`, `update`, `ask`, `respond`, `notify`, and `discover`. Messages are signed with HMAC-SHA256 and verified on receipt.

See [ROAR-EXCHANGE.md](ROAR-EXCHANGE.md) for the full specification.

## Layer 5 — Stream

Real-time events use `StreamEvent` objects with a type, source DID, session ID, data payload, and timestamp. Eight event types cover tool calls, MCP requests, reasoning traces, task updates, monitor alerts, agent status changes, checkpoints, and world updates.

See [ROAR-STREAM.md](ROAR-STREAM.md) for the full specification.

## Backward Compatibility

### MCP Adapter

`MCPAdapter` translates MCP tool calls to ROAR `EXECUTE` messages and back. The tool name maps to `payload.action` and parameters to `payload.params`.

### A2A Adapter

`A2AAdapter` translates A2A agent tasks to ROAR `DELEGATE` messages. The original protocol is preserved in `context.protocol`.

### ACP Adapter

ACP compatibility is provided by mapping ACP operation types to the corresponding ROAR `MessageIntent` values.

## Security

- **Message signing**: HMAC-SHA256 over `{id, intent, payload}` with a shared secret.
- **Identity verification**: DID resolution confirms agent identity before accepting messages.
- **Transport encryption**: TLS required for HTTP and WebSocket transports in production.
- **Secret management**: Signing secrets are never transmitted in message payloads.

## SDK Usage Examples

### Client

```python
from prowlrbot.protocols.sdk import AgentIdentity, MessageIntent
from prowlrbot.protocols.sdk.client import ROARClient

identity = AgentIdentity(display_name="my-agent", capabilities=["code-review"])
client = ROARClient(identity)

# Register with local directory
from prowlrbot.protocols.sdk import AgentCard
card = AgentCard(identity=identity, description="Reviews code")
client.register(card)

# Send a message
msg = client.send(
    to_agent_id="did:roar:agent:reviewer-abc123",
    intent=MessageIntent.DELEGATE,
    content={"task": "review", "files": ["main.py"]},
)
```

### Server

```python
from prowlrbot.protocols.sdk import AgentIdentity, MessageIntent, ROARMessage
from prowlrbot.protocols.sdk.server import ROARServer

identity = AgentIdentity(display_name="code-reviewer")
server = ROARServer(identity, port=8089, description="Code review agent")

@server.on(MessageIntent.DELEGATE)
async def handle_delegate(msg: ROARMessage) -> ROARMessage:
    return ROARMessage(
        **{"from": server.identity, "to": msg.from_identity},
        intent=MessageIntent.RESPOND,
        payload={"status": "ok", "review": "LGTM"},
    )
```

## References

- [MCP Specification v2025-11-25](https://spec.modelcontextprotocol.io/) — Anthropic / AAIF. Tool integration protocol.
- [A2A Protocol v0.3.0](https://github.com/google/A2A) — Google / Linux Foundation. Agent-to-agent collaboration.
- [ACP Specification v0.2.3](https://github.com/agntcy/acp-spec) — Agntcy Collective. IDE-agent communication.
- [W3C DID Core v1.0](https://www.w3.org/TR/did-core/) — W3C Recommendation, July 2022. Decentralized identifiers.
- [W3C VC Data Model v2.0](https://www.w3.org/TR/vc-data-model-2.0/) — W3C Recommendation, March 2025.
- [DIDComm Messaging v2.1](https://identity.foundation/didcomm-messaging/spec/) — Decentralized Identity Foundation.
- [AAIF Technical Committee](https://github.com/aaif/technical-committee) — Agentic AI Foundation, Linux Foundation. Founded March 2026.
- [IETF BANDAID](https://datatracker.ietf.org/doc/draft-mozleywilliams-dnsop-dnsaid/) — DNS-based Agent Discovery.
