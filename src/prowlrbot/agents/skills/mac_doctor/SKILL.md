---
name: mac_doctor
description: "Diagnose and repair macOS-specific issues with ProwlrBot and Python development environments. Covers Apple Silicon compatibility, Python version management, SSL certificates, port conflicts, Gatekeeper, networking, performance, and local model backends (MLX, llama.cpp, Ollama)."
metadata:
  {
    "prowlr":
      {
        "emoji": "🍎",
        "requires": { "platform": "darwin" }
      }
  }
---

# Mac Doctor — Diagnostic & Repair Skill

Diagnose and fix macOS-specific issues with ProwlrBot installation, runtime, and local AI model backends. Uses a progressive escalation approach — quick checks first, deep diagnostics only when needed.

## When to Use

- User says: "ProwlrBot won't install on Mac", "pip install fails", "port already in use"
- User gets SSL errors, architecture mismatch errors, or Gatekeeper blocks
- Local models (MLX, llama.cpp, Ollama) won't load or crash
- Console frontend build fails
- Networking or firewall issues
- Performance problems or high CPU/memory usage
- User is on Apple Silicon (M1/M2/M3/M4) and hitting ARM vs x86 issues

## Diagnostic Ladder

**Always run checks in this order. Stop as soon as you find the problem.**

### Level 1 — Environment Quick Check (5 seconds)

```bash
# What Mac is this?
uname -m                        # arm64 = Apple Silicon, x86_64 = Intel
sw_vers                         # macOS version
sysctl -n machdep.cpu.brand_string  # CPU model

# Python situation
which python3
python3 --version
which pip3

# Is ProwlrBot installed?
which prowlr
prowlr --version 2>/dev/null || echo "prowlr not found"
```

**If `uname -m` shows `x86_64` on Apple Silicon:** User is running under Rosetta. This causes problems with native packages. See Level 3.
**If `python3` is `/usr/bin/python3`:** System Python — see Level 2.
**If `prowlr` not found:** Installation issue — see Level 2.

### Level 2 — Python & Installation Issues

**System Python is too old or restricted:**

macOS ships with a minimal Python that lacks headers and has restrictions. Never use it for development.

```bash
# Check if using system Python
which python3
# BAD: /usr/bin/python3
# GOOD: /opt/homebrew/bin/python3, ~/.pyenv/shims/python3, or a venv path

# Install proper Python via Homebrew
brew install python@3.12

# Or via pyenv (recommended for version management)
brew install pyenv
pyenv install 3.12.8
pyenv global 3.12.8
# Add to ~/.zshrc:
# eval "$(pyenv init -)"
```

**pip install fails with "externally-managed-environment":**

Python 3.12+ on macOS (via Homebrew) enforces PEP 668. You MUST use a venv.

```bash
# This will fail:
pip install prowlrbot  # ERROR: externally-managed-environment

# This is correct:
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**pip install fails with SSL certificate errors:**

```bash
# Symptoms:
# SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
# urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED]>

# Fix 1: Install certificates (comes with Python installer)
/Applications/Python\ 3.12/Install\ Certificates.command

# Fix 2: If installed via Homebrew
pip install --upgrade certifi
# Then in Python:
import certifi
print(certifi.where())

# Fix 3: Set environment variable
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
# Add to ~/.zshrc to persist

# Fix 4: If behind corporate proxy
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org prowlrbot
```

**pip install fails building wheels (C extensions):**

```bash
# Symptoms: "error: command 'clang' failed"
# or "xcrun: error: invalid active developer path"

# Fix: Install Xcode Command Line Tools
xcode-select --install

# If already installed but broken:
sudo xcode-select --reset

# For specific packages needing build deps:
brew install cmake pkg-config openssl rust
export LDFLAGS="-L$(brew --prefix openssl)/lib"
export CPPFLAGS="-I$(brew --prefix openssl)/include"
```

**venv creation fails:**

```bash
# Symptoms: "Error: Command '[...python3', '-m', 'ensurepip']' returned non-zero"

# Fix: Install or reinstall pip
python3 -m ensurepip --upgrade

# Or create venv without pip, then bootstrap:
python3 -m venv .venv --without-pip
source .venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py | python3
```

### Level 3 — Apple Silicon (ARM64) Compatibility

**Architecture mismatch errors:**

```bash
# Check if running native ARM or Rosetta x86
file $(which python3)
# Should say: "Mach-O 64-bit executable arm64" on Apple Silicon
# If it says "x86_64" — you're using a Rosetta Python

# Check terminal
file /proc/self/exe 2>/dev/null || arch
# arm64 = native, i386 = Rosetta

# Fix: Make sure Terminal.app is NOT set to "Open using Rosetta"
# System Settings → Get Info on Terminal.app → uncheck "Open using Rosetta"
```

**onnxruntime crashes or won't install:**

```bash
# onnxruntime needs specific builds for ARM64
pip install onnxruntime
# If fails, try:
pip install onnxruntime-silicon  # Apple Silicon optimized build

# Or install the CPU-only version:
pip install onnxruntime --no-deps
```

**transformers / torch is slow or using CPU:**

```bash
# Check if MPS (Metal Performance Shaders) is available
python3 -c "import torch; print('MPS available:', torch.backends.mps.is_available())"

# If False — install the correct PyTorch build:
pip install torch torchvision torchaudio

# Use MPS in code:
device = "mps" if torch.backends.mps.is_available() else "cpu"
```

**llama-cpp-python build fails on Apple Silicon:**

```bash
# Needs Metal support compiled in
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python

# If cmake isn't found:
brew install cmake

# Verify Metal acceleration:
python3 -c "from llama_cpp import Llama; print('OK')"
```

### Level 4 — Port Conflicts

**Port 8088 (ProwlrBot app) or 8099 (bridge) already in use:**

```bash
# Find what's using the port
lsof -i :8088
lsof -i :8099

# Common culprits:
# - Another ProwlrBot instance
# - Previous crashed process still holding port

# Kill it:
kill -9 $(lsof -t -i :8088)

# Or use a different port:
prowlr app --port 8089
```

**Port 5000 conflict (AirPlay Receiver):**

```bash
# macOS Monterey+ uses port 5000 for AirPlay Receiver
# If any service tries to use 5000:
# System Settings → General → AirDrop & Handoff → AirPlay Receiver → OFF
```

**Port 7000 conflict (AirPlay):**

```bash
# Same as above — AirPlay also uses 7000
# Disable AirPlay Receiver if you need this port
```

### Level 5 — Networking & Firewall

**macOS firewall blocking connections:**

```bash
# Check firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# If enabled and blocking ProwlrBot:
# System Settings → Network → Firewall → Options
# Add Python / prowlr to allowed apps

# Or add programmatically:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which python3)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp $(which python3)
```

**"Accept Incoming Connections" popup keeps appearing:**

```bash
# This happens when the Python binary changes (venv rebuild, pip upgrade)
# Sign the binary to suppress:
sudo codesign --force --sign - $(which python3)
# Or the venv Python:
sudo codesign --force --sign - .venv/bin/python3
```

**Can't connect to WSL/Windows agents from Mac (war room):**

```bash
# Check if the bridge port is accessible
curl -s http://<remote-ip>:8099/healthz

# Common issues:
# 1. Windows firewall blocking 8099 — add rule on Windows side
# 2. Both machines need to be on same network or use Tailscale
# 3. WSL networking uses NAT — need port forwarding from Windows host

# Test with netcat:
nc -zv <remote-ip> 8099
```

**DNS resolution fails:**

```bash
# Check DNS
scutil --dns | head -20

# Flush DNS cache
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# Check /etc/hosts for conflicts
cat /etc/hosts
```

### Level 6 — Gatekeeper & Security

**"cannot be opened because the developer cannot be verified":**

```bash
# Gatekeeper blocking a downloaded binary (Ollama, llama.cpp, etc.)
# Fix for specific file:
xattr -d com.apple.quarantine /path/to/binary

# Fix for a directory:
xattr -dr com.apple.quarantine /path/to/directory/

# Check current Gatekeeper status:
spctl --status
```

**SIP (System Integrity Protection) blocking operations:**

```bash
# Check SIP status
csrutil status
# Should be "enabled" — don't disable unless absolutely necessary

# SIP blocks:
# - Writing to /usr, /System, /bin, /sbin
# - Modifying system Python
# - Attaching debuggers to system processes
# Solution: Don't use system paths. Use Homebrew, pyenv, or venvs.
```

**Keychain prompts when accessing credentials:**

```bash
# ProwlrBot stores secrets in ~/.prowlrbot.secret/envs.json
# If macOS Keychain keeps prompting:
security unlock-keychain ~/Library/Keychains/login.keychain-db

# For automated/headless operation, use environment variables instead:
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

### Level 7 — Local Model Backends

**Ollama won't start or isn't detected:**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags 2>/dev/null || echo "Ollama not running"

# Start Ollama
ollama serve &

# If not installed:
brew install ollama
# Or download from https://ollama.ai

# Pull a model:
ollama pull llama3.2

# Verify ProwlrBot detects it:
prowlr app  # Should show "Ollama detected" in startup
```

**MLX models fail on Apple Silicon:**

```bash
# MLX is Apple Silicon only — verify architecture
uname -m  # Must be arm64

# Install MLX backend:
pip install "prowlrbot[mlx]"
# Or:
pip install mlx-lm

# Test:
python3 -c "import mlx.core as mx; print('MLX OK, device:', mx.default_device())"
# Should show: MLX OK, device: gpu

# If "No module named mlx" — you might be on Intel Mac (not supported)
# If GPU not detected — update macOS to 13.3+
```

**llama.cpp / llama-cpp-python issues:**

```bash
# Install with Metal acceleration:
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# If Metal isn't available (Intel Mac):
pip install llama-cpp-python

# Test:
python3 -c "from llama_cpp import Llama; print('llama.cpp OK')"

# Common error: "Metal is not supported"
# → You're on Intel Mac, use CPU-only mode
# Common error: "Illegal instruction"
# → Architecture mismatch, rebuild with correct target
```

### Level 8 — Console Frontend (React/Node)

**npm ci / npm run build fails:**

```bash
# Check Node.js version
node --version  # Need 18+
npm --version

# If not installed or too old:
brew install node@20

# Common fix — clear cache and reinstall:
cd console
rm -rf node_modules package-lock.json
npm install
npm run build
```

**node-gyp build errors:**

```bash
# Needs Xcode CLT and Python
xcode-select --install
# node-gyp uses Python to build native addons
# Make sure a working Python is available:
npm config set python $(which python3)
```

**"EMFILE: too many open files":**

```bash
# macOS has a low default file descriptor limit
ulimit -n
# If 256 — that's too low

# Increase for current session:
ulimit -n 65536

# Persist in ~/.zshrc:
echo 'ulimit -n 65536' >> ~/.zshrc

# System-wide (survives reboot):
sudo launchctl limit maxfiles 65536 200000
```

### Level 9 — Performance & Resource Issues

**High CPU usage / fans spinning:**

```bash
# Check what's consuming CPU
top -l 1 -o cpu | head -20

# Common culprits:
# - Spotlight indexing the venv: exclude it
#   System Settings → Siri & Spotlight → Spotlight Privacy → Add .venv folder
# - fseventsd going crazy on node_modules:
#   Add to .git/info/exclude or .gitignore
# - Runaway Python process:
#   kill $(pgrep -f prowlr)
```

**Spotlight indexing slowing everything down:**

```bash
# Check indexing status
mdutil -s /

# Disable for project directories:
mdutil -i off /path/to/prowlrbot

# Or add to Spotlight Privacy list via System Settings
# This prevents Spotlight from indexing node_modules, .venv, etc.
```

**Process killed by macOS (memory pressure):**

```bash
# Check memory pressure
vm_stat | head -10
memory_pressure

# If "CRITICAL" — macOS will kill processes
# Reduce ProwlrBot memory usage:
# - Use smaller models (llama3.2:1b instead of llama3.2:8b)
# - Limit concurrent agents in config
# - Close memory-heavy apps

# Check swap usage
sysctl vm.swapusage
```

**Sleep/wake kills long-running processes:**

```bash
# Prevent sleep during long operations:
caffeinate -i prowlr app

# Or prevent sleep entirely while a command runs:
caffeinate -s -w $(pgrep -f "prowlr app")

# For background tasks, use launchd instead of running in terminal:
# Create ~/Library/LaunchAgents/com.prowlrbot.plist
```

### Level 10 — Miscellaneous macOS Issues

**Homebrew PATH not set correctly:**

```bash
# Apple Silicon Homebrew installs to /opt/homebrew
# Intel Homebrew installs to /usr/local

# Check:
which brew
brew --prefix

# If brew not found, add to ~/.zshrc:
# Apple Silicon:
eval "$(/opt/homebrew/bin/brew shellenv)"
# Intel:
eval "$(/usr/local/bin/brew shellenv)"
```

**zsh permission errors on venv activate:**

```bash
# "permission denied: .venv/bin/activate"
chmod +x .venv/bin/activate

# Or source with explicit shell:
source .venv/bin/activate

# If .venv was created on another machine (Linux/Windows), recreate it:
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Git credential issues:**

```bash
# macOS Keychain integration
git config --global credential.helper osxkeychain

# If getting 403s on push:
# GitHub now requires PAT or SSH, not password
# Generate PAT: https://github.com/settings/tokens
# Or use SSH:
ssh-keygen -t ed25519 -C "your@email.com"
cat ~/.ssh/id_ed25519.pub
# Add to GitHub: Settings → SSH Keys
```

**Playwright browsers won't install:**

```bash
# Playwright needs to download browser binaries
playwright install

# If blocked by firewall/proxy:
PLAYWRIGHT_BROWSERS_PATH=0 playwright install

# On Apple Silicon, Playwright uses ARM builds
# If getting architecture errors:
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 pip install playwright
playwright install chromium
```

**Docker Desktop eating resources:**

```bash
# Check Docker resource usage
docker stats --no-stream

# Limit Docker resources:
# Docker Desktop → Settings → Resources
# CPU: 2-4 cores, Memory: 4GB, Swap: 1GB

# Or use Colima as a lighter alternative:
brew install colima
colima start --cpu 2 --memory 4
```

## Prevention Checklist

Give this to the user after any successful setup:

```bash
# 1. Verify you're not using system Python
which python3  # Should NOT be /usr/bin/python3

# 2. Always use a venv
python3 -m venv .venv
source .venv/bin/activate

# 3. Set file descriptor limit
echo 'ulimit -n 65536' >> ~/.zshrc

# 4. Exclude project from Spotlight
mdutil -i off $(pwd)

# 5. Install Xcode CLT (needed for C extensions)
xcode-select --install

# 6. Keep Homebrew updated
brew update && brew upgrade

# 7. For Apple Silicon — verify native ARM Python
file $(which python3)  # Should say arm64

# 8. Backup your config
cp -r ~/.prowlrbot ~/.prowlrbot-backup
```

## Common Error Quick Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `externally-managed-environment` | PEP 668 on Python 3.12+ | Use a venv |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Missing root certs | Install Certificates.command or certifi |
| `xcrun: error: invalid active developer path` | Missing Xcode CLT | `xcode-select --install` |
| `cannot be opened because the developer cannot be verified` | Gatekeeper | `xattr -d com.apple.quarantine <file>` |
| `mach-o file, but is an incompatible architecture` | ARM/x86 mismatch | Rebuild package natively |
| `EMFILE: too many open files` | Low ulimit | `ulimit -n 65536` |
| `Address already in use :8088` | Port conflict | `kill -9 $(lsof -t -i :8088)` |
| `Address already in use :5000` | AirPlay Receiver | Disable in System Settings |
| `No module named mlx` | Intel Mac or Rosetta | MLX is Apple Silicon only |
| `Metal is not supported` | Intel Mac | Use CPU-only llama.cpp |
| `Killed: 9` | macOS OOM killer | Reduce memory usage, check `memory_pressure` |
| `Operation not permitted` | SIP / permissions | Don't modify /usr, use Homebrew paths |
| `pip: command not found` | Python not in PATH | `python3 -m pip` or fix PATH |
| `node-gyp` build errors | Missing CLT or Python | `xcode-select --install` |
| `EACCES: permission denied` | npm global install | Use `npx` or `npm --prefix` |

## Response Style

- Lead with what you found, not what you're checking
- macOS users often don't know their architecture — always check `uname -m` first
- If a fix needs `sudo`, explain why and what it does
- Apple Silicon vs Intel matters for almost every native package — always identify the platform early
- After fixing, verify with `prowlr --version` and a test `prowlr app` launch
- Suggest the prevention checklist after every successful repair
