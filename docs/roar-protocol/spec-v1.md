# ROAR Protocol Specification v1.0

**Reliable Open Agent Relay**

- Status: Implemented (reference SDK in Python)
- Version: 1.0
- Date: 2026-03-11
- Reference implementation: `src/prowlrbot/protocols/sdk/`
- Core types: `src/prowlrbot/protocols/roar.py`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Layer 1: Identity](#2-layer-1-identity)
3. [Layer 2: Discovery](#3-layer-2-discovery)
4. [Layer 3: Connect](#4-layer-3-connect)
5. [Layer 4: Exchange](#5-layer-4-exchange)
6. [Layer 5: Stream](#6-layer-5-stream)
7. [Protocol Adapters](#7-protocol-adapters)
8. [Security](#8-security)
9. [SDK Reference](#9-sdk-reference)

---

## 1. Overview

ROAR is a 5-layer protocol for agent-to-agent communication. It provides a
unified message format that bridges MCP, A2A, and ACP protocols while adding
identity, discovery, and streaming capabilities that none of them offer
individually.

### Design principles

- **One envelope for everything.** A single `ROARMessage` type carries all
  inter-agent communication -- tool calls, task delegation, IDE updates,
  human prompts, and discovery requests.
- **DID-based identity.** Every agent has a W3C DID. Three tiers cover
  ephemeral, cryptographic, and persistent identity needs.
- **Transport-agnostic.** The same message format works over HTTP, WebSocket,
  and stdio. Transport selection is automatic based on registered endpoints.
- **Backward compatible.** Adapters translate ROAR messages to/from MCP and
  A2A wire format. Auto-detection sniffs incoming messages to pick the right
  adapter.
- **Security by default.** HMAC-SHA256 message signing with replay protection.
  Ed25519 for cross-organization trust when shared secrets are impractical.

### Relationship to other protocols

| Feature              | MCP     | A2A     | ACP     | ROAR    |
|----------------------|---------|---------|---------|---------|
| Identity (DID)       | No      | No      | No      | Yes     |
| Discovery            | No      | Agent Card only | No | Hub + cache + SQLite |
| Transport            | stdio, HTTP | HTTP, SSE | stdio | HTTP, WS, stdio |
| Streaming            | No      | SSE only | No     | EventBus + SSE + WS |
| Signing              | No      | No      | No      | HMAC + Ed25519 |
| Delegation           | No      | Tasks   | No      | Tokens + autonomy levels |
| Backpressure         | No      | No      | No      | AIMD controller |

---

## 2. Layer 1: Identity

**Implementation:** `src/prowlrbot/protocols/roar.py` (AgentIdentity, AgentCard)
and `src/prowlrbot/protocols/sdk/identity/`

Every agent in ROAR has an `AgentIdentity` containing a W3C Decentralized
Identifier (DID), a display name, an agent type, a list of capabilities, and
an optional Ed25519 public key.

### 2.1 AgentIdentity

```python
class AgentIdentity(BaseModel):
    did: str           # e.g. "did:roar:agent:planner-a1b2c3d4"
    display_name: str
    agent_type: str    # "agent" | "tool" | "human" | "ide"
    capabilities: List[str]
    version: str       # default "1.0"
    public_key: Optional[str]  # Ed25519 hex-encoded
```

If `did` is not provided, it is auto-generated on construction:

```
did:roar:<agent_type>:<slugified-display-name>-<random-hex-16>
```

### 2.2 DID Method Tiers

ROAR supports three DID methods, each suited to a different trust model.

#### did:roar (ephemeral, auto-generated)

- Format: `did:roar:<type>:<slug>-<hex16>`
- No external registry needed. Generated on construction.
- Suitable for local agents within a single ProwlrBot instance.

#### did:key (ephemeral, cryptographic)

- Format: `did:key:z<base58-multicodec-ed25519-pubkey>`
- Self-certifying: the DID is derived entirely from the public key.
- Requires PyNaCl (`pip install pynacl`). Falls back to hex encoding if
  `base58` is not installed.
- Suitable for cross-organization trust without a registry.

**Implementation:** `sdk/identity/did_key.py` -- `DIDKeyMethod`

```python
from prowlrbot.protocols.sdk import DIDKeyMethod

method = DIDKeyMethod()
identity = method.generate()  # Returns DIDKeyIdentity(did, keypair)
doc = method.resolve(identity.did)  # Returns DIDDocument
```

#### did:web (persistent, DNS-bound)

- Format: `did:web:<domain>:<path>` (colons replace slashes)
- Resolved via HTTPS: `https://<domain>/<path>/did.json`
  (or `/.well-known/did.json` for root DIDs).
- Port encoding: `did:web:example.com%3A8080:agents:planner`
- Suitable for production agents with stable, verifiable identity.

**Implementation:** `sdk/identity/did_web.py` -- `DIDWebMethod`

```python
from prowlrbot.protocols.sdk import DIDWebMethod

method = DIDWebMethod()
identity = method.create(domain="example.com", path="agents/planner")
# identity.did -> "did:web:example.com:agents:planner"
# identity.document_url -> "https://example.com/agents/planner/did.json"
```

### 2.3 DID Documents

DID Documents follow the W3C DID Core v1.0 specification. They describe an
agent's public keys and service endpoints.

**Implementation:** `sdk/identity/did_document.py` -- `DIDDocument`

```python
doc = DIDDocument.for_agent(
    did="did:roar:agent:planner-abc12345",
    public_key="base64url-encoded-ed25519-key",
    endpoints={"http": "http://localhost:8089"},
)
json_ld = doc.to_dict()
```

Output structure:

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1"
  ],
  "id": "did:roar:agent:planner-abc12345",
  "controller": "did:roar:agent:planner-abc12345",
  "verificationMethod": [{
    "id": "did:roar:agent:planner-abc12345#key-1",
    "type": "Ed25519VerificationKey2020",
    "controller": "did:roar:agent:planner-abc12345",
    "publicKeyBase64": "<base64url-key>"
  }],
  "authentication": ["did:roar:agent:planner-abc12345#key-1"],
  "assertionMethod": ["did:roar:agent:planner-abc12345#key-1"],
  "service": [{
    "id": "did:roar:agent:planner-abc12345#svc-http",
    "type": "ROARMessaging",
    "serviceEndpoint": "http://localhost:8089"
  }]
}
```

### 2.4 AgentCard

An `AgentCard` is the discovery-facing descriptor for an agent. It contains
the agent's identity, description, skills, channels, endpoints, declared
capabilities, and arbitrary metadata. It is compatible with A2A agent cards.

```python
class AgentCard(BaseModel):
    identity: AgentIdentity
    description: str
    skills: List[str]
    channels: List[str]
    endpoints: Dict[str, str]  # transport -> URL
    declared_capabilities: List[AgentCapability]
    metadata: Dict[str, Any]
```

### 2.5 Capability Delegation and Graduated Autonomy

Agents operate at one of four autonomy levels:

| Level        | Value        | Can act? | Needs approval? |
|--------------|--------------|----------|-----------------|
| WATCH        | `"watch"`    | No       | Yes             |
| GUIDE        | `"guide"`    | No       | Yes             |
| DELEGATE     | `"delegate"` | Yes      | No              |
| AUTONOMOUS   | `"autonomous"` | Yes    | No              |

Capabilities are delegated via `DelegationToken` objects that encode who
granted what capability to whom, with optional time limits and scope
constraints.

**Implementation:** `sdk/identity/delegation.py` -- `CapabilityDelegation`, `DelegationToken`

```python
from prowlrbot.protocols.sdk import CapabilityDelegation, AutonomyLevel

delegation = CapabilityDelegation()

# Grant capabilities from human to agent
token = delegation.grant(
    grantor="did:roar:human:admin-12345678",
    grantee="did:roar:agent:planner-abcdef00",
    capabilities=["code-review", "testing"],
    autonomy_level=AutonomyLevel.DELEGATE,
    ttl_seconds=3600,  # 1 hour
)

# Check authorization
authorized = delegation.is_authorized(
    agent_did="did:roar:agent:planner-abcdef00",
    capability="code-review",
)

# Revoke
delegation.revoke(token.id)

# Get highest autonomy level for an agent
level = delegation.get_autonomy_level("did:roar:agent:planner-abcdef00")

# Clean up expired/revoked tokens
removed_count = delegation.cleanup_expired()
```

DelegationToken fields:

```
id              str             Auto-generated "dt-<hex16>"
grantor         str             DID of the granting agent/human
grantee         str             DID of the receiving agent
capabilities    List[str]       Capability names ("*" = wildcard)
autonomy_level  AutonomyLevel   Maximum level for these capabilities
constraints     Dict[str, Any]  Additional scope constraints
issued_at       float           Unix timestamp
expires_at      float           Unix timestamp (0 = no expiry)
revoked         bool            Whether manually revoked
```

---

## 3. Layer 2: Discovery

**Implementation:** `src/prowlrbot/protocols/roar.py` (AgentDirectory, DiscoveryEntry)
and `src/prowlrbot/protocols/sdk/discovery/`

Discovery has four tiers, from fastest to broadest:

### 3.1 Tier 0: In-memory Directory

The base `AgentDirectory` class provides fast, zero-latency lookups within a
single process. All other tiers ultimately populate or consult this directory.

**Implementation:** `src/prowlrbot/protocols/roar.py` -- `AgentDirectory`

```python
directory = AgentDirectory()
entry = directory.register(card)     # Returns DiscoveryEntry
found = directory.lookup(did)        # Returns Optional[DiscoveryEntry]
matches = directory.search("code-review")  # By capability
all_agents = directory.list_all()
directory.unregister(did)
```

`DiscoveryEntry` contains the agent card plus timestamps:

```python
class DiscoveryEntry(BaseModel):
    agent_card: AgentCard
    registered_at: float   # Unix timestamp
    last_seen: float       # Unix timestamp
    hub_url: str           # Which hub registered this agent
```

### 3.2 Tier 0.5: SQLite Persistent Directory

A drop-in replacement for the in-memory directory that persists agent cards to
a SQLite database. Same interface as `AgentDirectory`.

**Implementation:** `sdk/discovery/sqlite_directory.py` -- `SQLiteAgentDirectory`

```python
from prowlrbot.protocols.sdk.discovery import SQLiteAgentDirectory

directory = SQLiteAgentDirectory()  # default: ~/.prowlrbot/roar_directory.db
directory = SQLiteAgentDirectory("/path/to/custom.db")

# Same API as AgentDirectory
directory.register(card)
directory.lookup(did)
directory.search("code-review")
directory.list_all()
directory.unregister(did)
directory.close()
```

Storage schema:

```sql
CREATE TABLE agents (
    did TEXT PRIMARY KEY,
    card_json TEXT NOT NULL,
    registered_at REAL NOT NULL,
    last_seen REAL NOT NULL,
    hub_url TEXT NOT NULL DEFAULT ''
);
```

### 3.3 Tier 1: Discovery Hub (HTTP API)

A centralized or federated registry where agents publish their cards. Multiple
hubs can gossip with each other for cross-network discovery.

**Server implementation:** `sdk/discovery/hub_server.py` -- `create_hub_router`

The hub server is a FastAPI router with the following endpoints:

| Method   | Path              | Description                |
|----------|-------------------|----------------------------|
| POST     | /agents           | Register an agent card     |
| GET      | /agents/:did      | Look up by DID             |
| GET      | /agents?q=        | Search by capability       |
| DELETE   | /agents/:did      | Unregister                 |

Security:
- Optional API key authentication via `X-API-Key` header.
- Input validation: field length limits (500 chars), list length limits (50),
  max agents limit (10,000).
- Constant-time API key comparison via `hmac.compare_digest`.

```python
from fastapi import FastAPI
from prowlrbot.protocols.sdk.discovery import create_hub_router

app = FastAPI()
app.include_router(create_hub_router(api_key="my-secret-key"))
```

**Client implementation:** `sdk/discovery/hub.py` -- `HubClient`

```python
from prowlrbot.protocols.sdk.discovery import HubClient, HubConfig

hub = HubClient(HubConfig(url="https://hub.example.com", api_key="key"))
await hub.register(card)
entry = await hub.lookup("did:roar:agent:planner-abc12345")
results = await hub.search("code-review")
await hub.unregister("did:roar:agent:planner-abc12345")
```

### 3.4 Tier 1.5: Discovery Cache

A TTL + LRU cache layer that sits in front of upstream resolvers (Hub or DNS).
Prevents repeated network calls for recently discovered agents.

**Implementation:** `sdk/discovery/cache.py` -- `DiscoveryCache`

```python
from prowlrbot.protocols.sdk.discovery import DiscoveryCache

cache = DiscoveryCache(max_entries=1000, default_ttl=300.0)
cache.put(entry)                      # Cache a discovery entry
found = cache.get(did)                # Returns entry or None (TTL-aware)
matches = cache.search("code-review") # Search cached entries
cache.invalidate(did)                 # Remove specific entry
stats = cache.stats                   # {size, max_entries, hits, misses, hit_rate}
```

Cache behavior:
- Entries are evicted after TTL expiration.
- LRU eviction when the cache exceeds `max_entries`.
- Cache misses return None (caller should fall through to Hub or DNS).

### 3.5 Tier 2 and 3: DNS and mDNS (planned)

Tier 2 (DNS/SVCB) and Tier 3 (mDNS/DNS-SD) are defined in the architecture
but not yet implemented. These would enable internet-scale and LAN-local
discovery respectively.

---

## 4. Layer 3: Connect

**Implementation:** `src/prowlrbot/protocols/roar.py` (TransportType, ConnectionConfig)
and `src/prowlrbot/protocols/sdk/transports/`

### 4.1 Transport Types

```python
class TransportType(StrEnum):
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"
    GRPC = "grpc"  # Planned, not yet implemented
```

### 4.2 ConnectionConfig

```python
class ConnectionConfig(BaseModel):
    transport: TransportType  # default: HTTP
    url: str                  # Endpoint URL (or command for stdio)
    auth_method: str          # "hmac" | "jwt" | "mtls" | "none"
    secret: str               # Signing/auth secret
    timeout_ms: int           # default: 30000
```

### 4.3 Transport Selection

The `ROARClient` automatically selects the best transport for a target agent
based on its registered endpoints:

1. WebSocket (preferred for real-time, bidirectional)
2. HTTP (default fallback)
3. stdio (for local subprocess tools)

Override by passing `transport=` to `send_remote()`.

### 4.4 HTTP Transport

**Implementation:** `sdk/transports/http.py`

- Messages sent as JSON POST to `<url>/roar/message`.
- Request headers: `Content-Type: application/json`, `X-ROAR-Protocol: 1.0`.
- JWT auth: `Authorization: Bearer <token>` header.
- HMAC auth: embedded in message body (`auth` field).
- SSE streaming via `GET <url>/roar/events`.

```python
# Request-response
response = await http_send(config, message)

# SSE event streaming
async for event in http_stream_events(config, session_id="abc"):
    process(event)
```

### 4.5 WebSocket Transport

**Implementation:** `sdk/transports/websocket.py`

- Connects to `<url>/roar/ws` (auto-converts http:// to ws://).
- Bidirectional: both sides can send frames at any time.
- `X-ROAR-Protocol: 1.0` header on upgrade.
- Neither MCP nor A2A support WebSocket -- this is a ROAR differentiator.

Two modes:

**One-shot (send and close):**
```python
response = await websocket_send(config, message)
```

**Persistent connection:**
```python
conn = WebSocketConnection(config)
await conn.connect()
response = await conn.send(message)
async for event in conn.events():
    process(event)
await conn.close()
```

### 4.6 stdio Transport

**Implementation:** `sdk/transports/stdio.py`

- The `url` field in `ConnectionConfig` is treated as a shell command.
- Uses `asyncio.create_subprocess_exec` (not `shell=True`) to prevent injection.
- Command is split via `shlex.split` for safe argument parsing.
- Wire-compatible with MCP stdio (newline-delimited JSON).

Two modes:

**One-shot (spawn, send, collect, exit):**
```python
response = await stdio_send(config, message)
```

**Persistent subprocess:**
```python
conn = StdioConnection("python tool_server.py")
await conn.start()
response = await conn.send(message)
await conn.stop()
```

---

## 5. Layer 4: Exchange

**Implementation:** `src/prowlrbot/protocols/roar.py` (ROARMessage, MessageIntent)

### 5.1 MessageIntent

Every ROAR message declares what the sender wants the receiver to do:

```python
class MessageIntent(StrEnum):
    EXECUTE   = "execute"    # Agent -> Tool (run this)
    DELEGATE  = "delegate"   # Agent -> Agent (do this task)
    UPDATE    = "update"     # Agent -> IDE (status update)
    ASK       = "ask"        # Agent -> Human (need input)
    RESPOND   = "respond"    # Response to any of the above
    NOTIFY    = "notify"     # One-way notification
    DISCOVER  = "discover"   # Discovery request
```

### 5.2 ROARMessage

The universal message envelope:

```python
class ROARMessage(BaseModel):
    roar: str                    # Protocol version, "1.0"
    id: str                      # Auto-generated "msg_<hex10>"
    from_identity: AgentIdentity # Aliased as "from" in JSON
    to_identity: AgentIdentity   # Aliased as "to" in JSON
    intent: MessageIntent
    payload: Dict[str, Any]      # Arbitrary data
    context: Dict[str, Any]      # Metadata (protocol, in_reply_to, etc.)
    auth: Dict[str, Any]         # Signing data (timestamp, signature)
    timestamp: float             # Unix timestamp
```

JSON wire format (aliases applied):

```json
{
  "roar": "1.0",
  "id": "msg_a1b2c3d4e5",
  "from": {
    "did": "did:roar:agent:sender-abc123",
    "display_name": "sender",
    "agent_type": "agent",
    "capabilities": ["code-review"],
    "version": "1.0"
  },
  "to": {
    "did": "did:roar:agent:receiver-def456",
    "display_name": "receiver",
    "agent_type": "agent",
    "capabilities": [],
    "version": "1.0"
  },
  "intent": "delegate",
  "payload": {"task": "review this PR"},
  "context": {"protocol": "roar"},
  "auth": {
    "timestamp": 1741694400.0,
    "signature": "hmac-sha256:abc123..."
  },
  "timestamp": 1741694400.0
}
```

### 5.3 HMAC Signing

Messages are signed with HMAC-SHA256 over a canonical JSON body that covers
all security-relevant fields.

**Canonical signing body (sorted keys):**

```json
{
  "id": "<message-id>",
  "from": "<sender-did>",
  "to": "<receiver-did>",
  "intent": "<intent>",
  "payload": { ... },
  "context": { ... },
  "timestamp": <auth-timestamp>
}
```

**Sign:**

```python
msg.sign(secret)
# Sets auth.timestamp to current time
# Sets auth.signature to "hmac-sha256:<hex-digest>"
```

**Verify:**

```python
msg.verify(secret, max_age_seconds=300.0)
# Returns True if:
#   1. Signature prefix is "hmac-sha256:"
#   2. Message age is within max_age_seconds (replay protection)
#   3. HMAC digest matches (constant-time comparison)
```

### 5.4 Ed25519 Signing

For cross-organization trust where shared HMAC secrets are impractical.

**Implementation:** `sdk/crypto/ed25519.py` -- `KeyPair`, `Ed25519Signer`

```python
from prowlrbot.protocols.sdk import KeyPair, Ed25519Signer

# Generate keypair (requires PyNaCl)
kp = KeyPair.generate()
# kp.private_key -> base64url-encoded
# kp.public_key  -> base64url-encoded
# kp.did_key     -> "did:key:z6Mk..."

# Sign messages
signer = Ed25519Signer(kp)
sig = signer.sign(b"message bytes")
assert signer.verify(b"message bytes", sig)

# Sign a ROAR message dict
auth = signer.sign_message(msg_dict)
# Returns: {signature: "ed25519:<sig>", signer: "<did:key>", algorithm: "ed25519", public_key: "<b64>"}

# Verify with only a public key (no private key needed)
valid = Ed25519Signer.verify_with_public_key(b"message", sig, public_key_b64)
```

Requires: `pip install pynacl`. The `NACL_AVAILABLE` flag indicates whether
Ed25519 is operational.

### 5.5 ROARClient -- Sending Messages

**Implementation:** `sdk/client.py` -- `ROARClient`

```python
client = ROARClient(
    identity=my_identity,
    directory_url="https://hub.example.com",  # optional
    signing_secret="shared-secret",
)

# Register self with local directory
client.register(my_card)

# Discover agents
all_agents = client.discover()
reviewers = client.discover(capability="code-review")

# Local send (construct + sign, no transport)
msg = client.send(
    to_agent_id="did:roar:agent:target-abc123",
    intent=MessageIntent.DELEGATE,
    content={"task": "review this PR"},
    context={"priority": "high"},
)

# Remote send (over HTTP/WebSocket/stdio)
response = await client.send_remote(
    to_agent_id="did:roar:agent:target-abc123",
    intent=MessageIntent.DELEGATE,
    content={"task": "review this PR"},
    transport=TransportType.WEBSOCKET,  # optional override
)

# Build connection config for a target agent
config = client.connect("did:roar:agent:target-abc123", TransportType.HTTP)

# Stream events from a remote agent
async with client.stream_events(
    agent_id="did:roar:agent:target-abc123",
    callback=lambda event: print(event),
    filter_types=["reasoning", "tool_call"],
) as _:
    await asyncio.sleep(30)  # events arrive via callback
```

### 5.6 ROARServer -- Receiving Messages

**Implementation:** `sdk/server.py` -- `ROARServer`

```python
server = ROARServer(
    identity=my_identity,
    host="127.0.0.1",
    port=8089,
    description="Code review agent",
    skills=["code-review", "testing"],
    channels=["console"],
    signing_secret="shared-secret",
)

# Register intent handlers (decorator or direct call)
@server.on(MessageIntent.DELEGATE)
async def handle_delegate(msg: ROARMessage) -> ROARMessage:
    result = await do_work(msg.payload)
    return ROARMessage(
        **{"from": server.identity, "to": msg.from_identity},
        intent=MessageIntent.RESPOND,
        payload={"result": result},
    )

# Dispatch manually (used by router internals)
response = await server.handle_message(incoming_msg)

# Get agent card for directory registration
card = server.get_card()
server.register_with_directory(directory)

# Emit streaming events
await server.emit(StreamEvent(type="reasoning", data={"step": 1}))
```

### 5.7 FastAPI Router

**Implementation:** `sdk/router.py` -- `create_roar_router`

Mounts three endpoints on a FastAPI app:

| Method    | Path          | Description                          |
|-----------|---------------|--------------------------------------|
| POST      | /roar/message | Receive a ROAR message, return response |
| WebSocket | /roar/ws      | Bidirectional message exchange       |
| GET       | /roar/events  | SSE event stream                     |
| GET       | /roar/health  | Health check (no auth)               |

```python
from prowlrbot.protocols.sdk import create_roar_router

router = create_roar_router(
    server=my_server,
    rate_limit=60,        # max requests per minute (token bucket), 0 = disabled
    auth_token="secret",  # Bearer token for WS/SSE auth, "" = disabled
)
app.include_router(router)
```

Router security features:

- **Rate limiting:** In-memory token bucket. Returns HTTP 429 when exhausted.
  Applied to POST, WebSocket frames, and SSE connections.
- **HMAC verification:** When the server has a signing secret, incoming
  messages with invalid signatures are rejected with HTTP 403.
- **Replay protection:** Message IDs are tracked in a bounded set (max 10,000
  entries, 10 minute TTL). Duplicate messages return HTTP 409.
- **WebSocket auth:** When `auth_token` is set, the first WS frame must be
  `{"type": "auth", "token": "<bearer-token>"}`. Invalid tokens close the
  connection with code 4001.
- **SSE auth:** Bearer token via `Authorization` header.
- **SSE connection limit:** Maximum 100 concurrent SSE connections (returns
  HTTP 503 when exceeded).
- **Error sanitization:** Internal errors are mapped to generic messages to
  prevent information leakage.

---

## 6. Layer 5: Stream

**Implementation:** `src/prowlrbot/protocols/roar.py` (StreamEvent, StreamEventType)
and `src/prowlrbot/protocols/sdk/streaming/`

### 6.1 StreamEvent

```python
class StreamEvent(BaseModel):
    type: StreamEventType
    source: str          # DID of event source
    session_id: str
    data: Dict[str, Any]
    timestamp: float
```

### 6.2 Event Types

```python
class StreamEventType(StrEnum):
    TOOL_CALL      = "tool_call"
    MCP_REQUEST    = "mcp_request"
    REASONING      = "reasoning"
    TASK_UPDATE    = "task_update"
    MONITOR_ALERT  = "monitor_alert"
    AGENT_STATUS   = "agent_status"
    CHECKPOINT     = "checkpoint"
    WORLD_UPDATE   = "world_update"  # AgentVerse
```

### 6.3 EventBus (In-process Pub/Sub)

**Implementation:** `sdk/streaming/local.py` -- `EventBus`

Zero-dependency, in-process event bus using `asyncio.Queue` per subscriber.

```python
from prowlrbot.protocols.sdk import EventBus, StreamFilter

bus = EventBus(max_buffer=1000, replay_size=100)

# Subscribe with filter
sub = bus.subscribe(
    filter_spec=StreamFilter(
        event_types=["reasoning", "tool_call"],
        source_dids=["did:roar:agent:planner-abc123"],
        session_ids=["session-1"],
    ),
    buffer_size=500,   # per-subscriber queue size
    replay=True,       # pre-fill with matching events from replay buffer
)

# Publish
delivered = await bus.publish(event)           # Returns subscriber count
delivered = await bus.publish_many([e1, e2])   # Batch publish

# Consume (async iterator)
async for event in sub:
    process(event)

# Or poll
event = await sub.get(timeout=5.0)  # Returns None on timeout

# Stats
sub.events_received   # Counter
sub.events_dropped    # Counter (when queue is full)
bus.subscriber_count  # Active subscribers
bus.event_count       # Total events published

# Cleanup
sub.close()
bus.close_all()
```

**Backpressure behavior:** When a subscriber's queue is full, the oldest event
is dropped and the new event is enqueued. The `events_dropped` counter is
incremented.

**Replay buffer:** The bus maintains a bounded deque of recent events (default
100). Late subscribers can opt into replay to catch up on missed events.

### 6.4 StreamFilter

All filter fields are AND-combined. An event must match every non-empty filter
field to be delivered.

```python
@dataclass
class StreamFilter:
    event_types: List[str]   # empty = all types
    source_dids: List[str]   # empty = all sources
    session_ids: List[str]   # empty = all sessions
```

### 6.5 AIMD Backpressure Controller

**Implementation:** `sdk/streaming/backpressure.py` -- `AIMDController`

TCP-style congestion control adapted for event streaming. Adjusts the send
rate based on consumer feedback.

```python
from prowlrbot.protocols.sdk import AIMDController

ctrl = AIMDController(
    rate=100.0,                  # initial events/sec
    min_rate=1.0,                # floor
    max_rate=10000.0,            # ceiling
    additive_increase=10.0,      # added per success window
    multiplicative_decrease=0.5, # multiplied on drop
    window_size=50,              # events per adjustment window
)

ctrl.on_success()    # Record successful delivery
ctrl.on_drop()       # Record a drop (triggers multiplicative decrease)

ctrl.rate            # Current events/sec
ctrl.delay           # Seconds between events (1/rate)
ctrl.stats           # {rate, delay_ms, successes, drops, last_adjustment}
ctrl.reset()         # Return to initial state
```

Behavior:
- On success window (50 consecutive): `rate += 10.0` (linear)
- On drop: `rate *= 0.5` (exponential backoff), success counter resets
- Rate is clamped to `[min_rate, max_rate]`

### 6.6 Idempotency Guard

**Implementation:** `sdk/streaming/dedup.py` -- `IdempotencyGuard`

Bounded LRU-style set that prevents duplicate event processing.

```python
from prowlrbot.protocols.sdk import IdempotencyGuard

guard = IdempotencyGuard(max_keys=10000, ttl_seconds=300.0)

if guard.is_duplicate("event-id-123"):
    skip()
else:
    process()

guard.mark_seen("event-id-456")  # Explicit mark
guard.size                        # Number of tracked keys
guard.clear()                     # Clear all
```

Keys are evicted after TTL or when the set exceeds `max_keys` (oldest first).

---

## 7. Protocol Adapters

**Implementation:** `src/prowlrbot/protocols/sdk/adapters/`

ROAR adapters provide bidirectional translation between ROAR and external
protocol wire formats. Auto-detection routes incoming messages to the correct
adapter without configuration.

### 7.1 Auto-Detection

**Implementation:** `sdk/adapters/detect.py` -- `detect_protocol`

```python
from prowlrbot.protocols.sdk.adapters import detect_protocol, ProtocolType

protocol = detect_protocol(incoming_json)
# Returns: ProtocolType.ROAR | ProtocolType.MCP | ProtocolType.A2A | ProtocolType.UNKNOWN
```

Detection heuristics (priority order):

1. **ROAR native:** Has `"roar"` and `"intent"` fields.
2. **A2A:** Has `"jsonrpc": "2.0"` and method starts with `"tasks/"` or `"agent/"`.
3. **MCP:** Has `"jsonrpc": "2.0"` and method starts with `"tools/"`, `"resources/"`, `"prompts/"`, `"completion/"`, `"initialize"`, or `"notifications/"`.
4. **A2A result:** JSON-RPC result with `"status"` and `"id"` fields.
5. **MCP result:** JSON-RPC result with `"tools"` or `"resources"` fields.
6. **A2A envelope:** Has `"status"`, `"id"`, and `"artifacts"` fields.
7. **UNKNOWN:** None of the above matched.

### 7.2 MCP Adapter

**Implementation:** `sdk/adapters/mcp.py` -- `MCPFullAdapter`

Covers the full MCP tool lifecycle:

| MCP Method          | ROAR Intent   |
|---------------------|---------------|
| tools/list          | DISCOVER      |
| tools/call          | EXECUTE       |
| resources/list      | DISCOVER      |
| resources/read      | EXECUTE       |
| prompts/list        | DISCOVER      |
| prompts/get         | EXECUTE       |
| completion/complete | ASK           |
| initialize          | DISCOVER      |

```python
from prowlrbot.protocols.sdk.adapters import MCPFullAdapter

# MCP -> ROAR
roar_msg = MCPFullAdapter.mcp_to_roar(mcp_json_rpc, source_identity, target_identity)

# ROAR -> MCP
mcp_json_rpc = MCPFullAdapter.roar_to_mcp(roar_msg, method_override="tools/call")

# MCP result -> ROAR response
roar_response = MCPFullAdapter.mcp_result_to_roar(mcp_result, original_request, server_identity)

# ROAR response -> MCP result
mcp_result = MCPFullAdapter.roar_to_mcp_result(roar_response)
```

Payload convention for MCP-originated messages:

```json
{
  "mcp_method": "tools/call",
  "mcp_params": {"name": "shell", "arguments": {"command": "ls"}},
  "mcp_id": 42
}
```

Context always includes `{"protocol": "mcp"}`.

### 7.3 A2A Adapter

**Implementation:** `sdk/adapters/a2a.py` -- `A2AFullAdapter`

Covers A2A v0.3.0 task lifecycle:

| A2A Operation       | ROAR Intent   |
|---------------------|---------------|
| tasks/send          | DELEGATE      |
| tasks/get           | ASK           |
| tasks/cancel        | NOTIFY        |
| tasks/sendSubscribe | DELEGATE (streaming) |
| Agent Card          | AgentCard     |

A2A task state mapping to ROAR-compatible status:

```
submitted       -> pending
working         -> running
input-required  -> blocked
completed       -> completed
failed          -> failed
canceled        -> cancelled
rejected        -> rejected
```

```python
from prowlrbot.protocols.sdk.adapters import A2AFullAdapter

# A2A task send -> ROAR
roar_msg = A2AFullAdapter.a2a_send_to_roar(a2a_request, source, target)

# ROAR -> A2A task send
a2a_request = A2AFullAdapter.roar_to_a2a_send(roar_msg, task_id="task-123")

# A2A task result -> ROAR response
roar_response = A2AFullAdapter.a2a_task_to_roar_response(a2a_task, original, server)

# A2A SSE event -> ROAR StreamEvent
stream_event = A2AFullAdapter.a2a_sse_to_stream_event(sse_data, source_did, session_id)

# Agent Card conversion (bidirectional)
roar_card = A2AFullAdapter.a2a_card_to_roar(a2a_card_dict)
a2a_card = A2AFullAdapter.roar_card_to_a2a(roar_card)
```

### 7.4 Legacy Adapters

The core `roar.py` module also provides simpler adapter classes for basic
translation:

- `MCPAdapter.mcp_to_roar(tool_name, params, from_agent)` -- Tool call to ROAR
- `MCPAdapter.roar_to_mcp(msg)` -- ROAR to MCP tool call dict
- `A2AAdapter.a2a_task_to_roar(task, from_agent, to_agent)` -- Task to ROAR
- `A2AAdapter.roar_to_a2a(msg)` -- ROAR to A2A task dict

These are retained for backward compatibility. New code should use the full
adapters (`MCPFullAdapter`, `A2AFullAdapter`).

---

## 8. Security

### 8.1 Authentication Methods

| Method   | Use case                | Implementation status |
|----------|------------------------|-----------------------|
| HMAC-SHA256 | Shared-secret signing | Implemented |
| Ed25519  | Cross-org trust        | Implemented (requires PyNaCl) |
| JWT      | Bearer token auth      | Header support only |
| mTLS     | Mutual TLS             | Planned |
| API Key  | Hub authentication     | Implemented |

### 8.2 Message Signing

All messages SHOULD be signed in production. The `ROARClient` signs
automatically when `signing_secret` is provided. Unsigned messages trigger a
warning log.

Signing covers these fields (canonical JSON, sorted keys):
- `id` -- Message ID
- `from` -- Sender DID
- `to` -- Receiver DID
- `intent` -- Message intent
- `payload` -- Full payload dict
- `context` -- Full context dict
- `timestamp` -- Auth timestamp (set at signing time)

### 8.3 Replay Protection

- Message timestamps are checked against `max_age_seconds` (default 300s / 5 min).
- The router tracks seen message IDs in a bounded set (10,000 max, 10 min TTL).
- Duplicate messages are rejected with HTTP 409.

### 8.4 Rate Limiting

The `TokenBucket` rate limiter uses an in-memory token bucket algorithm:
- Configurable max tokens (burst capacity) and refill rate.
- Applied per-router (not per-client) in the current implementation.
- Returns HTTP 429 when tokens are exhausted.

### 8.5 Input Validation

The Hub server validates all input fields:
- String fields: max 500 characters
- List fields: max 50 items
- Agent limit: max 10,000 agents per hub
- Constant-time string comparison for API keys and tokens

### 8.6 Transport Security

- **HTTP:** HMAC auth in message body; JWT as Bearer header. HTTPS recommended.
- **WebSocket:** Auth frame required when `auth_token` is configured.
  Invalid tokens close with code 4001.
- **stdio:** Uses `create_subprocess_exec` (not `shell=True`) to prevent
  command injection. Commands parsed via `shlex.split`.

---

## 9. SDK Reference

### 9.1 Package Structure

```
src/prowlrbot/protocols/
    roar.py                      # Core types: AgentIdentity, ROARMessage, etc.
    acp_server.py                # ACP JSON-RPC 2.0 server
    a2a_server.py                # A2A protocol server
    sdk/
        __init__.py              # Public API re-exports
        client.py                # ROARClient
        server.py                # ROARServer
        router.py                # FastAPI router (create_roar_router)
        crypto/
            ed25519.py           # KeyPair, Ed25519Signer
        identity/
            did_document.py      # DIDDocument (W3C DID Core)
            did_key.py           # DIDKeyMethod (ephemeral crypto identity)
            did_web.py           # DIDWebMethod (persistent DNS identity)
            delegation.py        # CapabilityDelegation, DelegationToken, AutonomyLevel
        discovery/
            cache.py             # DiscoveryCache (TTL + LRU)
            hub.py               # HubClient (HTTP client)
            hub_server.py        # create_hub_router (FastAPI server)
            sqlite_directory.py  # SQLiteAgentDirectory (persistent)
        streaming/
            local.py             # EventBus, StreamFilter, Subscription
            backpressure.py      # AIMDController
            dedup.py             # IdempotencyGuard
        transports/
            __init__.py          # send_message dispatcher
            http.py              # HTTP POST + SSE
            websocket.py         # WebSocket (persistent + one-shot)
            stdio.py             # Subprocess stdio (persistent + one-shot)
        adapters/
            detect.py            # detect_protocol, ProtocolType
            mcp.py               # MCPFullAdapter
            a2a.py               # A2AFullAdapter
```

### 9.2 Public API (sdk/__init__.py)

All public symbols are re-exported from `prowlrbot.protocols.sdk`:

```python
from prowlrbot.protocols.sdk import (
    # Core types
    AgentIdentity, AgentCard, AgentCapability,
    AgentDirectory, DiscoveryEntry,
    TransportType, ConnectionConfig,
    ROARMessage, MessageIntent,
    StreamEvent, StreamEventType,
    # Protocol adapters (legacy)
    MCPAdapter, A2AAdapter,
    # SDK classes
    ROARClient, ROARServer, create_roar_router,
    # Streaming
    EventBus, StreamFilter, Subscription,
    AIMDController, IdempotencyGuard,
    # Crypto
    KeyPair, Ed25519Signer, NACL_AVAILABLE,
    # Identity
    DIDDocument, DIDKeyMethod, DIDWebMethod,
    CapabilityDelegation, DelegationToken, AutonomyLevel,
)
```

### 9.3 Dependencies

| Dependency  | Required | Used for                       |
|-------------|----------|--------------------------------|
| pydantic    | Yes      | Core types, validation         |
| httpx       | Yes      | HTTP transport, Hub client     |
| websockets  | Yes      | WebSocket transport            |
| fastapi     | Yes      | Router, Hub server             |
| pynacl      | Optional | Ed25519 (did:key, signing)     |
| base58      | Optional | did:key encoding (falls back to hex) |
