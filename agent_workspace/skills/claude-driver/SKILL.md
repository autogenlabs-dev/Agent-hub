---
name: claude-driver
description: Claude CLI integration for deep code reasoning, refactoring, and analysis. Use when tasks require Anthropic Claude's capabilities: (1) Complex refactoring across multiple files, (2) Deep architectural analysis, (3) Advanced debugging with reasoning, (4) Large-scale code transformations, (5) Second-opinion code reviews. This skill provides access to @anthropic-ai/claude-code CLI for complex coding tasks that benefit from Claude's superior reasoning.
---

# Claude Driver

"The Brain Extension" - Direct access to Anthropic's Claude Code CLI for advanced coding tasks.

## Requirements

### 1. Claude CLI Installed
`@anthropic-ai/claude-code` must be installed globally in the container.

**Installation:**
```bash
cd /home/node/.openclaw/workspace/skills/claude-driver
./install.sh
```

### 2. Authentication
User must authenticate with Anthropic API.

**Setup:**
```bash
claude login
```

### 3. Configuration Directory
Host `~/.claude` must be mounted to `/root/.claude` in container.

**Docker setup:**
```bash
docker run -v ~/.claude:/root/.claude ...
```

See `mount-setup.md` for detailed container/Docker configuration.

### 4. Validation
Verify setup:
```bash
./check.sh
```

## Usage Patterns

### When to Use Claude Driver

**Use for:**
- Complex refactoring across multiple files
- Deep architectural analysis and design decisions
- Advanced debugging with step-by-step reasoning
- Large-scale code transformations
- Second-opinion code reviews
- Tasks requiring context-aware reasoning about entire codebases

**Avoid for:**
- Simple code edits (use standard tools)
- Trivial explanations
- Quick fixes (latency makes it inefficient)
- One-liner changes

### Basic Query Mode

Use `-p` flag for non-interactive print mode (best for agents):

```bash
# Explain code
claude -p "Explain how the memory subsystem works in this project"

# Document code
claude -p "Write documentation for the authentication module"

# Find issues
claude -p "Analyze this code for race conditions"

# Architectural overview
claude -p "Describe the overall architecture and component interactions"
```

### Refactoring Mode

For complex code transformations:

```bash
# Add type safety
claude -p "Refactor login.ts to use Zod validation for all inputs"

# Modernize patterns
claude -p "Convert all callbacks to async/await in this codebase"

# Extract logic
claude -p "Extract authentication logic into a separate service module"

# Performance optimization
claude -p "Optimize these N+1 queries by adding proper eager loading"
```

See `examples/refactor-example.md` for comprehensive refactoring patterns.

### Interactive Mode

For complex multi-step tasks:

```bash
claude
# Then type interactive instructions
```

**Use when:**
- Tasks require back-and-forth iteration
- You want to guide Claude through decisions
- Exploring multiple approaches

### Piped Instructions

For predefined tasks:

```bash
echo "Add comprehensive unit tests to payment processing" | claude
echo "Update all dependencies and fix security vulnerabilities" | claude
```

**Caution:** Use carefully - piped instructions execute non-interactively.

## Cost & Performance

### API Costs
- Uses user's Anthropic API credits
- Token consumption: codebase context + query + response
- Larger codebases = significantly higher cost
- Each call triggers full context scan

### Performance Characteristics
- **Startup latency:** 5-10 seconds typical (node initialization)
- **Execution time:** varies with task complexity
- **Best for:** High-value tasks where latency is acceptable
- **Worst for:** Quick, trivial queries

## Error Handling & Safety

### Graceful Degradation

If Claude CLI is unavailable:
1. Check installation: `./check.sh`
2. Verify auth: `claude login` status
3. Check mount: `ls -la /root/.claude`
4. Fallback to standard tools for simple tasks

### Safety Guidelines

**Before applying changes:**
- Review all diffs carefully
- Use git branches for experimental work
- Test changes in non-production environment
- Maintain version control checkpoints

**Never use Claude for:**
- Executing unverified code
- Bypassing security controls
- Destructive operations without review
- Accessing unauthorized resources

## Advanced Usage

### Multi-File Operations

Claude can reason across multiple files:

```bash
claude -p "Refactor the entire auth flow across these files: auth.ts, user.ts, middleware.ts"
```

### Context Control

For targeted operations:

```bash
claude -p "Focus only on the database layer - optimize queries in models/"
```

### Architectural Decisions

Use Claude for design rationale:

```bash
claude -p "Evaluate moving from REST to GraphQL for this API. Consider: performance, complexity, team familiarity"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `claude: command not found` | Run `./install.sh` |
| `Not authenticated` | Run `claude login` on host |
| `~/.claude not found` | Configure mount (see `mount-setup.md`) |
| Slow responses | Normal - Claude CLI startup takes 5-10s |
| Auth errors in container | Verify mount path is `/root/.claude` |

## Examples & Reference

See `examples/` directory:
- `basic-query.md` - Simple explanations and analysis patterns
- `refactor-example.md` - Complex code transformation examples

## Skill Structure

```
claude-driver/
├── SKILL.md                    # This file (agent instructions)
├── install.sh                  # Automated installation script
├── check.sh                    # Environment validation script
├── mount-setup.md             # Docker/container setup guide
├── README.md                   # Quick start guide (for humans)
└── examples/
    ├── basic-query.md         # Simple usage examples
    └── refactor-example.md    # Advanced refactoring patterns
```

## Integration Notes

- This skill works alongside other OpenClaw tools
- Prefer standard tools for simple tasks
- Use Claude Driver only when superior reasoning adds significant value
- Combine with other skills: use `github` skill for PRs, `skill-creator` for packaging, etc.
