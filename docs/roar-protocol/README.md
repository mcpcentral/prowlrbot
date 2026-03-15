# ROAR Protocol — Reliable Open Agent Relay

**Install:** `pip install roar-protocol` · [PyPI](https://pypi.org/project/roar-protocol/) · [GitHub](https://github.com/ProwlrBot/roar-protocol)

ROAR is ProwlrBot's unified 5-layer agent communication protocol that wraps
MCP, ACP, and A2A into a single coherent message format with identity,
discovery, and streaming built in.

## Layers

1. **Identity** -- DID-based agent identity (did:roar, did:key, did:web), capability delegation, graduated autonomy
2. **Discovery** -- Hub-based agent registration, cached capability lookup, SQLite persistence
3. **Connect** -- Transport negotiation (HTTP, WebSocket, stdio; gRPC planned)
4. **Exchange** -- Unified ROARMessage envelope (identity + intent + payload + HMAC signing)
5. **Stream** -- In-process event bus with backpressure (AIMD), deduplication, SSE support

## Adapters

ROAR speaks natively and also adapts to:

- **MCP** -- Model Context Protocol (tool/resource/prompt lifecycle via JSON-RPC 2.0)
- **A2A** -- Agent-to-Agent Protocol (task delegation, agent cards, SSE streaming)
- **ACP** -- Agent Client Protocol (IDE integration via JSON-RPC 2.0 over stdio)

Auto-detection sniffs incoming messages to route them to the correct adapter
without configuration.

## Quick Start

```python
from prowlrbot.protocols.sdk import (
    ROARClient,
    ROARServer,
    AgentIdentity,
    AgentCard,
    MessageIntent,
    create_roar_router,
)

# Create an identity
identity = AgentIdentity(display_name="my-agent", capabilities=["code-review"])

# Client: discover and send
client = ROARClient(identity, signing_secret="shared-secret")
card = AgentCard(identity=identity, description="My agent")
client.register(card)
msg = client.send(
    to_agent_id="did:roar:agent:target-abc123",
    intent=MessageIntent.DELEGATE,
    content={"task": "review this PR"},
)

# Server: handle incoming messages
server = ROARServer(identity, signing_secret="shared-secret")

@server.on(MessageIntent.DELEGATE)
async def handle(msg):
    return ROARMessage(
        **{"from": server.identity, "to": msg.from_identity},
        intent=MessageIntent.RESPOND,
        payload={"result": "done"},
    )

# Mount on FastAPI
from fastapi import FastAPI
app = FastAPI()
app.include_router(create_roar_router(server, rate_limit=60))
```

## Documentation

- **spec-v1.md** -- Full protocol specification (this directory)
- **src/prowlrbot/protocols/roar.py** -- Core types and message format
- **src/prowlrbot/protocols/sdk/** -- Python reference implementation
