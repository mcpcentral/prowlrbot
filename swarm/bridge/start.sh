#!/bin/bash
# Bridge API startup script for Mac

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for .env file
if [ ! -f .env.bridge ]; then
    echo "Error: .env.bridge file not found"
    echo "Copy .env.bridge.example to .env.bridge and fill in your values"
    exit 1
fi

# Load environment
export $(grep -v '^#' .env.bridge | xargs)

# Validate required variables
if [ -z "$HMAC_SECRET" ] || [ "${#HMAC_SECRET}" -lt 32 ]; then
    echo "Error: HMAC_SECRET must be at least 32 characters"
    exit 1
fi

if [ -z "$ALLOWED_IPS" ]; then
    echo "Warning: ALLOWED_IPS not set - all IPs will be allowed"
fi

# Start the server
echo "Starting AI Swarm Bridge API..."
docker-compose -f docker-compose.bridge.yml up --build -d

echo "Bridge API starting..."
echo "Health check: curl http://localhost:8765/health"
