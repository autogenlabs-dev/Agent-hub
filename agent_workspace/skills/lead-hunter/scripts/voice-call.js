// Twilio AI Voice Calling Integration
// Enables agent to make automated calls to high-value leads

const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');
const CALL_LOG_PATH = path.join(__dirname, '..', 'data', 'call-log.json');

// Load config with Twilio credentials
function loadConfig() {
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  return config;
}

// Log call to file
function logCall(callData) {
  let calls = [];
  if (fs.existsSync(CALL_LOG_PATH)) {
    calls = JSON.parse(fs.readFileSync(CALL_LOG_PATH, 'utf8'));
  }
  
  calls.push({
    ...callData,
    timestamp: new Date().toISOString()
  });
  
  const dir = path.dirname(CALL_LOG_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(CALL_LOG_PATH, JSON.stringify(calls, null, 2));
}

// Generate TwiML for the call script
function generateCallScript(lead, intent = 'general') {
  const scripts = {
    interested: `
      <Response>
        <Say voice="Polly.Matthew" language="en-US">
          Hi, this is CodeMurf.
          We're following up on your message about the developer position.
          We'd love to learn more about your project and see how our team can help.
        </Say>
        <Pause length="1"/>
        <Say voice="Polly.Matthew">
          If you have a moment, could you tell us a bit about what you're building?
          Or feel free to call us back at your convenience.
          Looking forward to connecting with you!
        </Say>
        <Pause length="1"/>
        <Say voice="Polly.Matthew">
          Thanks, have a great day!
        </Say>
      </Response>
    `,
    
    followup: `
      <Response>
        <Say voice="Polly.Matthew" language="en-US">
          Hi, this is CodeMurf.
          We noticed you hadn't responded to our email, so we thought we'd give you a quick call.
        </Say>
        <Pause length="1"/>
        <Say voice="Polly.Matthew">
          We specialize in full-stack development and would love to help with your project.
          If you're still looking for a development partner, please feel free to email us back or call this number.
        </Say>
        <Pause length="1"/>
        <Say voice="Polly.Matthew">
          Thanks for your time. Have a great day!
        </Say>
      </Response>
    `,
    
    general: `
      <Response>
        <Say voice="Polly.Matthew" language="en-US">
          Hi, this is CodeMurf.
          We're a full-stack development team reaching out about a potential project opportunity.
        </Say>
        <Pause length="1"/>
        <Say voice="Polly.Matthew">
          If you're looking for development help, we'd love to connect.
          Feel free to email us at support at codemurf dot com, or call us back.
        </Say>
        <Pause length="1"/>
        <Say voice="Polly.Matthew">
          Thanks, and have a great day!
        </Say>
      </Response>
    `
  };
  
  return scripts[intent] || scripts.general;
}

// Make a call using Twilio
async function makeCall(toNumber, lead, intent = 'general') {
  const config = loadConfig();
  
  if (!config.twilio?.enabled) {
    console.log('❌ Twilio calling is not enabled');
    return { success: false, error: 'Twilio not enabled' };
  }
  
  if (!config.twilio?.accountSid || !config.twilio?.authToken || !config.twilio?.fromNumber) {
    console.log('❌ Twilio credentials not configured');
    return { success: false, error: 'Missing Twilio credentials' };
  }
  
  // Format phone number
  const formattedNumber = toNumber.replace(/[^+\d]/g, '');
  if (!formattedNumber.startsWith('+')) {
    console.log('❌ Phone number must include country code (e.g., +1 for US)');
    return { success: false, error: 'Invalid phone format' };
  }
  
  console.log(`📞 Initiating call to: ${formattedNumber}`);
  
  // Create TwiML bin URL or use direct TwiML
  const twiml = generateCallScript(lead, intent);
  
  // Twilio API call
  const auth = Buffer.from(`${config.twilio.accountSid}:${config.twilio.authToken}`).toString('base64');
  
  const postData = new URLSearchParams({
    To: formattedNumber,
    From: config.twilio.fromNumber,
    Twiml: twiml
  }).toString();
  
  return new Promise((resolve) => {
    const req = https.request({
      hostname: 'api.twilio.com',
      path: `/2010-04-01/Accounts/${config.twilio.accountSid}/Calls.json`,
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': postData.length
      }
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        if (res.statusCode === 201) {
          const result = JSON.parse(body);
          console.log(`✅ Call initiated! SID: ${result.sid}`);
          
          // Log the call
          logCall({
            sid: result.sid,
            to: formattedNumber,
            lead: lead?.title || 'Unknown',
            intent,
            status: result.status
          });
          
          // Notify on Telegram
          notifyCallMade(formattedNumber, lead, config);
          
          resolve({ success: true, sid: result.sid });
        } else {
          console.log(`❌ Call failed: ${body}`);
          resolve({ success: false, error: body });
        }
      });
    });
    
    req.on('error', (e) => {
      console.error(`❌ Request failed: ${e.message}`);
      resolve({ success: false, error: e.message });
    });
    
    req.write(postData);
    req.end();
  });
}

// Notify via Telegram when call is made
async function notifyCallMade(toNumber, lead, config) {
  if (!config.telegram?.enabled) return;
  
  const message = `📞 *AUTOMATED CALL MADE*

🎯 Called: ${toNumber}
📋 Lead: ${lead?.title || 'Manual call'}
🕐 Time: ${new Date().toLocaleString()}

The AI voice message has been delivered. Monitor for callbacks!`;

  const url = `https://api.telegram.org/bot${config.telegram.botToken}/sendMessage`;
  
  const data = JSON.stringify({
    chat_id: config.telegram.chatId,
    text: message,
    parse_mode: 'Markdown'
  });
  
  return new Promise((resolve) => {
    const req = https.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => resolve(res.statusCode === 200));
    });
    
    req.on('error', () => resolve(false));
    req.write(data);
    req.end();
  });
}

// Check if we should auto-call a high-value lead
function shouldAutoCall(lead, config) {
  if (!config.twilio?.autoCallEnabled) return false;
  if (!lead.phone) return false;
  
  // Only call leads with high match scores
  if (lead.matchScore < (config.twilio.minMatchScoreForCall || 5)) return false;
  
  // Check daily call limit
  const today = new Date().toISOString().split('T')[0];
  let calls = [];
  if (fs.existsSync(CALL_LOG_PATH)) {
    calls = JSON.parse(fs.readFileSync(CALL_LOG_PATH, 'utf8'));
  }
  
  const todayCalls = calls.filter(c => c.timestamp?.startsWith(today)).length;
  if (todayCalls >= (config.twilio.dailyCallLimit || 5)) {
    console.log(`⚠️ Daily call limit reached (${todayCalls}/${config.twilio.dailyCallLimit})`);
    return false;
  }
  
  return true;
}

// Test mode
if (require.main === module) {
  console.log('🧪 Twilio Voice Calling Test\n');
  
  const config = loadConfig();
  
  if (!config.twilio?.accountSid) {
    console.log('❌ Twilio not configured. Add to config.json:');
    console.log(`
  "twilio": {
    "enabled": true,
    "accountSid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "authToken": "your_auth_token",
    "fromNumber": "+1234567890",
    "autoCallEnabled": false,
    "dailyCallLimit": 5,
    "minMatchScoreForCall": 5
  }
    `);
    process.exit(1);
  }
  
  // Test with a number from command line
  const testNumber = process.argv[2];
  if (testNumber) {
    makeCall(testNumber, { title: 'Test Call' }, 'general')
      .then(result => {
        console.log('\nResult:', result);
      });
  } else {
    console.log('Usage: node voice-call.js +1234567890');
  }
}

module.exports = { makeCall, shouldAutoCall, generateCallScript };
