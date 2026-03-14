# Cross-Network War Room Setup

> **Problem:** Your Mac is on a guest WiFi and your WSL is on the main network (or vice versa). They can't see each other directly.
>
> **Solution:** Use a tunnel service to bridge the networks. Pick one below.

---

## Quick Decision

| Situation | Use This | Cost |
|-----------|----------|------|
| Ongoing development, multiple machines | **Tailscale** | Free (3 users, 100 devices) |
| Quick one-off session | **Cloudflare Tunnel** | Free (no account needed) |
| You have a VPS, want no third-party | **SSH reverse tunnel** | Free |
| Want self-hosted sovereignty | **ZeroTier** | Free (25 devices) |

---

## Option 1: Tailscale (Recommended)

Tailscale creates a private mesh network between your devices. Each device gets a stable IP (100.x.x.x) that works regardless of what WiFi/network it's on. **Best for ongoing development.**

### Install

```bash
# macOS
brew install tailscale

# Linux / WSL
curl -fsSL https://tailscale.com/install.sh | sh
```

### Setup (2 minutes)

**On both machines:**

```bash
# Start Tailscale
sudo tailscale up

# It opens a browser for authentication — log in with GitHub/Google/etc.
# Both machines must use the same account.
```

**Get your Tailscale IPs:**

```bash
tailscale ip -4
# → 100.x.x.x (this is your stable Tailscale IP)
```

**Start the bridge on the database host (e.g., Mac):**

```bash
cd prowlrbot
PYTHONPATH=src python3 -m prowlrbot.hub.bridge
# Starts on port 8099
```

**Configure WSL agents to connect via Tailscale IP:**

```bash
claude mcp add prowlr-hub -s local \
  -e PYTHONPATH="$(pwd)/src" \
  -e PROWLR_AGENT_NAME="wsl-agent" \
  -e PROWLR_CAPABILITIES="code,testing" \
  -e PROWLR_HUB_URL="http://100.x.x.x:8099" \
  -- python3 -m prowlrbot.hub
```

Replace `100.x.x.x` with the Mac's Tailscale IP.

**Verify:**

```bash
# From WSL, test connectivity
curl http://100.x.x.x:8099/health
# → {"status":"ok","room_id":"...","agents":0,"tasks":0}
```

### Why Tailscale?

- Works across **any** network (guest WiFi, VPN, LTE, different buildings)
- IPs are **stable** — no reconfiguration when you switch networks
- **Encrypted** (WireGuard) — safe even on public WiFi
- Free tier: 3 users, 100 devices, **no bandwidth limits**
- One `tailscale up` and you're done forever

### WSL2 Note

Tailscale works inside WSL2 directly. Install it in WSL (not Windows) so your Claude Code terminal can use the Tailscale IP. If you install Tailscale on Windows instead, you'd need to use the Windows Tailscale IP and forward the port into WSL.

```bash
# Inside WSL2
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

---

## Option 2: Cloudflare Tunnel (Quick & Free)

Cloudflare Tunnel (formerly Argo Tunnel) exposes your local bridge to the internet via a random HTTPS URL. **No account needed** for quick tunnels. Best for one-off sessions.

### Install

```bash
# macOS
brew install cloudflared

# Linux / WSL
# Download the latest release
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
```

### Setup (30 seconds)

**On the bridge host (Mac):**

```bash
# Start the bridge
cd prowlrbot
PYTHONPATH=src python3 -m prowlrbot.hub.bridge &

# Tunnel it to the internet
cloudflared tunnel --url http://localhost:8099
```

Cloudflare prints a URL like:
```
https://random-words-here.trycloudflare.com
```

**Configure WSL agents with that URL:**

```bash
claude mcp add prowlr-hub -s local \
  -e PYTHONPATH="$(pwd)/src" \
  -e PROWLR_AGENT_NAME="wsl-agent" \
  -e PROWLR_CAPABILITIES="code,testing" \
  -e PROWLR_HUB_URL="https://random-words-here.trycloudflare.com" \
  -- python3 -m prowlrbot.hub
```

**Verify:**

```bash
curl https://random-words-here.trycloudflare.com/health
```

### Limitations

- URL is **random and ephemeral** — changes every time you restart
- No custom domain on free tier (need a Cloudflare account for persistent tunnels)
- Exposed to the internet (but no auth endpoint, so low risk for a coordination server)
- Slight latency (traffic goes through Cloudflare's edge network)

---

## Option 3: SSH Reverse Tunnel

If one machine can SSH to the other (e.g., you have a VPS both can reach), you can tunnel through it. **No third-party service needed.**

### Setup

**Scenario:** Mac runs the bridge. WSL can SSH to the Mac (or a shared VPS).

```bash
# On Mac: start the bridge
cd prowlrbot
PYTHONPATH=src python3 -m prowlrbot.hub.bridge &

# On WSL: create an SSH tunnel that forwards local port 8099 to Mac's port 8099
ssh -L 8099:localhost:8099 user@mac-hostname -N
```

Now on WSL, `localhost:8099` tunnels to the Mac's bridge.

**Configure WSL agents:**

```bash
claude mcp add prowlr-hub -s local \
  -e PYTHONPATH="$(pwd)/src" \
  -e PROWLR_AGENT_NAME="wsl-agent" \
  -e PROWLR_CAPABILITIES="code,testing" \
  -e PROWLR_HUB_URL="http://localhost:8099" \
  -- python3 -m prowlrbot.hub
```

### Keep it alive

```bash
# Install autossh for auto-reconnect
sudo apt install autossh

# Use autossh instead of ssh
autossh -M 0 -L 8099:localhost:8099 user@mac-hostname -N
```

---

## Option 4: ZeroTier

Similar to Tailscale but self-hostable. Gives each device a virtual IP on a private network.

### Install

```bash
# macOS
brew install zerotier-one

# Linux / WSL
curl -s https://install.zerotier.com | sudo bash
```

### Setup

1. Create a network at [my.zerotier.com](https://my.zerotier.com) (free, no credit card)
2. Copy the network ID
3. On both machines: `sudo zerotier-cli join <network-id>`
4. Authorize both machines in the ZeroTier dashboard
5. Get IPs: `sudo zerotier-cli listnetworks`

Then configure the same way as Tailscale — use the ZeroTier IP for `PROWLR_HUB_URL`.

---

## Networking Troubleshooting

### Can my machines reach each other?

```bash
# Find your IP
# macOS
ipconfig getifaddr en0

# Linux / WSL
hostname -I | awk '{print $1}'

# Test connectivity
ping <other-machine-ip>
curl http://<other-machine-ip>:8099/health
```

If `ping` works but `curl` doesn't, it's a firewall issue.

### Firewall Issues

**macOS:**

```bash
# Check if firewall is enabled
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Allow Python through the firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3

# Or temporarily disable (development only!)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
```

**Linux / WSL:**

```bash
# Check if ufw is active
sudo ufw status

# Allow port 8099
sudo ufw allow 8099/tcp

# Or if using iptables
sudo iptables -A INPUT -p tcp --dport 8099 -j ACCEPT
```

**Windows (for WSL2):**

WSL2 runs behind a NAT by default. If the bridge is running inside WSL2 and you need to reach it from outside:

```powershell
# In PowerShell (Admin) — forward Windows port 8099 to WSL2
netsh interface portproxy add v4tov4 listenport=8099 listenaddress=0.0.0.0 connectport=8099 connectaddress=$(wsl hostname -I | ForEach-Object { $_.Trim() })

# Also allow through Windows Firewall
netsh advfirewall firewall add rule name="ProwlrHub Bridge" dir=in action=allow protocol=TCP localport=8099
```

**WSL2 Mirrored Networking (Windows 11 22H2+):**

The cleanest fix for WSL2 networking. Add to `%UserProfile%\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
```

Then `wsl --shutdown` and reopen. WSL2 now shares the Windows network directly — no port forwarding needed.

### Bridge won't start

```bash
# Check if port 8099 is already in use
lsof -i :8099  # macOS/Linux
# or
ss -tlnp | grep 8099  # Linux

# Kill the stuck process
kill $(lsof -ti :8099)

# Check if FastAPI/uvicorn are installed
pip install fastapi uvicorn
```

### Agent not appearing on the board

Agents auto-register on first tool call. If an agent isn't visible:

1. Have them call `check_mission_board` — this triggers registration
2. Check the bridge is running: `curl http://<bridge-url>/health`
3. Check `PROWLR_HUB_URL` is set correctly in their `.mcp.json`
4. Restart Claude Code (not just the conversation)

### "Database is locked"

SQLite WAL mode handles most concurrency. If persistent:

```bash
# Find stuck processes
ps aux | grep prowlrbot.hub

# Kill stale ones
kill <pid>

# Nuclear option: remove the WAL/SHM files (safe, they'll regenerate)
rm ~/.prowlrbot/warroom.db-wal ~/.prowlrbot/warroom.db-shm
```

### Bridge health check fails

```bash
# Verbose bridge startup
PYTHONPATH=src PROWLR_BRIDGE_HOST=0.0.0.0 PROWLR_BRIDGE_PORT=8099 python3 -m prowlrbot.hub.bridge

# Test from the same machine first
curl http://localhost:8099/health

# Then from the remote machine
curl http://<bridge-ip>:8099/health
```

### WSL2-specific issues

```bash
# Check WSL2 IP (it's different from Windows IP!)
ip addr show eth0 | grep inet

# Check if WSL2 can reach the internet at all
curl -s https://httpbin.org/ip

# Check if DNS works
nslookup google.com
```

---

## Architecture: How Cross-Network Works

```
┌─────── Guest WiFi ───────┐     ┌─────── Main Network ───────┐
│                          │     │                             │
│  Mac Terminal 1 ─┐       │     │       ┌─ WSL Terminal 1    │
│  Mac Terminal 2 ─┤       │     │       ├─ WSL Terminal 2    │
│  Mac Terminal 3 ─┘       │     │       └─ WSL Terminal 3    │
│       │                  │     │              │              │
│  SQLite ← Bridge :8099   │     │              │              │
│       │                  │     │              │              │
└───────┼──────────────────┘     └──────────────┼──────────────┘
        │                                       │
        └──── Tunnel (Tailscale/CF/SSH) ────────┘
             100.x.x.x:8099 or
             xxx.trycloudflare.com
```

The bridge is just a thin HTTP wrapper around SQLite. The tunnel makes it reachable across networks. All war room operations (claims, locks, broadcasts) go through the tunnel transparently.

---

## Quick Reference

| What | Command |
|------|---------|
| Start bridge | `PYTHONPATH=src python3 -m prowlrbot.hub.bridge` |
| Check bridge health | `curl http://localhost:8099/health` |
| Mac IP | `ipconfig getifaddr en0` |
| Linux/WSL IP | `hostname -I \| awk '{print $1}'` |
| Tailscale IP | `tailscale ip -4` |
| Tailscale start | `sudo tailscale up` |
| Cloudflare tunnel | `cloudflared tunnel --url http://localhost:8099` |
| SSH tunnel | `ssh -L 8099:localhost:8099 user@host -N` |
| Test connectivity | `curl http://<ip>:8099/health` |
| WSL2 port forward | `netsh interface portproxy add v4tov4 ...` |
