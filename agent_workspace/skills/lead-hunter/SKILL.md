---
name: lead-hunter
description: Autonomous lead discovery, proposal drafting, and opportunity logging
---

# Lead Hunter Skill

Enables agents to autonomously discover job opportunities, draft personalized proposals,
and log everything to a review queue (Google Sheets).

## Activation Triggers

This skill activates when:
- Scheduled cron job runs (every 4-6 hours)
- User requests "find leads" or "hunt jobs"
- Morning briefing is requested

## Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Fetch Jobs     │────▶│  Filter Match   │────▶│  Generate       │
│  (HN, RemoteOK) │     │  (Skills/Budget)│     │  Proposal       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Log to Sheets  │◀────│  Rate Quality   │◀────│  Parse Details  │
│  (Review Queue) │     │  (1-5 stars)    │     │  (Budget/Tech)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Job Sources

### 1. Hacker News Jobs (Primary)
- **Script**: `scripts/fetch-hn-jobs.js`
- **API**: Firebase (no auth needed)
- **Frequency**: Every 6 hours
- **Quality**: High (tech startups)

### 2. RemoteOK (Secondary)
- **Script**: `scripts/fetch-remoteok.js`
- **API**: REST (free, no auth)
- **Frequency**: Every 4 hours
- **Quality**: Medium-High (remote dev jobs)

### 3. IndieHackers (Discovery)
- **Method**: Browser snapshot
- **Frequency**: Daily
- **Quality**: Variable (early stage startups)

## Skill Scripts

### Required Environment
```bash
# In container
cd /workspace/skills/lead-hunter
npm install
```

### Run Job Fetch
```bash
node scripts/fetch-all-jobs.js
```

### Run Proposal Generator  
```bash
node scripts/generate-proposals.js
```

### Log to Google Sheets
```bash
node scripts/sync-to-sheets.js
```

## Configuration

Edit `config.json` to customize:
```json
{
  "targetSkills": ["javascript", "typescript", "react", "node", "python"],
  "minBudget": 500,
  "maxAgeHours": 72,
  "proposalStyle": "professional_friendly",
  "sheetsId": "YOUR_GOOGLE_SHEET_ID"
}
```

## Output Format

Each lead is logged with:
| Field | Description |
|-------|-------------|
| `foundAt` | Timestamp |
| `source` | HN / RemoteOK / IndieHackers |
| `title` | Job title |
| `company` | Company name |
| `budget` | Estimated budget |
| `techStack` | Detected technologies |
| `matchScore` | 1-5 skill match rating |
| `proposal` | AI-generated draft |
| `status` | new / reviewed / applied / rejected |
| `link` | Original job URL |

## Safety Rules

✅ **ALLOWED**:
- Fetch from public APIs
- Parse RSS feeds
- Generate proposal drafts
- Log to Google Sheets
- Send summary to Telegram

❌ **FORBIDDEN**:
- Auto-submit applications
- Scrape login-protected pages
- Bypass rate limits
- Send unsolicited emails
- Create fake profiles

## Integration with Other Skills

- **claude-driver**: Generate high-quality proposals
- **memory-manager**: Learn from successful proposals
- **project-deployer**: Quick demo deployments for pitches
