# ROAR Layer 5 — Stream

## Purpose

Provide real-time event streaming for live agent activity, reasoning traces, monitor alerts, and world updates. Streaming builds on the Connect layer's persistent transports (WebSocket, SSE) and complements the request-response pattern of the Exchange layer.

## Data Models

### StreamEventType

| Value           | Description                                      |
|-----------------|--------------------------------------------------|
| `tool_call`     | Agent invoked a tool                             |
| `mcp_request`   | Agent made an MCP protocol request               |
| `reasoning`     | Agent's chain-of-thought reasoning step          |
| `task_update`   | Progress update on a delegated task              |
| `monitor_alert` | Alert from the monitoring engine                 |
| `agent_status`  | Agent lifecycle event (online, busy, offline)    |
| `checkpoint`    | Memory or state checkpoint saved                 |
| `world_update`  | AgentVerse virtual world state change            |

### StreamEvent

| Field        | Type              | Default        | Description                          |
|--------------|-------------------|----------------|--------------------------------------|
| `type`       | `StreamEventType` | required       | Category of event                    |
| `source`     | `str`             | `""`           | DID of the event source              |
| `session_id` | `str`             | `""`           | Session this event belongs to        |
| `data`       | `dict`            | `{}`           | Event-specific payload               |
| `timestamp`  | `float`           | `time.time()`  | Unix timestamp of event creation     |

## Operations

### Emitting Events

Agents emit events during processing. Events are lightweight and do not require signing (they travel over an already-authenticated connection).

```python
from prowlrbot.protocols.sdk import StreamEvent, StreamEventType

event = StreamEvent(
    type=StreamEventType.REASONING,
    source="did:roar:agent:planner-abc12345",
    session_id="session_001",
    data={"step": 3, "thought": "Need to check the database first"},
)
```

### Consuming Events

Clients subscribe to an event stream, typically via WebSocket or SSE. The SDK provides a context manager placeholder:

```python
from prowlrbot.protocols.sdk.client import ROARClient

client = ROARClient(identity)

def on_event(event):
    print(f"[{event.type}] {event.data}")

with client.stream_events(on_event):
    # Connection is open; events arrive via callback
    pass
```

### Event Filtering

Consumers can filter events by type, source DID, or session ID. Filtering is applied server-side when supported, or client-side as a fallback.

### Backpressure

When a consumer cannot keep up with the event rate:

1. The server buffers up to a configurable limit (default: 1000 events).
2. Beyond the limit, oldest events are dropped and a `checkpoint` event is emitted.
3. The consumer can request a replay from the last checkpoint.

## Transport Mapping

| Transport   | Streaming Method                          |
|-------------|-------------------------------------------|
| `stdio`     | Newline-delimited JSON on stdout          |
| `http`      | Server-Sent Events (SSE)                 |
| `websocket` | JSON frames on the WebSocket connection   |
| `grpc`      | Server-streaming or bidirectional RPC     |

## Security Considerations

- Stream connections inherit the authentication from the Connect layer.
- Reasoning events may contain sensitive intermediate thoughts; filter before exposing to external consumers.
- Monitor alerts should be rate-limited to prevent notification flooding.
- Event data should not contain secrets or credentials.

## Standards Alignment

### Streaming Comparison

| Feature | ROAR Stream | A2A SSE | MCP Streamable HTTP |
|---------|------------|---------|---------------------|
| Transport | WebSocket, SSE, gRPC, stdio | SSE only | SSE (server-initiated) |
| Bidirectional | Yes (WebSocket) | No | No |
| Backpressure | AIMD adaptive | None | None |
| Event types | 8 application-level | 1 (task update) | 1 (tool progress) |
| Pub/Sub | NATS JetStream (planned) | — | — |
| Delivery | At-least-once + idempotency | At-most-once | At-most-once |

### Planned: NATS JetStream Integration

For production pub/sub streaming, ROAR will optionally use NATS JetStream:
- Subject-based routing maps to DID-based topics (`roar.events.<did>`)
- Optional persistence for replay from checkpoints
- Sub-millisecond latency, ~50MB memory footprint
- Embedded mode (no external dependency required)

## Example

```python
from prowlrbot.protocols.sdk import StreamEvent, StreamEventType

# Tool call event
tool_event = StreamEvent(
    type=StreamEventType.TOOL_CALL,
    source="did:roar:agent:coder-abc12345",
    session_id="session_42",
    data={
        "tool": "shell",
        "command": "pytest tests/",
        "status": "running",
    },
)

# Monitor alert event
alert_event = StreamEvent(
    type=StreamEventType.MONITOR_ALERT,
    source="did:roar:agent:monitor-def67890",
    data={
        "detector": "web_change",
        "url": "https://example.com/status",
        "change_type": "content_modified",
        "severity": "warning",
    },
)

# Agent status event
status_event = StreamEvent(
    type=StreamEventType.AGENT_STATUS,
    source="did:roar:agent:assistant-ghi13579",
    data={"status": "online", "load": 0.42},
)
```
