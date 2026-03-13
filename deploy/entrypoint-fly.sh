#!/bin/sh
# Fly.io entrypoint for ProwlrBot.
# The persistent volume at /data may be empty on first deploy.
# Initialize config if needed, then start the app.
set -e

# Ensure directories exist inside the volume
mkdir -p /data/.prowlrbot /data/.prowlrbot.secret

# Initialize config if not present (first deploy)
if [ ! -f /data/.prowlrbot/config.json ]; then
    echo "[entrypoint] First run — initializing default config..."
    prowlr init --defaults --accept-security 2>/dev/null || true
fi

exec prowlr app --host 0.0.0.0 --port "${PROWLRBOT_PORT:-8088}"
