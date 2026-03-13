# CLI Reference

Complete reference for every `prowlr` command group and subcommand.

**Default server:** `http://127.0.0.1:8088` (set with `prowlr --host HOST --port PORT`).

---

## Global flags

```
prowlr [--host HOST] [--port PORT] COMMAND ...
```

Both `--host` and `--port` default to the last-used values stored by the app (falls back to `127.0.0.1:8088`).

---

## `prowlr app`

Start the FastAPI/uvicorn server.

```bash
prowlr app                        # start on default port 8088
prowlr app --host 0.0.0.0         # listen on all interfaces
prowlr app --port 9000            # use custom port
prowlr app --debug                # verbose logging
```

The server starts the React console at `http://localhost:8088`.

---

## `prowlr init`

Initialize working directory (`~/.prowlrbot/config.json`).

```bash
prowlr init                       # interactive wizard
prowlr init --defaults            # skip prompts, accept all defaults
prowlr init --defaults --accept-security   # also accept security policy (for CI)
```

The wizard covers: provider API key, active model, channel selection, and skill selection.

---

## `prowlr channels`

Manage messaging channel configuration.

```bash
prowlr channels list              # show all channels and enabled/disabled status
prowlr channels config            # interactive configurator (TUI)
prowlr channels add discord       # add discord to config (runs interactive setup)
prowlr channels add telegram --no-configure   # add without prompting
prowlr channels install myslack   # scaffold custom channel stub in ~/.prowlrbot/custom_channels/
prowlr channels install myslack --path ./my_channel.py    # copy from file
prowlr channels install myslack --url https://...         # download from URL
prowlr channels remove myslack    # delete custom channel module + config entry
prowlr channels remove myslack --keep-config   # delete module only
```

Built-in channels: `console`, `discord`, `telegram`, `dingtalk`, `feishu`, `qq`, `imessage`.

See [Channel Setup Guide](channels.md) for per-channel setup instructions.

---

## `prowlr models`

Manage LLM providers and model selection.

```bash
prowlr models list                # show all providers and active model slot
prowlr models config              # interactive provider + model setup
prowlr models config-key [PROVIDER_ID]   # configure API key for one provider
prowlr models set-llm             # pick active LLM interactively

# User-added models
prowlr models add-model openai --model-id gpt-5-nano --model-name "GPT-5 Nano"
prowlr models remove-model openai --model-id gpt-5-nano

# Custom providers (OpenAI-compatible endpoints)
prowlr models add-provider my-api -n "My API" -u http://myhost/v1
prowlr models remove-provider my-api -y

# Local models (llama.cpp / MLX)
prowlr models download TheBloke/Mistral-7B-Instruct-v0.2-GGUF
prowlr models download TheBloke/Mistral-7B-Instruct-v0.2-GGUF -f mistral-7b-instruct-v0.2.Q4_K_M.gguf
prowlr models download Qwen/Qwen2-0.5B-Instruct-GGUF --source modelscope
prowlr models local               # list downloaded local models
prowlr models local -b llamacpp   # filter by backend
prowlr models remove-local MODEL_ID -y

# Ollama
prowlr models ollama-pull mistral:7b
prowlr models ollama-pull qwen2.5:3b
prowlr models ollama-list
prowlr models ollama-remove mistral:7b -y
```

Provider IDs: `openai`, `anthropic`, `groq`, `ollama`, `llamacpp`, `mlx`, `azure-openai`, `zai`, `dashscope`, `modelscope`, `aliyun-codingplan`.

See [Provider Configuration Guide](providers.md) for full setup details.

---

## `prowlr env`

Manage secrets stored in `~/.prowlrbot.secret/envs.json` (mode 0o600).

```bash
prowlr env list                   # list all stored keys (values shown plaintext)
prowlr env set OPENAI_API_KEY sk-...
prowlr env set ANTHROPIC_API_KEY sk-ant-...
prowlr env delete OPENAI_API_KEY
```

Keys stored here are automatically injected into the process at startup. This is the recommended way to store API keys — never put secrets in `config.json`.

---

## `prowlr skills`

Manage which skill packs are active in `~/.prowlrbot/active_skills/`.

```bash
prowlr skills list                # show all skills and enabled/disabled status
prowlr skills config              # interactive skill selection (TUI checkbox)
```

Built-in skills: `pdf`, `docx`, `pptx`, `xlsx`, `news`, `cron`, `file_reader`, `browser_visible`, `himalaya`, `dingtalk_channel`, `github_app`, `marketing`, `mac_doctor`, `wsl_doctor`.

See [Skills Guide](skills.md) for creating custom skills.

---

## `prowlr cron`

Manage scheduled jobs via the HTTP API (`/cron/jobs`).

```bash
prowlr cron list                  # list all cron jobs
prowlr cron get JOB_ID            # get one job by ID
prowlr cron state JOB_ID          # show runtime state (next run, paused?)

# Create from inline flags
prowlr cron create \
  --type agent \
  --name "Daily standup" \
  --cron "0 9 * * 1-5" \
  --channel console \
  --target-user me \
  --target-session default \
  --text "Summarize yesterday's commits and plan today"

# Create from JSON file
prowlr cron create -f job.json

prowlr cron pause JOB_ID          # pause a job
prowlr cron resume JOB_ID         # resume a paused job
prowlr cron run JOB_ID            # trigger once immediately
prowlr cron delete JOB_ID         # permanently delete
```

Task types: `agent` (prompt sent to agent, reply delivered to channel) and `text` (fixed message sent to channel).

See [Cron Jobs & Automation Guide](cron-jobs.md) for examples.

---

## `prowlr monitor`

Manage web/API monitors (stored in `~/.prowlrbot/monitors.json`).

```bash
prowlr monitor list
prowlr monitor add --name my-site --url https://example.com --interval 5m
prowlr monitor add --name my-site --url https://example.com --interval 5m \
  --type web --css-selector "h1.price"    # watch specific element
prowlr monitor add --name my-api --url https://api.example.com/status \
  --type api --expected-status 200 --json-path "$.status"
prowlr monitor remove my-site
prowlr monitor run my-site                # run check immediately
```

Intervals: `30s`, `5m`, `1h`, `24h`, etc.

See [Monitoring Guide](monitoring.md) for detailed setup.

---

## `prowlr market`

Browse, install, and publish marketplace packages.

```bash
prowlr market search "pdf tools"
prowlr market search "automation" -c skills --limit 20
prowlr market popular -l 10
prowlr market categories
prowlr market list                # show locally installed packages
prowlr market install LISTING_ID
prowlr market detail LISTING_ID
prowlr market review LISTING_ID --rating 5 --comment "Great skill!"
prowlr market tip LISTING_ID 2.50 -m "Thanks!"
prowlr market update              # sync registry from GitHub
prowlr market update --token $GITHUB_TOKEN

# Bundles
prowlr market bundles
prowlr market install-bundle BUNDLE_ID

# Publishing
prowlr market publish ./my-skill-dir -c skills --price 0 --pricing free
prowlr market publish ./my-skill-dir -c skills --price 4.99 --pricing one_time

# Credits and tiers
prowlr market credits
prowlr market tiers
prowlr market buy-credits
prowlr market upgrade pro
prowlr market repos
```

See [Marketplace Guide](marketplace.md) for publishing workflow.

---

## `prowlr agent`

Manage external agents (Claude Code, Codex, custom CLI, HTTP API, Docker).

```bash
prowlr agent install              # interactive wizard
prowlr agent install --type claude_code --command claude --name "claude-1"
prowlr agent install agents.yaml  # install from YAML/JSON file
prowlr agent list                 # list all installed agents
prowlr agent list --all           # include disabled agents
prowlr agent info AGENT_ID
prowlr agent health               # check health of all agents
prowlr agent health AGENT_ID
prowlr agent remove AGENT_ID
prowlr agent remove AGENT_ID --force
```

Backend types: `claude_code`, `codex`, `custom_cli`, `http_api`, `docker`.

---

## `prowlr team`

Manage agent teams (multi-agent coordination groups).

```bash
prowlr team list
prowlr team create "My Team"
prowlr team add TEAM_ID AGENT_ID
prowlr team remove TEAM_ID AGENT_ID
prowlr team delete TEAM_ID
```

---

## `prowlr swarm`

Manage the Redis-based remote execution swarm.

```bash
prowlr swarm status
prowlr swarm up                   # print docker compose command
prowlr swarm down
prowlr swarm logs
prowlr swarm logs -f              # follow logs
prowlr swarm capabilities         # list available capabilities
prowlr swarm config               # show env config (REDIS_HOST, etc.)
prowlr swarm enqueue browser:open -p url=https://example.com
prowlr swarm enqueue file:read -p path=~/Documents/notes.txt -w
prowlr swarm result JOB_ID --timeout 30
```

Capabilities: `browser:open`, `browser:screenshot`, `shell:execute`, `file:read`, `file:write`, `file:list`.

---

## `prowlr backup`

Backup and restore all ProwlrBot data.

```bash
prowlr backup create              # create backup to ~/.prowlrbot/backups/<timestamp>.tar.gz
prowlr backup create -o ~/my-backup.tar.gz
prowlr backup create --include-secrets   # also backup ~/.prowlrbot.secret/envs.json
prowlr backup list
prowlr backup restore ~/my-backup.tar.gz
prowlr backup restore ~/my-backup.tar.gz --force   # skip confirmation
```

---

## `prowlr export`

Export and manage data (GDPR-friendly).

```bash
prowlr export all                 # export to ~/prowlrbot-export-<timestamp>.tar.gz
prowlr export all -o my-data.tar.gz
prowlr export all --format json   # export as JSON
prowlr export chats               # export chat history only
prowlr export config              # print config.json with secrets redacted
prowlr export retention --days 30   # delete data older than 30 days
prowlr export retention --days 30 --dry-run   # preview what would be deleted
```

---

## `prowlr chats`

Manage chat history.

```bash
prowlr chats list
prowlr chats clear                # delete all chat history
```

---

## `prowlr migrate`

Database schema migrations for `~/.prowlrbot/prowlrbot.db`.

```bash
prowlr migrate status
prowlr migrate up                 # apply all pending migrations
prowlr migrate up --to 5          # apply migrations up to version 5
prowlr migrate down --to 3        # roll back to version 3
prowlr migrate history
```

---

## `prowlr acp`

Start ProwlrBot as an ACP (Agent Communication Protocol) server over stdio. Used for VS Code, Zed, and JetBrains integration.

```bash
prowlr acp
prowlr acp --debug
```

See [ACP / IDE Integration Guide](acp-ide-integration.md) for setup.

---

## `prowlr doctor`

Audit your Claude Code environment for token waste, broken hooks, and misconfiguration.

```bash
prowlr doctor                     # run audit (TUI if textual installed, else Rich report)
prowlr doctor --no-tui            # force Rich text report
prowlr doctor --profile developer   # use developer recommendation profile
prowlr doctor --profile security
prowlr doctor --profile minimal
prowlr doctor --profile agent-builder
prowlr doctor --profile research
prowlr doctor --json              # output JSON
prowlr doctor --write-plan        # write fix plan to ~/.claude/doctor-plan.json
prowlr doctor --diff              # show settings.json diff from saved plan
prowlr doctor --apply             # apply the saved plan
```

Requires `prowlr-doctor` package: `pip install prowlr-doctor`. For TUI: `pip install prowlr-doctor[tui]`.

---

## `prowlr studio`

Launch the ProwlrBot Studio (visual agent builder).

```bash
prowlr studio
```

---

## `prowlr completion`

Shell completion setup.

```bash
prowlr completion install         # install completion for current shell
prowlr completion bash            # print bash completion script
prowlr completion zsh
prowlr completion fish
```

---

## `prowlr clean`

Clean temporary files and caches.

```bash
prowlr clean
```

---

## `prowlr uninstall`

Remove all ProwlrBot data and config.

```bash
prowlr uninstall
prowlr uninstall --yes            # skip confirmation
```

---

## Quick reference

| Goal | Command |
|------|---------|
| Start server | `prowlr app` |
| First-time setup | `prowlr init` |
| Set an API key | `prowlr env set OPENAI_API_KEY sk-...` |
| Pick active model | `prowlr models set-llm` |
| Enable a skill | `prowlr skills config` |
| Add Discord | `prowlr channels add discord` |
| Schedule a job | `prowlr cron create --type agent ...` |
| Watch a website | `prowlr monitor add --name x --url https://...` |
| Install marketplace package | `prowlr market install LISTING_ID` |
| Health check all agents | `prowlr agent health` |
| Backup data | `prowlr backup create` |
| Audit Claude env | `prowlr doctor` |
