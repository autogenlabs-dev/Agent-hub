// Enhanced Lead Hunter - Full autonomous pipeline
// Find → Validate → Email → Notify → Log

const fs = require('fs');
const path = require('path');

const { fetchHNJobs } = require('./fetch-hn-jobs');
const { fetchRemoteOKJobs } = require('./fetch-remoteok');
const { logToSheets } = require('./log-to-sheets');
const { processEmailQueue, getRemainingToday } = require('./send-email');
const { notifyNewLeads } = require('./notify-telegram');
const { filterEmailableLeads, markAsContacted } = require('./validate-lead');

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');
const SEEN_PATH = path.join(__dirname, '..', 'data', 'seen-jobs.json');

async function runLeadHunter() {
  console.log('🚀 Starting Enhanced Lead Hunter...');
  console.log('📅', new Date().toISOString());
  console.log('═'.repeat(50));
  
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  
  // Load previously seen job IDs
  let seenJobs = new Set();
  if (fs.existsSync(SEEN_PATH)) {
    const seen = JSON.parse(fs.readFileSync(SEEN_PATH, 'utf8'));
    seenJobs = new Set(seen);
  }
  
  let allJobs = [];
  
  // ═══════════════════════════════════════════════
  // PHASE 1: FETCH JOBS
  // ═══════════════════════════════════════════════
  console.log('\n📥 PHASE 1: Fetching Jobs...');
  
  if (config.sources.hackerNews.enabled) {
    try {
      const hnJobs = await fetchHNJobs();
      allJobs.push(...hnJobs);
    } catch (err) {
      console.error('❌ HN fetch error:', err.message);
    }
  }
  
  if (config.sources.remoteOK.enabled) {
    try {
      const rokJobs = await fetchRemoteOKJobs();
      allJobs.push(...rokJobs);
    } catch (err) {
      console.error('❌ RemoteOK fetch error:', err.message);
    }
  }
  
  console.log(`📊 Total fetched: ${allJobs.length} jobs`);
  
  // Filter out already seen jobs
  const newJobs = allJobs.filter(job => {
    const jobKey = `${job.source}:${job.id}`;
    return !seenJobs.has(jobKey);
  });
  
  console.log(`🆕 New jobs: ${newJobs.length}`);
  
  if (newJobs.length === 0) {
    console.log('✅ No new jobs. Exiting.');
    return { total: allJobs.length, new: 0, logged: 0, emailed: 0 };
  }
  
  // Sort by match score
  newJobs.sort((a, b) => b.matchScore - a.matchScore);
  
  // ═══════════════════════════════════════════════
  // PHASE 2: VALIDATE & CATEGORIZE
  // ═══════════════════════════════════════════════
  console.log('\n🔍 PHASE 2: Validating Leads...');
  
  const { emailable, sheet_only, rejected } = filterEmailableLeads(newJobs, config);
  
  // Generate proposals for quality leads
  const topJobs = [...emailable, ...sheet_only].slice(0, 15);
  for (const job of topJobs) {
    job.proposal = generateQuickProposal(job, config);
  }
  
  // ═══════════════════════════════════════════════
  // PHASE 3: LOG TO SHEETS
  // ═══════════════════════════════════════════════
  console.log('\n📊 PHASE 3: Logging to Sheets...');
  
  try {
    await logToSheets(topJobs);
    console.log(`✅ Logged ${topJobs.length} leads`);
  } catch (err) {
    console.error('❌ Sheets error:', err.message);
  }
  
  // ═══════════════════════════════════════════════
  // PHASE 4: SEND EMAILS (if enabled)
  // ═══════════════════════════════════════════════
  let emailStats = { sent: 0, queued: 0 };
  
  if (config.email?.enabled && emailable.length > 0) {
    console.log('\n📧 PHASE 4: Sending Emails...');
    console.log(`   Remaining today: ${getRemainingToday(config)}`);
    
    try {
      emailStats = await processEmailQueue(emailable, config);
      
      // Mark sent as contacted
      for (const lead of emailable.slice(0, emailStats.sent)) {
        markAsContacted(lead.id);
      }
    } catch (err) {
      console.error('❌ Email error:', err.message);
    }
  } else if (!config.email?.enabled) {
    console.log('\n📧 PHASE 4: Email disabled, skipping...');
  }
  
  // ═══════════════════════════════════════════════
  // PHASE 5: TELEGRAM NOTIFICATION
  // ═══════════════════════════════════════════════
  if (config.telegram?.enabled && topJobs.length > 0) {
    console.log('\n📱 PHASE 5: Sending Telegram Notification...');
    
    try {
      await notifyNewLeads(topJobs, emailStats, config);
    } catch (err) {
      console.error('❌ Telegram error:', err.message);
    }
  }
  
  // ═══════════════════════════════════════════════
  // PHASE 6: MARK AS SEEN
  // ═══════════════════════════════════════════════
  for (const job of newJobs) {
    seenJobs.add(`${job.source}:${job.id}`);
  }
  
  const dataDir = path.dirname(SEEN_PATH);
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  fs.writeFileSync(SEEN_PATH, JSON.stringify([...seenJobs]));
  
  // ═══════════════════════════════════════════════
  // SUMMARY
  // ═══════════════════════════════════════════════
  console.log('\n' + '═'.repeat(50));
  console.log('🏁 LEAD HUNTER COMPLETE!');
  console.log(`   📥 Total: ${allJobs.length}`);
  console.log(`   🆕 New: ${newJobs.length}`);
  console.log(`   📊 Logged: ${topJobs.length}`);
  console.log(`   📧 Emailed: ${emailStats.sent}`);
  console.log(`   ⏳ Queued: ${emailStats.queued}`);
  
  if (topJobs.length > 0) {
    console.log('\n📋 Top Opportunities:');
    topJobs.slice(0, 3).forEach((j, i) => {
      console.log(`   ${i + 1}. [${j.matchScore}⭐] ${j.title.slice(0, 50)}`);
    });
  }
  
  return {
    total: allJobs.length,
    new: newJobs.length,
    logged: topJobs.length,
    emailed: emailStats.sent
  };
}

function generateQuickProposal(job, config) {
  const text = (job.title + ' ' + (job.tags || []).join(' ') + ' ' + (job.text || '')).toLowerCase();
  const companyName = job.company || 'your team';
  
  // Detect specific technologies mentioned
  const techs = {
    dotnet: text.includes('.net') || text.includes('c#') || text.includes('asp.net'),
    angular: text.includes('angular'),
    react: text.includes('react') || text.includes('next.js') || text.includes('nextjs'),
    vue: text.includes('vue'),
    python: text.includes('python') || text.includes('django') || text.includes('flask') || text.includes('fastapi'),
    node: text.includes('node') || text.includes('express') || text.includes('nestjs'),
    ai: text.includes(' ai ') || text.includes('ai/') || text.includes('ml') || text.includes('machine learning') || text.includes('llm') || text.includes('gpt'),
    mobile: text.includes('ios') || text.includes('android') || text.includes('react native') || text.includes('flutter'),
    devops: text.includes('devops') || text.includes('kubernetes') || text.includes('docker') || text.includes('aws') || text.includes('cloud'),
    frontend: text.includes('frontend') || text.includes('front-end') || text.includes('ui') || text.includes('ux'),
    backend: text.includes('backend') || text.includes('back-end') || text.includes('api') || text.includes('database'),
    fullstack: text.includes('fullstack') || text.includes('full-stack') || text.includes('full stack'),
  };
  
  // Detect common challenges from job description
  const challenges = {
    scaling: text.includes('scale') || text.includes('scaling') || text.includes('performance') || text.includes('optimize'),
    legacy: text.includes('legacy') || text.includes('refactor') || text.includes('modernize') || text.includes('migration'),
    mvp: text.includes('mvp') || text.includes('prototype') || text.includes('startup') || text.includes('launch'),
    integration: text.includes('integrat') || text.includes('api') || text.includes('third-party'),
  };
  
  // Build primary tech stack
  let primaryTech = [];
  if (techs.dotnet) primaryTech.push('.NET', 'C#');
  if (techs.angular) primaryTech.push('Angular');
  if (techs.react) primaryTech.push('React', 'Next.js');
  if (techs.vue) primaryTech.push('Vue.js');
  if (techs.python) primaryTech.push('Python');
  if (techs.node) primaryTech.push('Node.js');
  if (techs.ai) primaryTech.push('AI/ML');
  if (techs.mobile) primaryTech.push('Mobile');
  if (techs.devops) primaryTech.push('DevOps', 'AWS');
  
  // Default fallback
  if (primaryTech.length === 0) {
    if (techs.frontend) primaryTech = ['React', 'TypeScript', 'UI/UX'];
    else if (techs.backend) primaryTech = ['Node.js', 'Python', 'APIs'];
    else primaryTech = ['Full-Stack', 'Modern Web'];
  }
  
  const techString = primaryTech.slice(0, 3).join(' + ');
  
  // Generate challenge-specific hook (adapted for team)
  let challengeHook = '';
  let proofPoint = '';
  
  if (challenges.scaling) {
    challengeHook = 'scaling to handle increased load while maintaining performance';
    proofPoint = 'reduced API response times by 60% for a high-traffic SaaS platform';
  } else if (challenges.legacy) {
    challengeHook = 'modernizing the codebase without disrupting existing functionality';
    proofPoint = 'migrated a 5-year-old monolith to microservices with zero downtime';
  } else if (challenges.mvp) {
    challengeHook = 'moving fast from concept to production-ready product';
    proofPoint = 'shipped an MVP in 3 weeks that closed their first paying customers';
  } else if (challenges.integration) {
    challengeHook = 'integrating multiple systems while keeping things clean';
    proofPoint = 'built seamless integrations with Stripe, Salesforce, and custom APIs';
  } else {
    challengeHook = 'building reliable, maintainable software that scales';
    proofPoint = 'delivered 15+ production projects with repeat clients';
  }
  
  // Generate subject line (returned separately for email sending)
  const subjectLine = generateSubjectLine(job, techs);
  
  // Problem-Solution Framework Email (Team Version)
  const email = `Hi,

We came across ${companyName}'s ${job.title} role and noticed you're looking for help with ${challengeHook}.

We recently ${proofPoint}.

What made it work: our deep ${techString} expertise combined with a focus on shipping clean, tested code fast.

A few things we bring:
→ Full project ownership (architecture, testing, deployment)
→ Clear, async-friendly communication
→ Proven track record: codemurf.com

Would it make sense to hop on a 15-minute call this week to discuss the role?

Best,
CodeMurf
support@codemurf.com`;

  return {
    subject: subjectLine,
    body: email
  };
}

// Generate curiosity-driven subject lines (32% higher open rate)
function generateSubjectLine(job, techs) {
  const company = job.company || '';
  const role = job.title || 'your role';
  
  // Question-based subjects work best
  const templates = [
    `Quick thought on ${company ? company + "'s " : ''}${techs.fullstack ? 'architecture' : techs.frontend ? 'frontend' : techs.backend ? 'backend' : 'tech stack'}`,
    `${role} - idea that might help`,
    `Re: ${company || role}`,
    `Question about ${role.split(' ').slice(0, 3).join(' ')}`,
  ];
  
  // Pick based on available info
  if (company) {
    return templates[0];
  }
  return templates[Math.floor(Math.random() * templates.length)];
}

// Run if called directly
if (require.main === module) {
  runLeadHunter()
    .then(result => {
      console.log('\n📈 Final Report:', JSON.stringify(result));
    })
    .catch(err => {
      console.error('💥 Fatal error:', err);
      process.exit(1);
    });
}

module.exports = { runLeadHunter };
