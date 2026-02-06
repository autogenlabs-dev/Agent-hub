// Lead validator - ensures quality and prevents spam
const fs = require('fs');
const path = require('path');

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');
const CONTACTED_PATH = path.join(__dirname, '..', 'data', 'contacted-leads.json');

// Validation rules
const RULES = {
  MIN_MATCH_SCORE: 3,          // Minimum skill match
  MIN_MATCH_FOR_EMAIL: 4,      // Higher threshold for auto-email
  REQUIRED_FIELDS: ['title', 'url'],
  MAX_AGE_HOURS: 72,           // Don't contact old leads
  BLOCKED_KEYWORDS: ['intern', 'unpaid', 'equity only', 'volunteer'],
};

// Load contacted leads
function loadContactedLeads() {
  if (!fs.existsSync(CONTACTED_PATH)) {
    return new Set();
  }
  const data = JSON.parse(fs.readFileSync(CONTACTED_PATH, 'utf8'));
  return new Set(data);
}

// Save contacted lead
function markAsContacted(leadId) {
  const contacted = loadContactedLeads();
  contacted.add(leadId);
  
  const dir = path.dirname(CONTACTED_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  
  fs.writeFileSync(CONTACTED_PATH, JSON.stringify([...contacted], null, 2));
}

// Validate a single lead
function validateLead(lead, config = {}) {
  const errors = [];
  const warnings = [];
  
  // Required fields
  for (const field of RULES.REQUIRED_FIELDS) {
    if (!lead[field]) {
      errors.push(`Missing required field: ${field}`);
    }
  }
  
  // Match score check
  if (lead.matchScore < RULES.MIN_MATCH_SCORE) {
    errors.push(`Match score too low: ${lead.matchScore} < ${RULES.MIN_MATCH_SCORE}`);
  }
  
  // Email threshold (higher bar for auto-email)
  if (lead.matchScore < RULES.MIN_MATCH_FOR_EMAIL) {
    warnings.push(`Below auto-email threshold: ${lead.matchScore} < ${RULES.MIN_MATCH_FOR_EMAIL}`);
  }
  
  // Age check
  if (lead.postedAt) {
    const age = Date.now() - new Date(lead.postedAt).getTime();
    const ageHours = age / (1000 * 60 * 60);
    if (ageHours > RULES.MAX_AGE_HOURS) {
      warnings.push(`Lead is ${Math.round(ageHours)}h old (max: ${RULES.MAX_AGE_HOURS}h)`);
    }
  }
  
  // Blocked keywords
  const titleLower = (lead.title || '').toLowerCase();
  const textLower = (lead.text || '').toLowerCase();
  const combined = titleLower + ' ' + textLower;
  
  for (const keyword of RULES.BLOCKED_KEYWORDS) {
    if (combined.includes(keyword)) {
      errors.push(`Contains blocked keyword: "${keyword}"`);
    }
  }
  
  // Already contacted check
  const contacted = loadContactedLeads();
  if (contacted.has(lead.id)) {
    errors.push('Already contacted this lead');
  }
  
  return {
    valid: errors.length === 0,
    eligible_for_email: errors.length === 0 && lead.matchScore >= RULES.MIN_MATCH_FOR_EMAIL,
    errors,
    warnings
  };
}

// Validate and filter leads for email
function filterEmailableLeads(leads, config) {
  const results = {
    emailable: [],
    sheet_only: [],
    rejected: []
  };
  
  for (const lead of leads) {
    const validation = validateLead(lead, config);
    
    if (validation.eligible_for_email) {
      results.emailable.push({ ...lead, validation });
    } else if (validation.valid) {
      results.sheet_only.push({ ...lead, validation });
    } else {
      results.rejected.push({ ...lead, validation });
    }
  }
  
  console.log(`\n📋 Validation Results:`);
  console.log(`   ✅ Emailable: ${results.emailable.length}`);
  console.log(`   📊 Sheet only: ${results.sheet_only.length}`);
  console.log(`   ❌ Rejected: ${results.rejected.length}`);
  
  return results;
}

module.exports = { validateLead, filterEmailableLeads, markAsContacted, RULES };

// Test if called directly
if (require.main === module) {
  const testLead = {
    id: 'test-123',
    title: 'Senior React Developer',
    url: 'https://example.com/job',
    matchScore: 4,
    postedAt: new Date().toISOString()
  };
  
  console.log('Testing validation...');
  const result = validateLead(testLead);
  console.log(JSON.stringify(result, null, 2));
}
