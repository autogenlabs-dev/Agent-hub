# Task Manager Guide

## Overview
The Universal Task Manager coordinates work between CTO and Worker agents.

## Location
`/workspace/codemurf-workspace/universal-task-manager.js`

## Commands

### Claim a Task
```bash
node universal-task-manager.js claim <task-id>
```
- Claims a task for the worker
- Task must be unassigned or assigned to "any"
- Sets status to "claimed"

### Update Progress
```bash
node universal-task-manager.js update <task-id> <0-100>
```
- Updates task progress (0-100%)
- Auto-updates status based on progress
- 100% = "ready_for_review"
- 1-99% = "in_progress"

### Complete a Task
```bash
node universal-task-manager.js complete <task-id>
```
- Marks task as completed
- Sets progress to 100%
- Records completion timestamp

### Add Notes
```bash
node universal-task-manager.js note <task-id> "note text"
```
- Adds questions or comments to a task
- Includes timestamp and author
- Useful for asking for clarification

### List Tasks
```bash
node universal-task-manager.js list [filter]
```
- Shows all tasks (default)
- Filters: priority, claimed, pending

### Standup Report
```bash
node universal-task-manager.js standup
```
- Generates daily progress report
- Shows all claimed tasks
- Includes revenue/client tracking

### Help
```bash
node universal-task-manager.js help
```
- Shows all available commands

## Task Status Flow:
1. `pending` → `claimed` (when claimed)
2. `claimed` → `in_progress` (when progress > 0)
3. `in_progress` → `ready_for_review` (when progress = 100)
4. `ready_for_review` → `completed` (when completed)

## Priority System:
- **Priority 4**: Mission critical (first $2k client)
- **Priority 3**: High importance
- **Priority 2**: Normal importance  
- **Priority 1**: Low importance

## Best Practices:
1. Always claim a task before starting work
2. Update progress frequently (every 25%)
3. Add notes when you have questions
4. Complete tasks when truly finished
5. Submit standup daily

## Integration:
- Works with meeting mode (pauses/resumes)
- Integrates with communication system
- Tracks progress for revenue goals
- Coordinates between agents

Remember: This is our central coordination system!