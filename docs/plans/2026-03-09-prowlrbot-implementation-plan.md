# ProwlrBot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebrand CoPaw to ProwlrBot, build provider detection system, then launch parallel agents for all remaining features.

**Architecture:** Fork of CoPaw. Original source deleted from `src/copaw/`, backup at `prowlrbot/dupe/src/copaw/` (194 Python files). Restore as `src/prowlrbot/`, rename all internals, then build new features on top.

**Tech Stack:** Python 3.10+, FastAPI, AgentScope, APScheduler, React 18 + Vite + Ant Design, pytest + pytest-asyncio

---

## Phase 0: Full Rebrand (CoPaw → ProwlrBot)

### Task 1: Restore Source and Rename Package Directory

**Files:**
- Source: `prowlrbot/dupe/src/copaw/` (194 Python files + assets)
- Create: `src/prowlrbot/` (renamed copy)

**Step 1: Copy dupe source to new location**

```bash
mkdir -p src
cp -r prowlrbot/dupe/src/copaw src/prowlrbot
```

**Step 2: Verify copy**

```bash
find src/prowlrbot -name "*.py" | wc -l
```
Expected: 194 (or close — same as dupe)

**Step 3: Commit raw copy before renaming**

```bash
git add src/prowlrbot/
git commit -m "chore: restore copaw source as prowlrbot package (pre-rename)"
```

---

### Task 2: Rename All Python Imports (copaw → prowlrbot)

**Files:**
- Modify: ALL `.py` files in `src/prowlrbot/`

**Step 1: Bulk rename imports**

```bash
# Replace all 'from copaw.' with 'from prowlrbot.'
find src/prowlrbot -name "*.py" -exec sed -i '' 's/from copaw\./from prowlrbot./g' {} +

# Replace all 'import copaw' with 'import prowlrbot'
find src/prowlrbot -name "*.py" -exec sed -i '' 's/import copaw/import prowlrbot/g' {} +

# Replace string references like "copaw." in module paths
find src/prowlrbot -name "*.py" -exec sed -i '' 's/"copaw\./"prowlrbot./g' {} +
find src/prowlrbot -name "*.py" -exec sed -i '' "s/'copaw\./'prowlrbot./g" {} +
```

**Step 2: Verify no stale copaw references in imports**

```bash
grep -r "from copaw\." src/prowlrbot/ || echo "Clean: no stale imports"
grep -r "import copaw" src/prowlrbot/ || echo "Clean: no stale imports"
```
Expected: "Clean: no stale imports" for both

**Step 3: Commit**

```bash
git add src/prowlrbot/
git commit -m "refactor: rename all copaw imports to prowlrbot"
```

---

### Task 3: Update constant.py (Paths and Env Vars)

**Files:**
- Modify: `src/prowlrbot/constant.py`

**Step 1: Replace CoPaw references with ProwlrBot**

Change these constants:
```python
# BEFORE
WORKING_DIR = Path(os.environ.get("COPAW_WORKING_DIR", "~/.copaw"))
SECRET_DIR = Path(os.environ.get("COPAW_SECRET_DIR", ...))
JOBS_FILE = os.environ.get("COPAW_JOBS_FILE", "jobs.json")
CHATS_FILE = os.environ.get("COPAW_CHATS_FILE", "chats.json")
CONFIG_FILE = os.environ.get("COPAW_CONFIG_FILE", "config.json")
HEARTBEAT_FILE = os.environ.get("COPAW_HEARTBEAT_FILE", "HEARTBEAT.md")
LOG_LEVEL_ENV = "COPAW_LOG_LEVEL"
RUNNING_IN_CONTAINER = os.environ.get("COPAW_RUNNING_IN_CONTAINER", "false")
DOCS_ENABLED = os.environ.get("COPAW_OPENAPI_DOCS", "false")
MEMORY_COMPACT_KEEP_RECENT = int(os.environ.get("COPAW_MEMORY_COMPACT_KEEP_RECENT", "3"))
MEMORY_COMPACT_RATIO = float(os.environ.get("COPAW_MEMORY_COMPACT_RATIO", "0.7"))
CORS_ORIGINS = os.environ.get("COPAW_CORS_ORIGINS", "")

# AFTER
WORKING_DIR = Path(os.environ.get("PROWLRBOT_WORKING_DIR", "~/.prowlrbot"))
SECRET_DIR = Path(os.environ.get("PROWLRBOT_SECRET_DIR", ...))
JOBS_FILE = os.environ.get("PROWLRBOT_JOBS_FILE", "jobs.json")
CHATS_FILE = os.environ.get("PROWLRBOT_CHATS_FILE", "chats.json")
CONFIG_FILE = os.environ.get("PROWLRBOT_CONFIG_FILE", "config.json")
HEARTBEAT_FILE = os.environ.get("PROWLRBOT_HEARTBEAT_FILE", "HEARTBEAT.md")
LOG_LEVEL_ENV = "PROWLRBOT_LOG_LEVEL"
RUNNING_IN_CONTAINER = os.environ.get("PROWLRBOT_RUNNING_IN_CONTAINER", "false")
DOCS_ENABLED = os.environ.get("PROWLRBOT_OPENAPI_DOCS", "false")
MEMORY_COMPACT_KEEP_RECENT = int(os.environ.get("PROWLRBOT_MEMORY_COMPACT_KEEP_RECENT", "3"))
MEMORY_COMPACT_RATIO = float(os.environ.get("PROWLRBOT_MEMORY_COMPACT_RATIO", "0.7"))
CORS_ORIGINS = os.environ.get("PROWLRBOT_CORS_ORIGINS", "")
```

Also update any `copaw channels install` string references to `prowlr channels install`.

**Step 2: Commit**

```bash
git add src/prowlrbot/constant.py
git commit -m "refactor: update all env vars and paths from COPAW to PROWLRBOT"
```

---

### Task 4: Rename Memory Class (copaw_memory.py)

**Files:**
- Rename: `src/prowlrbot/agents/memory/copaw_memory.py` → `src/prowlrbot/agents/memory/prowlrbot_memory.py`
- Modify: `src/prowlrbot/agents/memory/__init__.py` (update import)
- Modify: Any files importing `CoPawInMemoryMemory` → `ProwlrBotInMemoryMemory`

**Step 1: Rename the file**

```bash
mv src/prowlrbot/agents/memory/copaw_memory.py src/prowlrbot/agents/memory/prowlrbot_memory.py
```

**Step 2: Update class name inside the file**

Replace `CoPawInMemoryMemory` with `ProwlrBotInMemoryMemory` and `CoPawAgent` references with `ProwlrBotAgent`.

**Step 3: Update all files that import the old name**

```bash
grep -r "copaw_memory\|CoPawInMemoryMemory\|CoPawAgent\|CoPaw" src/prowlrbot/ --include="*.py" -l
```

Update each file found. Key renames:
- `CoPawAgent` → `ProwlrBotAgent`
- `CoPawInMemoryMemory` → `ProwlrBotInMemoryMemory`
- `copaw_memory` → `prowlrbot_memory`

**Step 4: Commit**

```bash
git add src/prowlrbot/
git commit -m "refactor: rename CoPaw classes to ProwlrBot"
```

---

### Task 5: Update pyproject.toml

**Files:**
- Modify: `pyproject.toml` (root level)

**Step 1: Update package metadata**

```toml
[project]
name = "prowlrbot"
dynamic = ["version"]
description = "ProwlrBot — Always watching. Always ready. An autonomous AI agent platform for monitoring, automation, and multi-channel communication."

[tool.setuptools.dynamic]
version = {attr = "prowlrbot.__version__.__version__"}

[tool.setuptools.package-data]
"prowlrbot" = [
    "console/**",
    "agents/md_files/**",
    "agents/skills/**",
    "tokenizer/**",
]

[project.scripts]
prowlr = "prowlrbot.cli.main:cli"

[project.optional-dependencies]
dev = [
    "pytest>=8.3.5",
    "pytest-asyncio>=0.23.0",
    "pre-commit>=4.2.0",
    "pytest-cov>=6.2.1",
    "httpx>=0.27.0",
]
local = ["huggingface_hub>=0.20.0"]
llamacpp = ["prowlrbot[local]", "llama-cpp-python>=0.3.0"]
mlx = ["prowlrbot[local]", "mlx-lm>=0.10.0"]
ollama = ["ollama>=0.6.1"]
```

**Step 2: Verify install**

```bash
pip install -e ".[dev]"
```
Expected: Installs successfully

**Step 3: Verify CLI**

```bash
prowlr --help
```
Expected: Shows help text

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "refactor: update pyproject.toml for prowlrbot package"
```

---

### Task 6: Update Agent MD Files (Branding)

**Files:**
- Modify: `src/prowlrbot/agents/md_files/en/AGENTS.md`
- Modify: `src/prowlrbot/agents/md_files/en/SOUL.md`
- Modify: `src/prowlrbot/agents/md_files/en/PROFILE.md`
- Modify: `src/prowlrbot/agents/md_files/en/BOOTSTRAP.md`
- Modify: `src/prowlrbot/agents/md_files/en/HEARTBEAT.md`
- Modify: `src/prowlrbot/agents/md_files/en/MEMORY.md`
- Modify: Same files in `zh/` directory

**Step 1: Replace CoPaw with ProwlrBot in all MD files**

```bash
find src/prowlrbot/agents/md_files -name "*.md" -exec sed -i '' 's/CoPaw/ProwlrBot/g' {} +
find src/prowlrbot/agents/md_files -name "*.md" -exec sed -i '' 's/copaw/prowlrbot/g' {} +
```

**Step 2: Commit**

```bash
git add src/prowlrbot/agents/md_files/
git commit -m "docs: rebrand agent MD files from CoPaw to ProwlrBot"
```

---

### Task 7: Update Test Files

**Files:**
- Modify: `tests/test_react_agent_tool_choice.py`
- Modify: `tests/test_mcp_resilience.py`
- Modify: `tests/test_memory_compaction_hook.py`
- Modify: `tests/test_openai_stream_toolcall_compat.py`

**Step 1: Update imports in test files**

```bash
find tests -name "*.py" -exec sed -i '' 's/from copaw\./from prowlrbot./g' {} +
find tests -name "*.py" -exec sed -i '' 's/import copaw/import prowlrbot/g' {} +
find tests -name "*.py" -exec sed -i '' 's/CoPawAgent/ProwlrBotAgent/g' {} +
find tests -name "*.py" -exec sed -i '' 's/CoPawInMemoryMemory/ProwlrBotInMemoryMemory/g' {} +
```

**Step 2: Run tests**

```bash
pytest tests/ -v
```
Expected: All tests pass (or at least no import errors from renaming)

**Step 3: Commit**

```bash
git add tests/
git commit -m "test: update test imports for prowlrbot package"
```

---

### Task 8: Update README and CLAUDE.md

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

**Step 1: Rewrite README.md for ProwlrBot**

Replace CoPaw branding with ProwlrBot. Update:
- Title and badges
- Description: "ProwlrBot — Always watching. Always ready."
- Install commands: `pip install prowlrbot`, `prowlr init --defaults`, `prowlr app`
- Docker: `docker run prowlrbot`
- All references to copaw CLI → prowlr CLI

**Step 2: Update CLAUDE.md**

Replace all CoPaw references with ProwlrBot. Update commands section.

**Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: rebrand README and CLAUDE.md for ProwlrBot"
```

---

### Task 9: Verify Full Rebrand

**Step 1: Check for ANY remaining copaw references**

```bash
grep -ri "copaw" src/prowlrbot/ --include="*.py" | grep -v "# Originally from CoPaw" || echo "Clean"
grep -ri "copaw" tests/ --include="*.py" || echo "Clean"
grep -ri "copaw" pyproject.toml || echo "Clean"
```

**Step 2: Full test suite**

```bash
pip install -e ".[dev]"
prowlr --help
pytest tests/ -v
```

**Step 3: Final commit if any stragglers found**

```bash
git commit -am "chore: clean remaining copaw references"
```

---

## Phase 1: Provider Detection System

### Task 10: Provider Base Classes

**Files:**
- Modify: `src/prowlrbot/providers/models.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/test_provider_models.py`

**Step 1: Write failing test**

```python
# tests/unit/test_provider_models.py
from prowlrbot.providers.models import ProviderDefinition, ModelInfo

def test_provider_definition_has_detection_fields():
    p = ProviderDefinition(
        id="test",
        name="Test Provider",
        default_base_url="https://api.test.com/v1",
        env_var="TEST_API_KEY",
        api_key_prefix="sk-",
        is_local=False,
        url_based_detection=False,
        cost_tier="standard",
        health_check_endpoint="/v1/models",
    )
    assert p.env_var == "TEST_API_KEY"
    assert p.cost_tier == "standard"
    assert p.url_based_detection is False
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_provider_models.py -v
```
Expected: FAIL (missing fields on ProviderDefinition)

**Step 3: Add new fields to ProviderDefinition**

Add to `src/prowlrbot/providers/models.py`:
```python
class ProviderDefinition(BaseModel):
    # ... existing fields ...
    env_var: str = Field(default="", description="Env var for API key detection")
    url_based_detection: bool = Field(default=False, description="Detect via URL probe")
    cost_tier: str = Field(default="standard", description="Cost tier: free/low/standard/premium")
    health_check_endpoint: str = Field(default="", description="Health check URL path")
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_provider_models.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add src/prowlrbot/providers/models.py tests/unit/
git commit -m "feat: add detection fields to ProviderDefinition"
```

---

### Task 11: Provider Detector

**Files:**
- Create: `src/prowlrbot/providers/detector.py`
- Create: `tests/unit/test_detector.py`

**Step 1: Write failing test**

```python
# tests/unit/test_detector.py
import os
import pytest
from unittest.mock import patch
from prowlrbot.providers.detector import ProviderDetector

def test_detects_provider_by_env_var():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
        detector = ProviderDetector()
        detected = detector.scan_env_vars()
        provider_ids = [p.id for p in detected]
        assert "anthropic" in provider_ids

def test_no_providers_when_no_env_vars():
    with patch.dict(os.environ, {}, clear=True):
        detector = ProviderDetector()
        detected = detector.scan_env_vars()
        # Should not include cloud providers (local ones may still be probed)
        cloud = [p for p in detected if not p.is_local]
        assert len(cloud) == 0
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_detector.py -v
```

**Step 3: Implement detector**

```python
# src/prowlrbot/providers/detector.py
import os
import logging
from typing import List, Tuple
from .models import ProviderDefinition
from .registry import ProviderRegistry

logger = logging.getLogger(__name__)

class ProviderDetector:
    def scan_env_vars(self) -> List[ProviderDefinition]:
        detected = []
        for provider in ProviderRegistry.all():
            if provider.is_local and provider.url_based_detection:
                continue  # Local providers handled by scan_urls()
            if not provider.env_var:
                continue
            key = os.environ.get(provider.env_var, "")
            if key:
                if provider.api_key_prefix and not key.startswith(provider.api_key_prefix):
                    logger.warning(
                        "Key for %s doesn't start with expected prefix %s",
                        provider.id, provider.api_key_prefix
                    )
                logger.info("Detected provider: %s (via %s)", provider.name, provider.env_var)
                detected.append(provider)
        return detected
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_detector.py -v
```

**Step 5: Commit**

```bash
git add src/prowlrbot/providers/detector.py tests/unit/test_detector.py
git commit -m "feat: add provider auto-detection via environment variables"
```

---

### Task 12: Health Check System

**Files:**
- Create: `src/prowlrbot/providers/health.py`
- Create: `tests/unit/test_health.py`

**Step 1: Write failing test**

```python
# tests/unit/test_health.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from prowlrbot.providers.health import HealthChecker
from prowlrbot.providers.models import ProviderDefinition

@pytest.mark.asyncio
async def test_healthy_provider_returns_true():
    provider = ProviderDefinition(
        id="test", name="Test",
        default_base_url="https://api.test.com/v1",
        env_var="TEST_KEY",
        health_check_endpoint="/v1/models",
    )
    checker = HealthChecker(timeout=5.0)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        result = await checker.check(provider, api_key="test-key")
    assert result is True

@pytest.mark.asyncio
async def test_unreachable_provider_returns_false():
    provider = ProviderDefinition(
        id="test", name="Test",
        default_base_url="https://api.unreachable.com/v1",
        env_var="TEST_KEY",
        health_check_endpoint="/v1/models",
    )
    checker = HealthChecker(timeout=1.0)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=Exception("timeout")):
        result = await checker.check(provider, api_key="test-key")
    assert result is False
```

**Step 2: Implement health checker**

```python
# src/prowlrbot/providers/health.py
import logging
from typing import Dict, List, Tuple
import httpx
from .models import ProviderDefinition

logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self._status: Dict[str, bool] = {}

    async def check(self, provider: ProviderDefinition, api_key: str = "") -> bool:
        try:
            url = f"{provider.default_base_url.rstrip('/')}{provider.health_check_endpoint}"
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)
                healthy = resp.status_code < 500
                self._status[provider.id] = healthy
                if healthy:
                    logger.info("Health check passed: %s", provider.name)
                else:
                    logger.warning("Health check failed: %s (status %d)", provider.name, resp.status_code)
                return healthy
        except Exception as e:
            logger.warning("Health check error for %s: %s", provider.name, str(e))
            self._status[provider.id] = False
            return False

    def get_status(self, provider_id: str) -> bool:
        return self._status.get(provider_id, False)
```

**Step 3: Run tests**

```bash
pytest tests/unit/test_health.py -v
```

**Step 4: Commit**

```bash
git add src/prowlrbot/providers/health.py tests/unit/test_health.py
git commit -m "feat: add async health check system for providers"
```

---

### Task 13: Smart Router

**Files:**
- Create: `src/prowlrbot/providers/router.py`
- Create: `src/prowlrbot/providers/fallback.py`
- Create: `tests/unit/test_router.py`

**Step 1: Write failing test**

```python
# tests/unit/test_router.py
from prowlrbot.providers.router import SmartRouter
from prowlrbot.providers.models import ProviderDefinition

def test_router_selects_best_scored_provider():
    providers = [
        ProviderDefinition(id="cheap", name="Cheap", cost_tier="free", env_var="A"),
        ProviderDefinition(id="fast", name="Fast", cost_tier="premium", env_var="B"),
    ]
    router = SmartRouter(providers, health_status={"cheap": True, "fast": True})
    selected = router.select()
    # Free tier scores higher on cost, should win with default weights
    assert selected.id == "cheap"

def test_router_excludes_unhealthy():
    providers = [
        ProviderDefinition(id="healthy", name="Healthy", cost_tier="standard", env_var="A"),
        ProviderDefinition(id="dead", name="Dead", cost_tier="free", env_var="B"),
    ]
    router = SmartRouter(providers, health_status={"healthy": True, "dead": False})
    selected = router.select()
    assert selected.id == "healthy"
```

**Step 2: Implement router**

```python
# src/prowlrbot/providers/router.py
import logging
from typing import Dict, List, Optional
from .models import ProviderDefinition

logger = logging.getLogger(__name__)

COST_SCORES = {"free": 1.0, "low": 0.8, "standard": 0.5, "premium": 0.2}
PERF_SCORES = {"free": 0.5, "low": 0.8, "standard": 0.6, "premium": 0.8}

class SmartRouter:
    def __init__(
        self,
        providers: List[ProviderDefinition],
        health_status: Optional[Dict[str, bool]] = None,
        cost_weight: float = 0.3,
        perf_weight: float = 0.4,
        avail_weight: float = 0.3,
    ):
        self.providers = providers
        self.health_status = health_status or {}
        self.cost_weight = cost_weight
        self.perf_weight = perf_weight
        self.avail_weight = avail_weight

    def score(self, provider: ProviderDefinition) -> float:
        cost = COST_SCORES.get(provider.cost_tier, 0.5)
        perf = PERF_SCORES.get(provider.cost_tier, 0.5)
        avail = 1.0 if self.health_status.get(provider.id, False) else 0.0
        return self.cost_weight * cost + self.perf_weight * perf + self.avail_weight * avail

    def select(self) -> Optional[ProviderDefinition]:
        healthy = [p for p in self.providers if self.health_status.get(p.id, False)]
        if not healthy:
            return None
        ranked = sorted(healthy, key=lambda p: self.score(p), reverse=True)
        selected = ranked[0]
        logger.info("Router selected: %s (score=%.2f)", selected.name, self.score(selected))
        return selected

    def get_fallback_chain(self) -> List[ProviderDefinition]:
        healthy = [p for p in self.providers if self.health_status.get(p.id, False)]
        return sorted(healthy, key=lambda p: self.score(p), reverse=True)
```

**Step 3: Run tests**

```bash
pytest tests/unit/test_router.py -v
```

**Step 4: Commit**

```bash
git add src/prowlrbot/providers/router.py tests/unit/test_router.py
git commit -m "feat: add smart provider routing with scoring engine"
```

---

### Task 14: Register Built-in Provider Definitions

**Files:**
- Modify: `src/prowlrbot/providers/registry.py`

**Step 1: Add all 10+ providers to registry**

Add provider definitions for: Anthropic, OpenAI, Groq, Z.ai, Together AI, Cohere, Replicate, Ollama, LM Studio, AnythingLLM.

Each with: `env_var`, `api_key_prefix`, `cost_tier`, `health_check_endpoint`, `url_based_detection`, `is_local`.

Example for Anthropic:
```python
ProviderDefinition(
    id="anthropic",
    name="Anthropic",
    default_base_url="https://api.anthropic.com",
    env_var="ANTHROPIC_API_KEY",
    api_key_prefix="sk-ant-",
    cost_tier="premium",
    health_check_endpoint="/v1/models",
    models=[
        ModelInfo(id="claude-opus-4-6", name="Claude Opus 4.6"),
        ModelInfo(id="claude-sonnet-4-6", name="Claude Sonnet 4.6"),
    ],
)
```

**Step 2: Run all tests**

```bash
pytest tests/ -v
```

**Step 3: Commit**

```bash
git add src/prowlrbot/providers/registry.py
git commit -m "feat: register all built-in provider definitions with detection metadata"
```

---

### Task 15: Integration Test — Full Detection Pipeline

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/test_detection_flow.py`

**Step 1: Write integration test**

```python
# tests/integration/test_detection_flow.py
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from prowlrbot.providers.detector import ProviderDetector
from prowlrbot.providers.health import HealthChecker
from prowlrbot.providers.router import SmartRouter
from prowlrbot.providers.registry import ProviderRegistry

@pytest.mark.asyncio
async def test_full_detection_pipeline():
    """Detect → health check → route."""
    ProviderRegistry.register_defaults()

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
        detector = ProviderDetector()
        detected = detector.scan_env_vars()
        assert len(detected) >= 1

        checker = HealthChecker(timeout=2.0)
        health = {}
        for p in detected:
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock:
                mock.return_value = MagicMock(status_code=200)
                health[p.id] = await checker.check(p, api_key="test")

        router = SmartRouter(detected, health_status=health)
        selected = router.select()
        assert selected is not None
        assert selected.id == "anthropic"
```

**Step 2: Run integration test**

```bash
pytest tests/integration/ -v
```

**Step 3: Commit**

```bash
git add tests/integration/
git commit -m "test: add integration test for full provider detection pipeline"
```

---

## Phase 2: Parallel Agent Dispatch

### Task 16: Launch Parallel Agents

After Phase 0 and Phase 1 are verified working, dispatch these agents in parallel using worktree isolation:

**Agent A: Monitoring Engine** (Features 1-6)
- Create `src/prowlrbot/monitor/` subsystem
- Core scheduler, web change detection, notification system, CLI commands, Docker deployment
- Reuse existing APScheduler from `app/crons/`

**Agent B: Embedded IDE** (Spec 003)
- Create `src/prowlrbot/ide/` subsystem
- Multi-agent orchestration UI
- New console pages

**Agent C: AutoResearch Workflow** (Spec 004)
- Create `src/prowlrbot/research/` subsystem
- Training workflow pipeline

**Agent D: RAG Module** (Spec 005)
- Create `src/prowlrbot/rag/` subsystem
- Retrieval-augmented generation with vector storage

**Agent E: Model Registry** (Spec 006)
- Create `src/prowlrbot/model_registry/` subsystem
- Upload, manage, serve custom models

**Agent F: Phase 2+ Features** (Features 7-18)
- API monitoring, RSS feeds, execution logs, error handling
- Headless browser, composable pipelines, plugin architecture
- Dashboard, authenticated monitoring, security, intelligent analysis

**Agent G: Library Updates**
- Audit and update all dependencies in pyproject.toml
- Run full test suite after each update
- Document breaking changes

Each agent gets the design doc context and works in its own worktree branch. Merge back after review.

---

## Verification Checklist

After all phases complete:

- [ ] `prowlr --help` shows ProwlrBot branding
- [ ] `prowlr init --defaults` creates `~/.prowlrbot/config.json`
- [ ] `prowlr app` starts FastAPI on port 8088
- [ ] Console loads with ProwlrBot branding at http://127.0.0.1:8088
- [ ] `pytest tests/ -v` — all tests pass
- [ ] No `copaw` references in user-facing output
- [ ] Provider detection finds configured providers
- [ ] Smart routing selects optimal provider
- [ ] Monitoring engine can poll a web page for changes
- [ ] Docker build succeeds
