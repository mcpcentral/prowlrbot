# ProwlrDoctor — Design Spec

**Date:** 2026-03-12
**Status:** Approved for implementation
**Repo:** `ProwlrBot/prowlr-doctor` (standalone) + `prowlr doctor` CLI wrapper in prowlrbot

---

## What It Is

ProwlrDoctor is a **security-aware agent environment auditor with token cost intelligence**. It reads
a Claude Code environment (`settings.json`, installed plugins, hooks, agent registries, MCP servers,
CLAUDE.md, memory files) and produces:

- A full token overhead breakdown, measurable to the nearest thousand tokens
- Security findings (broken hooks, dangerous hook stacks, plugin conflicts)
- Profile-based recommendations (developer / security / agent-builder / minimal / research)
- A safe, reviewable batch of settings changes that can be applied in one command
- JSON output for statusline and community dashboard integration

It is **not** a plugin linter. It is an **agent ecosystem auditor**.

---

## Names and CLI

| Context | Command |
|---|---|
| Standalone (pip install prowlr-doctor) | `prowlr-doctor` |
| Integrated into prowlrbot | `prowlr doctor` |
| Claude Code plugin | `/prowlr-doctor` |
| Repo | `ProwlrBot/prowlr-doctor` |

### CLI Flags

```
prowlr doctor                         # full audit, beautiful TUI
prowlr doctor --profile security      # security-focused recommendations
prowlr doctor --profile minimal       # strip to bare minimum
prowlr doctor --profile developer     # developer tooling focus
prowlr doctor --profile agent-builder # agent building focus
prowlr doctor --profile research      # research/exploration focus
prowlr doctor --json                  # machine-readable output (also writes ~/.claude/doctor-cache.json)
prowlr doctor --write-plan            # write fix plan to ~/.claude/doctor-plan.json
prowlr doctor --diff                  # show exact settings.json diff before/after (reads plan from disk)
prowlr doctor --apply                 # apply plan at ~/.claude/doctor-plan.json (error if missing)
prowlr doctor --no-tui                # Rich report only, no Textual app
```

**`--apply` behavior:**
- Reads `~/.claude/doctor-plan.json`; exits with error and helpful message if not found
- Writes to a temp file first, then atomically renames to `settings.json` (never partial write)
- Creates a timestamped backup: `~/.claude/settings.json.bak.<timestamp>` before applying
- On partial failure (disk error during write): restores from backup, exits non-zero
- All `FixAction` entries with `action_type = "condense"` are skipped and listed as "manual required"

**`--json` behavior:**
- Writes JSON to stdout
- Also writes the same payload to `~/.claude/doctor-cache.json` for statusline consumption
- Cache is always written on any normal (non-`--apply`) run so statusline stays fresh

---

## Architecture

### Repository Layout

```
prowlr-doctor/
├── src/prowlr_doctor/
│   ├── __init__.py
│   ├── __main__.py          # python -m prowlr_doctor entry point
│   ├── cli.py               # Click CLI (prowlr-doctor command)
│   ├── models.py            # Finding, FixAction, TokenBudget, PatchPlan dataclasses
│   ├── paths.py             # Claude Code path constants (~/.claude, plugin cache, etc.)
│   ├── tokens.py            # Token counting via tiktoken (cl100k_base)
│   ├── scanner.py           # Orchestrator — runs all auditors, collects Finding list
│   ├── recommender.py       # Profile-aware keep/disable/review classification
│   ├── patch_planner.py     # Produce exact settings.json changes + diff
│   ├── reporter.py          # Rich terminal report renderer
│   ├── auditors/
│   │   ├── __init__.py
│   │   ├── base.py          # BaseAuditor ABC → list[Finding]
│   │   ├── plugins.py       # Duplicate plugin registries, version conflicts
│   │   ├── hooks.py         # Hook events, import paths, injection sizes
│   │   ├── agents.py        # Bundle sizes, byte-identical duplicates
│   │   ├── mcp.py           # MCP server health, duplicate tool names
│   │   ├── claude_md.py     # CLAUDE.md verbosity, redundant instructions
│   │   ├── memory.py        # Stale memory files (>30 days, >5k tokens)
│   │   └── security.py      # Broken imports, dangerous patterns, conflicts
│   └── tui/
│       ├── __init__.py
│       ├── app.py           # Textual TUI app (main interactive mode)
│       ├── screens/
│       │   ├── audit_screen.py   # Findings list + detail panel
│       │   └── fix_screen.py     # Interactive per-finding approve/skip
│       └── widgets/
│           ├── findings_list.py  # Scrollable findings panel
│           ├── detail_panel.py   # Detail + fix preview
│           └── summary_bar.py    # Top summary strip (counts + savings)
├── tests/
│   ├── fixtures/            # Synthetic settings.json, plugin dirs for testing
│   ├── test_models.py
│   ├── test_tokens.py
│   ├── test_auditors/
│   └── test_reporter.py
├── pyproject.toml
└── README.md
```

### Data Flow

```
settings.json + plugin cache + hooks.json + CLAUDE.md + memory files
        │
        ▼
   paths.py + scanner.py (parse settings, build EnvironmentSnapshot)
        │
        ├──► auditors/plugins.py  ──► list[Finding]
        ├──► auditors/hooks.py    ──► list[Finding]
        ├──► auditors/agents.py   ──► list[Finding]
        ├──► auditors/mcp.py      ──► list[Finding]
        ├──► auditors/claude_md.py ──► list[Finding]
        ├──► auditors/memory.py   ──► list[Finding]
        ├──► auditors/security.py ──► list[Finding]  [Sub-project 1 runs this]
        └──► tokens.py ──────────── TokenBudget (runs across all findings)
                    │
                    ▼
             recommender.py (profile-aware) ──► Recommendations
                    │
                    ▼
             patch_planner.py ──► PatchPlan (exact settings changes)
                    │
                    ├──► reporter.py ──► Rich terminal report (--no-tui)
                    ├──► tui/app.py  ──► Textual interactive app (default)
                    └──► json        ──► --json output → ~/.claude/doctor-cache.json
```

**Note on `security.py` scope:** `auditors/security.py` ships in Sub-project 1 with the
checks that are statically testable (broken import paths, duplicate PreToolUse hooks,
dangerous patterns via AST inspection). The deeper security profiles (`--profile security`
with network-aware checks) expand in Sub-project 3.

---

## Core Data Types

```python
@dataclass
class EnvironmentSnapshot:
    """Parsed Claude Code environment — passed to every auditor."""
    settings_path: Path                        # ~/.claude/settings.json
    settings: dict                             # raw parsed JSON
    enabled_plugins: dict[str, bool]           # plugin_id → enabled
    mcp_servers: dict[str, dict]               # server_id → config
    hooks: list[dict]                          # raw hook entries
    plugin_cache_dir: Path                     # ~/.claude/plugins/cache/
    global_claude_md: Path | None              # ~/.claude/CLAUDE.md
    project_claude_md: list[Path]              # all CLAUDE.md in cwd tree
    memory_files: list[Path]                   # ~/.claude/projects/*/memory/*.md
    installed_plugin_dirs: dict[str, Path]     # plugin_id → resolved cache dir

@dataclass
class Finding:
    id: str                        # stable ID (e.g. "dup-example-skills")
    severity: Literal["critical", "high", "medium", "info"]
    category: Literal["security", "token-waste", "duplicate", "conflict", "stale", "verbosity"]
    title: str
    detail: str                    # human explanation shown in TUI detail panel
    tokens_wasted: int             # 0 if not applicable
    fix_action: FixAction | None   # machine-actionable fix (None = manual action needed)
    explainability: str            # one-sentence "why this costs you"

# action_type values:
#   disable/enable → settings.json enabledPlugins toggle
#   patch          → any other settings.json key change
#   condense       → human must edit file (CLAUDE.md, memory file); fix_action = None
#   fix-import     → update a hook's sys.path (security.py findings)
ActionType = Literal["disable", "enable", "patch", "condense", "fix-import"]

@dataclass
class FixAction:
    action_type: ActionType
    target: str                    # plugin ID, hook name, file path, etc.
    settings_path: list[str] | None  # JSON path for settings.json changes; None for condense
    before: Any
    after: Any
    reversible: bool               # True for all disable/enable; False for patch
    requires_restart: bool         # False for all settings.json changes (Claude hot-reloads)

@dataclass
class Recommendations:
    profile: str
    disable: list[Finding]         # safe to disable with no functionality loss in this profile
    review: list[Finding]          # potential savings, needs human judgment
    keep: list[Finding]            # do not touch
    condense: list[Finding]        # manual file edits recommended (CLAUDE.md, memory)

@dataclass
class TokenBudget:
    per_session_fixed: int         # injected once at session start (CLAUDE.md, memory, hooks)
    per_turn_recurring: int        # injected every turn (skill list, recurring hooks)
    on_demand: int                 # loaded when specific skills invoked
    wasted: int                    # tokens from confirmed duplicates / broken items
    savings_if_cleaned: int        # tokens saved if all disable recommendations applied
    session_estimate_20turn: int   # total for a typical 20-turn session

@dataclass
class PatchPlan:
    version: str                   # schema version, currently "1"
    generated_at: str              # ISO8601
    profile: str
    findings_count: int
    actions: list[FixAction]       # ordered: low-risk first, high-risk last
    estimated_savings: int         # tokens saved if all applied
    settings_diff: dict            # {"before": {...}, "after": {...}}
    plan_path: Path                # where this plan was written (~/.claude/doctor-plan.json)
```

### Token Counting

`tokens.py` wraps `tiktoken.get_encoding("cl100k_base")` which is GPT-4's tokenizer —
close but **not identical** to Claude's vocabulary. Counts will be within ~5% accuracy,
sufficient for relative comparisons ("this registry wastes ~133k tokens") but should not
be presented as exact. All UI output uses "~" prefix and rounds to nearest 500 tokens.

---

## Analyzers

### 1. `paths.py` + `scanner.py`

Reads `~/.claude/settings.json`. Handles:
- `enabledPlugins` map (True/False values)
- `mcpServers` map
- `hooks` entries
- `model` and `statusLine` config
- Custom plugin dirs and cache paths

Also scans:
- `~/.claude/CLAUDE.md` (global)
- `<project>/CLAUDE.md` (project)
- `~/.claude/projects/*/memory/*.md` files
- `~/.claude/plugins/cache/` for installed plugin dirs

### 2. `auditors/plugins.py`

For each enabled plugin:
- Read plugin manifest (`plugin.json` or equivalent)
- Count: total agents, hooks, MCP registrations, skill files
- Detect: duplicate IDs across plugins (same agent name in two plugins)
- Detect: plugin version conflicts (same plugin from two registries)
- Classify: system (do not disable), recommended, optional, redundant

### 3. `auditors/hooks.py`

For each registered hook:
- Identify event type: PreToolUse, PostToolUse, Stop, UserPromptSubmit, SessionStart
- **Validate import path via AST/static inspection** (NOT `exec`): parse the hook file
  with `ast.parse()`, extract `import` and `from ... import` statements, check that
  `sys.path` inserts resolve to real directories containing the imported module
- Detect: multiple PreToolUse hooks (security concern — each adds interception overhead)
- Detect: SessionStart hooks that inject large prompts (measure token cost via `tokens.py`)
- Detect: duplicate hook logic (same pattern, two files)
- Classify each hook: essential / redundant / broken / high-overhead

### 4. `auditors/agents.py`

- Count total agents across all enabled plugins
- Group by bundle (plugin source)
- Estimate token overhead per bundle (agent definitions are injected into skill list)
- Detect: bundles with 50+ agents (voltagent pattern — high per-turn skill list overhead)
- Identify: byte-identical agent definitions across bundles (exact duplicates)
- Flag: agent files > 10KB (high per-invocation cost)

### 5. `auditors/mcp.py`

For each MCP server in `EnvironmentSnapshot.mcp_servers`:
- Check the binary path exists and is executable (`os.access(path, os.X_OK)`)
- Classify: essential (jcodemunch, serena) / productivity / niche / unknown
  based on a hard-coded well-known list; unknown → info finding
- Detect: duplicate entries (same binary path registered twice)
- **Live `tools/list` probe is out of scope for Sub-project 1.** Spawning and querying
  stdio MCP servers requires process lifecycle management beyond this phase.
  Tool count estimation is deferred to Sub-project 2.

### 6. `auditors/security.py`

Catches what generic plugin linters miss:

Detection is via **static AST analysis** of hook files -- no execution, no subprocess.

| Check | Detection Method | Why It Matters |
|---|---|---|
| Broken hook import path | AST: parse sys.path.insert args, check dir + module exist | Hook fails silently; security rule never enforces |
| Multiple PreToolUse hooks | Count hooks with event: PreToolUse | Each adds latency; conflicting rules can cancel each other |
| Hooks with unsafe subprocess usage | AST: detect subprocess.run/os.system patterns in hook source | Command injection surface in your own tooling |
| Duplicate security plugins from two registries | Cross-plugin ID comparison | Conflicting rules; one may shadow the other |
| SessionStart hooks injecting >2000 tokens | Token count the injected content | Large injections on every session start inflate cost |
| MCP server binary missing or not executable | os.access path check | Silent failures; server listed but never responds |

### 7. `tokens.py` (token counting + budget)

Produces the `TokenBudget` from measured values:

**Per-session fixed costs:**
- CLAUDE.md (global) — count tokens
- CLAUDE.md (project) — count tokens
- Memory files — sum all `~/.claude/projects/<hash>/memory/*.md`
- SessionStart hooks — count tokens injected
- Plugin system-reminder (initial) — estimate from agent count

**Per-turn recurring costs:**
- Skill list in system-reminder — 150 chars × enabled agent count → tokens
- Any hook that fires every turn

**Waste detection:**
- Identify byte-identical agent registries → full token count × 2 = waste
- Style plugins that duplicate each other

**Output example:**
```
Session overhead:    ~18,400 t   (injected once at start)
Per-turn overhead:   ~4,800 t    (every tool call)
20-turn session:     ~114,400 t  total
Wasted (duplicates): ~133,533 t  (example-skills registry)
Savings potential:   ~133,533 t  → ~$0.40/session at Sonnet pricing
```

### 8. `recommender.py` (profile engine)

Profile-aware recommendation engine. Takes all findings + profile name → `Recommendations`.

For each profile, applies a different disposition to each finding category:

| Finding Category | developer | security | minimal | agent-builder | research |
|---|---|---|---|---|---|
| Duplicate registry | DISABLE | DISABLE | DISABLE | DISABLE | DISABLE |
| Voltagent bundle (unused domain) | REVIEW | DISABLE | DISABLE | KEEP | KEEP |
| Broken security hook | DISABLE+fix-import | DISABLE+fix-import | DISABLE+fix-import | DISABLE+fix-import | DISABLE+fix-import |
| Style/output plugin | KEEP | REVIEW | DISABLE | KEEP | REVIEW |
| Niche MCP server | KEEP | REVIEW | DISABLE | KEEP | KEEP |
| Verbose CLAUDE.md | KEEP | CONDENSE | CONDENSE | KEEP | KEEP |
| Stale memory file | REVIEW | DISABLE | DISABLE | REVIEW | REVIEW |

Output lists:
- **`disable`** — safe, clear savings, no functionality loss in this profile (`action_type: disable`)
- **`review`** — potential savings, needs human judgment
- **`keep`** — do not touch
- **`condense`** — manual file edit recommended; no `FixAction` (cannot be auto-applied)

### 9. `patch_planner.py` (fix plan generation)

Takes the `Recommendations` list and produces:
- A `PatchPlan` with exact `settings.json` changes
- A human-readable diff showing before/after
- Ordered by risk (low-risk / reversible changes first)
- Each action tagged: `reversible: true/false`, `requires_restart: bool`

### 10. `reporter.py` (Rich, `--no-tui` mode)

Renders a Beautiful Rich terminal report:

```
  ProwlrDoctor v1.0 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Profile: developer  ·  30 plugins  ·  8 hooks  ·  2 MCP servers

  ● CRITICAL   example-skills registry — 133,533 tokens wasted/session
    Byte-identical copy of claude-api. Safe to disable.
    Fix: set enabledPlugins["example-skills@anthropic-agent-skills"] = false

  ◆ SECURITY   hookify@claude-code-plugins — broken import path
    from hookify.core.config_loader import load_rules → ImportError
    Fix: disable hookify@claude-code-plugins, use hookify@claude-plugins-official

  ◆ MEDIUM     5 voltagent bundles — ~2,600 tokens/turn not in developer profile
    Only voltagent-lang and voltagent-dev-exp used; rest optional for your profile.

  ✓ CLEAN      8 hooks — no conflicts, import paths verified
  ✓ CLEAN      2 MCP servers — binaries present, paths valid

  ─────────────────────────────────────────────────────────────────────
  Current:   ~114,400 t/session  →  After cleanup: ~79,200 t/session
  Savings:   ~35,200 t/session  ·  ~$0.11/session at Sonnet-4.6 pricing

  [prowlr doctor --write-plan] to generate a reviewable fix plan
  [prowlr doctor --apply]      to apply it
```

### 11. `tui/app.py` (Textual, default mode)

Full-screen Textual app modelled on `htop`/`lazygit` aesthetics:

```
┌─ ProwlrDoctor v1.0  ──────────────────────────────────────────────────┐
│ SUMMARY  Plugins: 30  Hooks: 8  MCP: 2  ● 1 critical  ◆ 2 medium     │
├───────────────────┬───────────────────────────────────────────────────┤
│ FINDINGS          │ DETAIL                                             │
│                   │                                                    │
│ ● example-skills  │ Duplicate registry: example-skills@anthropic-...  │
│ ◆ hookify (old)   │ Byte-identical copy of claude-api (133,533 t)     │
│ ◆ voltagent x5    │ All 66 skills present in claude-api already.      │
│ ✓ hooks clean     │                                                    │
│ ✓ MCP valid       │ [D] Disable  [S] Skip  [V] View diff  [Q] Quit   │
│                   │                                                    │
├───────────────────┴───────────────────────────────────────────────────┤
│ Savings estimate: ~133k tokens/session  ·  ~$0.40/session saved       │
└───────────────────────────────────────────────────────────────────────┘
```

**Keyboard shortcuts:**
- `↑↓` — navigate findings
- `D` — approve disable for selected finding
- `S` — skip (mark keep)
- `V` — view exact settings.json diff for this fix
- `A` — apply all approved actions
- `P` — cycle profiles (developer → security → minimal → agent-builder → research)
- `W` — write plan to disk
- `Q` — quit

---

## JSON Output Schema

```json
{
  "version": "1",
  "generated_at": "2026-03-12T...",
  "profile": "developer",
  "environment": {
    "plugins_enabled": 30,
    "hooks_count": 8,
    "mcp_servers": 2,
    "agents_total": 222
  },
  "token_budget": {
    "per_session_fixed": 18400,
    "per_turn_recurring": 4800,
    "on_demand": 5616,
    "wasted": 133533,
    "savings_if_cleaned": 133533,
    "session_estimate_20turn": 114400
  },
  "findings": [
    {
      "id": "dup-example-skills",
      "severity": "critical",
      "category": "token-waste",
      "title": "example-skills registry duplicates claude-api",
      "tokens_wasted": 133533,
      "fix_action": {
        "action_type": "disable",
        "target": "example-skills@anthropic-agent-skills",
        "settings_path": ["enabledPlugins", "example-skills@anthropic-agent-skills"],
        "before": true,
        "after": false,
        "reversible": true,
        "requires_restart": false
      }
    }
  ],
  "recommendations": {
    "disable": ["example-skills@anthropic-agent-skills"],
    "review": ["voltagent-biz@voltagent-subagents"],
    "keep": ["hookify@claude-plugins-official"],
    "condense": ["~/.claude/CLAUDE.md"]
  }
}
```

---

## Integration with prowlrbot

`prowlr doctor` in prowlrbot is a thin wrapper in `src/prowlrbot/cli/`:

```python
# src/prowlrbot/cli/doctor.py
import click
try:
    from prowlr_doctor.cli import run_audit
except ImportError:
    run_audit = None

@click.command("doctor")
@click.option("--profile", default="developer")
@click.option("--json", "as_json", is_flag=True)
@click.option("--write-plan", is_flag=True)
@click.option("--diff", is_flag=True)
@click.option("--apply", is_flag=True)
@click.option("--no-tui", is_flag=True)
def doctor_cmd(profile, as_json, write_plan, diff, apply, no_tui):
    """Audit your Claude Code environment for token waste and security issues."""
    if run_audit is None:
        click.echo("prowlr-doctor not installed. Run: pip install prowlr-doctor")
        raise SystemExit(1)
    run_audit(profile=profile, as_json=as_json, write_plan=write_plan,
              diff=diff, apply=apply, no_tui=no_tui)
```

---

## Statusline Integration

`prowlr doctor --json` writes a cache to `~/.claude/doctor-cache.json`. The statusline
script reads this cache (never runs a full audit inline) and shows:

```
◆ 133k wasted  ·  prowlr doctor to fix
```

or when clean:

```
✓ env clean
```

---

## Anonymous Telemetry (opt-in, Sub-project 3)

After a successful audit, if user has opted in (`prowlr doctor --opt-in-telemetry`):

```json
{
  "plugins_total": 30,
  "agents_total": 222,
  "tokens_wasted": 133533,
  "tokens_saved": 133533,
  "profile": "developer",
  "os": "linux",
  "prowlrbot_version": "0.1.x"
}
```

No PII. No file paths. No plugin names. Sent to `https://doctor.prowlrbot.com/telemetry`.

Aggregated and displayed on community dashboard (Sub-project 4):
> "2,847 users audited · 284M tokens saved · $852 saved this month"

---

## Build Order

1. **Sub-project 1 (this spec):** `paths.py` + `scanner.py` + `auditors/` (plugins, hooks, agents, mcp, claude_md, memory, security) + `tokens.py` + `recommender.py` + `reporter.py` + CLI
2. **Sub-project 2:** Textual TUI (`tui/app.py`)
3. **Sub-project 3:** `auditors/security.py` deeper profiles + telemetry client
4. **Sub-project 4:** Community dashboard (web app + collection endpoint)

Each sub-project ships independently. Sub-project 1 is a complete useful tool on its own.

---

## Dependencies

| Package | Purpose | Version |
|---|---|---|
| `click` | CLI | ≥8.0 |
| `rich` | Terminal report | ≥13.0 |
| `textual` | TUI app (Sub-project 2) | ≥0.60 |
| `tiktoken` | Accurate token counting (cl100k_base encoding) | ≥0.5 |
| `httpx` | Telemetry client | ≥0.27 |

`tiktoken` replaces heuristic estimates (chars ÷ 4) with accurate per-content token counts
from the same tokenizer Claude uses. This makes the savings estimates trustworthy.

No dependencies beyond the standard library for Sub-project 1 except `click`, `rich`, and `tiktoken`.

---

## Testing Strategy

- Unit tests for each analyzer with fixture `settings.json` files
- Fixture environments: minimal (5 plugins), typical (30), bloated (55 with duplicates)
- Integration test: run full audit against real `~/.claude/settings.json` in CI
- Snapshot tests for reporter output (assert Rich output matches expected)
- No network calls in tests (mock the MCP binary check and registry fetch)
