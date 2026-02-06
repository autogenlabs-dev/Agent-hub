// Log leads to Google Sheets
const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');
const SERVICE_ACCOUNT_PATH = '/workspace/credentials/service_account.json';

async function logToSheets(leads) {
  console.log('📊 Logging to Google Sheets...');
  
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  const SHEET_ID = config.sheetsId;
  
  if (!SHEET_ID) {
    throw new Error('No sheetsId configured in config.json');
  }
  
  const auth = new google.auth.GoogleAuth({
    keyFile: SERVICE_ACCOUNT_PATH,
    scopes: ['https://www.googleapis.com/auth/spreadsheets']
  });
  
  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });
  
  // Prepare rows
  const rows = leads.map(lead => [
    lead.fetchedAt || new Date().toISOString(),
    lead.source,
    lead.title,
    lead.company || 'N/A',
    lead.budget ? `$${lead.budget.min}-${lead.budget.max}` : 'N/A',
    lead.matchScore,
    'new', // status
    lead.proposal || '',
    lead.url
  ]);
  
  // Add header if sheet is empty
  const headerRow = [
    'Found At', 'Source', 'Title', 'Company', 'Budget', 
    'Match Score', 'Status', 'Proposal Draft', 'Link'
  ];
  
  // Check if header exists
  const existing = await sheets.spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range: 'Sheet1!A1:I1'
  });
  
  if (!existing.data.values || existing.data.values.length === 0) {
    // Add header first
    await sheets.spreadsheets.values.update({
      spreadsheetId: SHEET_ID,
      range: 'Sheet1!A1:I1',
      valueInputOption: 'RAW',
      requestBody: { values: [headerRow] }
    });
    console.log('✅ Added header row');
  }
  
  // Append lead rows
  if (rows.length > 0) {
    await sheets.spreadsheets.values.append({
      spreadsheetId: SHEET_ID,
      range: 'Sheet1!A:I',
      valueInputOption: 'RAW',
      insertDataOption: 'INSERT_ROWS',
      requestBody: { values: rows }
    });
    console.log(`✅ Logged ${rows.length} leads to sheet`);
  }
  
  return rows.length;
}

// Run if called directly
if (require.main === module) {
  // Test with sample data
  const sampleLeads = [
    {
      source: 'test',
      title: 'Test Lead',
      company: 'Test Corp',
      budget: { min: 1000, max: 5000 },
      matchScore: 3,
      url: 'https://example.com',
      fetchedAt: new Date().toISOString()
    }
  ];
  
  logToSheets(sampleLeads)
    .then(() => console.log('Done!'))
    .catch(console.error);
}

module.exports = { logToSheets };
