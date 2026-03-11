# ProwlrBot Ecosystem Roadmap — What Goes Where

> Last updated: 2026-03-11
> Status: Active — Week 1 complete, moving to Week 2

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
| ~~P1~~ | ~~`prowlr market update` — test against real prowlr-marketplace repo content~~ | **done** |
| ~~P1~~ | ~~Privacy and Terms pages — create placeholder content for Footer links~~ | **done** |
| ~~P1~~ | ~~Blog posts reference old 12-category marketplace — update to 6 categories~~ | **done** (already clean) |
| P2 | Website TechStack component — visual QA | todo |
| ~~P2~~ | ~~`file_io.py` — legacy `.copaw.secret` backward compat: add deprecation warning~~ | **done** |
| ~~P2~~ | ~~Add marketplace/credits/tiers documentation pages~~ | **done** |
| ~~P2~~ | ~~Add team builder documentation pages~~ | **done** |
| ~~P2~~ | ~~Add agent install documentation page (external agents, backends)~~ | **done** |

---

## 2. ProwlrBot/prowlr-marketplace (Registry)

**Status:** Populated with 12 starter listings, README rebranded
**Priority:** 1 (highest)

### What lives here
- Listing manifests (the "registry")
- Submission templates
- Category definitions (categories.json — 6 categories)
- Default packages that ship with ProwlrBot
- Publishing guidelines

### Work items

| Priority | Task | Status |
|----------|------|--------|
| ~~P0~~ | ~~README rebrand~~ | **done** — full personality rewrite with badges, Metcalfe's Law quote, category browser |
| ~~P0~~ | ~~Populate category directories~~ | **done** — all 6 directories with real listings |
| ~~P1~~ | ~~Default/starter listings~~ | **done** — 12 listings across all 6 categories |
| ~~P1~~ | ~~Manifest schema alignment~~ | **done** — all manifests match MarketplaceListing model |
| ~~P1~~ | ~~Add CONTRIBUTING.md~~ | **done** — links to main repo guide |
| P2 | Verify templates | Ensure `templates/` match MarketplaceListing model fields |
| P2 | Revenue sharing docs | Match our tier system (70/30 split, credit earn rates) |

### Starter listings (all done)

```
skills/
  ├── code-review/manifest.json      ✅ Code review skill
  ├── web-monitor/manifest.json      ✅ Web change detection
  └── pdf-reader/manifest.json       ✅ PDF processing skill

agents/
  ├── prowlr-scout/manifest.json     ✅ Research agent
  └── prowlr-guard/manifest.json     ✅ Security monitoring agent

prompts/
  ├── business-analyst/manifest.json ✅ Business analysis prompt pack
  └── code-assistant/manifest.json   ✅ Coding prompt pack

mcp-servers/
  ├── prowlr-hub/manifest.json       ✅ War Room coordination MCP
  └── prowlr-tools/manifest.json     ✅ File/shell/browser tools MCP

themes/
  ├── dark-prowler/manifest.json     ✅ Dark theme
  └── light-sentinel/manifest.json   ✅ Light theme

workflows/
  ├── deploy-review/manifest.json    ✅ Code review → deploy pipeline
  └── daily-standup/manifest.json    ✅ Daily status aggregation
```

---

## 3. ProwlrBot/prowlr-docs (Documentation)

**Status:** README rebranded, 17 topics en+zh
**Priority:** 2

### What lives here
- All user-facing documentation (en + zh)
- Getting started guides
- API reference
- Channel setup guides
- Skill development guides
- Architecture docs

### Work items

| Priority | Task | Status |
|----------|------|--------|
| ~~P0~~ | ~~README rebrand~~ | **done** — Damian Conway quote, 17-topic table, contribution guide |
| P0 | Verify all 17 topic files exist and are current | todo — audit against website/public/docs/ |
| P1 | Docs sync strategy | todo — copy at build time vs fetch from GitHub at runtime |
| P1 | Add marketplace documentation | todo — credits economy, tiers, publishing guide |
| P1 | Add agent install docs | todo — `prowlr agent install`, external agents, backends |
| P1 | Add team builder docs | todo — `prowlr team create`, coordination modes |
| P2 | Add protocol documentation | todo — or link to roar-protocol repo |
| P2 | Contributing guide as single source of truth | todo — main repo CONTRIBUTING.md links here |

### Missing doc topics

- ~~`marketplace.en.md`~~ **done** — Browsing, installing, publishing, credits, tiers
- ~~`agents-external.en.md`~~ **done** — Installing external agents (Claude Code, Codex, custom)
- ~~`teams.en.md`~~ **done** — Creating teams, coordination modes, config files
- ~~`credits.en.md`~~ **done** — Credits economy, earning, spending, premium content
- ~~`privacy.en.md`~~ **done** — Privacy policy
- ~~`terms.en.md`~~ **done** — Terms of service

---

## 4. ProwlrBot/roar-protocol (Protocol Spec)

**Status:** README rebranded, specification stage
**Priority:** 3

### What lives here
- Protocol specification documents (the "RFC")
- Reference implementations or test vectors
- Compliance test suites
- Protocol versioning

### Work items

| Priority | Task | Status |
|----------|------|--------|
| ~~P0~~ | ~~README rebrand~~ | **done** — Shaw quote, 5-layer ASCII diagram, MCP/A2A comparison |
| P1 | Verify 5-layer spec alignment | todo — match against `src/prowlrbot/protocols/roar.py` and `protocols/sdk/` |
| ~~P1~~ | ~~Version the spec~~ | **done** — spec/VERSION.json with layer-level semver (v0.1.0) |
| P2 | Identity layer → agent install | todo — should work with `agent_cmd.py` and external agent registry |
| P2 | Discovery layer → marketplace | todo — should work with marketplace search |
| P2 | Connect/Exchange/Stream → hub | todo — should work with hub coordination |
| P3 | Compliance test suite | todo — tests that verify a ROAR implementation is spec-compliant |

---

## 5. ProwlrBot/agentverse (Virtual World)

**Status:** README rebranded, early stage
**Priority:** 4

### What lives here
- Zone definitions and world map
- XP/leveling mechanics
- Guild/team configs
- Battle/tournament rules
- Agent avatar assets
- AgentVerse-specific API

### Work items

| Priority | Task | Status |
|----------|------|--------|
| ~~P0~~ | ~~README rebrand~~ | **done** — The Shining quote, Club Penguin analogy, zone map |
| ~~P1~~ | ~~Zone definitions~~ | **done** — 6 zones (Workshop, Arena, Library, Garden, Vault, Nexus) + XP table + tier gating |
| P1 | Credits integration | todo — XP/leveling ties into credits economy |
| P2 | Guild → Team mapping | todo — guilds map to Team model (`team_cmd.py`) |
| P2 | Trading system | todo — marketplace credits as currency |
| P2 | Avatar system | todo — agent identity from ROAR protocol |
| P3 | API endpoints | todo — design API that main prowlrbot app can call |
| P3 | Tier-gated access | todo — Free=Basic, Pro=Full, Team=Premium zones + tournaments |

---

## Cross-Repo Standards (All Repos)

Every ProwlrBot repo must have:

- [x] `README.md` with ProwlrBot branding (not mcpcentral) — **done across all 5 repos**
- [x] `CONTRIBUTING.md` or link to main repo's guide — **done across all 4 ecosystem repos**
- [x] `LICENSE` (Apache 2.0, copyright "The ProwlrBot Authors") — **done across all 5 repos**
- [x] `.github/ISSUE_TEMPLATE/` with bug report + feature request — **done across all 4 ecosystem repos**
- [x] `.github/PULL_REQUEST_TEMPLATE.md` — **done across all 4 ecosystem repos**
- [x] CI workflow (at minimum: lint, test if applicable) — **done across all 4 ecosystem repos**
- [x] `SECURITY.md` or link to main repo's security policy — **done across all 4 ecosystem repos**

---

## Execution Priority

```
Week 1:  ████████████████████████████████████████ 100%
  ✅ prowlr-marketplace — README rebrand, populate 12 starter listings
  ✅ prowlr-docs — README rebrand
  ✅ roar-protocol — README rebrand
  ✅ agentverse — README rebrand
  ✅ Core — Privacy/Terms pages, CoPaw purge, market update tested

Week 2:  ████████████████████████████████████████ 100%
  ✅ roar-protocol — VERSION.json with layer versioning (v0.1.0)
  ✅ agentverse — 6 zone definitions with XP table and tier gating
  ✅ All repos — CONTRIBUTING.md, LICENSE, issue templates, SECURITY.md, PR templates
  ✅ All repos — CI workflows (manifest validation, spec checks, zone validation, doc checks)
  ✅ prowlr-docs — marketplace, teams, credits doc pages created
  ✅ prowlr-docs — sync audit complete (23 topics, all sidebar entries match files)

Week 3:  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%
  ☐ prowlr-marketplace — CONTRIBUTING.md, template verification
  ☐ prowlr-docs → website sync strategy implementation
  ☐ Core platform — visual QA, deprecation warnings, new doc pages
```

---

## Done (All Sessions)

### Session 1 — Phase 2 Design
- [x] 60+ feature specs in leapfrog design doc
- [x] Competitive analysis (Manus, Devin, AutoGPT, OpenClaw, etc.)
- [x] 12-month roadmap (Q1-Q4)
- [x] 26 security vulnerabilities identified

### Session 2 — Phase 2 Implementation
- [x] Credits economy (CreditTransaction, CreditBalance, earn rates, tiers)
- [x] Marketplace models (6 categories, pricing, listings, reviews)
- [x] ACP server protocol implementation
- [x] Hub security hardening (19 audit findings fixed)
- [x] 76 security tests for learning engine, bridge API, war room
- [x] Session tokens, rate limiting, CSRF protection

### Session 3 — Ecosystem Buildout
- [x] Fork all 4 ecosystem repos into ProwlrBot org
- [x] Fix all hardcoded URLs across main repo (15+ wrong paths)
- [x] Align marketplace categories: 12 → 6 (matching prowlr-marketplace)
- [x] Build registry sync module (`prowlr market update`)
- [x] Build `prowlr market repos` command
- [x] Add `/marketplace/repos` API endpoint
- [x] Patch 14 Dependabot vulnerabilities (npm overrides + pip pins)
- [x] Fix 8 code review bugs (enum validation, blocking IO, mkdir, etc.)
- [x] Update LICENSE copyright (CoPaw → ProwlrBot Authors)
- [x] Replace stale Chinese CONTRIBUTING_zh.md with English redirect
- [x] Build 2.5D TechStack website component (25 tiles, 6 categories)
- [x] Fix Footer/CommunitySection internal doc links
- [x] Populate prowlr-marketplace with 12 starter listings (all 6 categories)
- [x] Rebrand all 4 ecosystem repo READMEs with personality and quotes
- [x] Rebrand org-github-template/profile/README.md
- [x] Remove all CoPaw references from user-facing content
- [x] Create Privacy Policy page (privacy.en.md)
- [x] Create Terms of Service page (terms.en.md)
- [x] Update Bug Reports & Community page (stale Discord/DingTalk → GitHub)
- [x] Add Privacy & Terms to docs sidebar + i18n
- [x] Test `prowlr market update` end-to-end — 13 listings synced
- [x] Test `prowlr market repos` — all 5 ecosystem repos display
