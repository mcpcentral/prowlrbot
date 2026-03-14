# ACP / IDE Integration

ProwlrBot can run as an ACP (Agent Communication Protocol) server over stdio, enabling integration with VS Code, Zed, JetBrains, and any editor that supports the ACP protocol.

---

## What is ACP?

ACP is a JSON-RPC 2.0 protocol over stdio. When you run `prowlr acp`, ProwlrBot:

1. Starts the `AgentRunner` (loads config, connects channels and MCP servers)
2. Listens on stdin for JSON-RPC requests
3. Writes responses to stdout
4. Logs errors/debug info to stderr

This lets editors communicate with ProwlrBot as an agent backend — sending queries, receiving streaming responses, and using all of ProwlrBot's tools (shell, file I/O, browser, memory, skills, MCP).

---

## Starting the ACP server

```bash
prowlr acp               # start ACP server on stdio
prowlr acp --debug       # verbose logging to stderr
```

The server runs until you send Ctrl+C or close stdin.

---

## VS Code integration

Add ProwlrBot as an ACP agent in VS Code's `.mcp.json` (or your workspace's `settings.json`):

```json
{
  "mcpServers": {
    "prowlrbot": {
      "command": "prowlr",
      "args": ["acp"],
      "env": {}
    }
  }
}
```

For Claude Code (if using ProwlrBot alongside Claude Code):

```bash
claude mcp add prowlrbot \
  -- prowlr acp
```

Or with a specific working directory or virtual environment:

```bash
claude mcp add prowlrbot \
  -e OPENAI_API_KEY=sk-... \
  -- /path/to/venv/bin/prowlr acp
```

---

## Zed integration

In `~/.config/zed/settings.json`:

```json
{
  "assistant": {
    "version": "2",
    "default_model": {
      "provider": "custom",
      "model": "prowlrbot"
    }
  },
  "language_models": {
    "prowlrbot": {
      "api_url": "stdio://prowlr acp",
      "protocol": "acp"
    }
  }
}
```

Exact configuration varies by Zed version — check [zed.dev/docs](https://zed.dev/docs) for the current ACP integration spec.

---

## JetBrains integration

JetBrains IDEs (IntelliJ, PyCharm, etc.) support ACP via the AI Assistant plugin. In the plugin settings:

1. Open **Settings → Tools → AI Assistant → AI Providers**
2. Add custom provider
3. Set type to **ACP (stdio)**
4. Command: `prowlr acp`

---

## Protocol details

The ACP server (`src/prowlrbot/protocols/acp_server.py`) implements JSON-RPC 2.0. Supported methods:

| Method | Description |
|--------|-------------|
| `agent/query` | Send a query to the agent, returns response |
| `agent/stream` | Send a query, stream incremental tokens |
| `agent/status` | Get agent health/status |
| `tools/list` | List available tools and MCP tools |

Example request:

```json
{"jsonrpc": "2.0", "method": "agent/query", "params": {"query": "List files in /tmp"}, "id": 1}
```

Example response:

```json
{"jsonrpc": "2.0", "result": {"response": "I found 3 files in /tmp:\n- foo.txt\n- bar.log\n- baz.sh"}, "id": 1}
```

---

## Combining with Claude Code MCP

ProwlrBot and Claude Code can work together. Claude Code can use ProwlrBot as an MCP tool server via the war room hub, while ProwlrBot uses Claude Code as an external agent backend.

```bash
# Register Claude Code as an external agent in ProwlrBot
prowlr agent install \
  --type claude_code \
  --command claude \
  --name "claude-code"

# Register ProwlrBot as an MCP server in Claude Code
claude mcp add prowlrbot-tools \
  -e OPENAI_API_KEY=sk-... \
  -- prowlr acp
```

---

## Environment for IDE use

When ProwlrBot is launched by an IDE, it may not inherit your shell environment. Make sure API keys are set either:

1. In `~/.prowlrbot.secret/envs.json` via `prowlr env set`
2. Passed explicitly via `env` in the MCP/ACP config

```json
{
  "mcpServers": {
    "prowlrbot": {
      "command": "prowlr",
      "args": ["acp"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

Keys stored via `prowlr env set` are always available because ProwlrBot loads `~/.prowlrbot.secret/envs.json` at startup before the ACP server initializes.
