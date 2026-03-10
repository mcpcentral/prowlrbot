# ROAR Layer 4 — Exchange

## Purpose

Define the universal message format for all agent communication. Every interaction — tool calls, agent delegation, human queries, notifications — uses a single `ROARMessage` structure. This eliminates the need for protocol-specific message formats and enables seamless interoperability.

## Data Models

### MessageIntent

Declares what the sender wants the receiver to do:

| Value      | Direction        | Description                        |
|------------|------------------|------------------------------------|
| `execute`  | Agent to Tool    | Invoke a tool or function          |
| `delegate` | Agent to Agent   | Hand off a task to another agent   |
| `update`   | Agent to IDE     | Push a status or result update     |
| `ask`      | Agent to Human   | Request human input or approval    |
| `respond`  | Any to Any       | Reply to any of the above intents  |
| `notify`   | Any to Any       | One-way informational notification |
| `discover` | Any to Directory | Request agent discovery             |

### ROARMessage

| Field           | Type            | Default          | Description                            |
|-----------------|-----------------|------------------|----------------------------------------|
| `roar`          | `str`           | `"1.0"`          | Protocol version                       |
| `id`            | `str`           | auto-generated   | Unique message ID (`msg_<hex10>`)      |
| `from_identity` | `AgentIdentity` | required         | Sender identity (JSON key: `"from"`)   |
| `to_identity`   | `AgentIdentity` | required         | Receiver identity (JSON key: `"to"`)   |
| `intent`        | `MessageIntent` | required         | What the sender wants                  |
| `payload`       | `dict`          | `{}`             | Message content (intent-specific)      |
| `context`       | `dict`          | `{}`             | Metadata (session, thread, protocol)   |
| `auth`          | `dict`          | `{}`             | Authentication data (signature, etc.)  |
| `timestamp`     | `float`         | `time.time()`    | Unix timestamp of creation             |

The `from` and `to` fields use Pydantic aliases (`from_identity`, `to_identity`) since `from` is a Python reserved word.

## Operations

### Sending a Message

```python
msg = ROARMessage(
    **{"from": sender_identity, "to": receiver_identity},
    intent=MessageIntent.DELEGATE,
    payload={"task": "summarize", "text": "..."},
)
```

### Signing

HMAC-SHA256 signature over the canonical JSON of `{id, intent, payload}`:

```python
signed_msg = msg.sign(secret="shared-secret")
# msg.auth => {"signature": "hmac-sha256:<hex>", "timestamp": ...}
```

### Verification

```python
is_valid = msg.verify(secret="shared-secret")
```

Verification recomputes the HMAC and uses `hmac.compare_digest` for constant-time comparison.

### Response Pattern

Responses reference the original message via `context.in_reply_to`:

```python
response = ROARMessage(
    **{"from": receiver_identity, "to": sender_identity},
    intent=MessageIntent.RESPOND,
    payload={"result": "done"},
    context={"in_reply_to": original_msg.id},
)
```

## Signing Algorithm

1. Construct the canonical body: `json.dumps({"id": msg.id, "intent": msg.intent, "payload": msg.payload}, sort_keys=True)`
2. Compute: `hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()`
3. Store in `auth.signature` as `"hmac-sha256:<hex>"`

## Security Considerations

- All messages should be signed before transmission.
- Recipients must verify signatures before processing payloads.
- The `timestamp` field enables replay attack detection (reject messages older than a configurable window).
- Payload content is not encrypted by the Exchange layer; transport-level encryption (TLS) handles confidentiality.
- The signing secret must be pre-shared via a secure out-of-band channel.

## Standards Alignment

### Intent Mapping to Existing Protocols

| ROAR Intent | MCP Equivalent | A2A Equivalent | ACP Equivalent |
|-------------|---------------|----------------|----------------|
| `execute` | Tool call | — | Run |
| `delegate` | — | tasks/send | — |
| `update` | — | Task status update | — |
| `ask` | Elicitation | input-required state | session/prompt |
| `respond` | Tool result | Task artifact | Run result |
| `notify` | Notification | Push notification | — |
| `discover` | — | Agent Card GET | agents/search |

### Signing

Current: HMAC-SHA256 with pre-shared secrets (symmetric).
Planned: Ed25519 asymmetric signing for cross-organization trust (aligns with W3C DID verification methods).

## Example

```python
from prowlrbot.protocols.sdk import AgentIdentity, MessageIntent, ROARMessage

alice = AgentIdentity(display_name="alice")
bob = AgentIdentity(display_name="bob")

msg = ROARMessage(
    **{"from": alice, "to": bob},
    intent=MessageIntent.ASK,
    payload={"question": "Should I deploy to production?"},
)
msg.sign("secret-key")

assert msg.verify("secret-key")
assert not msg.verify("wrong-key")
```
