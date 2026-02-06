// Fetch jobs from Hacker News "Who's Hiring" 
const fs = require('fs');
const path = require('path');

const HN_API = 'https://hacker-news.firebaseio.com/v0';
const CONFIG_PATH = path.join(__dirname, '..', 'config.json');
const OUTPUT_PATH = path.join(__dirname, '..', 'data', 'hn-jobs.json');

async function fetchHNJobs() {
  console.log('🔍 Fetching Hacker News Jobs...');
  
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  
  // Get job story IDs
  const resp = await fetch(`${HN_API}/jobstories.json`);
  const jobIds = await resp.json();
  console.log(`Found ${jobIds.length} job postings`);
  
  // Fetch job details (limit to 50 most recent)
  const jobs = [];
  const idsToFetch = jobIds.slice(0, 50);
  
  for (const id of idsToFetch) {
    try {
      const jobResp = await fetch(`${HN_API}/item/${id}.json`);
      const job = await jobResp.json();
      
      if (job && job.title) {
        // Check if job matches target skills
        const matchScore = calculateMatchScore(job.title + ' ' + (job.text || ''), config.targetSkills);
        
        jobs.push({
          id: job.id,
          source: 'hackernews',
          title: job.title,
          text: job.text || '',
          url: job.url || `https://news.ycombinator.com/item?id=${job.id}`,
          postedAt: new Date(job.time * 1000).toISOString(),
          matchScore,
          fetchedAt: new Date().toISOString()
        });
      }
    } catch (err) {
      console.error(`Error fetching job ${id}:`, err.message);
    }
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
  
  // Cap at 5
  return Math.min(score, 5);
}

// Run if called directly
if (require.main === module) {
  fetchHNJobs()
    .then(jobs => {
      console.log('\n📋 Top Jobs:');
      jobs.slice(0, 5).forEach(j => {
        console.log(`  [${j.matchScore}⭐] ${j.title.slice(0, 60)}...`);
      });
    })
    .catch(console.error);
}

module.exports = { fetchHNJobs };
