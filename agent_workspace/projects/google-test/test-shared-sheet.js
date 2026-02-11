// Test writing to a shared Google Sheet
const { google } = require('googleapis');
const fs = require('fs');

const SERVICE_ACCOUNT_PATH = '/workspace/credentials/service_account.json';
const SHEET_ID = '1Ql-k42m6iViRTH-H6x3I1sEk-yOJPNP0m3m9I_FbLAA';

async function main() {
  console.log('📊 Testing Shared Sheet Access...');
  console.log('Sheet ID:', SHEET_ID);
  
  const auth = new google.auth.GoogleAuth({
    keyFile: SERVICE_ACCOUNT_PATH,
    scopes: ['https://www.googleapis.com/auth/spreadsheets']
  });

  try {
    const authClient = await auth.getClient();
    const sheets = google.sheets({ version: 'v4', auth: authClient });
    
    // Read current data
    console.log('\n📖 Reading current data...');
    const readResult = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: 'Sheet1!A1:C5'
    });
    console.log('Current data:', readResult.data.values || 'Empty');
    
    // Write test data
    console.log('\n✍️ Writing test data...');
    const timestamp = new Date().toISOString();
    await sheets.spreadsheets.values.update({
      spreadsheetId: SHEET_ID,
      range: 'Sheet1!A1:C3',
      valueInputOption: 'RAW',
      requestBody: {
        values: [
          ['🤖 Agent Test', 'Status', 'Timestamp'],
          ['CodeMurf AI', '✅ Active', timestamp],
          ['Sheets API', '✅ Working', 'Verified']
        ]
      }
    });
    
    console.log('✅ Data written successfully!');
    console.log('\n🎉 SHEETS API VERIFIED!');
    console.log('Open your sheet to see the changes:', 
      `https://docs.google.com/spreadsheets/d/${SHEET_ID}`);
    
  } catch (err) {
    console.log('❌ Error:', err.message);
    if (err.response) {
      console.log('Details:', JSON.stringify(err.response.data, null, 2));
    }
  }
}

main();
