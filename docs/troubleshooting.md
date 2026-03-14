# Troubleshooting Guide

Common issues and solutions for ProwlrBot installation and operation.

---

## Installation Issues

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
