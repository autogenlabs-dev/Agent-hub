# Basic Query Examples

## Simple Explanations

### Understanding a file
```bash
claude -p "Explain what the memory-search function does in this codebase"
```

### Documenting code
```bash
claude -p "Write documentation for the authentication module"
```

### Explaining concepts
```bash
claude -p "Explain how the memory subsystem works in this project"
```

### Code review
```bash
claude -p "Review this pull request and identify any potential issues"
```

## Analysis Tasks

### Finding bugs
```bash
claude -p "Analyze this code for potential race conditions or security vulnerabilities"
```

### Performance review
```bash
claude -p "Identify performance bottlenecks in this database query"
```

### Architectural analysis
```bash
claude -p "Describe the overall architecture of this project and how components interact"
```

## Project Context

### Understanding a project
```bash
claude -p "Give me an overview of this project: what it does, tech stack, and key files"
```

### Explaining specific features
```bash
claude -p "How does the real-time notification system work in this codebase?"
```

### Dependency mapping
```bash
claude -p "Map out the dependencies between these services"
```

## Tips for Basic Queries

- Use `-p` flag for non-interactive "print mode" (best for agents)
- Keep queries focused and specific
- Claude can see your entire codebase context
- Latency is higher than typical agent responses due to Claude CLI startup
- Use for tasks requiring deep reasoning that benefits from Claude's capabilities
