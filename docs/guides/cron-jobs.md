# Cron Jobs and Automation Guide

ProwlrBot uses APScheduler to run scheduled tasks. Jobs run on a cron expression and can either send a fixed message to a channel or prompt the agent and deliver the reply.

---

## Two task types

| Type | What it does |
|------|-------------|
| `text` | Sends a fixed message string directly to the channel |
| `agent` | Sends a prompt to the ProwlrBotAgent, delivers the agent's reply to the channel |

Use `agent` type for anything that requires reasoning, current data lookups, or tool use.
Use `text` type for reminders or static broadcasts.

---

## Creating cron jobs

### Via CLI

```bash
prowlr cron create \
  --type agent \
  --name "Daily digest" \
  --cron "0 8 * * 1-5" \
  --channel console \
  --target-user me \
  --target-session main \
  --text "Summarize my top GitHub notifications and any open PRs that need review"
```

Required flags:
- `--type`: `agent` or `text`
- `--name`: Display name
- `--cron`: 5-field cron expression (minute hour day month weekday)
- `--channel`: Channel to deliver to (`console`, `discord`, `telegram`, `dingtalk`, `feishu`, `qq`, `imessage`)
- `--target-user`: User identifier in that channel
- `--target-session`: Session identifier
- `--text`: Message content (for `text` type) or agent prompt (for `agent` type)

Optional:
- `--timezone`: Default `UTC`. Use IANA names like `America/New_York`, `Europe/London`, `Asia/Shanghai`
- `--mode`: `final` (default) or `stream` for incremental delivery
- `--no-enabled`: Create in disabled state

### Via JSON file

```bash
prowlr cron create -f job.json
```

Example `job.json`:

```json
{
  "id": "",
  "name": "Daily standup",
  "enabled": true,
  "schedule": {
    "type": "cron",
    "cron": "0 9 * * 1-5",
    "timezone": "America/New_York"
  },
  "task_type": "agent",
  "request": {
    "input": [
      {
        "role": "user",
        "type": "message",
        "content": [{"type": "text", "text": "List my top 5 priorities for today based on recent git commits and open issues"}]
      }
    ],
    "session_id": "standup",
    "user_id": "cron"
  },
  "dispatch": {
    "type": "channel",
    "channel": "console",
    "target": {"user_id": "me", "session_id": "standup"},
    "mode": "final",
    "meta": {}
  },
  "runtime": {
    "max_concurrency": 1,
    "timeout_seconds": 120,
    "misfire_grace_seconds": 60
  },
  "meta": {}
}
```

### Via the web UI

1. Open `http://localhost:8088`
2. Go to **Control** tab → **Cron** section
3. Click **Add Job**
4. Fill in the schedule and task

---

## Managing existing jobs

```bash
prowlr cron list                  # show all jobs
prowlr cron get JOB_ID            # get full job spec
prowlr cron state JOB_ID          # show next run time, paused status

prowlr cron pause JOB_ID          # pause (keeps config, stops running)
prowlr cron resume JOB_ID         # resume a paused job
prowlr cron run JOB_ID            # trigger once immediately (ignores schedule)
prowlr cron delete JOB_ID         # remove permanently
```

---

## Cron expression reference

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── weekday (0=Sun, 1=Mon ... 6=Sat)
│ │ │ │ │
* * * * *
```

| Expression | When it runs |
|-----------|-------------|
| `0 9 * * *` | Daily at 09:00 |
| `0 9 * * 1-5` | Weekdays at 09:00 |
| `*/15 * * * *` | Every 15 minutes |
| `0 8,12,17 * * *` | 08:00, 12:00, 17:00 every day |
| `0 0 1 * *` | First day of every month at midnight |
| `30 6 * * 1` | Every Monday at 06:30 |
| `0 */4 * * *` | Every 4 hours |

---

## Practical examples

### Daily news briefing

```bash
prowlr cron create \
  --type agent \
  --name "Morning briefing" \
  --cron "0 7 * * *" \
  --channel telegram \
  --target-user your_telegram_chat_id \
  --target-session briefing \
  --timezone "America/New_York" \
  --text "Using the news skill, fetch the top 5 tech and world news headlines for today. Format as a short briefing."
```

### Weekly GitHub summary

```bash
prowlr cron create \
  --type agent \
  --name "Weekly PR review" \
  --cron "0 9 * * 1" \
  --channel console \
  --target-user me \
  --target-session weekly \
  --text "List all open pull requests across my GitHub repos that have been waiting more than 3 days. Include the PR title, author, and a one-line summary."
```

### Hourly website monitor alert

```bash
prowlr cron create \
  --type agent \
  --name "Price check" \
  --cron "0 * * * *" \
  --channel discord \
  --target-user 123456789 \
  --target-session price-alerts \
  --text "Check if the price of the RTX 5090 on newegg.com has dropped below $1500. If yes, notify me urgently."
```

### Scheduled reminder (text type)

```bash
prowlr cron create \
  --type text \
  --name "Standup reminder" \
  --cron "45 9 * * 1-5" \
  --channel console \
  --target-user me \
  --target-session reminders \
  --text "Standup in 15 minutes!"
```

### Send fixed message to DingTalk group

```bash
prowlr cron create \
  --type text \
  --name "Daily checkin" \
  --cron "0 9 * * *" \
  --channel dingtalk \
  --target-user GROUP_ID \
  --target-session daily \
  --timezone "Asia/Shanghai" \
  --text "Good morning! What's everyone working on today?"
```

---

## Heartbeat: scheduled agent check-in

The Heartbeat is a special built-in scheduled job. It runs the agent on a fixed interval with `HEARTBEAT.md` as the prompt — useful for keeping the agent "alive" and doing proactive tasks.

Configure in `~/.prowlrbot/config.json`:

```json
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "enabled": true,
        "every": "1h",
        "target": "console",
        "activeHours": {
          "start": "08:00",
          "end": "22:00"
        }
      }
    }
  }
}
```

Create `~/.prowlrbot/HEARTBEAT.md` with what the agent should do on each heartbeat:

```markdown
# Heartbeat

You are running a scheduled check. Do the following:
1. Check for any important emails or messages
2. Look for any critical alerts in your monitored websites
3. If anything important is found, notify via console
4. Otherwise, just log a brief status: "All clear at <time>"
```

---

## REST API

All cron operations are available via the API:

```bash
# List jobs
curl http://localhost:8088/cron/jobs

# Create job
curl -X POST http://localhost:8088/cron/jobs \
  -H "Content-Type: application/json" \
  -d @job.json

# Get job
curl http://localhost:8088/cron/jobs/JOB_ID

# Pause
curl -X POST http://localhost:8088/cron/jobs/JOB_ID/pause

# Resume
curl -X POST http://localhost:8088/cron/jobs/JOB_ID/resume

# Run immediately
curl -X POST http://localhost:8088/cron/jobs/JOB_ID/run

# Delete
curl -X DELETE http://localhost:8088/cron/jobs/JOB_ID
```

---

## Runtime settings

Each job has a `runtime` block controlling execution:

```json
"runtime": {
  "max_concurrency": 1,       // max simultaneous runs of this job
  "timeout_seconds": 120,     // abort if agent doesn't finish in time
  "misfire_grace_seconds": 60 // if job couldn't run on time, retry within this window
}
```

`misfire_grace_seconds`: If the server was down when the job was scheduled, APScheduler will run it if we're within `misfire_grace_seconds` of the missed time. After that, it skips until the next scheduled time.
