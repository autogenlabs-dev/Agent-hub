// Test email sender with NEW professional templates
const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');

// Import the proposal generator from run-lead-hunter
const { generateQuickProposal, generateSubjectLine } = (() => {
  // Inline the functions for testing
  function generateQuickProposal(job, config) {
    const text = (job.title + ' ' + (job.tags || []).join(' ') + ' ' + (job.text || '')).toLowerCase();
    const companyName = job.company || 'your team';
    
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
    
    const challenges = {
      scaling: text.includes('scale') || text.includes('scaling') || text.includes('performance') || text.includes('optimize'),
      legacy: text.includes('legacy') || text.includes('refactor') || text.includes('modernize') || text.includes('migration'),
      mvp: text.includes('mvp') || text.includes('prototype') || text.includes('startup') || text.includes('launch'),
      integration: text.includes('integrat') || text.includes('api') || text.includes('third-party'),
    };
    
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
    
    const subjectLine = generateSubjectLine(job, techs);
    
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

    return { subject: subjectLine, body: email };
  }

  function generateSubjectLine(job, techs) {
    const company = job.company || '';
    const role = job.title || 'your role';
    
    const templates = [
      `Quick thought on ${company ? company + "'s " : ''}${techs.fullstack ? 'architecture' : techs.frontend ? 'frontend' : techs.backend ? 'backend' : 'tech stack'}`,
      `${role} - idea that might help`,
      `Re: ${company || role}`,
      `Question about ${role.split(' ').slice(0, 3).join(' ')}`,
    ];
    
    if (company) {
      return templates[0];
    }
    return templates[Math.floor(Math.random() * templates.length)];
  }

  return { generateQuickProposal, generateSubjectLine };
})();

async function sendTestEmail(toEmail, scenario = 'default') {
  console.log(`📧 Sending professional test email to: ${toEmail}`);
  console.log(`📋 Scenario: ${scenario}\n`);
  
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  
  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: config.email.from,
      pass: config.email.gmailAppPassword
    }
  });
  
  // Different test scenarios
  const testJobs = {
    dotnet: {
      title: 'Senior Full Stack Developer .NET Angular',
      company: 'TechCorp',
      tags: ['.net', 'angular', 'typescript', 'azure'],
      text: 'Looking for someone to help scale our enterprise platform and optimize performance.'
    },
    startup: {
      title: 'Full Stack Developer',
      company: 'RocketStartup',
      tags: ['react', 'node', 'startup'],
      text: 'Fast-paced startup looking to launch MVP in 4 weeks. Need someone who can move fast.'
    },
    ai: {
      title: 'AI/ML Engineer',
      company: 'AILabs',
      tags: ['python', 'machine learning', 'llm', 'gpt'],
      text: 'Building next-gen AI product. Need help integrating LLMs and building scalable ML pipelines.'
    },
    legacy: {
      title: 'Backend Developer',
      company: 'EnterpriseCo',
      tags: ['python', 'django', 'postgresql'],
      text: 'Modernizing legacy codebase. Need to refactor monolith to microservices architecture.'
    },
    default: {
      title: 'Senior Full Stack Developer',
      company: 'TechCompany',
      tags: ['react', 'node', 'typescript'],
      text: 'Looking for an experienced developer to join our growing team.'
    }
  };
  
  const job = testJobs[scenario] || testJobs.default;
  const proposal = generateQuickProposal(job, config);

  console.log('━'.repeat(60));
  console.log('📬 EMAIL PREVIEW:');
  console.log('━'.repeat(60));
  console.log(`To: ${toEmail}`);
  console.log(`Subject: ${proposal.subject}`);
  console.log('━'.repeat(60));
  console.log(proposal.body);
  console.log('━'.repeat(60));

  try {
    await transporter.sendMail({
      from: `"CodeMurf Team" <${config.email.from}>`,
      to: toEmail,
      subject: proposal.subject,
      text: proposal.body,
      html: proposal.body.replace(/\n/g, '<br>').replace(/→/g, '&rarr;')
    });
    
    console.log('\n✅ Email sent successfully!');
    
  } catch (err) {
    console.error('\n❌ Failed to send:', err.message);
  }
}

// Parse command line args
const targetEmail = process.argv[2] || 'autogencodelabs@gmail.com';
const scenario = process.argv[3] || 'default';

console.log('');
console.log('🚀 CodeMurf Professional Email Test');
console.log('═'.repeat(60));
console.log('Available scenarios: dotnet, startup, ai, legacy, default');
console.log('Usage: node test-email.js <email> <scenario>');
console.log('═'.repeat(60));
console.log('');

sendTestEmail(targetEmail, scenario);
