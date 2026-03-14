# War Room MCP – Debugging and install

Quick reference for fixing `prowlr-hub` MCP setup and duplicate-scope errors.

## "prowlr-hub exists in multiple scopes"

Claude Code can load `prowlr-hub` from:

- **Local** — `~/.claude.json` under `projects["<path>"].mcpServers.prowlr-hub`
- **Project** — repo `.mcp.json` or plugin `plugins/prowlr-hub/.mcp.json`

If both define `prowlr-hub`, you get the duplicate error.

**Fix:**

1. Remove from project scope so only local remains:
   ```bash
   claude mcp remove prowlr-hub -s project
   ```
2. Ensure local config is correct (see below). Re-add if needed:
   ```bash
   cd /path/to/prowlrbot
   claude mcp add prowlr-hub -s local \
     -e PYTHONPATH="$(pwd)/src" \
     -e PROWLR_AGENT_NAME=wsl-main \
     -e PROWLR_CAPABILITIES=orchestrator,planning \
     -e PROWLR_HUB_URL=http://localhost:8099 \
     -- python3 -m prowlrbot.hub
   ```
   **Do not use `-c`** — that option does not exist. Use `cd` to the repo or set `PYTHONPATH` to an absolute path.

3. Fully restart Claude Code.

## Correct local config (reference)

For project path `/home/anon/dev/prowlrbot`, the entry in `~/.claude.json` under `projects["/home/anon/dev/prowlrbot"].mcpServers` should look like:

```json
"prowlr-hub": {
  "type": "stdio",
  "command": "python3",
  "args": ["-m", "prowlrbot.hub"],
  "env": {
    "PYTHONPATH": "/home/anon/dev/prowlrbot/src",
    "PROWLR_AGENT_NAME": "wsl-main",
    "PROWLR_CAPABILITIES": "orchestrator,planning",
    "PROWLR_HUB_URL": "http://localhost:8099"
  }
}
```

- **PYTHONPATH** — Must be the `src` directory inside the prowlrbot repo (absolute path recommended).
- **PROWLR_HUB_URL** — `http://localhost:8099` for same-machine; for remote use the bridge URL (e.g. `http://<host-ip>:8099`).
- **PROWLR_AGENT_NAME** / **PROWLR_CAPABILITIES** — Any string; used for the mission board.

## Bridge must be running (same machine)

For agents to see each other, the HTTP bridge must be running in one terminal:

```bash
cd /path/to/prowlrbot
PYTHONPATH=src python3 -m prowlrbot.hub.bridge
```

Then `curl http://localhost:8099/health` should return a response. If it doesn’t, tools will fail or show "No agents connected".

## If there’s already a prowlr-hub entry

1. Run `claude mcp list` and note which scope(s) show `prowlr-hub`.
2. Remove from project: `claude mcp remove prowlr-hub -s project`.
3. Remove from local only if you want to re-add from scratch: `claude mcp remove prowlr-hub -s local`.
4. Re-add with the command above (from repo dir, `-s local`, no `-c`).
5. Restart Claude Code.

See [INSTALL.md](../../INSTALL.md) for full setup and [cross-network-setup.md](cross-network-setup.md) for remote/bridge options.
