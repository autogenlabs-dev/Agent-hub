const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '../data');
const REVENUE_FILE = path.join(DATA_DIR, 'revenue.json');

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

// Initialize file if not exists
if (!fs.existsSync(REVENUE_FILE)) {
  fs.writeFileSync(REVENUE_FILE, JSON.stringify({
    total: 0,
    goal: 2000,
    history: []
  }, null, 2));
}

const amount = parseFloat(process.argv[2]);
const description = process.argv[3] || 'Manual Entry';

if (isNaN(amount)) {
  console.log('❌ Error: Please provide a valid amount.');
  console.log('Usage: node log-revenue.js <amount> [description]');
  console.log('Example: node log-revenue.js 500 "Project Alpha Deposit"');
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(REVENUE_FILE, 'utf8'));

data.total += amount;
data.history.push({
  date: new Date().toISOString(),
  amount: amount,
  description: description
});

fs.writeFileSync(REVENUE_FILE, JSON.stringify(data, null, 2));

console.log('✅ Revenue Logged!');
console.log(`💰 New Total: $${data.total} / $${data.goal}`);

if (data.total >= data.goal) {
  console.log('🎉 GOAL REACHED! Amazing work!');
}
