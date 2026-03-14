# Cross-Network Connectivity Guide

How to connect two machines on different isolated networks (e.g., guest WiFi + main network) to reach a local HTTP service (port 8099 or any port).

---

## Quick Comparison

| Solution | Install Complexity | Free Tier | Stable URL | Best For |
|---|---|---|---|---|
| **Tailscale** | Easy | 3 users, 100 devices | Yes (MagicDNS) | Dev + production |
| **Cloudflare Tunnel** | Easy | Unlimited (quick tunnel) | No (random URL) | Quick demos, webhooks |
| **ngrok** | Easy | 1GB/mo, 20K req/mo | Kinda (dev domain) | Quick demos, webhooks |
| **SSH Reverse Tunnel** | Medium | N/A (self-hosted) | Yes (your server) | When you have a VPS |
| **ZeroTier** | Easy | 25 devices | Yes (virtual IP) | Self-hosters |

**Recommendation**: Use **Tailscale** for ongoing development work. Use **Cloudflare Quick Tunnel** for one-off demos or sharing. Use **SSH reverse tunnel** if you already have a VPS.

---

## 1. Tailscale (Mesh VPN over WireGuard)

Creates a peer-to-peer encrypted mesh network. Both machines get a stable `100.x.y.z` IP and a MagicDNS name (e.g., `macbook.tail1234.ts.net`). Traffic goes directly between peers when possible, relayed through Tailscale DERP servers when not.

### Install

```bash
# macOS
brew install tailscale

# Linux / WSL
curl -fsSL https://tailscale.com/install.sh | sh
```

### Setup (3 steps)

```bash
# 1. Start and authenticate (opens browser)
sudo tailscale up

# 2. On the OTHER machine, do the same
sudo tailscale up

# 3. Find the other machine's Tailscale IP
tailscale status
# Example output:
#   100.64.0.1   macbook    user@   macOS   -
#   100.64.0.2   linux-dev  user@   linux   -
```

### Connect

From machine B, reach machine A's service at:
```
http://100.64.0.1:8099
# or via MagicDNS:
http://macbook:8099
```

### Free Tier Limits

- 3 users, 100 devices
- All features included (ACLs, MagicDNS, exit nodes, subnet routers)
- No bandwidth limits
- Free forever for personal use

### Security

- End-to-end WireGuard encryption (peer-to-peer)
- SSO authentication required
- ACLs control which devices can talk to which
- No ports opened on your firewall
- Tailscale never sees your traffic (only coordination)

---

## 2. Cloudflare Tunnel (cloudflared)

Creates an outbound-only tunnel from your machine to Cloudflare's edge. Gives you a public HTTPS URL that proxies to your local port. No account needed for quick tunnels.

### Install

```bash
# macOS
brew install cloudflared

# Linux / WSL
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
```

### Setup - Quick Tunnel (1 step, no account needed)

```bash
# Expose local port 8099 instantly
cloudflared tunnel --url http://localhost:8099

# Output:
#   Your quick Tunnel has been created! Visit it at:
#   https://seasonal-deck-organisms-sf.trycloudflare.com
```

Share that URL with the other machine. Done.

### Setup - Named Tunnel (persistent, needs free Cloudflare account)

```bash
# 1. Authenticate
cloudflared tunnel login

# 2. Create a named tunnel
cloudflared tunnel create my-dev-tunnel

# 3. Route DNS (requires a domain on Cloudflare)
cloudflared tunnel route dns my-dev-tunnel dev.yourdomain.com

# 4. Run it
cloudflared tunnel run --url http://localhost:8099 my-dev-tunnel
```

### Free Tier Limits

- Quick tunnels: unlimited, no account needed, random URL, no SLA
- Named tunnels: free with Cloudflare Zero Trust (free for up to 50 users)
- No bandwidth limits
- Automatic HTTPS/TLS

### Security

- Outbound-only connections (no ports opened)
- Automatic TLS certificates
- Cloudflare DDoS protection included
- Quick tunnel URLs are random and unguessable (but public)
- Anyone with the URL can access your service -- add authentication if needed

---

## 3. ngrok

Similar to Cloudflare Tunnel but with tighter free tier limits. Good for quick testing.

### Install

```bash
# macOS
brew install ngrok

# Linux / WSL
curl -fsSL https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz | tar xz -C /usr/local/bin
```

### Setup (3 steps)

```bash
# 1. Sign up at https://dashboard.ngrok.com/signup (free)
# 2. Add your auth token
ngrok config add-authtoken YOUR_TOKEN

# 3. Expose your port
ngrok http 8099

# Output:
#   Forwarding  https://abc123.ngrok-free.app -> http://localhost:8099
```

### Free Tier Limits

- 1 GB bandwidth/month
- 20,000 HTTP requests/month
- 1 static dev domain (e.g., `your-name.ngrok-free.app`)
- Up to 3 endpoints simultaneously
- Browser interstitial warning page on HTML responses
- URL changes each restart (unless you use the static dev domain)

### Security

- TLS encryption to ngrok edge
- Auth token required
- Free tier exposes a public URL -- anyone with it can access your service
- Add `--basic-auth="user:pass"` for simple protection:
  ```bash
  ngrok http 8099 --basic-auth="dev:secretpass"
  ```

---

## 4. SSH Reverse Tunnel

No third-party service needed. Requires one machine that can SSH to the other, OR a VPS/jump server both can reach.

### Scenario A: Machine A can SSH to Machine B

Machine A runs the service on port 8099. You want Machine B to access it.

```bash
# On Machine A (the one running the service):
ssh -R 8099:localhost:8099 user@machine-b-ip

# Now on Machine B, access the service at:
curl http://localhost:8099
```

### Scenario B: Neither can reach the other, but both can reach a VPS

```bash
# On Machine A (runs the service):
ssh -R 8099:localhost:8099 user@your-vps.com

# On Machine B (wants to access the service):
curl http://your-vps.com:8099
```

**Important**: For the VPS to listen on all interfaces (not just localhost), edit `/etc/ssh/sshd_config`:
```
GatewayPorts yes
```
Then restart sshd: `sudo systemctl restart sshd`

### Keep Alive

```bash
# Prevent timeout disconnects
ssh -R 8099:localhost:8099 -o ServerAliveInterval=60 -o ServerAliveCountMax=3 user@server

# Run in background with autossh (auto-reconnect)
# Install: brew install autossh  OR  apt install autossh
autossh -M 0 -f -N -R 8099:localhost:8099 user@server
```

### Security

- Standard SSH encryption
- No third-party service involved
- Limit access with SSH keys (disable password auth)
- Use `GatewayPorts clientspecified` instead of `yes` for finer control

---

## 5. ZeroTier (Virtual LAN)

Similar to Tailscale but uses its own protocol (not WireGuard). Creates a virtual Layer 2 network -- machines get virtual IPs as if on the same LAN. Can be fully self-hosted.

### Install

```bash
# macOS
brew install zerotier-one

# Linux / WSL
curl -fsSL https://install.zerotier.com | sudo bash
```

### Setup (4 steps)

```bash
# 1. Create a network at https://my.zerotier.com (free account)
#    Note your Network ID (e.g., 8056c2e21c000001)

# 2. Join the network on Machine A
sudo zerotier-cli join 8056c2e21c000001

# 3. Authorize Machine A in the ZeroTier web console (check the Auth checkbox)

# 4. Repeat steps 2-3 on Machine B
sudo zerotier-cli join 8056c2e21c000001
```

### Connect

```bash
# Find assigned IPs
sudo zerotier-cli listnetworks
# Example: 10.147.20.1 (Machine A), 10.147.20.2 (Machine B)

# From Machine B:
curl http://10.147.20.1:8099
```

### Free Tier Limits

- 1 network
- 25 devices
- No bandwidth limits
- Self-hosting available (controller + root servers)

### Security

- End-to-end encryption
- Network-level access control
- Self-hostable (full sovereignty)
- Less polished than Tailscale but more flexible

---

## Networking Troubleshooting

### Check if Two Machines Can Reach Each Other

```bash
# Basic connectivity
ping <other-machine-ip>

# Check if a specific port is open
nc -zv <ip> 8099           # netcat
curl -v http://<ip>:8099    # HTTP check

# Trace the route
traceroute <ip>             # macOS/Linux
tracert <ip>                # Windows
```

### Find Your IP Address

```bash
# macOS - local network IP
ipconfig getifaddr en0          # WiFi
ipconfig getifaddr en1          # Ethernet (some Macs)
ifconfig | grep "inet " | grep -v 127.0.0.1

# Linux - local network IP
hostname -I
ip addr show | grep "inet " | grep -v 127.0.0.1

# WSL2 - WSL's internal IP (behind NAT)
hostname -I                     # WSL IP (172.x.x.x range)
cat /etc/resolv.conf | grep nameserver  # Windows host IP

# Any platform - public IP
curl -s ifconfig.me
curl -s ipinfo.io/ip
```

### macOS Firewall

```bash
# Check firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Temporarily disable (for testing only)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off

# Re-enable
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Allow a specific app
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/app

# Check if stealth mode is blocking pings
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode
```

System Settings > Network > Firewall also controls this. If your service is unreachable, try disabling the firewall temporarily to isolate the issue.

### Linux Firewall (ufw)

```bash
# Check status
sudo ufw status verbose

# Allow a port
sudo ufw allow 8099/tcp

# Allow from specific IP only
sudo ufw allow from 192.168.1.100 to any port 8099

# Temporarily disable (testing only)
sudo ufw disable
```

### WSL2-Specific Networking

**The Problem**: WSL2 runs inside a lightweight VM with its own NAT. By default:
- WSL2 can reach the Windows host via `localhost`
- Windows can reach WSL2 services via `localhost` (auto-forwarded)
- Other machines on the LAN CANNOT reach WSL2

**Solution 1: Mirrored Networking (Windows 11 22H2+, recommended)**

Edit `%USERPROFILE%\.wslconfig`:
```ini
[wsl2]
networkingMode=mirrored
```

Then restart WSL: `wsl --shutdown` and reopen. WSL2 now shares the Windows host's network stack. Other LAN machines can reach WSL2 services directly via the Windows host IP.

**Solution 2: Port Forwarding (legacy, Windows 10)**

```powershell
# In PowerShell as Administrator:
# Get WSL2 IP
wsl hostname -I

# Forward Windows port to WSL2
netsh interface portproxy add v4tov4 `
    listenport=8099 listenaddress=0.0.0.0 `
    connectport=8099 connectaddress=<WSL2_IP>

# Also allow it through Windows Firewall
netsh advfirewall firewall add rule name="WSL2 Port 8099" `
    dir=in action=allow protocol=TCP localport=8099

# List current forwards
netsh interface portproxy show all

# Remove when done
netsh interface portproxy delete v4tov4 listenport=8099 listenaddress=0.0.0.0
```

**Gotcha**: WSL2's IP changes on every reboot. You must re-run the portproxy command after restarting WSL. Use mirrored networking mode to avoid this entirely.

**Solution 3: Use Tailscale inside WSL2**

Install Tailscale inside WSL2 and connect both machines to the same Tailnet. This bypasses all WSL2 NAT issues entirely:
```bash
# Inside WSL2:
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

---

## Decision Matrix

| Your Situation | Best Solution |
|---|---|
| Two dev machines, ongoing work | **Tailscale** |
| Quick demo to a colleague | **Cloudflare Quick Tunnel** |
| Webhook testing (Stripe, GitHub, etc.) | **ngrok** or **Cloudflare Quick Tunnel** |
| You have a VPS, want no third-party | **SSH reverse tunnel** |
| Want full self-hosting / sovereignty | **ZeroTier** |
| WSL2 machine + another machine | **Tailscale inside WSL2** |
| Production / always-on | **Tailscale** or **Cloudflare Named Tunnel** |

---

## Sources

- [Tailscale Pricing](https://tailscale.com/pricing)
- [Tailscale Quickstart](https://tailscale.com/docs/how-to/quickstart)
- [Tailscale macOS Install](https://tailscale.com/docs/install/mac)
- [Tailscale Linux Install](https://tailscale.com/docs/install/linux)
- [Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/)
- [cloudflared GitHub](https://github.com/cloudflare/cloudflared)
- [ngrok Free Plan Limits](https://ngrok.com/docs/pricing-limits/free-plan-limits)
- [ngrok Pricing](https://ngrok.com/pricing)
- [SSH Reverse Tunneling Explained (Teleport)](https://goteleport.com/blog/ssh-tunneling-explained/)
- [SSH Reverse Tunneling Guide (JFrog)](https://jfrog.com/blog/reverse-ssh-tunneling-from-start-to-end/)
- [ZeroTier vs Tailscale (Tailscale)](https://tailscale.com/compare/zerotier)
- [ZeroTier vs Tailscale (DEV Community)](https://dev.to/afeiszli/tailscale-vs-zerotier-1m79)
- [WSL Networking (Microsoft)](https://learn.microsoft.com/en-us/windows/wsl/networking)
- [WSL2 Mirrored Networking](https://hy2k.dev/en/blog/2025/10-31-wsl2-mirrored-networking-dev-server/)
- [Port Forwarding WSL2 to LAN](https://jwstanly.com/blog/article/Port+Forwarding+WSL+2+to+Your+LAN/)
