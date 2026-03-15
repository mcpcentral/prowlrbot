# ROAR protocol — Using ProwlrBot as an agent

ProwlrBot implements the [ROAR protocol](https://github.com/ProwlrBot/roar-protocol). Install the protocol package to build compatible agents: **`pip install roar-protocol`** · [PyPI](https://pypi.org/project/roar-protocol/)

This guide shows how to discover ProwlrBot over ROAR and send it tasks (EXECUTE/DELEGATE) via HTTP.

## Public endpoints (no auth)

Use these from scripts, health checks, or other agents without credentials.

- **`GET /roar/health`** — Protocol health check. Returns `{"status": "ok", "protocol": "roar/1.0"}`.
- **`GET /roar/card`** — Agent discovery. Returns this instance’s ROAR card (identity, description, skills, channels, endpoints).

Example:

```bash
curl -s https://your-app.fly.dev/roar/health
curl -s https://your-app.fly.dev/roar/card
```

The card’s `endpoints` object includes URLs for `http` (POST message), `websocket`, and `events` (SSE).

## Sending a task (auth required)

`POST /roar/message` and `GET /roar/events` (SSE) use the same API authentication as the rest of ProwlrBot (e.g. Bearer token or session). Send a ROAR message with intent `execute` or `delegate` and a task in the payload.

### Minimal ROAR message

You must send a valid [ROARMessage](../protocols/ROAR-EXCHANGE.md): `from`, `to` (AgentIdentity), `intent`, and `payload`. The handler reads the task from `payload.task`, `payload.prompt`, or `payload.text`.

Example request body:

```json
{
  "roar": "1.0",
  "from": {
    "did": "did:roar:agent:your-client-id",
    "display_name": "My Script",
    "agent_type": "agent",
    "capabilities": ["execute"]
  },
  "to": {
    "did": "did:roar:agent:prowlrbot",
    "display_name": "ProwlrBot",
    "agent_type": "agent",
    "capabilities": ["execute", "delegate", "monitor", "stream"]
  },
  "intent": "execute",
  "payload": {
    "task": "What is 2 + 2? Reply in one sentence."
  }
}
```

Example with curl (replace `BASE` and `TOKEN`):

```bash
curl -s -X POST "$BASE/roar/message" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "roar": "1.0",
    "from": {"did": "did:roar:agent:cli", "display_name": "CLI", "agent_type": "agent", "capabilities": ["execute"]},
    "to": {"did": "did:roar:agent:prowlrbot", "display_name": "ProwlrBot", "agent_type": "agent", "capabilities": ["execute","delegate"]},
    "intent": "execute",
    "payload": {"task": "Say hello in one word."}
  }'
```

The response is a ROAR message with `intent: "respond"` and `payload.result` containing the agent’s reply text.

## Event stream (War Room)

To stream ROAR events (e.g. in the War Room UI), open a GET request to `/roar/events` with the same auth. The response is Server-Sent Events. The console’s War Room uses this to show live ROAR activity.

## Protocol specs

- [ROAR-SPEC](../protocols/ROAR-SPEC.md) — Overview
- [ROAR-IDENTITY](../protocols/ROAR-IDENTITY.md) — AgentIdentity and DIDs
- [ROAR-EXCHANGE](../protocols/ROAR-EXCHANGE.md) — ROARMessage, intents, signing
- [ROAR-CONNECT](../protocols/ROAR-CONNECT.md) — Transports (HTTP, WebSocket)
- [ROAR-DISCOVERY](../protocols/ROAR-DISCOVERY.md) — Discovery and AgentCard
