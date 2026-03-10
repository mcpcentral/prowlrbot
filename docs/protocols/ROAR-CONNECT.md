# ROAR Layer 3 — Connect

## Purpose

Negotiate and configure transport connections between agents. Connect sits between Discovery (which locates agents) and Exchange (which defines message format). It abstracts the underlying transport so that higher layers work identically regardless of whether agents communicate over stdio, HTTP, WebSocket, or gRPC.

## Data Models

### TransportType

Enum of supported transports:

| Value       | Description                                      |
|-------------|--------------------------------------------------|
| `stdio`     | Standard input/output (local process, MCP-style) |
| `http`      | HTTP/HTTPS request-response                      |
| `websocket` | Persistent bidirectional WebSocket connection     |
| `grpc`      | gRPC with Protocol Buffers                       |

### ConnectionConfig

| Field         | Type            | Default                | Description                        |
|---------------|-----------------|------------------------|------------------------------------|
| `transport`   | `TransportType` | `TransportType.HTTP`   | Selected transport                 |
| `url`         | `str`           | `""`                   | Endpoint URL                       |
| `auth_method` | `str`           | `"hmac"`               | Authentication: hmac, jwt, mtls, none |
| `secret`      | `str`           | `""`                   | Shared secret for HMAC signing     |
| `timeout_ms`  | `int`           | `30000`                | Connection timeout in milliseconds |

## Operations

### Transport Negotiation

When a client wants to connect to an agent:

1. Look up the agent's `AgentCard` via Discovery.
2. Read the `endpoints` dictionary for available transports.
3. Select the preferred transport (caller specifies, or fall back to HTTP).
4. Build a `ConnectionConfig` with the endpoint URL and auth details.

```python
config = client.connect(
    agent_id="did:roar:agent:reviewer-abc12345",
    transport=TransportType.WEBSOCKET,
)
```

### Connection Lifecycle

1. **Open**: Establish transport connection using `ConnectionConfig`.
2. **Authenticate**: Exchange credentials (HMAC signature on first message, JWT bearer token, or mTLS handshake).
3. **Exchange**: Send and receive `ROARMessage` objects (Layer 4).
4. **Close**: Graceful shutdown with optional final status message.

## Transport Details

### stdio

Used for local tool execution (MCP compatibility). The parent process spawns the tool, writes JSON messages to stdin, and reads responses from stdout. No URL or TLS required.

### HTTP

Standard request-response. Messages are sent as JSON POST bodies to the endpoint URL. Responses are returned synchronously. TLS required in production.

### WebSocket

Persistent bidirectional connection for real-time communication. After the HTTP upgrade handshake, both sides can send `ROARMessage` frames at any time. Used for streaming (Layer 5).

### gRPC

High-performance binary transport. Service definitions use Protocol Buffers. Supports unary, server-streaming, client-streaming, and bidirectional streaming RPCs.

## Security Considerations

- HTTP and WebSocket transports must use TLS in production environments.
- The `secret` field in `ConnectionConfig` must never be logged or included in message payloads.
- Connection timeouts prevent resource exhaustion from unresponsive agents.
- mTLS provides the strongest transport-level authentication but requires certificate management.

## Standards Alignment

### Transport Selection vs. Existing Protocols

| Transport | ROAR Use | Also Used By |
|-----------|----------|-------------|
| stdio | Local tools, MCP compat | MCP (primary), ACP |
| HTTP | Request-response, REST | MCP (Streamable HTTP), A2A (primary), ACP |
| WebSocket | Real-time bidirectional | — (gap in MCP/A2A) |
| gRPC | Internal high-throughput | — (gap in MCP/A2A) |

WebSocket and gRPC are ROAR's differentiators — no existing agent protocol supports persistent bidirectional connections or high-performance binary transport.

## Example

```python
from prowlrbot.protocols.sdk import TransportType, ConnectionConfig

# Manual config for a known agent
config = ConnectionConfig(
    transport=TransportType.WEBSOCKET,
    url="wss://agent.example.com/roar",
    auth_method="hmac",
    secret="shared-secret-here",
    timeout_ms=15000,
)

# Or use the client to auto-negotiate from directory
from prowlrbot.protocols.sdk.client import ROARClient
from prowlrbot.protocols.sdk import AgentIdentity

client = ROARClient(AgentIdentity(display_name="caller"))
config = client.connect("did:roar:agent:target-abc12345", TransportType.HTTP)
```
