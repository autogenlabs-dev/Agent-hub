#!/bin/bash
# Install script for Claude Driver skill
# This script sets up the environment required for Claude CLI access

set -e

echo "🧠 Claude Driver - Installation"
echo "=============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we have npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

# Install @anthropic-ai/claude-code globally
echo "📦 Installing @anthropic-ai/claude-code..."
if [ "$EUID" -ne 0 ]; then
    echo "  (using sudo for global install)"
    sudo npm install -g @anthropic-ai/claude-code
else
    npm install -g @anthropic-ai/claude-code
fi

# Verify installation
if command -v claude &> /dev/null; then
    echo -e "${GREEN}✅ claude CLI installed successfully${NC}"
    echo ""
    echo "📝 Next steps:"
    echo "1. Check if ~/.claude directory exists on your host machine"
    echo "2. If running in Docker, ensure ~/.claude is mounted to /root/.claude"
    echo "3. Run: claude login"
    echo "4. Run: ./check.sh to validate your setup"
    echo ""
else
    echo -e "${RED}❌ Installation failed - claude command not found${NC}"
    echo "Try: npm list -g @anthropic-ai/claude-code"
    exit 1
fi
