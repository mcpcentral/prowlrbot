# Skills Guide

Skills are Markdown-based capability packs that give ProwlrBot specialized knowledge and instructions. A skill is a directory containing a `SKILL.md` file with YAML frontmatter — no code required for basic skills.

---

## Built-in skills

| Skill | What it does |
|-------|-------------|
| `pdf` | Read, extract, merge, split, create, OCR, encrypt PDFs |
| `docx` | Read, create, edit Microsoft Word documents |
| `pptx` | Read, create, edit PowerPoint presentations |
| `xlsx` | Read, create, edit Excel spreadsheets |
| `news` | Browse news sites and summarize headlines |
| `cron` | Schedule agent tasks and manage cron jobs |
| `file_reader` | Read any file type using the file tool |
| `browser_visible` | Launch a visible browser window for automation |
| `himalaya` | Manage email via the Himalaya CLI |
| `dingtalk_channel` | Send messages to DingTalk groups |
| `github_app` | Manage GitHub repositories, issues, PRs |
| `marketing` | Marketing copy, campaigns, social media |
| `mac_doctor` | Diagnose and fix macOS-specific issues |
| `wsl_doctor` | Diagnose and fix WSL environment issues |

### List and enable skills

```bash
prowlr skills list                # show all skills and status
prowlr skills config              # interactive multi-select (TUI)
```

---

## SKILL.md format

A skill is a directory with at minimum a `SKILL.md` file. ProwlrBot reads this file and provides it to the agent as part of the system prompt when the skill is active.

### Minimal example

```markdown
---
name: weather
description: Get the current weather for any city using the wttr.in API.
---

# Weather Guide

Use the `shell` tool to fetch weather:

```bash
curl -s "https://wttr.in/London?format=3"
```

This returns: `London: ☁️  +12°C`

For a full forecast:
```bash
curl -s "https://wttr.in/London"
```
```

### Full SKILL.md with all frontmatter fields

```yaml
---
name: my-skill
description: One-sentence description of when to use this skill. Be specific — this is what the agent reads to decide whether to activate the skill.
license: MIT
metadata:
  prowlr:
    emoji: "🔧"
    requires:
      python: ">=3.10"
      pip: ["requests", "beautifulsoup4"]
---
```

### Frontmatter fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique skill identifier. Must match directory name. |
| `description` | Yes | Used by agent to decide when to use this skill. Be precise. |
| `license` | No | License for distribution |
| `metadata.prowlr.emoji` | No | Emoji shown in UI |
| `metadata.prowlr.requires` | No | Dependencies (informational only) |

---

## Skill directory layout

```
my-skill/
├── SKILL.md              # required — frontmatter + instructions
├── references/           # optional — additional docs the agent can read
│   ├── API.md
│   └── examples.md
└── scripts/              # optional — helper scripts
    └── fetch_data.py
```

The agent has access to all files in the skill directory via the file system tools. Reference files extend the main SKILL.md with more detailed documentation.

---

## Creating a custom skill

### Step 1: Create the skill directory

Skills live in `~/.prowlrbot/active_skills/` when enabled, but you create them as standalone directories and install them.

```bash
mkdir ~/my-skills/slack-notify
```

### Step 2: Write SKILL.md

```markdown
---
name: slack-notify
description: Send notifications to a Slack channel using a webhook URL. Use this when the user asks to notify a Slack channel or send a Slack message.
---

# Slack Notify

Send a message to Slack using a webhook:

## Prerequisites

Set the webhook URL:
```bash
prowlr env set SLACK_WEBHOOK_URL https://hooks.slack.com/services/...
```

## Usage

Use the `shell` tool to send a notification:

```bash
curl -s -X POST "$SLACK_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$MESSAGE\"}"
```

Replace `$MESSAGE` with the actual message text.

## Examples

Alert on completion:
```bash
curl -s -X POST "$SLACK_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Deployment complete! Version 1.2.3 is live."}'
```
```

### Step 3: Install the skill

Copy the skill directory into ProwlrBot's skills directory:

```bash
cp -r ~/my-skills/slack-notify ~/.prowlrbot/active_skills/
```

Or create a symlink for easier development:

```bash
ln -s ~/my-skills/slack-notify ~/.prowlrbot/active_skills/slack-notify
```

### Step 4: Enable it

```bash
prowlr skills config
# Toggle slack-notify to enabled
```

The skill is immediately active for the next agent query — no restart needed.

---

## Skills with scripts

For more complex skills, include helper scripts in a `scripts/` subdirectory.

```
youtube-dl/
├── SKILL.md
└── scripts/
    └── download.sh
```

`SKILL.md`:

```markdown
---
name: youtube-dl
description: Download YouTube videos, extract audio, convert to MP3.
---

# YouTube Downloader

Use `yt-dlp` to download videos.

## Install (if needed)
```bash
pip install yt-dlp
```

## Download video
```bash
yt-dlp -f "best[height<=1080]" "VIDEO_URL" -o "~/Downloads/%(title)s.%(ext)s"
```

## Extract audio as MP3
```bash
yt-dlp -x --audio-format mp3 "VIDEO_URL" -o "~/Downloads/%(title)s.%(ext)s"
```

## Helper script
See `scripts/download.sh` for a batch download wrapper.
```

---

## Skills with references

For skills with lots of documentation (API references, examples, etc.), split them into files under `references/`:

```
stripe/
├── SKILL.md
└── references/
    ├── payments.md
    ├── subscriptions.md
    └── webhooks.md
```

The `SKILL.md` acts as the index and links to detailed docs:

```markdown
---
name: stripe
description: Process payments, manage subscriptions, handle webhooks using the Stripe API.
---

# Stripe Integration

## Quick start

For payment processing, see references/payments.md.
For subscriptions, see references/subscriptions.md.
For webhook handling, see references/webhooks.md.
```

---

## Publishing to the marketplace

Once your skill is working:

```bash
# Add a manifest.json (optional — SKILL.md is detected automatically)
cat > ~/.prowlrbot/active_skills/slack-notify/manifest.json << 'EOF'
{
  "name": "slack-notify",
  "title": "Slack Notify",
  "description": "Send notifications to Slack channels via webhooks",
  "version": "1.0.0",
  "tags": ["slack", "notifications", "messaging"]
}
EOF

# Publish
prowlr market publish ~/.prowlrbot/active_skills/slack-notify \
  -c skills \
  --price 0 \
  --pricing free
```

See [Marketplace Guide](marketplace.md) for the full publishing workflow.

---

## How skills work internally

When ProwlrBot starts a conversation:

1. `SkillsManager` scans `~/.prowlrbot/active_skills/` and `src/prowlrbot/agents/skills/`
2. For each enabled skill, it reads `SKILL.md` and appends the content to the agent's system prompt
3. The agent can see all skill docs in its context and uses the `description` field to decide which skill applies
4. Skills can reference files in the skill directory — the agent can read them via the `file_read` tool

This means: the more precise your `description` field, the better the agent is at knowing when to apply the skill.

---

## Skill discovery path

| Location | Purpose |
|----------|---------|
| `src/prowlrbot/agents/skills/` | Built-in skills (shipped with ProwlrBot) |
| `~/.prowlrbot/active_skills/` | Enabled skills (both built-in copies and custom) |

`prowlr skills config` syncs enabled skills into `active_skills/`.
