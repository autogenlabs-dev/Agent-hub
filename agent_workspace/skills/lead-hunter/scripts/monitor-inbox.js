// Email Inbox Monitor - Watches ONLY for client replies
const Imap = require('imap');
const { simpleParser } = require('mailparser');
const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');
const SEEN_EMAILS_PATH = path.join(__dirname, '..', 'data', 'seen-emails.json');
const SENT_EMAILS_PATH = path.join(__dirname, '..', 'data', 'sent-emails.json');

// Domains to IGNORE (system notifications)
const IGNORE_DOMAINS = [
  'github.com',
  'google.com',
  'accounts.google.com',
  'vercel.com',
  'render.com',
  'supabase.com',
  'netlify.com',
  'railway.app',
  'stripe.com',
  'paypal.com',
  'facebook.com',
  'twitter.com',
  'linkedin.com',
  'noreply',
  'no-reply',
  'donotreply',
  'mailer-daemon',
  'postmaster',
  'notifications',
  'newsletter',
  'marketing',
  'promo',
  'support@',  // Generic support emails (not from clients)
];

// Load seen email UIDs
function loadSeenEmails() {
  if (!fs.existsSync(SEEN_EMAILS_PATH)) {
    return new Set();
  }
  return new Set(JSON.parse(fs.readFileSync(SEEN_EMAILS_PATH, 'utf8')));
}

// Save seen email UIDs
function saveSeenEmails(seen) {
  const dir = path.dirname(SEEN_EMAILS_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(SEEN_EMAILS_PATH, JSON.stringify([...seen]));
}

// Check if email is from ignored domain
function isIgnoredSender(fromEmail) {
  const emailLower = fromEmail.toLowerCase();
  return IGNORE_DOMAINS.some(domain => emailLower.includes(domain));
}

// Check if this looks like a reply to our outreach
function isLikelyClientReply(subject, fromEmail) {
  const subjectLower = (subject || '').toLowerCase();
  
  // Must have "Re:" in subject (indicates reply)
  if (!subjectLower.startsWith('re:')) {
    return false;
  }
  
  // Must NOT be from ignored domains
  if (isIgnoredSender(fromEmail)) {
    return false;
  }
  
  return true;
}

// Send Telegram notification
async function notifyTelegram(subject, from, preview, config) {
  const message = `🎯 *CLIENT REPLY RECEIVED!*

📧 *From:* ${from}
📋 *Subject:* ${subject}

💬 *Message Preview:*
${preview.slice(0, 400)}${preview.length > 400 ? '...' : ''}

---
⚡ Check inbox: codemurfagent@gmail.com
📱 Respond quickly to close the deal!`;

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
          console.log('✅ Telegram notification sent for CLIENT REPLY!');
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

// Check inbox for new CLIENT REPLIES only
async function checkInbox() {
  console.log(`[${new Date().toISOString()}] 📬 Checking for client replies...`);
  
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  const seenEmails = loadSeenEmails();
  
  const imap = new Imap({
    user: config.email.from,
    password: config.email.gmailAppPassword,
    host: 'imap.gmail.com',
    port: 993,
    tls: true,
    tlsOptions: { rejectUnauthorized: false }
  });
  
  return new Promise((resolve, reject) => {
    imap.once('ready', () => {
      imap.openBox('INBOX', false, (err, box) => {
        if (err) {
          imap.end();
          return reject(err);
        }
        
        // Search for unread emails
        imap.search(['UNSEEN'], (err, results) => {
          if (err) {
            imap.end();
            return reject(err);
          }
          
          if (!results || results.length === 0) {
            console.log('   No new emails');
            imap.end();
            return resolve({ newEmails: 0, clientReplies: 0 });
          }
          
          console.log(`   Found ${results.length} unread email(s)`);
          
          const f = imap.fetch(results, { bodies: '', markSeen: false });
          let clientReplies = 0;
          let processingPromises = [];
          
          f.on('message', (msg, seqno) => {
            const promise = new Promise((resolveMsg) => {
              msg.on('body', (stream, info) => {
                simpleParser(stream, async (err, parsed) => {
                  if (err) {
                    resolveMsg();
                    return;
                  }
                  
                  const uid = `${parsed.messageId}`;
                  
                  // Skip if already seen by our system
                  if (seenEmails.has(uid)) {
                    resolveMsg();
                    return;
                  }
                  
                  // Get sender info
                  const fromEmail = parsed.from?.value?.[0]?.address || '';
                  const fromName = parsed.from?.text || 'Unknown';
                  const subject = parsed.subject || '(No subject)';
                  
                  // Skip sent emails (from ourselves)
                  if (fromEmail === config.email.from) {
                    seenEmails.add(uid);
                    resolveMsg();
                    return;
                  }
                  
                  // Check if this is a CLIENT REPLY
                  if (isLikelyClientReply(subject, fromEmail)) {
                    console.log(`\n🎯 CLIENT REPLY DETECTED: [${uid}]`);
                    console.log(`   From: ${fromName}`);
                    console.log(`   Subject: ${subject}`);
                    
                    // Get email body
                    const emailBody = parsed.text || parsed.html?.replace(/<[^>]*>/g, '') || '(No content)';
                    
                    // Generate auto-reply draft
                    let draftInfo = null;
                    try {
                      const { processClientReply } = require('./auto-reply');
                      draftInfo = await processClientReply({
                        from: fromName,
                        subject: subject,
                        body: emailBody
                      });
                      console.log(`   📝 Draft generated (intent: ${draftInfo.intent})`);
                    } catch (e) {
                      console.log(`   ⚠️ Could not generate draft: ${e.message}`);
                      // Still notify even if draft fails
                      await notifyTelegram(subject, fromName, emailBody, config);
                    }
                    
                    clientReplies++;
                  } else {
                    // Skip but mark as seen (system email)
                    console.log(`   ⏭️ Ignored: ${fromEmail.slice(0, 30)}...`);
                  }
                  
                  // Mark as seen by our system
                  seenEmails.add(uid);
                  resolveMsg();
                });
              });
            });
            
            processingPromises.push(promise);
          });
          
          f.once('error', (err) => {
            console.error('Fetch error:', err);
          });
          
          f.once('end', async () => {
            console.log('   Fetch complete, waiting for parsing...');
            await Promise.all(processingPromises);
            console.log('   All messages processed.');
            
            saveSeenEmails(seenEmails);
            imap.end();
            resolve({ newEmails: results.length, clientReplies });
          });
        });
      });
    });
    
    imap.once('error', (err) => {
      console.error('IMAP error:', err.message);
      reject(err);
    });
    
    imap.once('end', () => {
      console.log('   Connection closed');
    });
    
    imap.connect();
  });
}

// Run once if called directly
if (require.main === module) {
  checkInbox()
    .then(result => {
      console.log(`\n✅ Check complete: ${result.newEmails} emails, ${result.clientReplies} client replies`);
    })
    .catch(err => {
      console.error('❌ Error:', err.message);
      process.exit(1);
    });
}

module.exports = { checkInbox };
