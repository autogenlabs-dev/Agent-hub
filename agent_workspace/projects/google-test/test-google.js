// Google Services Test Script
// Tests Drive, Sheets, and Gmail API access using Service Account

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

// Load service account credentials
const SERVICE_ACCOUNT_PATH = '/workspace/credentials/service_account.json';

async function main() {
  console.log('🔑 Loading Service Account credentials...');
  
  if (!fs.existsSync(SERVICE_ACCOUNT_PATH)) {
    console.error('❌ Service account file not found at:', SERVICE_ACCOUNT_PATH);
    process.exit(1);
  }

  const credentials = JSON.parse(fs.readFileSync(SERVICE_ACCOUNT_PATH, 'utf8'));
  console.log('✅ Credentials loaded for:', credentials.client_email);

  // Create auth client
  const auth = new google.auth.GoogleAuth({
    keyFile: SERVICE_ACCOUNT_PATH,
    scopes: [
      'https://www.googleapis.com/auth/drive',
      'https://www.googleapis.com/auth/spreadsheets',
      'https://www.googleapis.com/auth/gmail.readonly'
    ]
  });

  const authClient = await auth.getClient();
  console.log('✅ Auth client created successfully');

  // Test 1: Drive API
  console.log('\n📁 Testing Google Drive API...');
  try {
    const drive = google.drive({ version: 'v3', auth: authClient });
    const driveAbout = await drive.about.get({ fields: 'user' });
    console.log('✅ Drive API works! User:', driveAbout.data.user.displayName || 'Service Account');
  } catch (err) {
    console.log('⚠️ Drive API error:', err.message);
    console.log('   Note: Service accounts need Drive API enabled in Google Cloud Console');
  }

  // Test 2: Sheets API - Create a test spreadsheet
  console.log('\n📊 Testing Google Sheets API...');
  try {
    const sheets = google.sheets({ version: 'v4', auth: authClient });
    
    // Create a new spreadsheet
    const spreadsheet = await sheets.spreadsheets.create({
      requestBody: {
        properties: {
          title: 'CodeMurf Agent Test - ' + new Date().toISOString()
        }
      }
    });
    
    console.log('✅ Sheets API works! Created spreadsheet:', spreadsheet.data.spreadsheetUrl);
    
    // Write some data
    await sheets.spreadsheets.values.update({
      spreadsheetId: spreadsheet.data.spreadsheetId,
      range: 'Sheet1!A1:B2',
      valueInputOption: 'RAW',
      requestBody: {
        values: [
          ['Agent Test', 'Status'],
          ['CodeMurf', 'Active']
        ]
      }
    });
    console.log('✅ Data written to spreadsheet');
    
  } catch (err) {
    console.log('⚠️ Sheets API error:', err.message);
    console.log('   Note: Service accounts need Sheets API enabled in Google Cloud Console');
  }

  // Test 3: Gmail API
  console.log('\n📧 Testing Gmail API...');
  try {
    const gmail = google.gmail({ version: 'v1', auth: authClient });
    const profile = await gmail.users.getProfile({ userId: 'me' });
    console.log('✅ Gmail API works! Email:', profile.data.emailAddress);
  } catch (err) {
    console.log('⚠️ Gmail API error:', err.message);
    console.log('   Note: Gmail API requires domain-wide delegation for service accounts');
    console.log('   This is expected to fail unless you configured delegation');
  }

  console.log('\n🏁 Google Services Test Complete!');
}

main().catch(console.error);
