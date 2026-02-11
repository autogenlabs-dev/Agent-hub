#!/bin/bash
# Validation script for Claude Driver skill
# Checks if all requirements are met

set -e

echo "🧠 Claude Driver - Environment Check"
echo "====================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

CHECKS_PASSED=0
CHECKS_FAILED=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check 1: claude CLI installed
echo "Checking claude CLI installation..."
if command -v claude &> /dev/null; then
    VERSION=$(claude --version 2>/dev/null || echo "unknown")
    check_pass "claude CLI is installed (version: $VERSION)"
else
    check_fail "claude CLI is not installed"
    echo "   Run: ./install.sh"
fi
echo ""

# Check 2: Claude directory exists
echo "Checking Claude configuration directory..."
if [ -d "$HOME/.claude" ]; then
    check_pass "~/.claude directory exists"
else
    check_warn "~/.claude directory not found"
    echo "   This is expected on first run. Run 'claude login' to create it."
fi
echo ""

# Check 3: Auth credentials
echo "Checking authentication status..."
if [ -f "$HOME/.claude/auth_credentials.json" ]; then
    check_pass "Authentication credentials found"
    # Check if we can actually use claude (simple test)
    if claude -p "echo" 2>&1 | grep -q "error"; then
        check_warn "Auth found but may need refresh. Try: claude login"
    else
        check_pass "Authentication appears valid"
    fi
else
    check_fail "Not authenticated"
    echo "   Run: claude login"
fi
echo ""

# Check 4: Test claude CLI (non-destructive)
echo "Testing claude CLI (dry run)..."
if command -v claude &> /dev/null; then
    # Quick non-destructive test
    TIMEOUT=5
    if timeout $TIMEOUT claude -p "say 'test'" &> /dev/null; then
        check_pass "claude CLI is responsive"
    else
        check_warn "claude CLI did not respond within ${TIMEOUT}s (may be slow to start)"
    fi
else
    check_fail "Cannot test - claude CLI not installed"
fi
echo ""

# Summary
echo "====================================="
echo -e "${GREEN}Passed:${NC} $CHECKS_PASSED"
echo -e "${RED}Failed:${NC} $CHECKS_FAILED"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Claude Driver is ready to use.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please resolve issues above.${NC}"
    exit 1
fi
