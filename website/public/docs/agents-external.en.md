# External Agents

ProwlrBot supports installing and coordinating external AI agents alongside its built-in agents. Connect Claude Code, OpenAI Codex, custom agents, or any tool that speaks MCP/ROAR.

---

## Installing an External Agent

```bash
# Install from the marketplace
prowlr agent install prowlr-scout

# Register a custom external agent
prowlr agent add --name "my-agent" --type custom --endpoint http://localhost:9000

# List all agents (built-in + external)
prowlr agent list
```

## Supported Agent Types

| Type | Description | Connection |
|:-----|:-----------|:-----------|
| **Built-in** | ProwlrBot's native ReAct agent | Direct (in-process) |
| **MCP** | Any MCP-compatible tool server | stdio or HTTP |
| **ROAR** | Agents speaking the ROAR protocol | HTTP, WebSocket, stdio |
| **Custom** | Your own agent with a REST API | HTTP endpoint |

## Configuring Agent Backends

Each agent can use a different AI provider:

```json
{
  "agents": [
    {
      "name": "scout",
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514",
      "tools": ["web_search", "file_read"],
      "autonomy": "delegate"
    },
    {
      "name": "coder",
      "provider": "openai",
      "model": "gpt-4o",
      "tools": ["shell", "file_write", "file_read"],
      "autonomy": "guided"
    },
    {
      "name": "local-analyst",
      "provider": "ollama",
      "model": "llama3:70b",
      "tools": ["file_read"],
      "autonomy": "watch"
    }
  ]
}
```

## Autonomy Levels

Every agent operates at one of four autonomy levels:

| Level | What It Means | When to Use |
|:------|:-------------|:-----------|
| **Watch** | Agent observes but doesn't act | Monitoring, learning |
| **Guided** | Agent suggests actions, you approve | Early trust-building |
| **Delegate** | Agent acts, you review after | Trusted tasks |
| **Autonomous** | Agent acts independently | Proven reliability |

## Agent Personality

Each agent can have a customized personality via markdown files in the working directory:

| File | Purpose |
|:-----|:--------|
| `AGENTS.md` | Agent instructions and behavior guidelines |
| `SOUL.md` | Personality traits, communication style |
| `PROFILE.md` | Agent identity, name, role description |

## Multi-Agent Coordination

External agents can participate in War Room coordination:

```bash
# Start the hub
prowlr hub start

# External agents connect via MCP
# They get access to: claim_task, lock_file, share_finding, broadcast_status
```

### How External Agents Join

1. **MCP agents** — Add as an MCP server in config, they automatically get War Room tools
2. **ROAR agents** — Register via discovery layer, connect over any transport
3. **Custom agents** — Call the hub REST API directly (`/api/hub/tasks`, `/api/hub/locks`)

## Agent Registry

The marketplace includes pre-built agent configurations:

```bash
# Search for agents
prowlr market search --category agents

# Currently available:
# - prowlr-scout    — Research and information gathering
# - prowlr-guard    — Security monitoring and alerting
```

## Smart Routing

When multiple agents are available, ProwlrBot's smart router picks the best one:

```
Score = w_cost * cost + w_perf * performance + w_avail * availability
```

Configure routing weights in `~/.prowlrbot/config.json` under `providers.routing`.

---

*One agent is useful. A coordinated pack is unstoppable.*
