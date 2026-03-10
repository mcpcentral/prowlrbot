# Contributing to ProwlrBot

Thank you for your interest in contributing to ProwlrBot! ProwlrBot is an open-source autonomous AI agent platform for monitoring, automation, and multi-channel communication. We welcome contributions that help make ProwlrBot more capable: whether you add a new channel, a new model provider, a skill, improve docs, or fix bugs.

**Quick links:** [GitHub](https://github.com/mcpcentral/prowlrbot) · [Docs](https://mcpcentral.github.io/prowlr-docs) · [License: Apache 2.0](LICENSE)

---

## How to Contribute

To keep collaboration smooth and maintain quality, please follow these guidelines.

### 1. Check Existing Plans and Issues

Before starting:

- **Check [Open Issues](https://github.com/mcpcentral/prowlrbot/issues)** and any [Projects](https://github.com/mcpcentral/prowlrbot/projects) or roadmap labels.
- **If a related issue exists** and is open or unassigned: comment to say you want to work on it to avoid duplicate effort.
- **If no related issue exists**: open a new issue describing your proposal. The maintainers will respond and can help align with the project direction.

### 2. Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for clear history and tooling.

**Format:**
```
<type>(<scope>): <subject>
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code style (whitespace, formatting, etc.)
- `refactor:` Code change that neither fixes a bug nor adds a feature
- `perf:` Performance improvement
- `test:` Adding or updating tests
- `chore:` Build, tooling, or maintenance

**Examples:**
```bash
feat(channels): add Telegram channel stub
fix(skills): correct SKILL.md front matter parsing
docs(readme): update quick start for Docker
refactor(providers): simplify custom provider validation
test(agents): add tests for skill loading
```

### 3. Pull Request Title Format

PR titles should follow the same convention:

**Format:** ` <type>(<scope>): <description> `

- Use one of: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`, `style`, `build`, `revert`.
- **Scope must be lowercase** (letters, numbers, hyphens, underscores only).
- Keep the description short and descriptive.

**Examples:**
```
feat(models): add custom provider for Azure OpenAI
fix(channels): handle empty content_parts in Discord
docs(skills): document skill development workflow
```

### 4. Code and Quality

- **Pre-commit:** Install and run pre-commit for consistent style and checks:
  ```bash
  pip install -e ".[dev]"
  pre-commit install
  pre-commit run --all-files
  ```
- **Tests:** Run tests before submitting:
  ```bash
  pytest
  ```
- **Frontend formatting:** If your changes involve the `console` or `website` directories, run the formatter before committing:
  ```bash
  cd console && npm run format
  cd website && npm run format
  ```
- **Documentation:** Update docs and README when you add or change user-facing behavior. See [docs/README.md](docs/README.md) for the documentation hub.

---

## Types of Contributions

ProwlrBot is designed to be **extensible**: you can add models, channels, skills, and more. Below are the main contribution areas.

---

### Adding New Models / Model Providers

ProwlrBot supports **multiple model backends**: cloud APIs (OpenAI, Anthropic, Groq, Z.ai), **Ollama**, and local backends (**llama.cpp**, **MLX**). You can contribute in two ways:

#### A. Custom provider (user configuration)

Users can add **custom providers** via the Console or `providers.json`: any OpenAI-compatible API (e.g. vLLM, SGLang, private endpoints) can be configured with a unique ID, base URL, API key, and optional model list. No code change is required for standard OpenAI-compatible APIs.

#### B. New built-in provider or new ChatModel (code contribution)

If you want to add a **new built-in provider** or a **new API protocol** that is not OpenAI-compatible:

1. **Provider definition** (in `src/prowlrbot/providers/registry.py`):
   - Add a `ProviderDefinition` with `id`, `name`, `default_base_url`, `api_key_prefix`, and optionally `models` and `chat_model`.
   - For local/self-hosted backends, set `is_local` as appropriate.

2. **Chat model class** (if the API is not OpenAI-compatible):
   - Implement a class inheriting from `agentscope.model.ChatModelBase` (or ProwlrBot's local/remote wrappers where applicable).
   - Support streaming and non-streaming if the agent uses both; respect `tool_choice` and tools API if used.
   - Register the class in the registry's chat model map so the runtime can resolve it by name (see `_CHAT_MODEL_MAP` in `src/prowlrbot/providers/registry.py`).

3. **Documentation:** Document the new provider in the docs and mention any env vars or config keys.

Adding a fully new API (new message format, token counting, tools) is a larger change; we recommend opening an issue first to discuss scope and design.

---

### Adding New Channels

Channels are how ProwlrBot communicates with **Discord, Telegram, DingTalk, Feishu, QQ, iMessage**, and more. You can add a new channel for any IM or bot platform.

- **Protocol:** All channels use a unified in-process contract: **native payload -> `content_parts`** (e.g. `TextContent`, `ImageContent`, `FileContent`). The agent receives `AgentRequest` with these content parts; replies are sent back via the channel's send path.
- **Implementation:** Implement a **subclass of `BaseChannel`** (in `src/prowlrbot/app/channels/base.py`):
  - Set the class attribute `channel` to a unique channel key (e.g. `"telegram"`).
  - Implement the lifecycle and message handling (receive -> `content_parts` -> `process` -> send response).
  - Use the manager's queue and consumer loop if the channel is long-lived (default).
- **Discovery:** Built-in channels are registered in `src/prowlrbot/app/channels/registry.py`. **Custom channels** are loaded from `~/.prowlrbot/custom_channels/`: place a module that defines a `BaseChannel` subclass with a `channel` attribute.
- **CLI:** Users manage channels with:
  ```bash
  prowlr channels add <key>        # Add and configure
  prowlr channels remove <key>     # Remove
  prowlr channels list             # List all
  prowlr channels config           # Interactive config
  ```

If you contribute a **new built-in channel**, add it to the registry and document the new channel (auth, webhooks, etc.) in the docs.

---

### Adding Skills

**Skills** define what ProwlrBot can do: cron scheduling, file reading, PDF/Office processing, news, browser automation, etc. We welcome **broadly useful** skills that fit the majority of users.

- **Structure:** Each skill is a **directory** containing:
  - **`SKILL.md`** — Markdown instructions for the agent. Use YAML front matter for at least `name` and `description`.
  - **`references/`** (optional) — Reference documents the agent can use.
  - **`scripts/`** (optional) — Scripts or tools the skill uses.
- **Location:** Built-in skills live under `src/prowlrbot/agents/skills/<skill_name>/`. The app merges built-in and user customized skills from the working dir into `active_skills/`; no extra registration is needed beyond placing a valid `SKILL.md` in a directory.
- **Content:** Write clear, task-oriented instructions. Describe **when** the skill should be used and **how** (steps, commands, file formats).

#### Writing Effective Skill Descriptions

The `description` field in SKILL.md front matter must be **clear, specific, and include trigger keywords**:

```yaml
---
name: example_skill
description: "Use this skill whenever user wants to [main functionality]. Trigger especially when user mentions: [trigger keywords]. Also use when [other scenarios]."
---
```

**Best practices:**
1. **Clearly state when to trigger**: Use phrases like "Use this skill whenever user wants to..."
2. **List trigger keywords explicitly**: "Trigger especially when user mentions: \"call\", \"dial\", \"phone\""
3. **Be specific about scope**: What it does AND what it doesn't do
4. **Provide usage examples**: Show specific usage patterns in the body of SKILL.md

| Skill | Not ideal | Better |
|-------|-----------|--------|
| Desktop Control | "Control desktop applications" | "Use this skill whenever user wants to control desktop applications or make phone calls. Trigger especially when user mentions: \"call\", \"dial\", \"phone\"." |
| File Reader | "Read files" | "Use this skill when user asks to read or summarize local text-based files. PDFs and Office documents are out of scope." |

---

### Adding MCP Servers

ProwlrBot supports runtime **MCP tool** discovery and hot-plug. Contributing new MCP server integrations helps users extend the agent without changing core code. See [MCP Integration](README.md#mcp-integration) for config format.

---

### Platform Support

ProwlrBot aims to run on **Windows**, **Linux**, and **macOS**. Contributions that improve platform support are welcome:

- **Compatibility fixes:** Path handling, shell commands, platform-specific dependencies.
- **Install and startup:** `pip install prowlrbot` and `prowlr init` / `prowlr app` should work on each platform.
- **Platform-specific features:** Optional integrations are fine as long as they don't break other platforms. Use runtime checks or optional dependencies.
- **Documentation:** Document platform-specific steps or known limitations.

---

## Do's and Don'ts

### DO

- Start with small, focused changes
- Discuss large or design-sensitive changes in an issue first
- Write or update tests where applicable
- Update documentation for user-facing changes
- Use conventional commit messages and PR titles
- Be respectful and constructive

### DON'T

- Don't open very large PRs without prior discussion
- Don't ignore CI or pre-commit failures
- Don't mix unrelated changes in one PR
- Don't break existing APIs without a good reason and clear migration notes
- Don't add heavy or optional dependencies to the core install without discussing in an issue

---

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/mcpcentral/prowlrbot/issues)
- **Docs:** [docs/README.md](docs/README.md) — the documentation hub
- **Architecture:** [CLAUDE.md](CLAUDE.md) — full source layout and conventions

Thank you for contributing to ProwlrBot. Your work helps make it a better platform for everyone.
