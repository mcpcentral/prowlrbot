# Deploying ProwlrBot

## Fly.io (App Server)

ProwlrBot runs on Fly.io as a Docker container with persistent storage for config, SQLite databases, and chat history.

### First-time setup

```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Authenticate
fly auth login

# 3. Create the app (from repo root)
fly apps create prowlrbot

# 4. Create persistent volume for data (config, SQLite, chats, skills)
fly volumes create prowlrbot_data --region sjc --size 1

# 5. Set secrets (add your API keys)
fly secrets set \
  OPENAI_API_KEY=sk-... \
  ANTHROPIC_API_KEY=sk-ant-... \
  PROWLRBOT_API_TOKEN=your-dashboard-password

# 6. Deploy
fly deploy
```

### Subsequent deploys

```bash
fly deploy
```

Or push to `main` — the GitHub Action at `.github/workflows/deploy-fly.yml` auto-deploys.

### Required GitHub secret

Add `FLY_API_TOKEN` to your repo secrets:
```bash
fly tokens create deploy -x 999999h
```
Copy the token to **Settings > Secrets > Actions > New repository secret** as `FLY_API_TOKEN`.

### Useful commands

```bash
fly status              # App status
fly logs                # Live logs
fly ssh console         # SSH into the machine
fly volumes list        # Check volumes
fly scale show          # Current machine size
fly scale vm shared-cpu-2x --memory 1024  # Resize
```

### Custom domain

```bash
fly certs add your-domain.com
# Then point your DNS A/AAAA records to the IPs shown
```

---

## Cloudflare Pages (Marketing Website)

The ProwlrBot marketing website deploys to Cloudflare Pages.

### First-time setup

```bash
# 1. Install wrangler
npm install -g wrangler

# 2. Authenticate
wrangler login

# 3. Create the Pages project
cd website
wrangler pages project create prowlrbot

# 4. Build and deploy (use --branch=production so prowlrbot.com updates)
npm ci && npm run build
wrangler pages deploy dist --project-name=prowlrbot --branch=production
```

### Required GitHub secrets

Add these to your repo secrets for CI/CD:

- `CLOUDFLARE_API_TOKEN` — Create at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens) with "Cloudflare Pages: Edit" permission
- `CLOUDFLARE_ACCOUNT_ID` — Found on your Cloudflare dashboard overview page

### Custom domain (e.g. prowlrbot.com)

1. Go to **Cloudflare Dashboard > Pages > prowlrbot > Custom domains**
2. Add your domain (e.g., `prowlrbot.com` or `www.prowlrbot.com`)
3. If domain is already on Cloudflare, DNS records are auto-configured
4. If not, add the CNAME record shown

**Important:** Custom domains serve the **production** deployment. When deploying with wrangler (Direct Upload), use `--branch=production` so the deploy updates production and thus prowlrbot.com. Without it, each deploy gets a preview URL only (e.g. `2e8e98b3.prowlrbot.pages.dev`).

---

## Cloudflare as CDN Proxy for Fly.io

To put Cloudflare in front of your Fly.io app (recommended for DDoS protection, caching, and SSL):

1. Add your domain to Cloudflare (free plan works)
2. Point DNS to Fly.io:
   ```
   A     app.prowlrbot.com    → <fly-ipv4>
   AAAA  app.prowlrbot.com    → <fly-ipv6>
   ```
   Get IPs from `fly ips list`
3. Set SSL mode to **Full (Strict)** in Cloudflare dashboard
4. Enable **Always Use HTTPS**
5. Add a Page Rule for `/api/*` to bypass cache (or use Cache Rules)

---

## Docker Images

Two Dockerfiles are available:

| File | Use Case | Size |
|------|----------|------|
| `deploy/Dockerfile` | Full image with Xvfb + XFCE for visible browser automation | ~2GB |
| `deploy/Dockerfile.fly` | Lean headless-only image for cloud deployment | ~800MB |

### Build locally

```bash
# Lean image (recommended)
docker build -f deploy/Dockerfile.fly -t prowlrbot:latest .

# Full image with browser desktop
docker build -f deploy/Dockerfile -t prowlrbot:full .

# Run
docker run -p 8088:8088 -v prowlrbot_data:/data prowlrbot:latest
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROWLRBOT_PORT` | `8088` | HTTP port |
| `PROWLRBOT_WORKING_DIR` | `~/.prowlrbot` | Config/data directory |
| `PROWLRBOT_API_TOKEN` | — | Dashboard auth token |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `GROQ_API_KEY` | — | Groq API key |
| `PROWLRBOT_ENABLED_CHANNELS` | `console` | Comma-separated channel list |
