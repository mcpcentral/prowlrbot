# Agent Communication Protocol Landscape Research

**Date**: 2026-03-10 | **Status**: Research Complete

---

## Executive Summary — 5 Key Findings

1. **The protocol landscape is fragmented across four distinct concerns**: tool integration (MCP), agent-to-agent collaboration (A2A), workflow orchestration (ACP), and network-level discovery (ANP). No single protocol addresses all four. This fragmentation is the primary opportunity for ROAR.

2. **MCP dominates tool integration but has structural limitations**: With 7,442 stars on its spec repo and backing from the AAIF (Anthropic, Google, Microsoft, OpenAI, Amazon, Block, Bloomberg, Cloudflare), MCP is the de facto standard for LLM-to-tool communication. However, it has no native agent-to-agent communication, no agent identity system, and its "tasks" feature (added 2025-11-25) is still experimental.

3. **A2A has the strongest community momentum**: Google's A2A protocol has 22,397 stars and is now under the Linux Foundation. It solves the agent-to-agent problem with Agent Cards, task lifecycle management, and streaming. But it has no tool integration primitives and requires agents to be fully opaque.

4. **ACP and ANP fill niche gaps but lack critical mass**: ACP (160 stars, last updated May 2025) provides clean REST-based workflow orchestration with threads/runs semantics. ANP (1,219 stars) tackles P2P discovery with W3C DID-based identity. Neither has sufficient adoption to become a standard alone.

5. **The AAIF is the kingmaker**: Founded March 2026 with Anthropic (chair), Microsoft (co-chair), Google, OpenAI, Amazon, Block, Bloomberg, and Cloudflare on the Technical Committee. MCP is its first project. Any protocol that gets AAIF adoption becomes dominant. ROAR should position as complementary to AAIF projects, not competitive.

---

## Protocol Deep Dives

### MCP (Model Context Protocol) — Anthropic / AAIF

- **Spec Version**: 2025-11-25 (active draft branch in progress)
- **Architecture**: Client-Host-Server, JSON-RPC 2.0
- **Transport**: stdio, Streamable HTTP (replaced SSE from 2024-11-05 spec)
- **Primitives**: Tools, Resources, Prompts, Sampling, Elicitation, Roots, Tasks (experimental)
- **Stars**: 7,442 | **License**: Open protocol | **Governance**: AAIF (Linux Foundation)

**Recent additions (2025-11-25)**: Experimental Tasks for durable request tracking, OpenID Connect Discovery, tool icons, incremental scope consent, tool calling in sampling, URL mode elicitation, SDK tiering system.

**Strengths**: Massive ecosystem (60,000+ servers), AAIF backing, simplicity, IDE integration (Claude, Cursor, VS Code, Windsurf, Zed), framework adoption (LangChain, LlamaIndex, CrewAI, AutoGen).

**Weaknesses**: No agent-to-agent communication, no identity layer, limited security model, no discovery mechanism, stateful by default, no streaming of partial results, single-hop only.

### A2A (Agent-to-Agent Protocol) — Google / Linux Foundation

- **Spec Version**: v0.3.0 (proto3 format, 794 lines, 47 message types)
- **Architecture**: HTTP(S) + JSON-RPC 2.0 with Agent Cards
- **Transport**: HTTP POST, SSE streaming, Push Notifications
- **Task Lifecycle**: submitted → working → completed/input-required/failed/canceled/rejected
- **Stars**: 22,397 | **License**: Apache 2.0 | **Governance**: Linux Foundation

**Service Methods**: SendMessage, SendStreamingMessage, GetTask, ListTasks, CancelTask, SubscribeToTask, push notification CRUD, GetExtendedAgentCard. Multi-tenant support built-in.

**Strengths**: Agent discovery via Agent Cards (`.well-known/agent.json`), full task lifecycle state machine, native SSE streaming + push notifications, opacity-preserving, enterprise auth (OAuth2, mTLS, OIDC), 5 official SDKs, 50+ launch partners, DeepLearning.AI course.

**Weaknesses**: No tool integration, no shared state between agents, no workflow orchestration (no DAGs), no P2P discovery, no cryptographic identity, HTTP-only (no stdio).

### ACP (Agent Connect Protocol) — Agntcy Collective

- **Spec Version**: 0.2.3 | **Stars**: 160 | **Last Activity**: May 2025 (stale)
- **Architecture**: REST API, OpenAPI-first, threads + runs model
- **Strengths**: Clean thread/run separation, SSE streaming, thread forking for branching workflows
- **Weaknesses**: Very low adoption, 9+ months stale, no auth/identity, no P2P, unclear governance

### ANP (Agent Network Protocol)

- **Stars**: 1,219 | **Status**: Active development, no formal version
- **Three-layer architecture**: Identity (W3C DID), Meta-Protocol (negotiation), Application (Semantic Web)
- **Unique innovation**: Meta-protocol for dynamic communication format negotiation
- **Strengths**: Decentralized DID identity, P2P-native, W3C CG adoption
- **Weaknesses**: No formal spec, minimal tooling, no enterprise adoption

---

## Standards Bodies & Governance

### AAIF (Agentic AI Foundation)

Founded March 2026, Linux Foundation directed fund. Charter adopted March 3, 2026.

**Technical Committee**: David Soria Parra (Anthropic, Chair), Caitie McCaffrey (Microsoft, Co-Chair), Alan Blount (Google), Nick Cooper (OpenAI), James Ward (AWS), Bradley Axen (Block), Sambhav Kothari (Bloomberg), Steve Faulkner (Cloudflare).

**Current Projects**: MCP, Goose (Block), AGENTS.MD

**Working Groups**: Accuracy & Reliability, Agentic Commerce, Governance/Risk/Regulatory, **Identity & Trust**, Observability & Traceability, Security & Privacy, **Workflows & Process Integration**

**Critical**: The Identity & Trust and Workflows working groups signal AAIF will address exactly the gaps in MCP. ROAR should adopt emerging AAIF standards rather than building permanent proprietary alternatives.

### W3C AI Agent Protocol Community Group

Active (biweekly meetings), created 2025-05-13, uses ANP white paper as foundation. Community Group only (cannot produce W3C Recommendations).

### IETF BANDAID

`draft-mozleywilliams-dnsop-dnsaid-01` — DNS-based Agent Identification and Discovery. Uses DNS records for agent discovery. Already MCP-aware (agents can declare `protocol="mcp"`). Reference implementation: `github.com/infobloxopen/dns-aid-core`.

### FIPA Lessons

| FIPA Mistake | Lesson for ROAR |
|-------------|----------------|
| Over-specified formal semantics (modal logic) | Keep message formats simple (JSON) |
| Assumed BDI agent architecture | Be architecture-agnostic |
| No reference implementation | Ship working code alongside every spec |
| Ignored the web | Be HTTP/web-native first |
| Centralized directory services | Use decentralized discovery |
| Academic focus | Focus on developer experience |
| Monolithic standard | Modular layers, independently adoptable |

---

## Protocol Comparison Matrix

| Capability | MCP | A2A | ACP | ANP | ROAR |
|-----------|-----|-----|-----|-----|------|
| Tool Integration | **NATIVE** | None | None | None | **NATIVE** |
| Agent-to-Agent | None | **NATIVE** | Partial | **NATIVE** | **NATIVE** |
| Agent Discovery | None | Agent Cards (URL) | API search | DID + meta | **Federated** |
| Agent Identity | None | Self-declared | None | W3C DID | **W3C DID** |
| Task Lifecycle | Experimental | **Full SM** | Runs | None | **Full** |
| Streaming | SSE (transport) | SSE + push | SSE | None | **Multi-transport** |
| Workflow Orchestration | None | None | Threads/runs | None | **Planned** |
| Authentication | OAuth 2.0, OIDC | OAuth2, mTLS | None | DID-based | **HMAC/JWT/mTLS** |
| Transport | stdio, HTTP | HTTP only | HTTP, stdio | HTTP | **stdio/HTTP/WS/gRPC** |
| Message Signing | None | None | None | None | **HMAC-SHA256** |
| P2P Discovery | None | None | None | **NATIVE** | **Tier 4 (DHT)** |
| Multi-Tenancy | None | **NATIVE** | None | None | **Planned** |
| Governance | AAIF (LF) | Linux Foundation | Agntcy | W3C CG | ProwlrBot |
| Maturity | Production | Production | Prototype | Research | **Draft** |
| Stars | 7,442 | 22,397 | 160 | 1,219 | — |

---

## Gap Analysis — What ROAR Uniquely Fills

### Use Cases Impossible with Any Single Protocol Today

1. **Agent discovers peer, negotiates capabilities, delegates sub-task using shared tools**: Requires discovery (ANP) + negotiation (A2A) + tool sharing (MCP) + task tracking (A2A).
2. **Multi-agent workflow with branching, parallel execution, and shared context**: Requires orchestration (ACP) + communication (A2A) + shared tools (MCP).
3. **Trustless agent collaboration across organizations**: Requires crypto identity (ANP DID) + secure communication + capability verification.
4. **Agent publishes itself to the internet and is discoverable by any agent**: Requires DNS discovery (BANDAID) + Agent Card (A2A) + protocol negotiation (ANP) + tool exposure (MCP).
5. **Real-time collaborative task with human-in-the-loop approval gates**: Requires streaming (A2A) + human input (MCP elicitation) + task state + approval workflow.

### Specific Gaps ROAR Targets

| Gap | Current State | ROAR Solution |
|-----|--------------|---------------|
| Unified agent identity | MCP: none, A2A: self-declared, ANP: DID | Single DID identity across all protocols |
| Protocol bridge | MCP and A2A disconnected | Adapters translating between formats |
| Agent health/lifecycle | No protocol monitors liveness | Heartbeat, health checks, graceful degradation |
| Shared context | A2A fully opaque, MCP per-session | Opt-in context sharing between agents |
| Discovery registry | BANDAID DNS and A2A Agent Cards disconnected | Unified: DNS → Agent Card → MCP tools |
| Trust/reputation | Nothing exists | Reputation based on completion, quality, uptime |
| Observability | No built-in tracing | OpenTelemetry-compatible distributed tracing |

---

## Strategic Positioning

### ROAR as Runtime, Not Protocol

```
+----------------------------------------------------------+
|                    ROAR Runtime Layer                      |
|  +----------+  +----------+  +---------+  +-----------+  |
|  | MCP      |  | A2A      |  | ACP     |  | ANP/DID   |  |
|  | Adapter  |  | Adapter  |  | Adapter |  | Adapter   |  |
|  +----------+  +----------+  +---------+  +-----------+  |
|  +---------------------------------------------------+   |
|  | ROAR Native Services                              |   |
|  | - Unified Identity    - Workflow Engine            |   |
|  | - Discovery Registry  - Health Monitor             |   |
|  | - Context Broker      - Observability              |   |
|  | - Trust/Reputation    - Cost Tracking              |   |
|  +---------------------------------------------------+   |
+----------------------------------------------------------+
```

### What NOT to Do

1. **Do not create a new wire protocol**: JSON-RPC, proto3, and OpenAPI all work fine
2. **Do not compete with AAIF**: Position as complementary; implement AAIF standards faithfully
3. **Do not repeat FIPA's mistakes**: Keep it simple, ship working code, focus on DX
4. **Do not require all protocols**: Each adapter should be optional

### Watch Closely

- AAIF "Identity & Trust" working group output
- AAIF "Workflows & Process Integration" output
- Whether A2A becomes an AAIF project (Google is on the TC)
- IETF BANDAID progression through standards track
- MCP draft spec for new features beyond 2025-11-25

---

## Sources

1. Model Context Protocol Specification, v2025-11-25. AAIF/Anthropic. `github.com/modelcontextprotocol/specification` (7,442 stars)
2. Agent2Agent Protocol Specification, v0.3.0. Google/Linux Foundation. `github.com/google/A2A` (22,397 stars)
3. Agent Connect Protocol Specification, v0.2.3. Agntcy. `github.com/agntcy/acp-spec` (160 stars)
4. Agent Network Protocol. ANP Community. `github.com/agent-network-protocol/AgentNetworkProtocol` (1,219 stars)
5. IETF draft-mozleywilliams-dnsop-dnsaid-01 (BANDAID). Infoblox. `github.com/infobloxopen/dns-aid-core`
6. AAIF Technical Committee Charter, adopted 2026-03-03. `github.com/aaif/technical-committee`
7. W3C AI Agent Protocol Community Group. `github.com/w3c-cg/ai-agent-protocol` (48 stars)
8. Fetch.ai uAgents Framework. `github.com/fetchai/uAgents` (1,555 stars)
9. W3C DID Core v1.0 (July 2022), VC Data Model v2.0 (March 2025), DIDComm v2.1 (DIF)
