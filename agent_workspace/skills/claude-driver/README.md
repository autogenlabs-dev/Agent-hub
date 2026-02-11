# Claude Driver Skill

## Quick Start

```bash
# 1. Install dependencies
./install.sh

# 2. Authenticate
claude login

# 3. Validate setup
./check.sh

# 4. Use it!
claude -p "Explain how this code works"
```

## Requirements

- **Node.js & npm**: For installing the Claude CLI
- **Claude CLI**: `@anthropic-ai/claude-code` installed globally
- **Mount**: `~/.claude` directory accessible in container (see mount-setup.md)
- **Auth**: Valid Anthropic API credentials via `claude login`

## Documentation

- **SKILL.md**: Complete skill documentation (for agents)
- **mount-setup.md**: Docker/container setup instructions
- **examples/**: Usage examples and patterns
  - `basic-query.md`: Simple explanations and analysis
  - `refactor-example.md`: Code transformation examples

## Installation

See **install.sh** for automated setup.

## Validation

Run **check.sh** to verify your environment is properly configured.

## Usage

```bash
# Basic queries
claude -p "Explain the authentication system"

# Refactoring
claude -p "Refactor to use async/await instead of callbacks"

# Complex tasks (pipe instructions)
echo "Add tests for all API endpoints" | claude

# Interactive mode (for complex work)
claude
```

## Cost Considerations

- Uses your Anthropic API credits
- Each call consumes tokens based on context + response
- Larger codebases = higher cost
- Claude CLI has startup latency (5-10s typical)

## Security

- Claude can execute code - review changes before applying
- Use git branches for experimental work
- Never share auth credentials
- This skill respects OpenClaw's safety boundaries

## Troubleshooting

**"claude command not found"**
→ Run `./install.sh`

**"Not authenticated"**
→ Run `claude login` on host machine

**"No ~/.claude directory"**
→ Ensure Docker mount is configured (see mount-setup.md)

**Slow responses**
→ Normal - Claude CLI has startup overhead
