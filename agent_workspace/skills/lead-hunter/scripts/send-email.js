// Email sender with rate limiting
const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');
const SENT_LOG_PATH = path.join(__dirname, '..', 'data', 'sent-emails.json');

// Load sent emails log
function loadSentLog() {
  if (!fs.existsSync(SENT_LOG_PATH)) {
    return { emails: [], dailyCount: {}, lastReset: new Date().toISOString().split('T')[0] };
  }
  return JSON.parse(fs.readFileSync(SENT_LOG_PATH, 'utf8'));
}

// Save sent emails log
function saveSentLog(log) {
  const dir = path.dirname(SENT_LOG_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(SENT_LOG_PATH, JSON.stringify(log, null, 2));
}

// Check if we can send more emails today
function canSendToday(config) {
  const log = loadSentLog();
  const today = new Date().toISOString().split('T')[0];
  
  // Reset counter if new day
  if (log.lastReset !== today) {
    log.dailyCount = {};
    log.lastReset = today;
    saveSentLog(log);
  }
  
  const todayCount = log.dailyCount[today] || 0;
  const limit = config.email?.dailyLimit || 10;
  
  return todayCount < limit;
}

// Get remaining emails for today
function getRemainingToday(config) {
  const log = loadSentLog();
  const today = new Date().toISOString().split('T')[0];
  const todayCount = log.dailyCount[today] || 0;
  const limit = config.email?.dailyLimit || 10;
  return Math.max(0, limit - todayCount);
}

// Check if already emailed this lead
function alreadyEmailed(leadId) {
  const log = loadSentLog();
  return log.emails.some(e => e.leadId === leadId);
}

// Create transporter
function createTransporter(config) {
  return nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: config.email.from,
      pass: config.email.gmailAppPassword
    }
  });
}

// Send email with rate limiting
async function sendEmail(lead, config) {
  console.log(`📧 Preparing to send email for: ${lead.title}`);
  
  // Validate config
  if (!config.email?.enabled) {
    console.log('❌ Email sending is disabled in config');
    return { success: false, reason: 'disabled' };
  }
  
  if (!config.email?.from || !config.email?.gmailAppPassword) {
    console.log('❌ Email credentials not configured');
    return { success: false, reason: 'no_credentials' };
  }
  
  // Check rate limit
  if (!canSendToday(config)) {
    console.log('⏳ Daily limit reached, queuing for tomorrow');
    return { success: false, reason: 'rate_limited' };
  }
  
  // Check if already emailed
  if (alreadyEmailed(lead.id)) {
    console.log('⏭️ Already emailed this lead');
    return { success: false, reason: 'already_sent' };
  }
  
  // Validate lead has contact info
  if (!lead.contactEmail && !lead.applyUrl) {
    console.log('❌ No contact email found for this lead');
    return { success: false, reason: 'no_email' };
  }
  
  const toEmail = lead.contactEmail || extractEmailFromUrl(lead.applyUrl);
  if (!toEmail) {
    console.log('❌ Could not extract email address');
    return { success: false, reason: 'no_email' };
  }
  
  // Prepare email
  const subject = `Re: ${lead.title} - Experienced Developer Available`;
  const body = lead.proposal || generateDefaultProposal(lead);
  
  try {
    const transporter = createTransporter(config);
    
    await transporter.sendMail({
      from: `"CodeMurf AI" <${config.email.from}>`,
      to: toEmail,
      subject: subject,
      text: body,
      html: body.replace(/\n/g, '<br>')
    });
    
    console.log(`✅ Email sent to: ${toEmail}`);
    
    // Log the sent email
    const log = loadSentLog();
    const today = new Date().toISOString().split('T')[0];
    
    log.emails.push({
      leadId: lead.id,
      to: toEmail,
      subject: subject,
      sentAt: new Date().toISOString(),
      source: lead.source
    });
    
    log.dailyCount[today] = (log.dailyCount[today] || 0) + 1;
    saveSentLog(log);
    
    return { success: true, to: toEmail };
    
  } catch (err) {
    console.error(`❌ Failed to send email: ${err.message}`);
    return { success: false, reason: 'send_error', error: err.message };
  }
}

// Extract email from URL (basic)
function extractEmailFromUrl(url) {
  if (!url) return null;
  // Look for mailto: links
  const match = url.match(/mailto:([^\?]+)/);
  return match ? match[1] : null;
}

// Default proposal template
function generateDefaultProposal(lead) {
  return `Hi there,

I noticed your ${lead.title} opening and wanted to reach out.

I'm CodeMurf, an AI-powered development team offering full-stack development services. I specialize in:
- React, Next.js, TypeScript
- Node.js, Python backends
- AI/ML integrations
- Rapid prototyping & MVPs

I'd love to discuss how I can help with your project. Check out my portfolio: https://codemurf-landing.vercel.app

Best regards,
CodeMurf AI
support@codemurf.com`;
}

// Process email queue
async function processEmailQueue(leads, config) {
  console.log(`\n📬 Processing email queue (${leads.length} leads)...`);
  
  const remaining = getRemainingToday(config);
  console.log(`📊 Remaining emails today: ${remaining}`);
  
  if (remaining === 0) {
    console.log('⏳ Daily limit reached. Try again tomorrow.');
    return { sent: 0, queued: leads.length };
  }
  
  let sent = 0;
  const toProcess = leads.slice(0, remaining);
  
  for (const lead of toProcess) {
    const result = await sendEmail(lead, config);
    if (result.success) sent++;
    
    // Small delay between emails (non-blocking but rate-limited)
    await new Promise(r => setTimeout(r, 2000));
  }
  
  console.log(`\n📊 Email Summary: Sent ${sent}/${toProcess.length}`);
  
  return { sent, queued: leads.length - toProcess.length };
}

module.exports = { sendEmail, processEmailQueue, canSendToday, getRemainingToday, alreadyEmailed };

// Run if called directly
if (require.main === module) {
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  console.log('📧 Email Sender Status:');
  console.log(`   Enabled: ${config.email?.enabled || false}`);
  console.log(`   Remaining today: ${getRemainingToday(config)}`);
}
