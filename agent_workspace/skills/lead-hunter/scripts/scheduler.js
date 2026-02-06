// Combined scheduler for Lead Hunter + Inbox Monitor
// Runs both tasks on different schedules

const { runLeadHunter } = require('./run-lead-hunter');
const { checkInbox } = require('./monitor-inbox');

const LEAD_HUNT_INTERVAL = 4 * 60 * 60 * 1000; // 4 hours
const INBOX_CHECK_INTERVAL = 5 * 60 * 1000;     // 5 minutes

console.log('🚀 Lead Hunter + Inbox Monitor Starting');
console.log(`📅 Lead hunting every ${LEAD_HUNT_INTERVAL / 1000 / 60 / 60} hours`);
console.log(`📬 Inbox check every ${INBOX_CHECK_INTERVAL / 1000 / 60} minutes`);
console.log('');

// Track intervals for cleanup
let leadHunterInterval;
let inboxMonitorInterval;

// Run lead hunter
async function doLeadHunt() {
  console.log(`\n[${new Date().toISOString()}] 🕐 Starting lead hunt...`);
  try {
    const result = await runLeadHunter();
    console.log(`[${new Date().toISOString()}] ✅ Lead hunt complete: ${result.total} total, ${result.new} new, ${result.logged} logged`);
  } catch (err) {
    console.error(`[${new Date().toISOString()}] ❌ Lead hunt error:`, err.message);
  }
}

// Run inbox check
async function doInboxCheck() {
  try {
    const result = await checkInbox();
    if (result.newEmails > 0) {
      console.log(`[${new Date().toISOString()}] 🎉 ${result.newEmails} new client replies!`);
    }
  } catch (err) {
    // Silent fail for inbox - don't spam logs
    if (!err.message.includes('ECONNRESET')) {
      console.error(`[${new Date().toISOString()}] ❌ Inbox error:`, err.message);
    }
  }
}

// Initial runs
doLeadHunt();
setTimeout(doInboxCheck, 10000); // Delay inbox check by 10s

// Schedule recurring
leadHunterInterval = setInterval(doLeadHunt, LEAD_HUNT_INTERVAL);
inboxMonitorInterval = setInterval(doInboxCheck, INBOX_CHECK_INTERVAL);

// Keep alive message
setInterval(() => {
  console.log(`[${new Date().toISOString()}] 💓 Still running...`);
}, 30 * 60 * 1000); // Every 30 minutes

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n⏹️ Shutting down...');
  clearInterval(leadHunterInterval);
  clearInterval(inboxMonitorInterval);
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n⏹️ Received SIGTERM, shutting down...');
  clearInterval(leadHunterInterval);
  clearInterval(inboxMonitorInterval);
  process.exit(0);
});

console.log('');
console.log('📋 Schedule:');
console.log('   • Lead Hunt: Every 4 hours');
console.log('   • Inbox Check: Every 5 minutes');
console.log('   • Telegram notifications on new client replies');
console.log('');
console.log('   Press Ctrl+C to stop');
