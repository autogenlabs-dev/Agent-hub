// Simpler Drive-only test with full error details
const { google } = require('googleapis');
const fs = require('fs');

const SERVICE_ACCOUNT_PATH = '/workspace/credentials/service_account.json';

async function main() {
  console.log('🔑 Loading credentials...');
  const credentials = JSON.parse(fs.readFileSync(SERVICE_ACCOUNT_PATH, 'utf8'));
  console.log('Service Account:', credentials.client_email);
  console.log('Project ID:', credentials.project_id);

  const auth = new google.auth.GoogleAuth({
    keyFile: SERVICE_ACCOUNT_PATH,
    scopes: ['https://www.googleapis.com/auth/drive']
  });

  try {
    const authClient = await auth.getClient();
    console.log('✅ Auth successful');

    const drive = google.drive({ version: 'v3', auth: authClient });
    
    // List files in the service account's own drive
    console.log('\n📁 Listing files in Service Account Drive...');
    const res = await drive.files.list({
      pageSize: 5,
      fields: 'files(id, name)'
    });
    
    console.log('✅ Drive API works!');
    console.log('Files found:', res.data.files.length);
    res.data.files.forEach(f => console.log(' -', f.name));
    
  } catch (err) {
    console.log('❌ Error:', err.message);
    if (err.response) {
      console.log('Status:', err.response.status);
      console.log('Details:', JSON.stringify(err.response.data, null, 2));
    }
  }
}

main();
