# ROAR Protocol — Comprehensive Design & Implementation Plan

**Date**: 2026-03-10
**Status**: Research Complete → Implementation Planning
**Authors**: ProwlrBot Team

---

## Executive Summary

ROAR (Real-time Open Agent Runtime) is a five-layer protocol for agent identity, discovery, communication, and streaming. This document synthesizes research across four domains — protocol landscape analysis, identity & discovery architecture, transport & streaming mechanisms, and codebase audit — into an actionable implementation plan.

**Key Finding**: The ROAR specification (6 documents) is 100% complete, but implementation is ~35-40% done with **critical Python/TypeScript SDK divergence** that must be resolved before any further development.

---

## 1. Protocol Landscape Analysis

### 1.1 Existing Protocols

| Protocol | Owner | Focus | Transport | Maturity | Adoption |
|----------|-------|-------|-----------|----------|----------|
| **MCP** | Anthropic | Tool integration | stdio, SSE, Streamable HTTP | Production (v2025-11-25) | Very High |
| **A2A** | Google/Linux Foundation | Agent collaboration | HTTP+SSE, Push Notifications | Production (v0.3.0, proto3) | Very High (22K stars) |
| **ACP** | agentscope-ai/OpenClaw | IDE-agent comm | HTTP, stdio | Early (v0.1) | Low |
| **ANP** | Community | Agent networking | HTTP/WebSocket | Draft | Very Low |
| **DIDComm** | W3C/DIF | Secure messaging | HTTP, WebSocket, Bluetooth | Spec Complete | Medium |

### 1.2 Standards Bodies

- **AAIF** (Agentic AI Foundation): Founded March 2026, Linux Foundation. TC: Anthropic (chair), Microsoft (co-chair), Google, OpenAI, AWS, Block, Bloomberg, Cloudflare. MCP is its first project. Working groups on "Identity & Trust" and "Workflows & Process Integration" will define standards ROAR must adopt.
- **W3C**: DIDs (v1.0 Recommendation), Verifiable Credentials (v2.0 Recommendation), DIDComm (v2.1). AI Agent Protocol Community Group uses ANP white paper.
- **IETF**: BANDAID draft (`draft-mozleywilliams-dnsop-dnsaid-01`) — DNS-based agent discovery, already MCP-aware. Validates ROAR Tier 2 approach.
- **FIPA**: Legacy ACL/interaction protocols (IEEE); valuable lessons on what NOT to do (over-specification, academic focus, no reference implementations).

### 1.3 Gap Analysis — Why ROAR?

| Gap | MCP | A2A | ACP | ROAR Fills? |
|-----|-----|-----|-----|-------------|
| Agent-to-agent delegation | No | Yes | No | Yes |
| Tool invocation | Yes | No | Partial | Yes |
| IDE integration | Partial | No | Yes | Yes |
| Decentralized identity | No | No | No | Yes (W3C DIDs) |
| Agent discovery | No | Agent Cards | No | Yes (federated) |
| Real-time streaming | SSE only | SSE | No | Yes (multi-transport) |
| Cross-protocol bridge | N/A | N/A | N/A | Yes (adapters) |
| Graduated autonomy | No | No | No | Yes |
| Virtual world events | No | No | No | Yes (AgentVerse) |

**ROAR's unique value**: First protocol to unify tool invocation (MCP), agent delegation (A2A), and IDE communication (ACP) under a single message format with decentralized identity and graduated autonomy.

---

## 2. Identity & Discovery Architecture

### 2.1 Identity — Recommendations

#### Signing Algorithm: Ed25519

| Algorithm | Key Size | Sig Speed | Verify Speed | Deterministic | Standard |
|-----------|----------|-----------|--------------|---------------|----------|
| **Ed25519** | 32 bytes | ~76μs | ~227μs | Yes | RFC 8032 |
| secp256k1 | 32 bytes | ~37μs | ~80μs | No* | Bitcoin/Ethereum |
| HMAC-SHA256 | Variable | ~1μs | ~1μs | Yes | RFC 2104 |

**Decision**: Ed25519 as default asymmetric signing (agent-to-agent). HMAC-SHA256 retained for pre-shared-secret scenarios (backward compat, local tool calls).

#### DID Strategy: Tiered

| Tier | DID Method | Use Case | Lifecycle |
|------|-----------|----------|-----------|
| **Ephemeral** | `did:key` | Short-lived tools, session agents | Auto-expire |
| **Persistent** | `did:web` | Long-running agents, published services | DNS-anchored |
| **Self-Sovereign** | `did:roar` | ProwlrBot-native agents | Directory-registered |

Current `did:roar:<type>:<slug>-<uuid8>` format is retained for ProwlrBot-native agents. Interop with `did:key` and `did:web` added for external agents.

#### Capability Delegation: Akta-Style

```python
class CapabilityDelegation(BaseModel):
    """Delegated capability with constraints."""
    capability: str           # e.g. "file:write"
    delegated_by: str         # DID of delegator
    delegated_to: str         # DID of delegate
    usage_limit: int = -1     # -1 = unlimited
    can_delegate: bool = False  # Can further delegate?
    expires_at: float = 0     # 0 = no expiry
    scope: dict = {}          # Additional constraints
```

Maps directly to ProwlrBot's graduated autonomy model:
- **Watch**: `usage_limit=0, can_delegate=False` (observe only)
- **Guide**: `usage_limit=N, can_delegate=False` (limited actions with approval)
- **Delegate**: `usage_limit=-1, can_delegate=False` (full execution, no re-delegation)
- **Autonomous**: `usage_limit=-1, can_delegate=True` (full execution + can delegate)

### 2.2 Discovery — Four-Tier Hybrid Architecture

```
┌─────────────────────────────────────────────────┐
│ Tier 1: Local Cache (sub-ms)                    │
│  In-memory AgentDirectory, LRU eviction         │
├─────────────────────────────────────────────────┤
│ Tier 2: DNS/SVCB (50-200ms)                     │
│  _roar._tcp.example.com SVCB records            │
│  did:web resolution via .well-known/did.json    │
├─────────────────────────────────────────────────┤
│ Tier 3: Federated Hub (200-1000ms)              │
│  HTTP API for cross-org agent lookup             │
│  Hub-to-hub gossip for eventual consistency      │
├─────────────────────────────────────────────────┤
│ Tier 4: DHT + mDNS Fallback (1-5s)             │
│  libp2p Kademlia DHT for global discovery        │
│  mDNS/DNS-SD for LAN-local agents              │
└─────────────────────────────────────────────────┘
```

**Implementation priority**: Tier 1 (done) → Tier 3 (next) → Tier 2 → Tier 4

---

## 3. Transport & Streaming Architecture

### 3.1 Transport Selection Matrix

| Transport | Use Case | Latency | Throughput | Streaming |
|-----------|----------|---------|------------|-----------|
| **HTTP** | Request-response, REST APIs | Medium | Medium | SSE only |
| **WebSocket** | Real-time bidirectional | Low | High | Native |
| **gRPC** | Internal microservices | Very Low | Very High | Native |
| **stdio** | Local tools, MCP compat | Lowest | Low | Line-delimited |

**Default selection**:
- External agents: WebSocket (with HTTP fallback)
- Internal services: gRPC
- LLM streaming: SSE (for HTTP) or WebSocket frames
- Local tools: stdio (MCP compatibility)

### 3.2 Streaming Architecture

#### Pub/Sub: NATS JetStream (Recommended)

| Feature | NATS JetStream | Redis Streams | Kafka |
|---------|----------------|---------------|-------|
| Latency | Sub-ms | ~1ms | 2-5ms |
| Persistence | Optional | Yes | Yes |
| Ordering | Per-subject | Per-stream | Per-partition |
| Complexity | Low | Medium | High |
| Memory | ~50MB | ~100MB | ~500MB+ |

NATS JetStream selected for: lowest latency, optional persistence, subject-based routing (maps to DID-based topics), embedded mode (no external dependency required).

#### Backpressure: AIMD (Additive Increase / Multiplicative Decrease)

```
on_success: rate = rate + α (additive increase, α = 1)
on_congestion: rate = rate × β (multiplicative decrease, β = 0.5)
on_failure: rate = max(rate × β, min_rate)
```

- Starts at 100 events/sec
- Increases by 1 event/sec per successful batch
- Halves on buffer overflow or consumer lag
- Minimum floor: 10 events/sec

#### Delivery Guarantees

- **At-least-once** with idempotency keys (message ID)
- Server-side deduplication window: 5 minutes
- Consumer acknowledges after processing (not receipt)
- Dead letter queue for messages failing after 3 retries

---

## 4. Codebase Audit — Critical Gaps

### 4.1 Python/TypeScript SDK Divergence (CRITICAL)

The two SDKs implement fundamentally different type systems:

#### MessageIntent Mismatch

| Python (Canonical) | TypeScript (Divergent) |
|--------------------|-----------------------|
| `execute` | `tool_call` |
| `respond` | `response`, `tool_result` |
| `delegate` | *(missing)* |
| `update` | *(missing)* |
| `ask` | `query` |
| `notify` | *(missing)* |
| `discover` | `negotiate` |
| *(none)* | `heartbeat` |
| *(none)* | `error` |
| *(none)* | `stream_start/data/end` |

#### AgentIdentity Mismatch

| Field | Python | TypeScript |
|-------|--------|------------|
| ID | `did` (W3C DID) | `agent_id` (opaque string) |
| Capabilities | `list[str]` | `AgentCapability[]` (objects) |
| Type | `agent_type` | *(missing)* |
| Version | `version` | *(missing)* |
| Public key | *(missing)* | `public_key` |
| Created | *(missing)* | `created_at` |

#### ROARMessage Mismatch

| Field | Python | TypeScript |
|-------|--------|------------|
| Sender | `from_identity: AgentIdentity` | `from_agent: string` |
| Receiver | `to_identity: AgentIdentity` | `to_agent: string` |
| Content | `payload: dict` | `content: unknown` |
| Auth | `auth: dict` | `signature?: string` |
| Context | `context: dict` | `metadata?: Record<string, unknown>` |
| Protocol version | `roar: str` | *(missing)* |

#### Signing Incompatibility

- **Python** signs: `{id, intent, payload}` → `hmac-sha256:<hex>`
- **TypeScript** signs: `{id, from_agent, to_agent, intent, content, timestamp}` → raw hex

**Cross-SDK messages will fail signature verification.**

### 4.2 Implementation Completeness

| Component | Python | TypeScript | Spec |
|-----------|--------|------------|------|
| Identity (Layer 1) | 80% | 40% | 100% |
| Discovery (Layer 2) | 70% | 50% | 100% |
| Connect (Layer 3) | 30% | 20% | 100% |
| Exchange (Layer 4) | 60% | 50% | 100% |
| Stream (Layer 5) | 20% | 15% | 100% |
| MCP Adapter | 60% | 50% | 100% |
| A2A Adapter | 50% | 50% | 100% |
| ACP Adapter | 10% | 0% | 100% |
| Transport (actual) | 0% | 0% | 100% |
| Streaming (actual) | 0% | 0% | 100% |

### 4.3 What's Missing

1. **No actual transport**: `send()` constructs messages but doesn't transmit them
2. **No WebSocket/gRPC**: Only data models exist; no connection handling
3. **No streaming**: `stream_events()` is a no-op placeholder
4. **No Ed25519**: Only HMAC-SHA256 implemented
5. **No federation**: Discovery is local-only
6. **No capability delegation**: Autonomy model not wired to protocol
7. **No ACP adapter**: Stub only

---

## 5. Unified Type System (Resolution)

### 5.1 Canonical Types (Python = Source of Truth)

Python SDK is closer to the spec. TypeScript must be aligned to Python.

#### MessageIntent (unified)

```typescript
export enum MessageIntent {
  EXECUTE = "execute",       // Agent → Tool (was: tool_call)
  DELEGATE = "delegate",     // Agent → Agent (new)
  UPDATE = "update",         // Agent → IDE (new)
  ASK = "ask",               // Agent → Human (was: query)
  RESPOND = "respond",       // Reply (was: response)
  NOTIFY = "notify",         // One-way (new)
  DISCOVER = "discover",     // Discovery (was: negotiate)
}
```

Remove `tool_result`, `heartbeat`, `error`, `stream_start/data/end` from TypeScript — these are handled by:
- `tool_result` → `RESPOND` with `context.in_reply_to` pointing to `EXECUTE` message
- `heartbeat` → `StreamEventType.AGENT_STATUS`
- `error` → `RESPOND` with `payload.error` field
- `stream_*` → `StreamEvent` system (Layer 5)

#### AgentIdentity (unified)

```typescript
export interface AgentIdentity {
  did: string;                // W3C DID format (was: agent_id)
  display_name: string;
  agent_type: "agent" | "tool" | "human" | "ide";
  capabilities: string[];    // Simple strings (was: AgentCapability[])
  version: string;
  public_key?: string;       // Optional Ed25519 public key (keep from TS)
}
```

#### ROARMessage (unified)

```typescript
export interface ROARMessage {
  roar: string;              // Protocol version (new)
  id: string;
  from_identity: AgentIdentity;  // Full identity (was: from_agent string)
  to_identity: AgentIdentity;    // Full identity (was: to_agent string)
  intent: MessageIntent;
  payload: Record<string, unknown>;  // Renamed from content
  context: Record<string, unknown>;  // Renamed from metadata
  auth: {                    // Structured auth (was: signature string)
    signature?: string;
    signer?: string;
    timestamp?: string;
  };
  timestamp: number;         // Unix epoch (was: ISO string)
}
```

#### Signing (unified)

Both SDKs must sign the same canonical body:

```
canonical = JSON.stringify({id, intent, payload}, sort_keys/Object.keys().sort())
signature = HMAC-SHA256(secret, canonical)
format = "hmac-sha256:<hex>"
```

#### StreamEventType (unified)

```typescript
export enum StreamEventType {
  TOOL_CALL = "tool_call",
  MCP_REQUEST = "mcp_request",
  REASONING = "reasoning",
  TASK_UPDATE = "task_update",
  MONITOR_ALERT = "monitor_alert",
  AGENT_STATUS = "agent_status",
  CHECKPOINT = "checkpoint",
  WORLD_UPDATE = "world_update",
}
```

TypeScript's `started/data/progress/completed/error/cancelled` are transport-level concerns, not application events. They move to a separate `StreamTransportState` enum for connection management.

---

## 6. Implementation Plan

### Phase 1: Type Unification (Priority: CRITICAL)

**Goal**: Python and TypeScript SDKs speak the same protocol.

| Task | Effort | Files |
|------|--------|-------|
| Align TS `MessageIntent` to Python's 7 values | 2h | `types.ts` |
| Align TS `AgentIdentity` to use `did` + `agent_type` | 2h | `types.ts`, `identity.ts` |
| Align TS `ROARMessage` to use `from_identity`/`to_identity`/`payload`/`context`/`auth` | 3h | `types.ts`, `message.ts` |
| Align TS `StreamEventType` to Python's 8 values | 1h | `types.ts` |
| Unify signing canonical body | 2h | `message.ts` |
| Update TS adapters for new types | 2h | `adapters.ts` |
| Cross-SDK signing verification test | 2h | New test files |
| Add `public_key` field to Python `AgentIdentity` | 30m | `roar.py` |

**Estimated**: 2 days

### Phase 2: Transport Layer (Priority: HIGH)

**Goal**: Messages actually get sent over the wire.

| Task | Effort | Files |
|------|--------|-------|
| HTTP transport (aiohttp/httpx client + FastAPI routes) | 4h | `sdk/transports/http.py` |
| WebSocket transport (websockets library) | 6h | `sdk/transports/websocket.py` |
| stdio transport (asyncio subprocess) | 2h | `sdk/transports/stdio.py` |
| Transport dispatcher (route by `ConnectionConfig`) | 2h | `sdk/transports/__init__.py` |
| Wire `ROARClient.send()` to actual transport | 2h | `sdk/client.py` |
| Wire `ROARServer` to FastAPI endpoint | 3h | `sdk/server.py` |
| TS HTTP transport (fetch/node:http) | 3h | `transports/http.ts` |
| TS WebSocket transport (ws library) | 4h | `transports/websocket.ts` |

**Estimated**: 4 days

### Phase 3: Streaming (Priority: HIGH)

**Goal**: Real-time event streaming works end-to-end.

| Task | Effort | Files |
|------|--------|-------|
| NATS JetStream integration (optional dep) | 6h | `sdk/streaming/nats.py` |
| In-process event bus (no external deps) | 3h | `sdk/streaming/local.py` |
| SSE streaming endpoint (FastAPI) | 3h | `sdk/streaming/sse.py` |
| WebSocket streaming (extend WS transport) | 2h | `sdk/streaming/ws.py` |
| AIMD backpressure controller | 2h | `sdk/streaming/backpressure.py` |
| Idempotency key deduplication | 1h | `sdk/streaming/dedup.py` |
| Wire `ROARClient.stream_events()` | 2h | `sdk/client.py` |

**Estimated**: 3 days

### Phase 4: Identity Enhancement (Priority: MEDIUM)

**Goal**: Ed25519 signing, capability delegation, Verifiable Credentials.

| Task | Effort | Files |
|------|--------|-------|
| Ed25519 keypair generation (PyNaCl) | 2h | `sdk/crypto/ed25519.py` |
| Ed25519 message signing/verification | 3h | `sdk/crypto/signing.py` |
| DID Document generation | 2h | `sdk/identity/did_document.py` |
| `did:key` support (ephemeral agents) | 2h | `sdk/identity/did_key.py` |
| `did:web` support (persistent agents) | 3h | `sdk/identity/did_web.py` |
| Capability delegation model | 2h | `sdk/identity/delegation.py` |
| Wire to graduated autonomy | 2h | `sdk/identity/autonomy.py` |

**Estimated**: 3 days

### Phase 5: Discovery Enhancement (Priority: MEDIUM)

**Goal**: Federated discovery beyond local in-memory.

| Task | Effort | Files |
|------|--------|-------|
| Hub HTTP API (FastAPI router) | 4h | `sdk/discovery/hub.py` |
| Hub-to-hub gossip protocol | 4h | `sdk/discovery/gossip.py` |
| DNS/SVCB resolution | 3h | `sdk/discovery/dns.py` |
| TTL-based cache with LRU eviction | 2h | `sdk/discovery/cache.py` |
| mDNS/DNS-SD for LAN discovery | 3h | `sdk/discovery/mdns.py` |

**Estimated**: 3 days

### Phase 6: Backward Compatibility (Priority: MEDIUM)

**Goal**: Full adapters for MCP, A2A, and ACP.

| Task | Effort | Files |
|------|--------|-------|
| MCP adapter: full tool lifecycle (list/call/result) | 4h | `sdk/adapters/mcp.py` |
| MCP adapter: resource/prompt primitives | 3h | `sdk/adapters/mcp.py` |
| A2A adapter: Agent Card ↔ ROAR AgentCard | 2h | `sdk/adapters/a2a.py` |
| A2A adapter: Task lifecycle (submit/working/done/failed) | 3h | `sdk/adapters/a2a.py` |
| A2A adapter: SSE streaming ↔ ROAR StreamEvent | 2h | `sdk/adapters/a2a.py` |
| ACP adapter: full implementation | 4h | `sdk/adapters/acp.py` |
| Protocol auto-detection (sniff incoming format) | 2h | `sdk/adapters/detect.py` |

**Estimated**: 3 days

### Phase 7: Testing & Documentation (Priority: HIGH)

**Goal**: Comprehensive test coverage and developer documentation.

| Task | Effort | Files |
|------|--------|-------|
| Unit tests for all layers | 6h | `tests/protocols/` |
| Integration tests (cross-SDK) | 4h | `tests/protocols/integration/` |
| Conformance test suite | 4h | `tests/protocols/conformance/` |
| Developer quickstart guide | 2h | `docs/protocols/QUICKSTART.md` |
| API reference (auto-generated) | 2h | `docs/protocols/API.md` |
| Migration guide (from raw MCP/A2A) | 2h | `docs/protocols/MIGRATION.md` |

**Estimated**: 3 days

---

## 7. Implementation Order

```
Phase 1 (Type Unification) ──→ Phase 2 (Transport) ──→ Phase 3 (Streaming)
                                       │                       │
                                       ▼                       ▼
                               Phase 7 (Tests)         Phase 7 (Tests)
                                       │
                                       ▼
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
            Phase 4 (Identity)  Phase 5 (Discovery)  Phase 6 (Compat)
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       ▼
                               Phase 7 (Final Tests)
```

**Critical path**: Phase 1 → Phase 2 → Phase 3 (must be sequential)
**Parallelizable**: Phases 4, 5, 6 (after Phase 2 complete)

---

## 8. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing MCP integration | High | Adapter tests + feature flag for ROAR transport |
| Ed25519 adds PyNaCl dependency | Medium | Make it optional; fallback to HMAC |
| NATS JetStream complexity | Medium | In-process event bus as zero-dep fallback |
| TypeScript SDK rewrite scope | Medium | Automated migration script for consumers |
| gRPC requires protobuf compilation | Low | Defer gRPC to Phase 4+; HTTP/WS covers 95% |

---

## 9. Success Criteria

1. **Cross-SDK parity**: Python and TypeScript messages are byte-identical for the same input
2. **Wire protocol works**: `client.send()` transmits over HTTP/WebSocket and receives response
3. **Streaming works**: Real-time events flow from agent to consumer with backpressure
4. **MCP bridge**: Existing MCP tools work through ROAR without changes
5. **A2A bridge**: Can exchange tasks with Google A2A agents
6. **Tests**: >80% coverage on protocol code, cross-SDK conformance suite passes

---

## 10. Strategic Positioning

**ROAR is a runtime, not a competing protocol.** It bridges MCP (tools), A2A (agent collaboration), ACP (IDE), and ANP (discovery) under a unified identity and message format.

### Positioning Rules

1. **Do not compete with AAIF** — Position as complementary; adopt AAIF standards as they emerge
2. **Do not create new wire protocols** — JSON-RPC, proto3, and OpenAPI all work fine
3. **Do not repeat FIPA's mistakes** — Keep it simple, ship working code, focus on DX
4. **Do not require all protocols** — Each adapter is optional; ROAR works standalone

### Watch List

- AAIF "Identity & Trust" WG output → may define agent identity for MCP (adopt, don't compete)
- AAIF "Workflows & Process Integration" WG → may define orchestration patterns
- Whether A2A becomes an AAIF project (Google is on the TC)
- IETF BANDAID progression → validates DNS-based discovery approach
- MCP draft spec evolution beyond 2025-11-25

### Full Research

See `docs/research/2026-03-10-agent-protocol-landscape.md` for the complete protocol landscape analysis with live GitHub metrics, AAIF governance details, and FIPA historical lessons.

---

## 11. Open Questions

1. **gRPC proto definitions**: Define now or defer? (Recommendation: defer)
2. **NATS vs embedded**: Should NATS be required or optional? (Recommendation: optional with in-process fallback)
3. **DID resolution**: Self-hosted resolver or use universal-resolver? (Recommendation: self-hosted for `did:roar`, universal for others)
4. **Capability schema**: JSON Schema or custom format? (Recommendation: JSON Schema for interop)
5. **Versioning strategy**: Semver on protocol version field? (Recommendation: yes, `roar: "1.0"` → `roar: "1.1"` for backward-compatible additions)
