// Fetch jobs from RemoteOK API
const fs = require('fs');
const path = require('path');

const REMOTEOK_API = 'https://remoteok.com/api';
const CONFIG_PATH = path.join(__dirname, '..', 'config.json');
const OUTPUT_PATH = path.join(__dirname, '..', 'data', 'remoteok-jobs.json');

async function fetchRemoteOKJobs() {
  console.log('🔍 Fetching RemoteOK Jobs...');
  
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  
  // RemoteOK requires proper User-Agent
  const resp = await fetch(REMOTEOK_API, {
    headers: {
      'User-Agent': 'CodeMurf-LeadHunter/1.0'
    }
  });
  
  const data = await resp.json();
  
  // First item is metadata, rest are jobs
  const rawJobs = data.slice(1);
  console.log(`Found ${rawJobs.length} job postings`);
  
  const jobs = [];
  const maxAge = config.maxAgeHours * 60 * 60 * 1000;
  const now = Date.now();
  
  for (const job of rawJobs) {
    // Filter by age
    const postedAt = new Date(job.date).getTime();
    if (now - postedAt > maxAge) continue;
    
    // Build searchable text
    const searchText = [
      job.position,
      job.company,
      job.description,
      ...(job.tags || [])
    ].join(' ');
    
    const matchScore = calculateMatchScore(searchText, config.targetSkills);
    
    // Parse salary if available
    let budget = null;
    if (job.salary_min && job.salary_max) {
      budget = {
        min: job.salary_min,
        max: job.salary_max,
        currency: 'USD'
      };
    }
    
    jobs.push({
      id: job.id,
      source: 'remoteok',
      title: job.position,
      company: job.company,
      companyLogo: job.company_logo,
      location: job.location || 'Remote',
      tags: job.tags || [],
      budget,
      url: job.url,
      applyUrl: job.apply_url,
      postedAt: job.date,
      matchScore,
      fetchedAt: new Date().toISOString()
    });
  }
  
  // Filter by match score
  const relevantJobs = jobs.filter(j => j.matchScore >= 2);
  console.log(`✅ Found ${relevantJobs.length} relevant jobs (score >= 2)`);
  
  // Ensure data directory exists
  const dataDir = path.dirname(OUTPUT_PATH);
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  // Save to file
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(relevantJobs, null, 2));
  console.log(`💾 Saved to ${OUTPUT_PATH}`);
  
  return relevantJobs;
}

function calculateMatchScore(text, targetSkills) {
  const lowerText = text.toLowerCase();
  let score = 0;
  
  for (const skill of targetSkills) {
    if (lowerText.includes(skill.toLowerCase())) {
      score++;
    }
  }
  
  return Math.min(score, 5);
}

// Run if called directly
if (require.main === module) {
  fetchRemoteOKJobs()
    .then(jobs => {
      console.log('\n📋 Top Jobs:');
      jobs.slice(0, 5).forEach(j => {
        console.log(`  [${j.matchScore}⭐] ${j.company}: ${j.title}`);
        if (j.budget) {
          console.log(`      💰 $${j.budget.min} - $${j.budget.max}`);
        }
      });
    })
    .catch(console.error);
}

module.exports = { fetchRemoteOKJobs };
