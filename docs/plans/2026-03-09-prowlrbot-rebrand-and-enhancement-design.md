# ProwlrBot: Rebrand & Enhancement Design

**Date**: 2026-03-09
**Status**: Approved
**Tagline**: "Always watching. Always ready."

---

## 1. Brand Identity

| Attribute | Value |
|-----------|-------|
| Brand name | **ProwlrBot** |
| CLI command | `prowlr` |
| Python package | `prowlrbot` |
| Config directory | `~/.prowlrbot/` |
| Secrets directory | `~/.prowlrbot.secret/` |
| Server port | `8088` |
| Tagline | "Always watching. Always ready." |

### Origin

ProwlrBot is a fork of CoPaw (agentscope-ai/CoPaw). CoPaw provided the foundation — channel system, agent architecture, skills, MCP, cron, memory, and React console. ProwlrBot rebrands and enhances it into an autonomous monitoring and AI agent platform.

---

## 2. Phase 0: Full Rebrand (CoPaw -> ProwlrBot)

**Must complete before any feature work.**

### Scope

- Rename Python package: `src/copaw/` -> `src/prowlrbot/`
- Update all imports: `from copaw.` -> `from prowlrbot.`
- CLI entry point: `copaw` -> `prowlr` (in pyproject.toml `[project.scripts]`)
- Config paths: `~/.copaw/` -> `~/.prowlrbot/`, `~/.copaw.secret/` -> `~/.prowlrbot.secret/`
- pyproject.toml: package name, description, version attribute
- Console frontend: all branding text, page titles, references
- Agent MD files: CoPaw references -> ProwlrBot
- Docker files (Dockerfile, docker-compose): image names, labels
- README.md, CLAUDE.md, CONTRIBUTING.md: all references
- Test files: import paths

### Safety Net

If the full rename breaks at runtime, keep a thin `src/copaw/__init__.py` re-export shim:
```python
# Backward compat — remove after stabilization
from prowlrbot import *
```

### Verification

- `pip install -e ".[dev]"` succeeds
- `prowlr --help` works
- `pytest` passes
- Console builds and loads

---

## 3. Phase 1: Provider Detection System (Spec 001)

**Foundation — all AI features depend on this.**

### Architecture

Enhances existing CoPaw provider system at `src/prowlrbot/providers/`:

```
src/prowlrbot/providers/
├── base.py              # ProviderDefinition, BaseChatModel ABC
├── registry.py          # ProviderRegistry (enhanced)
├── detector.py          # Auto-detect via env vars + URL probes
├── health.py            # Async health check probes
├── router.py            # SmartRouter with scoring engine
├── fallback.py          # FallbackChain with circuit breaker
├── capabilities.py      # Per-provider capability map
├── models/
│   ├── openai_compat.py # OpenAI, Groq, Together, Z.ai, LM Studio, Ollama
│   ├── anthropic_model.py
│   ├── cohere_model.py
│   ├── replicate_model.py
│   └── anythingllm_model.py
└── configs/
    ├── provider_defaults.py  # All 10+ provider definitions
    └── scoring_weights.py    # Routing score weights
```

### Supported Providers (Priority Order)

| Provider | API Style | Status | Priority |
|----------|-----------|--------|----------|
| Anthropic | Native Messages API | Active subscription | 1 - Test immediately |
| Z.ai (GLM-5) | OpenAI-compat | Active subscription | 2 - Test immediately |
| Ollama (Cloud) | OpenAI-compat | Available | 3 - Test next |
| Groq | OpenAI-compat | Can create | 4 - Set up and test |
| OpenAI | OpenAI-compat | Inactive (will reactivate) | 5 - Ready when key active |
| Together AI | OpenAI-compat | Available | 6 |
| Cohere | Native ClientV2 | Available | 7 |
| Replicate | Predictions API | Available | 8 |
| LM Studio | OpenAI-compat (local) | Available | 9 |
| AnythingLLM | REST API (local) | Available | 10 |

### Smart Routing

```
score(provider) = w_cost * cost_score + w_perf * perf_score + w_avail * avail_score
```

Default weights: cost=0.3, performance=0.4, availability=0.3. Configurable via env vars.

---

## 4. Phase 2: Parallel Feature Development

After Phase 0 + 1 complete, all of these run simultaneously via isolated agents:

### Agent A: Monitoring Engine (Roadmap Features 1-6)

New subsystem at `src/prowlrbot/monitor/`:

```
src/prowlrbot/monitor/
├── engine.py            # Core scheduler/executor (APScheduler integration)
├── config.py            # YAML config-as-code parser
├── detectors/
│   ├── web.py           # Web page change detection
│   ├── api.py           # REST API monitoring
│   └── rss.py           # RSS/Atom feeds
├── notifications/
│   ├── base.py          # Notification interface
│   ├── webhook.py       # Webhook (JSON payload)
│   ├── email_.py        # SMTP email
│   ├── discord_.py      # Discord (reuse channel)
│   └── telegram.py      # Telegram (reuse channel)
├── diff.py              # Content diffing engine
├── storage.py           # SQLite execution state
└── cli.py               # prowlr monitor subcommands
```

Key design: Reuses existing channel system for notifications. The monitoring engine plugs into the existing APScheduler cron system rather than creating a new one.

### Agent B: Embedded IDE (Spec 003)

Multi-agent orchestration UI at `src/prowlrbot/ide/` + new console pages.

### Agent C: AutoResearch Workflow (Spec 004)

Training workflow pipeline at `src/prowlrbot/research/`.

### Agent D: RAG Module (Spec 005)

Retrieval-augmented generation at `src/prowlrbot/rag/`.

### Agent E: Model Registry (Spec 006)

Upload/manage custom models at `src/prowlrbot/model_registry/`.

### Agent F: Phase 2+ Roadmap Features

Features 7-18: API monitoring, RSS feeds, execution logs, error handling, headless browser, pipelines, plugin architecture, dashboard, authenticated monitoring, security hardening, intelligent change analysis.

### Agent G: Library Updates & Dependency Audit

Update all dependencies to latest compatible versions. Verify no breaking changes.

---

## 5. What Stays the Same

The core architecture is enhanced, not rebuilt:

- **FastAPI + AgentScope ReAct agent** — same foundation
- **Channel system** — rebranded, same protocol (DingTalk, Feishu, Discord, Telegram, QQ, iMessage, Console)
- **Skills system** — rebranded, same SKILL.md manifest format
- **MCP integration** — rebranded, same stdio/http transports
- **Cron/scheduler** — enhanced with monitoring engine, not replaced
- **Memory system** — enhanced with RAG, not replaced
- **Console frontend** — rebranded, enhanced with new pages

---

## 6. New Capabilities (Beyond CoPaw)

| Capability | Description |
|------------|-------------|
| Smart Provider Routing | Auto-detect AI providers, health check, score, route, fallback |
| Web Monitoring Engine | Poll web pages, detect changes, CSS selectors, diffing |
| API Monitoring | REST endpoint health, JSON field tracking, response time alerts |
| RSS/Atom Monitoring | Feed tracking with keyword filters and deduplication |
| Notification System | Webhook, email, Discord, Telegram — pluggable |
| YAML Config-as-Code | Declarative monitor definitions, Git-friendly |
| RAG Module | Retrieval-augmented generation for knowledge bases |
| Model Registry | Upload, manage, and serve custom models |
| Embedded IDE | Multi-agent orchestration interface |
| AutoResearch | Training workflow pipeline |
| Headless Browser | Playwright-based JS-rendered page monitoring |
| Composable Pipelines | Multi-step monitoring workflows |
| Plugin Architecture | Community extensions for monitors and notifiers |
| Security Hardening | SSRF protection, sandboxing, credential encryption |
| Intelligent Analysis | Change significance scoring, noise filtering |

---

## 7. Docker Deployment

```yaml
# docker-compose.yml
services:
  prowlrbot:
    image: prowlrbot:latest
    ports:
      - "8088:8088"
    volumes:
      - prowlrbot-data:/app/working
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ZAI_API_KEY=${ZAI_API_KEY}
```

Target: `docker run prowlrbot` starts a working instance with zero config.

---

## 8. Success Criteria

- [x] `prowlr --help` works after rebrand
- [x] All existing tests pass with new package name
- [x] Console loads with ProwlrBot branding
- [x] Provider detection finds Anthropic + Z.ai from env vars
- [x] Smart routing selects best provider per request
- [x] Fallback chain activates on provider failure
- [x] Web monitor detects page changes and sends notifications
- [x] YAML config defines monitors declaratively (monitors.yaml / monitors.yml in working dir)
- [x] Docker deployment works with single command
- [x] No CoPaw references remain in user-facing surfaces
