# Meeting Mode Feature

## Triggering Meeting Mode
When CTO (@codemurf_one_bot) includes the keyword "meeting" in any message:

### For Workers (@codemurf_agent_two_bot):
1. **PAUSE ALL WORK** immediately
2. **STOP** current task execution
3. **RESPOND** to meeting questions
4. **WAIT** for "meeting complete" from CTO
5. **RESUME** previous work

### Meeting Protocol:
- **Response Time**: Immediately (within 1 minute)
- **Focus**: Answer all meeting questions thoroughly
- **Duration**: Until CTO says "meeting complete"
- **Priority**: Meeting > ALL tasks

### Meeting Response Format:
```
MEETING RESPONSE: [meeting topic]

1. [Answer to question 1]
2. [Answer to question 2]
3. [Answer to question 3]

Additional context: [any relevant information]

Awaiting further instructions.
```

### CTO Meeting Commands:
- "meeting" - Trigger meeting mode
- "meeting complete" - End meeting mode, resume work
- "urgent meeting" - Highest priority, drop everything

## Examples:

**CTO**: "We need to have a meeting about the landing page"
**Worker**: [Pauses work, responds to meeting questions]

**CTO**: "meeting complete" 
**Worker**: [Resumes previous tasks]

## Why This Matters:
- Owner directive: CTO meetings are top priority
- Quick coordination prevents delays
- Ensures team alignment on critical decisions