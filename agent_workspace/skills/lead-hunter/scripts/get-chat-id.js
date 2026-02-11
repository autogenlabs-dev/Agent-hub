const https = require('https');
const fs = require('fs');
const path = require('path');

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');

async function getUpdates() {
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  const token = config.telegram.botToken;

  if (!token) {
    console.error('No bot token found in config.json');
    return;
  }

  const url = `https://api.telegram.org/bot${token}/getUpdates`;

  https.get(url, (res) => {
    let body = '';
    res.on('data', chunk => body += chunk);
    res.on('end', () => {
      if (res.statusCode === 200) {
        const data = JSON.parse(body);
        if (data.result.length === 0) {
            console.log('No updates found. Please send a message to the bot in the group and run this again.');
        } else {
            console.log('Recent Updates:');
            data.result.forEach(update => {
                const chat = update.message?.chat || update.my_chat_member?.chat;
                if (chat) {
                    console.log(`Chat: ${chat.title || chat.username || chat.first_name} (ID: ${chat.id}, Type: ${chat.type})`);
                }
            });
        }
      } else {
        console.error(`Error fetching updates: ${body}`);
      }
    });
  }).on('error', (e) => {
    console.error(`Request failed: ${e.message}`);
  });
}

getUpdates();
