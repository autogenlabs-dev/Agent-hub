// Telegram notifier for lead updates
const https = require('https');
const fs = require('fs');
const path = require('path');

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');

// Send message to Telegram
async function sendTelegramMessage(message, config) {
  if (!config.telegram?.enabled || !config.telegram?.botToken || !config.telegram?.chatId) {
    console.log('⚠️ Telegram notifications not configured');
    return false;
  }

  // Add Revenue Goal Status
  try {
    const revenuePath = path.join(__dirname, '../data/revenue.json');
    if (fs.existsSync(revenuePath)) {
      const revenue = JSON.parse(fs.readFileSync(revenuePath, 'utf8'));
      const percent = Math.min(100, Math.round((revenue.total / revenue.goal) * 100));
      const bars = '▓'.repeat(Math.floor(percent / 10)) + '░'.repeat(10 - Math.floor(percent / 10));

      message += `\n\n🎯 **Goal Progress:** $${revenue.total} / $${revenue.goal}`;
      message += `\n${bars} ${percent}%`;
    }
  } catch (e) {
    // Ignore error if revenue file missing
  }

  const url = `https://api.telegram.org/bot${config.telegram.botToken}/sendMessage`;

  const data = JSON.stringify({
    chat_id: config.telegram.chatId,
    text: message,
    parse_mode: 'Markdown'
  });

  return new Promise((resolve) => {
    const req = https.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
      }
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log('✅ Telegram notification sent');
          resolve(true);
        } else {
          console.log(`❌ Telegram error: ${body}`);
          resolve(false);
        }
      });
    });
    
    req.on('error', (e) => {
      console.error(`❌ Telegram request failed: ${e.message}`);
      resolve(false);
    });
    
    req.write(data);
    req.end();
  });
}

// Format lead summary for Telegram
function formatLeadSummary(leads, emailStats) {
  let message = `🎯 *Lead Hunter Report*\n`;
  message += `📅 ${new Date().toISOString().split('T')[0]}\n\n`;
  
  if (leads.length === 0) {
    message += `No new leads found this run.\n`;
  } else {
    message += `📥 *${leads.length} leads found*\n\n`;
    
    // Top 3 leads
    const top = leads.slice(0, 3);
    top.forEach((lead, i) => {
      const stars = '⭐'.repeat(Math.min(lead.matchScore, 5));
      message += `${i + 1}. ${stars} *${truncate(lead.title, 40)}*\n`;
      if (lead.company) message += `   🏢 ${lead.company}\n`;
      if (lead.budget) message += `   💰 $${lead.budget.min}-${lead.budget.max}\n`;
    });
    
    if (leads.length > 3) {
      message += `\n... and ${leads.length - 3} more\n`;
    }
  }
  
  // Email stats
  if (emailStats) {
    message += `\n📧 *Emails*: ${emailStats.sent} sent, ${emailStats.queued} queued\n`;
  }
  
  message += `\n📊 [View Sheet](https://docs.google.com/spreadsheets/d/1Ql-k42m6iViRTH-H6x3I1sEk-yOJPNP0m3m9I_FbLAA)`;
  
  return message;
}

// Format single lead notification
function formatLeadNotification(lead) {
  const stars = '⭐'.repeat(Math.min(lead.matchScore, 5));
  let message = `🆕 *New High-Quality Lead!*\n\n`;
  message += `${stars}\n`;
  message += `*${lead.title}*\n`;
  if (lead.company) message += `🏢 ${lead.company}\n`;
  if (lead.budget) message += `💰 $${lead.budget.min}-${lead.budget.max}\n`;
  message += `🔗 [View Job](${lead.url})\n`;
  
  return message;
}

function truncate(str, len) {
  return str.length > len ? str.slice(0, len) + '...' : str;
}

// Notify about new leads
async function notifyNewLeads(leads, emailStats, config) {
  const message = formatLeadSummary(leads, emailStats);
  return sendTelegramMessage(message, config);
}

// Notify about single high-value lead
async function notifyHighValueLead(lead, config) {
  const message = formatLeadNotification(lead);
  return sendTelegramMessage(message, config);
}

module.exports = { sendTelegramMessage, notifyNewLeads, notifyHighValueLead };

// Test if called directly
if (require.main === module) {
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  const testLeads = [
    { title: 'Test Lead', company: 'Test Corp', matchScore: 4, url: 'https://example.com' }
  ];
  notifyNewLeads(testLeads, { sent: 1, queued: 0 }, config)
    .then(() => console.log('Test complete'));
}
