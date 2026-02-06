#!/bin/bash
# Lead Hunter Cron Job
# Runs automatically every 4 hours

echo "🕐 [$(date)] Starting Lead Hunter cron job..."

cd /workspace/skills/lead-hunter

# Run the lead hunter
node scripts/run-lead-hunter.js >> /workspace/logs/lead-hunter.log 2>&1

echo "✅ [$(date)] Lead Hunter cron job complete"
