# MCP Server Setup

Model Context Protocol (MCP) lets ProwlrBot connect to external tool servers. Any MCP server — filesystem, database, GitHub, Slack, browser, etc. — can be wired in and its tools become available to the agent.

---

## How MCP works in ProwlrBot

MCP clients are configured in `~/.prowlrbot/config.json` under `mcp.clients`. The `MCPClientManager` initializes clients at startup and supports **hot-reload**: if you add or change an MCP server config, ProwlrBot picks it up without a full restart.

Two transports are supported:
- `stdio` — launch a subprocess, communicate over stdin/stdout
- `streamable_http` / `sse` — connect to an HTTP endpoint

---

## Config structure

In `~/.prowlrbot/config.json`:

```json
{
  "mcp": {
    "clients": {
      "filesystem": {
        "name": "filesystem",
        "description": "Read and write local files",
        "enabled": true,
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/Documents"],
        "env": {}
      },
      "github": {
        "name": "github",
        "description": "GitHub repository management",
        "enabled": true,
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
          "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
        }
      },
      "remote-tool": {
        "name": "remote-tool",
        "description": "Remote MCP tool server",
        "enabled": true,
        "transport": "streamable_http",
        "url": "http://my-mcp-server:3000/mcp",
        "headers": {
          "Authorization": "Bearer my-token"
        }
      }
    }
  }
}
```

### MCPClientConfig fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | required | Unique identifier |
| `description` | string | `""` | Shown in UI; helps agent know what the server provides |
| `enabled` | bool | `true` | Set `false` to disable without deleting |
| `transport` | `stdio` / `streamable_http` / `sse` | `stdio` | Connection type |
| `command` | string | `""` | Executable to run (stdio only) |
| `args` | list | `[]` | Arguments passed to command (stdio only) |
| `env` | dict | `{}` | Additional env vars for the subprocess (stdio only) |
| `cwd` | string | `""` | Working directory for subprocess (stdio only) |
| `url` | string | `""` | HTTP endpoint URL (http/sse transports) |
| `headers` | dict | `{}` | HTTP headers (http/sse transports) |

---

## Common MCP servers

### Official @modelcontextprotocol servers

Requires Node.js / `npx`.

```json
"filesystem": {
  "name": "filesystem",
  "transport": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allow"]
}
```

```json
"github": {
  "name": "github",
  "transport": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."}
}
```

```json
"postgres": {
  "name": "postgres",
  "transport": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"]
}
```

```json
"brave-search": {
  "name": "brave-search",
  "transport": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-brave-search"],
  "env": {"BRAVE_API_KEY": "BSA..."}
}
```

### Python MCP servers

```json
"python-tool": {
  "name": "python-tool",
  "transport": "stdio",
  "command": "python3",
  "args": ["-m", "my_mcp_server"],
  "env": {"MY_API_KEY": "..."},
  "cwd": "/path/to/server"
}
```

### Remote HTTP MCP servers

```json
"remote-server": {
  "name": "remote-server",
  "transport": "streamable_http",
  "url": "https://my-server.example.com/mcp",
  "headers": {
    "Authorization": "Bearer my-token",
    "X-Custom-Header": "value"
  }
}
```

---

## Adding MCP servers via the web UI

1. Open `http://localhost:8088`
2. Go to **Agent** tab → **MCP** section
3. Click **Add Server**
4. Fill in transport, command/URL, and optional env vars
5. Click **Save** — the server connects immediately (hot-reload)

---

## Editing config.json directly

```bash
# Open config in your editor
$EDITOR ~/.prowlrbot/config.json

# Or using prowlr's export to inspect current config
prowlr export config
```

After saving, the `MCPWatcher` detects the change and reconnects automatically within a few seconds. Check the server log for connection status.

---

## Disabling an MCP server

Set `enabled: false` in the client config:

```json
"github": {
  "name": "github",
  "enabled": false,
  ...
}
```

---

## Hot-reload behavior

`MCPWatcher` polls `config.json` for changes to the `mcp.clients` section. When a change is detected:

1. New clients are connected immediately
2. Modified clients are disconnected and reconnected
3. Deleted clients are disconnected and removed

This means you can add/remove MCP servers without restarting the app. The change takes effect within the polling interval (typically 5 seconds).

---

## Debugging MCP connections

Start the app with debug logging:

```bash
prowlr app --debug
```

Look for log lines like:
```
DEBUG - MCP client 'filesystem' initialized successfully
WARNING - Failed to initialize MCP client 'github': Connection refused
```

Test the MCP server independently:

```bash
# For stdio servers, run directly:
npx -y @modelcontextprotocol/server-filesystem /tmp

# For HTTP servers:
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

---

## Writing your own MCP server

ProwlrBot uses the [agentscope-runtime](https://github.com/agentscope-ai/agentscope) MCP client implementation. Any server that implements the MCP spec will work.

Minimal Python MCP server using `mcp` SDK:

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("my-tools")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="greet",
            description="Greet someone by name",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "greet":
        return [TextContent(type="text", text=f"Hello, {arguments['name']}!")]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

Register it:

```json
"my-tools": {
  "name": "my-tools",
  "transport": "stdio",
  "command": "python3",
  "args": ["/path/to/my_server.py"]
}
```
