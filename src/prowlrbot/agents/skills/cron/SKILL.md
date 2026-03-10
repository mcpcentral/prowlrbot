---
name: cron
description: Manage scheduled tasks via the prowlr command — create, list, pause, resume, delete jobs
metadata: { "prowlr": { "emoji": "⏰" } }
---

# Scheduled Task Management

Use the `prowlr cron` command to manage scheduled tasks.

## Common Commands

```bash
# List all jobs
prowlr cron list

# View job details
prowlr cron get <job_id>

# View job status
prowlr cron state <job_id>

# Delete a job
prowlr cron delete <job_id>

# Pause/resume a job
prowlr cron pause <job_id>
prowlr cron resume <job_id>

# Run a job immediately
prowlr cron run <job_id>
```

## Creating Jobs

Two job types are supported:
- **text**: Send a fixed message to a channel on schedule
- **agent**: Ask the Agent a question on schedule and send the reply to a channel

### Quick Create

```bash
# Send a text message every day at 9:00
prowlr cron create \
  --type text \
  --name "daily-greeting" \
  --cron "0 9 * * *" \
  --channel imessage \
  --target-user "CHANGEME" \
  --target-session "CHANGEME" \
  --text "Good morning!"

# Ask the Agent every 2 hours
prowlr cron create \
  --type agent \
  --name "check-todos" \
  --cron "0 */2 * * *" \
  --channel dingtalk \
  --target-user "CHANGEME" \
  --target-session "CHANGEME" \
  --text "What are my pending tasks?"
```

### Required Parameters

Creating a job requires:
- `--type`: Job type (text or agent)
- `--name`: Job name
- `--cron`: Cron expression (e.g. `"0 9 * * *"` for daily at 9:00)
- `--channel`: Target channel (imessage / discord / dingtalk / qq / console)
- `--target-user`: User identifier
- `--target-session`: Session identifier
- `--text`: Message content (text type) or question (agent type)

### Create from JSON (advanced)

```bash
prowlr cron create -f job_spec.json
```

## Cron Expression Examples

```
0 9 * * *      # Every day at 9:00
0 */2 * * *    # Every 2 hours
30 8 * * 1-5   # Weekdays at 8:30
0 0 * * 0      # Every Sunday at midnight
*/15 * * * *   # Every 15 minutes
```

## Usage Tips

- If parameters are missing, ask the user to provide them before creating
- Before pausing/deleting/resuming, use `prowlr cron list` to find the job_id
- For troubleshooting, use `prowlr cron state <job_id>` to check status
- Provide complete, copy-pasteable commands to the user
