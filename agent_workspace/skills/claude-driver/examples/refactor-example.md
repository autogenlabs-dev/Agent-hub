# Refactoring Examples

## Code Transformations

### Adding Type Safety
```bash
claude -p "Refactor the login.ts file to use Zod validation for all input fields"
```

### Modernizing Patterns
```bash
claude -p "Update this codebase to use async/await instead of callback patterns"
```

### Error Handling
```bash
claude -p "Add comprehensive error handling to the API client, including retry logic and circuit breakers"
```

### Extracting Logic
```bash
claude -p "Extract the authentication logic from the user controller into a separate service module"
```

## Architectural Changes

### Database Migrations
```bash
claude -p "Refactor the user model to use a separate profile table and create the migration"
```

### API Design
```bash
claude -p "Convert these REST endpoints to GraphQL schema with proper resolvers"
```

### State Management
```bash
claude -p "Refactor this Redux store to use Zustand for simpler state management"
```

## Testing & Quality

### Adding Tests
```bash
claude -p "Write comprehensive unit tests for the payment processing module"
```

### Test Coverage
```bash
claude -p "Identify untested code and add tests to reach 80% coverage"
```

### Type Safety Improvements
```bash
claude -p "Add TypeScript types and interfaces to the entire utilities module"
```

## Performance Optimizations

### Database Queries
```bash
claude -p "Optimize these N+1 queries by adding proper eager loading"
```

### Caching
```bash
claude -p "Add Redis caching layer for frequently accessed data"
```

### Algorithm Improvements
```bash
claude -p "Optimize the search algorithm from O(n²) to O(n log n)"
```

## Security Hardening

### Input Validation
```bash
claude -p "Add input sanitization and validation to all user-facing endpoints"
```

### Authentication
```bash
claude -p "Implement JWT refresh token rotation for better security"
```

### Dependency Updates
```bash
claude -p "Update all dependencies and fix any security vulnerabilities"
```

## Advanced Refactoring

### Multi-file Changes
```bash
claude -p "Refactor the entire authentication flow to use OAuth2 with multiple providers"
```

### Breaking Changes
```bash
claude -p "Plan and execute the migration from v1 to v2 API, maintaining backward compatibility"
```

### Large-scale Restructuring
```bash
claude -p "Restructure this monolith into microservices with proper service boundaries"
```

## Tips for Refactoring

1. **Be Specific**: Describe exactly what you want changed
2. **Scope**: Claude can handle multiple files - be clear about the scope
3. **Testing**: Always ask for tests when refactoring
4. **Incremental**: For large refactors, break into smaller steps
5. **Interactive Mode**: For complex refactors, consider using interactive mode:
   ```bash
   claude
   # Then type: "Refactor the auth system..."
   ```
6. **Review Changes**: Always review what Claude produces before applying
7. **Version Control**: Commit before major refactors so you can rollback if needed

## Safety Precautions

- Always backup before large refactors
- Run tests after changes
- Review diff before committing
- Use git branches for experimental refactors
- Test in staging environment before production
