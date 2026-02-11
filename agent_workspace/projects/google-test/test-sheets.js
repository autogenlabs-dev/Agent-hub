// Sheets test - create a spreadsheet owned by service account
const { google } = require('googleapis');
const fs = require('fs');

const SERVICE_ACCOUNT_PATH = '/workspace/credentials/service_account.json';

async function main() {
  console.log('📊 Testing Google Sheets API...');
  
  const auth = new google.auth.GoogleAuth({
    keyFile: SERVICE_ACCOUNT_PATH,
    scopes: ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
  });

  try {
    const authClient = await auth.getClient();
    const sheets = google.sheets({ version: 'v4', auth: authClient });
    const drive = google.drive({ version: 'v3', auth: authClient });
    
    // Create a new spreadsheet
    console.log('Creating spreadsheet...');
    const spreadsheet = await sheets.spreadsheets.create({
      requestBody: {
        properties: {
          title: 'CodeMurf Agent Test - ' + new Date().toISOString().slice(0,10)
        }
      }
    });
    
    console.log('✅ Spreadsheet created!');
    console.log('ID:', spreadsheet.data.spreadsheetId);
    console.log('URL:', spreadsheet.data.spreadsheetUrl);
    
    // Write data
    await sheets.spreadsheets.values.update({
      spreadsheetId: spreadsheet.data.spreadsheetId,
      range: 'Sheet1!A1:C3',
      valueInputOption: 'RAW',
      requestBody: {
        values: [
          ['Test', 'Status', 'Time'],
          ['Agent', 'Active', new Date().toISOString()],
          ['CodeMurf', 'Online', '24/7']
        ]
      }
    });
    console.log('✅ Data written to spreadsheet');
    
    // Share with user's email
    console.log('Sharing with codemurf@gmail.com...');
    await drive.permissions.create({
      fileId: spreadsheet.data.spreadsheetId,
      requestBody: {
        type: 'user',
        role: 'writer',
        emailAddress: 'codemurf@gmail.com'
      }
    });
    console.log('✅ Shared successfully!');
    console.log('\n🎉 Open this URL:', spreadsheet.data.spreadsheetUrl);
    
  } catch (err) {
    console.log('❌ Error:', err.message);
    if (err.response) {
      console.log('Details:', JSON.stringify(err.response.data, null, 2));
    }
  }
}

main();
