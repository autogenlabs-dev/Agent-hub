# Project Deployer Skill

## Description
Deploy projects to various cloud platforms using agent-dedicated credentials.

## Supported Platforms
- **Render.com** - Full-stack apps, APIs
- **Vercel** - Frontend, Next.js
- **Railway** - Full-stack, databases
- **Netlify** - Static sites, Jamstack

## Credentials
Load from `/workspace/credentials/.env.agent`:
```bash
AGENT_RENDER_API_KEY=rnd_xxx
AGENT_VERCEL_TOKEN=xxx
AGENT_RAILWAY_TOKEN=xxx
AGENT_NETLIFY_TOKEN=xxx
```

## Deployment Workflows

### Deploy to Render
```bash
# 1. Build project
cd /workspace/projects/myapp
npm run build

# 2. Deploy via Render API
curl -X POST "https://api.render.com/v1/services" \
  -H "Authorization: Bearer ${AGENT_RENDER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "web_service",
    "name": "my-deployed-app",
    "repo": "https://github.com/agent-user/myapp",
    "branch": "main",
    "buildCommand": "npm install && npm run build",
    "startCommand": "npm start"
  }'
```

### Deploy to Vercel
```bash
cd /workspace/projects/myapp
npx vercel --token ${AGENT_VERCEL_TOKEN} --prod
```

### Deploy to Railway
```bash
cd /workspace/projects/myapp
railway login --token ${AGENT_RAILWAY_TOKEN}
railway up
```

### Deploy to Netlify
```bash
cd /workspace/projects/myapp
npm run build
npx netlify deploy --prod --dir=./build --auth=${AGENT_NETLIFY_TOKEN}
```

## Deployment Log
All deployments should be logged:
```bash
echo "$(date) - Deployed myapp to Render: https://myapp.onrender.com" >> /workspace/logs/deployments.log
```

## Pre-Deployment Checklist
1. ✅ Project builds successfully
2. ✅ Tests pass
3. ✅ Environment variables configured
4. ✅ Correct branch selected
5. ✅ Deployment platform credentials valid

## Post-Deployment
- Log deployment URL
- Run health check
- Notify owner of successful deployment
