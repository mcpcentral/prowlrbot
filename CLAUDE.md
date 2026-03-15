# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ProwlrBot — "Always watching. Always ready." An autonomous AI agent platform for monitoring, automation, and multi-channel communication. Fork of CoPaw (agentscope-ai/CoPaw), fully rebranded and enhanced. Python backend with React frontend console.

## Build & Development Commands

```bash
# Install (dev)
pip install -e ".[dev]"

# Run the app server (FastAPI + uvicorn on port 8088)
prowlr app

# Initialize config
prowlr init --defaults

# Run tests
pytest
pytest tests/test_react_agent_tool_choice.py   # single test
pytest -m "not slow"                            # skip slow tests

# Pre-commit checks (formatting, linting)
pre-commit install
pre-commit run --all-files

# Build console frontend
cd console && npm ci && npm run build

# Format frontend
cd console && npm run format
```

## Architecture

### Core Flow

```
User Message → Channel → ChannelManager (queue + debounce) → AgentRunner
→ ProwlrBotAgent (ReActAgent) → Model (OpenAI/Anthropic/Groq/Z.ai/Ollama) → Response
→ Channel Output + ChatManager (persistence)
```

### Provider Detection Flow

```
Environment Scan → ProviderDetector (env vars) → HealthChecker (async probes)
→ SmartRouter (score = w_cost * cost + w_perf * perf + w_avail * avail) → Selected Provider
→ FallbackChain on failure
```

### Source Layout (`src/prowlrbot/`)

- **`cli/`** — Click CLI. Entry point: `cli/main.py` → `prowlr` command. Lazy-loaded subcommands. Full command list: `prowlr agent`, `team`, `market`, `backup`, `export`, `chats`, `migrate`, `acp`, `studio`, `doctor`, `completion`, `clean`, `uninstall`, `swarm`, plus `app`, `init`, `models`, `env`, etc. See `docs/guides/cli-reference.md`.
- **`app/_app.py`** — FastAPI app with lifespan that wires all subsystems together.
- **`app/channels/`** — Channel system. `base.py` defines `BaseChannel` (abstract). `manager.py` runs per-channel async queues with 4 workers each. Channels: dingtalk, feishu, discord_, telegram, qq, imessage, console. Custom channels loaded from `~/.prowlrbot/custom_channels/`.
- **`app/runner/`** — `AgentRunner` wraps query execution. `runner.py` handles agent creation, session management, query processing.
- **`app/crons/`** — APScheduler-based. `manager.py` schedules cron/interval jobs. `executor.py` runs them. `heartbeat.py` is a special periodic agent check-in.
- **`app/mcp/`** — MCP client lifecycle. `manager.py` manages MCP transports: `stdio`, `streamable_http`, `sse` (see `config/config.py` MCPClientConfig). `watcher.py` polls config for MCP changes.
- **`app/routers/`** — FastAPI API routes for agent, channels, skills, MCP, cron, config, providers, etc.
- **`agents/react_agent.py`** — `ProwlrBotAgent` extends AgentScope's `ReActAgent`. Integrates tools, skills, memory, MCP clients.
- **`agents/model_factory.py`** — Creates chat models from active provider config. Supports OpenAI-compatible, Anthropic, local (llama.cpp/MLX), Ollama, plus dashscope, modelscope, aliyun-codingplan, zai, azure-openai (see `providers/registry.py`).
- **`agents/prompt.py`** — Builds system prompt from `AGENTS.md`, `SOUL.md`, `PROFILE.md` in working dir.
- **`agents/tools/`** — Built-in tools: shell, file I/O, browser, screenshot, send_file, memory_search.
- **`agents/skills/`** — Built-in skills: cron, pdf, docx, pptx, xlsx, news, file_reader, browser_visible, himalaya, dingtalk_channel, github_app, marketing, mac_doctor, wsl_doctor. Each has a `SKILL.md` manifest.
- **`agents/skills_manager.py`** — Syncs builtin + customized skills to `active_skills/`.
- **`agents/memory/`** — `ProwlrBotInMemoryMemory` + `MemoryManager` with auto-compaction when token budget exceeded.
- **`config/`** — Pydantic config models (`config.py`), load/save utils (`utils.py`), hot-reload watcher (`watcher.py`). Main config: `~/.prowlrbot/config.json`.
- **`providers/`** — Provider registry, detector (env var scanning), health checker, smart router with scoring engine. Custom providers via `providers.json`.
- **`envs/`** — Environment variable store. Persists to `~/.prowlrbot.secret/envs.json` (mode 0o600).
- **`local_models/`** — Local model backends: llama.cpp, MLX, Ollama.
- **`monitor/`** — Web change detection, API monitoring, notification system, content diffing.

### Console Frontend (`console/`)

React 18 + TypeScript + Vite + Ant Design. Pages: Chat, Agent (config/MCP/skills/workspace), Control (channels/cron/sessions/heartbeat), Settings (models/envs). Built output served as static files by FastAPI.

### Key Data Paths

- `~/.prowlrbot/` — Working directory: config.json, chats, skills, custom channels
- `~/.prowlrbot.secret/` — Secrets (envs.json)
- `src/prowlrbot/agents/md_files/en/` — Default agent personality/prompt files

## Conventions

- **Commit messages**: Conventional Commits format — `<type>(<scope>): <subject>` (feat, fix, docs, refactor, test, chore, perf, style)
- **Code style**: Black formatter, enforced via pre-commit
- **Python**: 3.10–3.13, async/await throughout
- **Config validation**: Pydantic BaseModel
- **Tests**: pytest with pytest-asyncio (`asyncio_mode = "auto"`)
- **Language**: All code, comments, docs, and UI in English
- **Channel protocol**: Native payload → `content_parts` (TextContent, ImageContent, FileContent) → `AgentRequest`
- **Skill structure**: Directory with `SKILL.md` (YAML frontmatter: name, description), optional `references/` and `scripts/`
- **New providers**: Add `ProviderDefinition` in `providers/registry.py` with `env_var`, `cost_tier`, `health_check_endpoint`; implement `ChatModelBase` subclass if not OpenAI-compatible
- **New channels**: Subclass `BaseChannel` in `app/channels/`, set `channel` class attribute, register in `app/channels/registry.py`
- **New monitors**: Subclass `BaseDetector` in `monitor/detectors/`, implement `async detect()` method
