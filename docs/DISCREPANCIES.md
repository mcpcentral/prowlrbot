# CLAUDE.md Accuracy Check

This file documents findings from cross-checking `CLAUDE.md` against the actual source code. Where possible, exact file paths and code references are provided.

Last audited: 2026-03-13.

---

## No critical errors found

The architecture section in `CLAUDE.md` accurately describes the codebase. The following are minor gaps or additions found during the audit:

---

## Additional CLI commands not listed in CLAUDE.md

`CLAUDE.md`'s Quick Reference section lists a subset of CLI commands. The following commands exist in the source (`src/prowlrbot/cli/`) but are not mentioned:

| Command group | Source file | Notes |
|--------------|-------------|-------|
| `prowlr agent` | `agent_cmd.py` | External agent management (install, list, health, remove, info) |
| `prowlr team` | `team_cmd.py` | Agent team management |
| `prowlr market` | `market_cmd.py` | Marketplace (search, install, publish, credits, tiers, etc.) |
| `prowlr backup` | `backup_cmd.py` | Backup/restore data |
| `prowlr export` | `export_cmd.py` | Data export and retention |
| `prowlr chats` | `chats_cmd.py` | Chat history management |
| `prowlr migrate` | `migrate_cmd.py` | DB schema migrations |
| `prowlr acp` | `acp_cmd.py` | ACP server for IDE integration |
| `prowlr studio` | `studio_cmd.py` | ProwlrBot Studio |
| `prowlr doctor` | `doctor_cmd.py` | Environment health check (requires `pip install prowlr-doctor`) |
| `prowlr completion` | `completion_cmd.py` | Shell completion |
| `prowlr clean` | `clean_cmd.py` | Clean temp files |
| `prowlr uninstall` | `uninstall_cmd.py` | Remove all data |
| `prowlr swarm` | `swarm_cmd.py` | Swarm management (status, up, down, logs, enqueue, etc.) |

The `CLAUDE.md` command list is a quick reference, not exhaustive. These additions are documented in `docs/guides/cli-reference.md`.

---

## Skills list discrepancy

`CLAUDE.md` lists these built-in skills:
> `cron`, `pdf`, `docx`, `pptx`, `xlsx`, `news`, `file_reader`, `browser_visible`, `himalaya`, `dingtalk_channel`

The actual skills directory (`src/prowlrbot/agents/skills/`) also contains:
- `github_app` — GitHub repository management
- `marketing` — Marketing copy and campaigns
- `mac_doctor` — macOS diagnostics
- `wsl_doctor` — WSL diagnostics

These were added after the `CLAUDE.md` was written.

---

## Provider registry additions

`CLAUDE.md` mentions: "OpenAI-compatible, Anthropic, local (llama.cpp/MLX), Ollama"

The actual registry (`src/prowlrbot/providers/registry.py`) also includes:
- `dashscope` (Alibaba)
- `modelscope`
- `aliyun-codingplan`
- `zai` (Zhipu AI)
- `azure-openai`

These are all fully functional built-in providers with `env_var` detection.

---

## MCP transport types

`CLAUDE.md` mentions: "stdio/http transports"

The actual `MCPClientConfig` model (`src/prowlrbot/config/config.py`) supports three transport values:
- `stdio`
- `streamable_http`
- `sse`

The distinction between `streamable_http` and `sse` is real and matters for server-side event streaming vs HTTP.

---

## Notes on CLAUDE.md accuracy

Everything in `CLAUDE.md`'s architecture section (core flow, provider detection flow, key directories) accurately matches the code. The discrepancies above are additions and expansions that were made after CLAUDE.md was last updated, not errors.
