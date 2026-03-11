# ProwlrBot Ecosystem Roadmap — What Goes Where

> Last updated: 2026-03-11
> Status: Active — work in progress across all repos

---

## Architecture Overview

```
prowlrbot (core)
  ├── fetches listings from → prowlr-marketplace (via registry.py)
  ├── implements spec from  → roar-protocol (via protocols/)
  ├── renders docs from     → prowlr-docs (via website or copy)
  └── integrates world from → agentverse (via API calls)

prowlr-marketplace
  └── manifest schema must match → prowlrbot MarketplaceListing model

roar-protocol
  └── spec layers must match → prowlrbot protocols/roar.py + sdk/

prowlr-docs
  └── content must match → prowlrbot website/public/docs/ files

agentverse
  └── credits/XP must integrate → prowlrbot credits economy
  └── guilds must map to       → prowlrbot team system
```

---

## 1. ProwlrBot/prowlrbot (Core Platform)

**Status:** Active development, main codebase

### What lives here
- All Python backend code (CLI, FastAPI, agents, marketplace store, registry sync)
- Console frontend (React/Ant Design admin UI)
- Marketing website (React/Vite landing page)
- Hub/War Room MCP server
- All CI/CD workflows
- Blog posts, docs that render on-site

### Remaining work

| Priority | Task | Status |
|----------|------|--------|
| P0 | Verify CI workflows pass after StrEnum + path traversal fixes | pending-ci |
| P0 | Dependabot alerts — pip deps need lockfile regeneration in CI | pending-ci |
| P1 | `prowlr market update` — test against real prowlr-marketplace repo content | todo |
| P1 | Privacy and Terms pages — create placeholder content for Footer links | todo |
| P1 | Blog posts reference old 12-category marketplace — update to 6 categories | todo |
| P2 | Website TechStack component — visual QA | todo |
| P2 | `file_io.py` line 17-18 — `.copaw.secret` backward compat: add deprecation warning | todo |
| P2 | Add marketplace/credits/tiers documentation pages | todo |
| P2 | Add agent install and team builder documentation pages | todo |

---

## 2. ProwlrBot/prowlr-marketplace (Registry)

**Status:** Forked from mcpcentral, needs population
**Priority:** 1 (highest — `prowlr market update` needs real content)

### What lives here
- Listing manifests (the "registry")
- Submission templates
- Category definitions (categories.json — 6 categories)
- Default packages that ship with ProwlrBot
- Publishing guidelines

### Work items

| Priority | Task | Details |
|----------|------|---------|
| P0 | README rebrand | Update from mcpcentral branding to ProwlrBot |
| P0 | Populate category directories | Create `skills/`, `agents/`, `prompts/`, `mcp-servers/`, `themes/`, `workflows/` with real listings |
| P1 | Default/starter listings | Add defaults that ship with every install (the `defaults/` directory) |
| P1 | Manifest schema alignment | Each manifest.json must match our `MarketplaceListing` model fields: id, title, description, author, version, tags, pricing_model, category |
| P1 | Add CONTRIBUTING.md | PR template for new listing submissions |
| P2 | Verify templates | Ensure `templates/` match MarketplaceListing model fields |
| P2 | Revenue sharing docs | Match our tier system (70/30 split, credit earn rates) |

### Starter listings to create

```
skills/
  ├── code-review/manifest.json      — Code review skill
  ├── web-monitor/manifest.json      — Web change detection
  └── pdf-reader/manifest.json       — PDF processing skill

agents/
  ├── prowlr-scout/manifest.json     — Research agent
  └── prowlr-guard/manifest.json     — Security monitoring agent

prompts/
  ├── business-analyst/manifest.json — Business analysis prompt pack
  └── code-assistant/manifest.json   — Coding prompt pack

mcp-servers/
  ├── prowlr-hub/manifest.json       — War Room coordination MCP
  └── prowlr-tools/manifest.json     — File/shell/browser tools MCP

themes/
  ├── dark-prowler/manifest.json     — Dark theme
  └── light-sentinel/manifest.json   — Light theme

workflows/
  ├── deploy-review/manifest.json    — Code review → deploy pipeline
  └── daily-standup/manifest.json    — Daily status aggregation
```

---

## 3. ProwlrBot/prowlr-docs (Documentation)

**Status:** Forked from mcpcentral, 17 topics en+zh
**Priority:** 2

### What lives here
- All user-facing documentation (en + zh)
- Getting started guides
- API reference
- Channel setup guides
- Skill development guides
- Architecture docs

### Work items

| Priority | Task | Details |
|----------|------|---------|
| P0 | README rebrand | Update from mcpcentral to ProwlrBot |
| P0 | Verify all 17 topic files exist and are current | Audit against website/public/docs/ |
| P1 | Docs sync strategy | Decide: copy docs to website/public/docs/ at build time, OR fetch from GitHub at runtime |
| P1 | Add marketplace documentation | Credits economy, tiers, publishing guide |
| P1 | Add agent install docs | `prowlr agent install`, external agents, backends |
| P1 | Add team builder docs | `prowlr team create`, coordination modes |
| P2 | Add protocol documentation | Or link to roar-protocol repo |
| P2 | Contributing guide as single source of truth | Main repo CONTRIBUTING.md links here |

### Missing doc topics

- `marketplace.en.md` — Browsing, installing, publishing, credits, tiers
- `agents-external.en.md` — Installing external agents (Claude Code, Codex, custom)
- `teams.en.md` — Creating teams, coordination modes, config files
- `credits.en.md` — Credits economy, earning, spending, premium content
- `privacy.en.md` — Privacy policy
- `terms.en.md` — Terms of service

---

## 4. ProwlrBot/roar-protocol (Protocol Spec)

**Status:** Forked from mcpcentral, specification stage
**Priority:** 3

### What lives here
- Protocol specification documents (the "RFC")
- Reference implementations or test vectors
- Compliance test suites
- Protocol versioning

### Work items

| Priority | Task | Details |
|----------|------|---------|
| P0 | README rebrand | Update from mcpcentral to ProwlrBot |
| P1 | Verify 5-layer spec alignment | Match against `src/prowlrbot/protocols/roar.py` and `protocols/sdk/` |
| P1 | Version the spec | Semver so implementations can declare compatibility |
| P2 | Identity layer → agent install | Should work with `agent_cmd.py` and external agent registry |
| P2 | Discovery layer → marketplace | Should work with marketplace search |
| P2 | Connect/Exchange/Stream → hub | Should work with hub coordination |
| P3 | Compliance test suite | Tests that verify a ROAR implementation is spec-compliant |

---

## 5. ProwlrBot/agentverse (Virtual World)

**Status:** Forked from mcpcentral, early stage
**Priority:** 4

### What lives here
- Zone definitions and world map
- XP/leveling mechanics
- Guild/team configs
- Battle/tournament rules
- Agent avatar assets
- AgentVerse-specific API

### Work items

| Priority | Task | Details |
|----------|------|---------|
| P0 | README rebrand | Update from mcpcentral to ProwlrBot |
| P1 | Zone definitions | Verify: Workshop, Arena, Library, Garden, Secret zones |
| P1 | Credits integration | XP/leveling ties into our credits economy |
| P2 | Guild → Team mapping | Guilds should map to our Team model (`team_cmd.py`) |
| P2 | Trading system | Use marketplace credits as currency |
| P2 | Avatar system | Agent identity from ROAR protocol |
| P3 | API endpoints | Design API that main prowlrbot app can call |
| P3 | Tier-gated access | Free=Basic, Pro=Full, Team=Premium zones + tournaments |

---

## Cross-Repo Standards (All Repos)

Every ProwlrBot repo must have:

- [ ] `README.md` with ProwlrBot branding (not mcpcentral)
- [ ] `CONTRIBUTING.md` or link to main repo's guide
- [ ] `LICENSE` (Apache 2.0, copyright "The ProwlrBot Authors")
- [ ] `.github/ISSUE_TEMPLATE/` with bug report + feature request
- [ ] `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] CI workflow (at minimum: lint, test if applicable)
- [ ] `SECURITY.md` or link to main repo's security policy

---

## Execution Priority

```
Week 1:  prowlr-marketplace — README rebrand, populate 12 starter listings
Week 1:  prowlr-docs — README rebrand, sync audit, add missing topics
Week 2:  roar-protocol — README rebrand, version spec, alignment check
Week 2:  agentverse — README rebrand, zone definitions
Week 2:  All repos — CONTRIBUTING.md, issue templates, CI
Week 3:  prowlr-marketplace — test prowlr market update end-to-end
Week 3:  prowlr-docs → website sync strategy implementation
Week 3:  Core platform — Privacy/Terms pages, visual QA, blog post updates
```

---

## Done (Completed This Session)

- [x] Fork all 4 ecosystem repos into ProwlrBot org
- [x] Fix all hardcoded URLs across main repo (15+ wrong paths)
- [x] Align marketplace categories: 12 → 6 (matching prowlr-marketplace)
- [x] Build registry sync module (`prowlr market update`)
- [x] Build `prowlr market repos` command
- [x] Add `/marketplace/repos` API endpoint
- [x] Patch 14 Dependabot vulnerabilities
- [x] Fix 8 code review bugs (enum validation, blocking IO, mkdir, etc.)
- [x] Update LICENSE copyright
- [x] Replace stale Chinese CONTRIBUTING_zh.md
- [x] Build 2.5D TechStack website component
- [x] Fix Footer/CommunitySection internal doc links
