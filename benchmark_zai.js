const https = require('https');

// Multi-task benchmark with REASONING support
const MODELS = ['GLM-4.6', 'GLM-4.7', 'GLM-4.5', 'GLM-4.5-air'];
const API_KEY = 'c83ff4924c36424bb507431e63640fc1.A1piew9xWOGxOK8R';
const HOST = 'api.z.ai';
const PATH = '/api/coding/paas/v4/chat/completions';

const TASKS = [
    { name: 'Code Gen', prompt: 'Write a Python quicksort function. Be concise.', maxTokens: 600 },
    { name: 'Debug', prompt: 'Fix this code: def add(a,b) return a+b', maxTokens: 400 },
    { name: 'Explain', prompt: 'Explain what a closure is in JavaScript in 2 sentences.', maxTokens: 400 },
    { name: 'Math', prompt: 'Calculate: If a train travels 120km in 2 hours, what is its speed in m/s?', maxTokens: 400 },
    { name: 'Chat', prompt: 'Hello! How are you today?', maxTokens: 300 }
];

function testTask(model, task) {
    return new Promise((resolve) => {
        const start = Date.now();
        
        const data = JSON.stringify({
            model: model,
            messages: [{ role: 'user', content: task.prompt }],
            max_tokens: task.maxTokens
        });

        const options = {
            hostname: HOST,
            path: PATH,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`,
                'Content-Length': data.length
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                const elapsed = Date.now() - start;
                try {
                    const response = JSON.parse(body);
                    if (response.error) {
                         resolve({ ok: false, time: elapsed, error: response.error.message });
                    } else {
                        const content = response.choices?.[0]?.message?.content || '';
                        const reasoning = response.choices?.[0]?.message?.reasoning_content || '';
                        const hasOutput = content.length > 5 || reasoning.length > 10;
                        resolve({ ok: hasOutput, time: elapsed, contentLen: content.length, reasoningLen: reasoning.length });
                    }
                } catch (e) {
                    resolve({ ok: false, time: elapsed, error: 'JSON Parse Error: ' + body.slice(0, 50) });
                }
            });
        });

        req.on('error', (e) => {
            resolve({ ok: false, time: Date.now() - start, error: e.message });
        });

        req.write(data);
        req.end();
    });
}

async function run() {
    console.log('╔═══════════════════════════════════════════════════════════════════════════════╗');
    console.log('║    Z.AI GLM CODING PLAN - MULTI-TASK BENCHMARK (with Reasoning Support)     ║');
    console.log('╚═══════════════════════════════════════════════════════════════════════════════╝\n');
    
    const results = {};
    for (const m of MODELS) {
        results[m] = { total: 0, success: 0, tasks: {} };
    }
    
    for (const task of TASKS) {
        console.log(`\n📋 Task: ${task.name}`);
        console.log(`   "${task.prompt.slice(0, 50)}..."`);
        console.log('   ─────────────────────────────────────────────────');
        
        for (const model of MODELS) {
            const result = await testTask(model, task);
            results[model].tasks[task.name] = result;
            results[model].total += result.time;
            if (result.ok) results[model].success++;
            
            const status = result.ok ? '✅' : '❌';
            const time = String(result.time).padStart(5);
            const detail = result.ok 
                ? `content:${result.contentLen} reasoning:${result.reasoningLen}` 
                : (result.error || 'Empty');
            console.log(`   ${status} ${model.padEnd(12)} | ${time}ms | ${detail}`);
        }
    }
    
    console.log('\n╔═══════════════════════════════════════════════════════════════════════════════╗');
    console.log('║                              FINAL RESULTS                                   ║');
    console.log('╚═══════════════════════════════════════════════════════════════════════════════╝\n');
    
    console.log('Model         | Success | Avg Time | Total Time');
    console.log('──────────────┼─────────┼──────────┼───────────');
    
    const rankings = MODELS.map(m => ({
        model: m,
        success: results[m].success,
        total: results[m].total,
        avg: Math.round(results[m].total / TASKS.length)
    })).sort((a, b) => b.success - a.success || a.avg - b.avg);
    
    rankings.forEach((r, i) => {
        const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '  ';
        console.log(`${medal} ${r.model.padEnd(11)} | ${r.success}/${TASKS.length}     | ${String(r.avg).padStart(5)}ms  | ${r.total}ms`);
    });
    
    console.log(`\n🏆 BEST MODEL: ${rankings[0].model}`);
    console.log(`   Success Rate: ${rankings[0].success}/${TASKS.length} tasks`);
    console.log(`   Average Response: ${rankings[0].avg}ms`);
}

run();
