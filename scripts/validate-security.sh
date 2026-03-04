#!/bin/bash
# Security validation script for AI Swarm
# Run this before deployment to verify security settings

echo "=========================================="
echo "AI Swarm Security Validation"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ERRORS=$((ERRORS + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

echo "1. Checking Docker Compose files..."
echo "-----------------------------------"

if [ -f "docker-compose.swarm.yml" ]; then
    check_pass "docker-compose.swarm.yml exists"

    # Check for Redis password
    if grep -q "requirepass\|REDIS_PASSWORD" docker-compose.swarm.yml 2>/dev/null; then
        check_pass "Redis password configured"
    else
        check_warn "Redis has no password (consider adding for production)"
    fi

    # Check for healthcheck
    if grep -q "healthcheck" docker-compose.swarm.yml 2>/dev/null; then
        check_pass "Healthcheck configured"
    else
        check_warn "No healthcheck configured"
    fi
else
    check_fail "docker-compose.swarm.yml not found"
fi

if [ -f "swarm/bridge/docker-compose.bridge.yml" ]; then
    check_pass "docker-compose.bridge.yml exists"
else
    check_warn "docker-compose.bridge.yml not found (Mac-side)"
fi

echo ""
echo "2. Checking environment files..."
echo "-----------------------------------"

if [ -f ".env.swarm" ]; then
    check_pass ".env.swarm exists"

    # Check HMAC_SECRET
    if grep -q "HMAC_SECRET=" .env.swarm 2>/dev/null; then
        SECRET=$(grep "HMAC_SECRET=" .env.swarm | cut -d'=' -f2 | tr -d '"' "'" | head -1)
        if [ ${#SECRET} -ge 32 ]; then
            check_pass "HMAC_SECRET is at least 32 characters"
        else
            check_fail "HMAC_SECRET must be at least 32 characters"
        fi
    else
        check_fail "HMAC_SECRET not set in .env.swarm"
    fi

    # Check BRIDGE_HOST
    if grep -q "BRIDGE_HOST=" .env.swarm 2>/dev/null; then
        HOST=$(grep "BRIDGE_HOST=" .env.swarm | cut -d'=' -f2 | head -1)
        if [ "$HOST" = "100.x.x.x" ] || [ -z "$HOST" ]; then
            check_fail "BRIDGE_HOST is not configured (still set to placeholder)"
        else
            check_pass "BRIDGE_HOST is configured: $HOST"
        fi
    else
        check_fail "BRIDGE_HOST not set"
    fi
else
    if [ -f ".env.swarm.example" ]; then
        check_warn ".env.swarm not found (copy from .env.swarm.example)"
    else
        check_fail ".env.swarm.example not found"
    fi
fi

echo ""
echo "3. Checking security implementations..."
echo "-----------------------------------"

# Check HMAC implementation
if [ -f "swarm/worker/main.py" ]; then
    if grep -q "hmac.new" swarm/worker/main.py 2>/dev/null; then
        check_pass "HMAC signing implemented in worker"
    else
        check_fail "HMAC signing not found in worker"
    fi
else
    check_fail "swarm/worker/main.py not found"
fi

if [ -f "swarm/bridge/main.py" ]; then
    if grep -q "hmac.compare_digest" swarm/bridge/main.py 2>/dev/null; then
        check_pass "HMAC verification implemented in bridge"
    else
        check_fail "HMAC verification not found in bridge"
    fi
else
    check_fail "swarm/bridge/main.py not found"
fi

# Check IP allowlist
if [ -f "swarm/bridge/config.py" ]; then
    if grep -q "ALLOWED_IPS\|allowed_ips" swarm/bridge/config.py 2>/dev/null; then
        check_pass "IP allowlist configured"
    else
        check_warn "IP allowlist not configured"
    fi
fi

# Check path traversal protection
if [ -f "swarm/bridge/capabilities.py" ]; then
    if grep -q "abspath\|expanduser\|startswith.*home" swarm/bridge/capabilities.py 2>/dev/null; then
        check_pass "Path traversal protection in capabilities"
    else
        check_warn "Path traversal protection may be missing"
    fi
fi

# Check shell command blocking
if grep -q "rm -rf /\|blocked\|> /dev/sda" swarm/bridge/capabilities.py 2>/dev/null; then
    check_pass "Shell command security checks in place"
else
    check_warn "Shell command security checks may be missing"
fi

echo ""
echo "4. Checking Dockerfiles..."
echo "-----------------------------------"

if [ -f "swarm/worker/Dockerfile" ]; then
    if grep -q "USER appuser\|USER 1000" swarm/worker/Dockerfile 2>/dev/null; then
        check_pass "Worker runs as non-root user"
    else
        check_warn "Worker may run as root"
    fi
else
    check_fail "swarm/worker/Dockerfile not found"
fi

if [ -f "swarm/bridge/Dockerfile" ]; then
    if grep -q "USER appuser\|USER 1000" swarm/bridge/Dockerfile 2>/dev/null; then
        check_pass "Bridge runs as non-root user"
    else
        check_warn "Bridge may run as root"
    fi
else
    check_fail "swarm/bridge/Dockerfile not found"
fi

echo ""
echo "5. Checking tests..."
echo "-----------------------------------"

if [ -d "tests/swarm" ]; then
    check_pass "Swarm tests directory exists"
    TEST_COUNT=$(find tests/swarm -name "test_*.py" 2>/dev/null | wc -l)
    if [ "$TEST_COUNT" -gt 0 ]; then
        check_pass "Found $TEST_COUNT test files"
    else
        check_warn "No test files found"
    fi
else
    check_warn "tests/swarm directory not found"
fi

echo ""
echo "=========================================="
echo "Security Validation Complete"
echo "=========================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}$WARNINGS warnings${NC} - review recommended"
    exit 0
else
    echo -e "${RED}$ERRORS errors, $WARNINGS warnings${NC} - fix before deployment"
    exit 1
fi
