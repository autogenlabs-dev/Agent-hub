// Auto-Reply Draft Generator
// Generates professional follow-up drafts when clients reply

const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');
const DRAFTS_PATH = path.join(__dirname, '..', 'data', 'reply-drafts.json');

// Analyze client reply to determine intent
function analyzeClientReply(subject, body) {
  const text = (subject + ' ' + body).toLowerCase();
  
  const intents = {
    interested: {
      keywords: ['interested', 'tell me more', 'would like to', 'sounds good', 'let\'s talk', 'schedule', 'call', 'available', 'discuss'],
      priority: 1
    },
    askingPrice: {
      keywords: ['rate', 'pricing', 'cost', 'budget', 'quote', 'how much', 'charge', 'fee', 'hourly', 'project cost'],
      priority: 2
    },
    askingPortfolio: {
      keywords: ['portfolio', 'examples', 'previous work', 'case study', 'samples', 'experience', 'background', 'projects'],
      priority: 3
    },
    askingAvailability: {
      keywords: ['available', 'start', 'timeline', 'when can', 'how soon', 'capacity', 'bandwidth'],
      priority: 4
    },
    askingTech: {
      keywords: ['do you know', 'experience with', 'familiar with', 'worked with', 'tech stack', 'skills'],
      priority: 5
    },
    general: {
      keywords: [],
      priority: 99
    }
  };
  
  // Find matching intent
  for (const [intent, config] of Object.entries(intents).sort((a, b) => a[1].priority - b[1].priority)) {
    if (config.keywords.some(kw => text.includes(kw))) {
      return intent;
    }
  }
  
  return 'general';
}

// Generate appropriate follow-up draft
function generateReplyDraft(clientEmail, intent) {
  const drafts = {
    interested: {
      subject: `Re: ${clientEmail.subject}`,
      body: `Hi,

Thanks for getting back! We're excited to connect.

To put together a solid proposal for you, could you share:

1. What's the main problem you're trying to solve?
2. Do you have a rough timeline or deadline?
3. Any budget range you're working within?

Also, what's the best way to reach your team for a quick chat?
→ Phone/WhatsApp: _______________
→ Or happy to do a Zoom/Google Meet

We typically like to do a 15-min discovery call to make sure we fully understand your needs before proposing anything.

What time works this week?

Best,
CodeMurf
codemurf.com
📞 Available for calls: +91 XXXX (WhatsApp preferred)`
    },
    
    askingPrice: {
      subject: `Re: ${clientEmail.subject}`,
      body: `Hi,

Great question! Here's how we typically work:

**Project-based (most common):**
• Small project (1-2 weeks): $2,000 - $5,000
• Medium project (3-4 weeks): $5,000 - $12,000
• Large project (6+ weeks): Custom quote

**Hourly (for ongoing work):**
• $75-100/hour depending on complexity

These ranges flex based on scope, urgency, and complexity.

To give you an accurate quote, could you share:
1. A brief project description (2-3 sentences is fine)
2. Any deadline or timeline?
3. Best contact for a quick call: _______________

Happy to hop on a 15-min call to understand your needs and give you an exact number.

Best,
CodeMurf
📧 support@codemurf.com | 📞 WhatsApp available`
    },
    
    askingPortfolio: {
      subject: `Re: ${clientEmail.subject}`,
      body: `Hi,

Happy to share more about our work!

**Recent Projects:**
• AI-powered customer support platform (Python, OpenAI, React)
• Enterprise SaaS dashboard (.NET, Angular, Azure)
• MVP launch for YC-backed startup (Next.js, Node, Postgres)

**Portfolio:** codemurf.com

We focus on:
→ Full-stack web applications
→ API design and integrations
→ AI/ML implementations
→ Performance optimization

To share more relevant examples, tell us:
1. What are you building?
2. What's your timeline?
3. Best way to reach you (phone/WhatsApp): _______________

Happy to share case studies that match your project type on a quick call.

Best,
CodeMurf Team
📞 WhatsApp/Call available for quick discussion`
    },
    
    askingAvailability: {
      subject: `Re: ${clientEmail.subject}`,
      body: `Hi,

Good timing! We have availability starting next week.

**Current capacity:**
• Can take on a new project immediately
• Typically work with dedicated team allocation
• Timezone: Global coverage (IST/US/EU overlap)

For most projects, we can kick off within 2-3 days.

Quick questions to plan the engagement:
1. Target start date?
2. Approximate project duration?
3. Your phone/WhatsApp for a quick sync: _______________

Let's book a 15-min call to align on timeline and next steps.

Best,
CodeMurf
codemurf.com | Available for calls`
    },
    
    askingTech: {
      subject: `Re: ${clientEmail.subject}`,
      body: `Hi,

Here's our core tech stack:

**Frontend:** React, Next.js, Angular, TypeScript, Tailwind
**Backend:** Node.js, Python, .NET/C#, FastAPI, NestJS
**Databases:** PostgreSQL, MongoDB, Redis, Supabase
**Cloud/DevOps:** AWS, Vercel, Docker, CI/CD
**AI/ML:** OpenAI API, LangChain, vector DBs, LLM integrations

Is there a specific technology you're evaluating us for?

To share relevant experience, tell us:
1. What's your project about?
2. What tech decisions are you making?
3. Best contact for a quick chat: _______________

We can share specific code samples or case studies that match your needs.

Best,
CodeMurf Team
📞 Happy to do a quick tech deep-dive call`
    },
    
    general: {
      subject: `Re: ${clientEmail.subject}`,
      body: `Hi,

Thanks for reaching out!

We'd love to learn more about what you're working on.

Quick questions:
1. What problem are you trying to solve?
2. Any timeline or budget constraints?
3. What's the best way to reach you?
   → Phone/WhatsApp: _______________
   → Email works too, but calls are faster!

We find a quick 15-min discovery call helps us understand your needs much better than back-and-forth emails.

Looking forward to connecting!

Best,
CodeMurf Team
codemurf.com`
    }
  };
  
  return drafts[intent] || drafts.general;
}

// Save draft for review
function saveDraft(clientEmail, draft, intent) {
  let drafts = [];
  if (fs.existsSync(DRAFTS_PATH)) {
    drafts = JSON.parse(fs.readFileSync(DRAFTS_PATH, 'utf8'));
  }
  
  drafts.push({
    id: Date.now(),
    timestamp: new Date().toISOString(),
    clientEmail: {
      from: clientEmail.from,
      subject: clientEmail.subject,
      preview: clientEmail.body?.slice(0, 200) || ''
    },
    intent,
    draft,
    status: 'pending_review'
  });
  
  // Keep last 50 drafts
  drafts = drafts.slice(-50);
  
  const dir = path.dirname(DRAFTS_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(DRAFTS_PATH, JSON.stringify(drafts, null, 2));
  
  return drafts[drafts.length - 1];
}

// Send Telegram notification with draft preview
async function notifyWithDraft(clientEmail, draft, intent, config) {
  const message = `🎯 *CLIENT REPLY + DRAFT READY*

📧 *From:* ${clientEmail.from}
📋 *Subject:* ${clientEmail.subject}

💬 *Their Message:*
${(clientEmail.body || '').slice(0, 300)}${(clientEmail.body || '').length > 300 ? '...' : ''}

---

🤖 *Detected Intent:* ${intent}

📝 *Suggested Reply:*
\`\`\`
${draft.body.slice(0, 400)}${draft.body.length > 400 ? '...' : ''}
\`\`\`

---
📱 Review & send from: codemurfagent@gmail.com`;

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
        'Content-Length': Buffer.byteLength(data)
      }
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        resolve(res.statusCode === 200);
      });
    });
    
    req.on('error', () => resolve(false));
    req.write(data);
    req.end();
  });
}

// Main function - process client reply and generate draft
async function processClientReply(clientEmail) {
  console.log(`📝 Processing reply from: ${clientEmail.from}`);
  
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  
  // Analyze intent
  const intent = analyzeClientReply(clientEmail.subject, clientEmail.body);
  console.log(`   Detected intent: ${intent}`);
  
  // Generate draft
  const draft = generateReplyDraft(clientEmail, intent);
  console.log(`   Draft generated`);
  
  // Save draft
  const saved = saveDraft(clientEmail, draft, intent);
  console.log(`   Draft saved (ID: ${saved.id})`);
  
  // Notify via Telegram
  if (config.telegram?.enabled) {
    await notifyWithDraft(clientEmail, draft, intent, config);
    console.log(`   Telegram notification sent`);
  }
  
  return { intent, draft, saved };
}

// Test mode
if (require.main === module) {
  const testEmail = {
    from: 'client@example.com',
    subject: 'Re: Quick thought on your tech stack',
    body: `Hi Abhishek,

Thanks for reaching out! We're interested in discussing further.

What's your hourly rate? And do you have experience with React Native?

Looking forward to hearing from you.

Best,
John`
  };
  
  console.log('🧪 Testing Auto-Reply Draft Generator\n');
  
  processClientReply(testEmail)
    .then(result => {
      console.log('\n📋 Result:');
      console.log(`Intent: ${result.intent}`);
      console.log(`\n📝 Draft:\n${result.draft.body}`);
    })
    .catch(console.error);
}

module.exports = { processClientReply, analyzeClientReply, generateReplyDraft };
