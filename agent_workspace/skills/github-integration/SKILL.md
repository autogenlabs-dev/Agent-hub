# GitHub Integration Skill

## Description
Clone, manage, and deploy projects from GitHub using agent-dedicated credentials.

## Authentication
Use the dedicated agent GitHub token from `/workspace/credentials/.env.agent`:
```bash
AGENT_GITHUB_TOKEN=ghp_xxx
AGENT_GITHUB_USERNAME=agent-bot-username
```

## Capabilities
- Clone repositories
- Create branches
- Commit and push changes
- Create pull requests
- Check CI/CD status

## Usage Examples

### Clone a Repository
```bash
cd /workspace/projects
git clone https://${AGENT_GITHUB_TOKEN}@github.com/owner/repo.git
```

### Create a Branch and Commit
```bash
cd /workspace/projects/repo
git checkout -b feature/new-feature
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
```

### Create Pull Request (via API)
```python
import requests

def create_pr(repo: str, title: str, head: str, base: str = "main"):
    token = os.environ.get("AGENT_GITHUB_TOKEN")
    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "head": head,
        "base": base
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()
```

## Security Notes
- Token should have minimal required permissions
- Use fine-grained personal access tokens (PATs)
- Never commit the token to repositories
- All cloned repos go to `/workspace/projects/`

## Workflow
1. Clone project → `/workspace/projects/project-name/`
2. Make changes
3. Build & test → `/workspace/builds/`
4. Commit & push
5. Create PR
6. Monitor CI status
