# Web and API Monitoring Guide

ProwlrBot can watch websites and APIs for changes and alert you when something changes. Monitors are stored in `~/.prowlrbot/monitors.json`.

---

## Monitor types

| Type | What it watches |
|------|----------------|
| `web` | Fetches a web page, optionally extracting a CSS selector, diffs the content |
| `api` | Makes an HTTP request, checks the status code and optionally a JSON path value |

---

## Adding monitors

### Via CLI

```bash
# Watch a full web page
prowlr monitor add \
  --name apple-pricing \
  --url https://www.apple.com/shop/buy-mac \
  --interval 1h \
  --type web

# Watch a specific CSS element (e.g., a price)
prowlr monitor add \
  --name rtx-price \
  --url https://www.bestbuy.com/site/nvidia-geforce-rtx-5090/... \
  --interval 15m \
  --type web \
  --css-selector ".priceView-customer-price span"

# Watch an API endpoint
prowlr monitor add \
  --name github-status \
  --url https://www.githubstatus.com/api/v2/status.json \
  --interval 5m \
  --type api \
  --expected-status 200 \
  --json-path "$.status.indicator"
```

### Via the web UI

1. Open `http://localhost:8088`
2. Go to **Agent** tab → **Monitor** section (or Control tab)
3. Click **Add Monitor**
4. Fill in URL, interval, and optional selector

---

## Interval format

| Value | Meaning |
|-------|---------|
| `30s` | Every 30 seconds |
| `5m` | Every 5 minutes |
| `1h` | Every hour |
| `6h` | Every 6 hours |
| `24h` | Once per day |

---

## Managing monitors

```bash
prowlr monitor list               # show all configured monitors
prowlr monitor run apple-pricing  # run a single check immediately
prowlr monitor remove apple-pricing
```

---

## monitors.json format

Monitors are stored in `~/.prowlrbot/monitors.json`. You can edit this directly:

```json
[
  {
    "name": "apple-pricing",
    "type": "web",
    "url": "https://www.apple.com/shop/buy-mac",
    "interval": "1h",
    "enabled": true
  },
  {
    "name": "rtx-price",
    "type": "web",
    "url": "https://www.bestbuy.com/...",
    "interval": "15m",
    "enabled": true,
    "css_selector": ".priceView-customer-price span"
  },
  {
    "name": "my-api",
    "type": "api",
    "url": "https://api.example.com/status",
    "interval": "5m",
    "enabled": true,
    "expected_status": 200,
    "json_path": "$.status"
  }
]
```

---

## How monitors work

1. The `MonitorEngine` runs all enabled monitors on their configured intervals (via APScheduler)
2. Each check fetches the URL and compares it to the last stored snapshot
3. If a change is detected, `diff_summary` is computed
4. Changes can trigger notifications via the channel system or cron-style alerts

When you run `prowlr monitor run NAME`, it:
- Fetches the URL
- Runs the configured detector (web diff or API check)
- Prints whether content changed and a brief diff summary
- Stores the current snapshot for next comparison

---

## Change detection

### Web monitors

- Fetches the full page HTML (or the CSS selector's text if `css_selector` is set)
- Strips whitespace normalization
- Diffs against the previous snapshot
- Reports `changed: true` if any text content differs

### API monitors

- Makes an HTTP GET to the URL
- Checks that `status_code == expected_status`
- If `json_path` is set, extracts that JSON value and diffs it
- Reports `changed: true` if value differs or status code changed

---

## Connecting monitors to notifications

Monitors detect changes but don't send notifications by themselves. Connect them to alerts by creating a cron job that asks the agent to check monitors:

```bash
prowlr cron create \
  --type agent \
  --name "Monitor alert check" \
  --cron "*/15 * * * *" \
  --channel discord \
  --target-user YOUR_CHANNEL_ID \
  --target-session monitor-alerts \
  --text "Check all active monitors for any changes detected. If anything has changed, describe what changed and why it might matter. If nothing changed, say nothing."
```

Or use a web monitor to check your own API status endpoint and alert via Telegram:

```bash
# Add the monitor
prowlr monitor add \
  --name my-app-health \
  --url https://myapp.example.com/health \
  --interval 1m \
  --type api \
  --expected-status 200

# Create a cron job that checks and alerts
prowlr cron create \
  --type agent \
  --name "App health alert" \
  --cron "* * * * *" \
  --channel telegram \
  --target-user YOUR_CHAT_ID \
  --target-session health-alerts \
  --text "Run a check on the 'my-app-health' monitor. If the status is down, send an urgent alert."
```

---

## Practical examples

### Track software prices

```json
{
  "name": "macbook-pro-price",
  "type": "web",
  "url": "https://www.apple.com/shop/buy-mac/macbook-pro/14-inch",
  "interval": "2h",
  "css_selector": ".rc-price",
  "enabled": true
}
```

### Monitor competitor landing pages

```json
{
  "name": "competitor-pricing",
  "type": "web",
  "url": "https://competitor.com/pricing",
  "interval": "6h",
  "enabled": true
}
```

### Watch for GitHub releases

```json
{
  "name": "prowlrbot-releases",
  "type": "api",
  "url": "https://api.github.com/repos/ProwlrBot/prowlrbot/releases/latest",
  "interval": "1h",
  "json_path": "$.tag_name",
  "expected_status": 200,
  "enabled": true
}
```

### Check server health

```json
{
  "name": "production-api",
  "type": "api",
  "url": "https://api.myapp.com/health",
  "interval": "30s",
  "expected_status": 200,
  "json_path": "$.status",
  "enabled": true
}
```

---

## Storage

Monitor snapshots are stored in `~/.prowlrbot/` using `MonitorStorage` (SQLite-based). When you remove a monitor with `prowlr monitor remove NAME`, both the config entry and the stored snapshot are deleted.
