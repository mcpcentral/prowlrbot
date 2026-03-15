# Troubleshooting Guide

Common issues and solutions for ProwlrBot installation and operation.

---

## Installation Issues

### Install fails on other devices (git / GitHub / “Cannot find version”)

**Symptoms:**
- `pip install .` or `pip install prowlrbot` fails on a different machine, CI, or minimal environment
- `ERROR: Cannot find a matching version` or `Could not find a version that satisfies the requirement agentscope`
- `fatal: could not read Username for 'https://github.com'` or SSL/timeout when resolving dependencies

**Cause:** ProwlrBot depends on two packages installed **from GitHub** (not PyPI):
- `agentscope` from `github.com/prowlrbot/agentscope`
- `agentscope-runtime` from `github.com/prowlrbot/agentscope-runtime`

So every install needs:
1. **Git** installed and on `PATH` (e.g. `git --version` works)
2. **Network access** to GitHub (no strict firewall/proxy blocking `github.com`)
3. **pip** that supports `git+https` URLs (recent pip/setuptools)

**Fix:**

1. **Install Git** on the target device:
   - **Windows:** [git-scm.com](https://git-scm.com/) or `winget install Git.Git`
   - **Linux:** `sudo apt install git` / `sudo dnf install git`
   - **Docker:** Use an image that includes git, or a multi-stage build that installs deps in a stage with git

2. **Use a fresh venv and upgrade pip:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install --upgrade pip setuptools wheel
   pip install -e .
   ```

3. **If GitHub is blocked or flaky:** use a VPN, or install from a machine that can reach GitHub and copy the built venv/artifacts. For CI, ensure the job has git and can reach GitHub.

4. **Prefer Docker on “other devices”** so the image is built once (with git in the build stage) and runs anywhere:
   ```bash
   docker build -f deploy/Dockerfile.fly -t prowlrbot .
   docker run -p 8088:8088 -v prowlrbot_data:/data prowlrbot
   ```

**Long-term:** Publishing ProwlrBot (and the two AgentScope forks) to **PyPI** would remove the need for Git and make `pip install prowlrbot` work everywhere. See [Publishing to PyPI](guides/pypi-publish.md).

---

### WSL: I/O Error During pip install

**Symptoms:**
- `OSError: [Errno 5] Input/output error` during `pip install`
- WSL crashes or becomes unresponsive after the error
- WSL won't start after restarting the terminal

**Cause:** pip installing a large number of packages (240+) can overwhelm the WSL virtual filesystem. The most common hidden trigger is **NTFS compression enabled on the WSL VHDX file** — this causes write failures under heavy I/O and can crash the entire WSL VM, potentially destroying the WslService registry entry.

**First, check for NTFS compression** (this is the #1 cause):

```powershell
Get-ChildItem "$env:LOCALAPPDATA\wsl" -Recurse -Filter "ext4.vhdx" | Select-Object FullName, Attributes
# If Attributes includes "Compressed" — that's your problem. See the NTFS compression fix below.
```

**Fix:**

1. Restart Windows fully (not just WSL)
2. Once WSL is back:

```bash
# If WSL won't start, run in PowerShell (Admin):
wsl --shutdown
wsl -d Ubuntu    # or your distro name

# If still broken:
wsl --terminate Ubuntu
# Last resort (deletes WSL data):
# wsl --unregister Ubuntu && wsl --install Ubuntu
```

3. Clean install with a venv inside the project:

```bash
git clone https://github.com/ProwlrBot/prowlrbot.git
cd prowlrbot

# Create venv INSIDE the project directory (not elsewhere)
python3 -m venv .venv
source .venv/bin/activate

# Install in steps (reduces I/O pressure)
pip install --upgrade pip
pip install -e .            # core packages first
pip install -e ".[dev]"     # dev dependencies second
```

**Prevention:**
- Always create the venv inside the project directory (`.venv/`), not in a separate location
- This keeps the venv on the same filesystem as the project
- Avoid cross-filesystem operations in WSL (e.g., venv on Windows mount, project on Linux FS)
- Use the Linux filesystem (`/home/user/`) not Windows mounts (`/mnt/c/`)

---

### pip install fails with dependency conflicts

**Symptoms:**
- `ERROR: Cannot install prowlrbot` with version conflict messages

**Fix:**

```bash
# Create a fresh venv (don't reuse old ones)
python3 -m venv .venv --clear
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e .
```

If a specific package conflicts, check `pyproject.toml` for version constraints and report an issue.

**After installing `nacos-sdk-python`:** its dependencies can downgrade `cryptography` and upgrade `jmespath`, which conflicts with ProwlrBot and with `aliyun-python-sdk-core` (used by agentscope-runtime). Fix:

1. Restore ProwlrBot’s required cryptography:
   ```bash
   pip install 'cryptography>=46.0.5'
   ```
2. Prefer the optional extra so pip keeps cryptography and nacos together:
   ```bash
   pip install -e ".[nacos]"
   ```
   The `jmespath` conflict with aliyun-python-sdk-core (aliyun wants \<1.0, nacos deps want 1.x) is harmless unless you use Aliyun OSS; if you need both, use a separate venv or accept the resolver warning.

---

### ModuleNotFoundError: No module named 'prowlrbot'

**Symptoms:**
- `prowlr` command not found after install
- Python can't import prowlrbot

**Fix:**

```bash
# Make sure you're in the activated venv
source .venv/bin/activate
which python3    # Should show .venv/bin/python3

# Reinstall in editable mode
pip install -e .

# Verify
prowlr --version
```

---

## Runtime Issues

### Port 8088 already in use

**Symptoms:**
- `ERROR: [Errno 98] Address already in use`

**Fix:**

```bash
# Find what's using the port
lsof -i :8088    # macOS/Linux
netstat -ano | findstr :8088    # Windows

# Set alias
alias ports="ss -tlnp | grep"

# If it’s an old prowlr app:

pkill -f "uvicorn.*prowlrbot.app._app"

# Kill it or use a different port
prowlr app --port 8089
```
Then start again:

```bash
prowlr app
```

---

### Deprecation warnings and log noise when running `prowlr app`

**What you see:**
- `DeprecationWarning: websockets.server.WebSocketServerProtocol is deprecated` (from uvicorn/websockets)
- `PydanticDeprecatedSince20` in `nacos/naming/model/service.py` (from a dependency)
- `Vector search disabled` (memory manager — optional embedding config)
- `reme.core` INFO lines (memory/embedding library loading `.env` and config)

**Why:** These come from **dependencies** (uvicorn, websockets, nacos, reme), not from ProwlrBot’s own code. They are harmless; the app runs normally.

**What we do:** The `prowlr app` command installs warning filters at startup so the websockets and Pydantic deprecation messages are suppressed by default. If you still see them (e.g. from a different entry point), you can run `PYTHONWARNINGS=ignore::DeprecationWarning prowlr app`.

To enable vector search and remove that warning, set in `.env`: `EMBEDDING_API_KEY`, `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL_NAME`, and `EMBEDDING_DIMENSIONS` (see memory/embedding docs).

---

### Provider detection finds no providers

**Symptoms:**
- `No providers detected` on startup

**Fix:**

```bash
# Set at least one API key
prowlr env set OPENAI_API_KEY sk-your-key
# Or for Anthropic:
prowlr env set ANTHROPIC_API_KEY sk-ant-your-key

# Or run Ollama locally (auto-detected):
ollama serve
prowlr app
```

---

### MCP connection refused

**Symptoms:**
- `Connection refused` when war room tries to connect
- MCP tools not available

**Fix:**

```bash
# Check if the bridge is running
curl http://localhost:8099/healthz

# If not, start it
prowlr app    # Bridge starts automatically with the app

# For cross-machine connections, ensure:
# 1. Both machines can reach each other (Tailscale recommended)
# 2. Port 8099 is open
# 3. HMAC secret matches on both sides
```

---

### Console shows blank page

**Symptoms:**
- `http://localhost:8088` loads but shows white screen

**Fix:**

```bash
# Rebuild the console
cd console
npm ci
npm run build

# Restart the server
prowlr app
```

---

### Local model 'X' not found (e.g. kimi-k2.5:cloud)

**Symptoms:**
- `ValueError: Local model 'kimi-k2.5:cloud' not found. Download it first with 'prowlr models download'.`
- Or similar for another model ID

**Cause:** Previously the app treated **Ollama** (including Ollama’s `:cloud` proxy models) as a manifest local provider (llama.cpp/MLX). That is fixed: Ollama is now routed to the daemon. If you still see this, the active provider is llama.cpp/MLX with a model ID you haven’t downloaded.

**Fix:**

1. **Ollama models** (e.g. `kimi-k2.5:cloud`, `deepseek-v3.1:671b-cloud` from `ollama list`): Ensure Ollama is running (`ollama serve`) and in Settings → Models choose provider **Ollama** and the model name. No extra step needed after the fix.

2. **If the active provider is llama.cpp or MLX** but the model ID isn't one you downloaded: either download a model and set it, or switch provider:
   - Cloud: `prowlr models set-llm aliyun-codingplan kimi-k2.5` (set that provider's API key)
   - Local: `prowlr models download <repo_id>` then `prowlr models set-llm llamacpp <model_id>`
   - Other: `prowlr models set-llm anthropic claude-sonnet-4-6` (or openai, groq, etc.)

---

### War Room returns 401 or 403

**Symptoms:**
- War Room page in the console shows errors or "Request failed: 401/403"
- Or `curl http://localhost:8088/api/warroom/health` returns 401/403

**Cause:** War Room is **built into the main app** — there is no separate bridge or server to start. The `/api/warroom/*` and `/ws/warroom` endpoints are protected by the same auth as the rest of the console. So 401/403 means authentication failed.

**You do not need to start anything extra.** Run only:

```bash
prowlr app
```

Then open the console in the browser (e.g. http://localhost:8088), **log in** (admin + password from `.env` or `prowlr set-admin-password`), and go to the War Room page. The browser sends your JWT with each request, so once you're logged in, War Room API and WebSocket work.

**If you're testing from the terminal** (e.g. curl), you must send a valid token:

```bash
# After logging in via the console, copy the JWT from localStorage (DevTools → Application → Local Storage → prowlrbot-jwt)
# Or use an API token if you have PROWLRBOT_API_TOKEN_HASH set:
curl -H "Authorization: Bearer YOUR_JWT_OR_API_TOKEN" http://localhost:8088/api/warroom/health
```

**If you use the standalone bridge** (e.g. for multi-machine coordination), that's a separate process: `python -m prowlrbot.hub.bridge`. The in-app War Room does not depend on it.

---

### Clerk: "Production Keys are only allowed for domain …" / Origin must match

**Symptoms:**
- Console at `https://prowlrbot.fly.dev` (or another URL) shows: *Clerk: Production Keys are only allowed for domain "prowlrbot.com"* or *The Request HTTP Origin header must be equal to or a subdomain of the requesting URL*
- Clerk API calls return 400; sign-in doesn’t load

**Cause:** Clerk **production** keys are restricted to the domain(s) you configured in the Clerk Dashboard. If the app is served from a different origin (e.g. `https://prowlrbot.fly.dev`) than that domain (e.g. `prowlrbot.com`), Clerk blocks the request.

**Fix:**

1. **Allow the deployment origin in Clerk:** In [Clerk Dashboard](https://dashboard.clerk.com) → your application → **Domains**, add the exact origin users use (e.g. `https://prowlrbot.fly.dev`). Save. Reload the console.
2. **Or use a custom domain:** Point your Fly (or other) app at a subdomain of the same domain (e.g. `https://app.prowlrbot.com` or `https://console.prowlrbot.com`) and ensure that domain is allowed in Clerk. Then users open the app at that URL so the Origin matches.

After fixing, the CSP change that allows Clerk’s worker (`worker-src 'self' blob: …`) will let Clerk load without the "violates Content Security Policy" worker error.

---

## WSL-Specific Issues

### WSL: WslService Destroyed After Crash (0x80070422 / Error 1058)

**Symptoms:**
- Every WSL command fails with `Wsl/0x80070422`
- `sc.exe query WslService` shows STOPPED (exit code 1077) or "service does not exist"
- `sc.exe start WslService` fails with error 1058
- Reinstalling WSL via `winget`, `wsl --install`, or Appx re-registration does NOT fix it
- Rebooting does NOT fix it

**Cause:** A crash during heavy I/O (like pip installing 240+ packages) can corrupt or destroy the WslService registry entry. The WSL Store package's AppxManifest does not define the service, so no standard reinstall method can recreate it.

**Fix (requires elevated PowerShell):**

```powershell
# 1. Delete the broken service entry if it exists
sc.exe delete WslService

# 2. Recreate the service with correct configuration
New-Service -Name 'WslService' `
    -BinaryPathName '"C:\Program Files\WSL\wslservice.exe"' `
    -DisplayName 'WSL Service' `
    -StartupType Manual `
    -Description 'Windows Subsystem for Linux Service'

# 3. Add the vmcompute dependency
sc.exe config WslService depend= vmcompute

# 4. Start it
sc.exe start WslService

# 5. Verify
wsl -l -v
```

**Important details:**
- The binary path MUST be quoted (space in "Program Files") or you get error 1058 again
- StartupType must be Manual, not Automatic
- The vmcompute dependency is required -- without it, WslService may fail on cold boot
- Your distro VHDX files survive this -- they are not deleted

**Prevention -- export your working service key:**

```powershell
reg export "HKLM\SYSTEM\CurrentControlSet\Services\WslService" WslService-backup.reg
```

If it breaks again, just double-click the .reg file to restore it.

**If WSL starts but shows SCSI errors or HCS_E_CONNECTION_TIMEOUT:**

The VHDX disk may be in a dirty state from the crash. Try:

```powershell
wsl --shutdown
# Wait 10 seconds
wsl -d kali-linux   # or your distro
```

If disk errors persist, run filesystem repair from another distro or recovery mode:

```bash
sudo e2fsck -f /dev/sdX   # replace with actual device
```

See the [full blog post](blog/2026-03-11-pip-install-broke-my-wsl.md) for the complete story.

---

### WSL filesystem best practices

1. **Always work on the Linux filesystem** — use `/home/user/prowlrbot`, NOT `/mnt/c/Users/.../prowlrbot`
2. **Keep venvs inside the project** — `.venv/` in the repo root
3. **Don't mix Windows and Linux tools** — use Linux `git`, `python3`, `pip` inside WSL
4. **Check disk space** — `df -h /home` should show sufficient space before installing

### WSL networking for war room

The war room bridge needs network connectivity between agents. In WSL:

```bash
# Get your WSL IP
hostname -I

# The bridge listens on 0.0.0.0:8099 by default
# From Windows, access via the WSL IP
# From other machines, you may need port forwarding or Tailscale
```

---

## Getting Help

- [GitHub Issues](https://github.com/ProwlrBot/prowlrbot/issues/new?template=bug_report.yml) — bug reports
- [GitHub Discussions](https://github.com/ProwlrBot/prowlrbot/discussions) — questions
- [SECURITY.md](https://github.com/ProwlrBot/prowlrbot/blob/main/SECURITY.md) — security vulnerabilities
