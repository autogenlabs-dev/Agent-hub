# Installation Guide: OpenClaw Skills

## Step-by-Step Installation

### 1. Acquire Skills
Obtain skills from:
- **Official Registry**: [ClawHub](https://clawhub.ai/skills) (Browse for community skills)
- **GitHub**: Search for OpenClaw/Moltbot compatible skill repositories.
- **Custom Creation**: Write your own `SKILL.md` and scripts.

### 2. Place in Directory
1. Navigate to your OpenClaw/Moltbot root directory.
2. Go to the `skills/` folder.
3. Create a new subfolder for the skill (e.g., `skills/google-search`).
4. Place all skill files (`SKILL.md`, scripts) inside this new folder.

### 3. Configure Environment
Most skills require external API keys or configuration.
1. Open your `.env` file in the root directory.
2. Add the required variables as specified in the skill's documentation.
   - Example: `SEARCH_API_KEY=your_key_here`

### 4. Activate & Test
1. **Restart** your OpenClaw agent to load the new skills.
2. **Verify** by asking the agent: *"What skills do you have available?"*
3. **Test** by triggering the skill with a natural language command.

---

## Troubleshooting

### Skill Not Detected
- **Check Filename**: Ensure the instruction file is named exactly `SKILL.md` (all uppercase).
- **Check Structure**: Ensure the file is inside a subfolder in `skills/`.

### Missing Dependencies
- If a skill uses Python scripts with imports (e.g., `import requests`), you must install them:
  ```bash
  pip install requests
  ```
- For Node.js skills, ensure `node_modules` are handled or global packages are available.

### Permission Denied
- **Executable Rights**: If a script fails to run, it might need execution permissions.
  ```bash
  chmod +x path/to/script.py
  ```
- **Windows Users**: Run via WSL2 (Ubuntu) for best compatibility. Native CMD/PowerShell may have issues with some shell scripts.

### Temporarily Disable a Skill
- Rename the skill folder with a leading underscore to ignore it:
  - `skills/my-skill` -> `skills/_my-skill`
- Restart the agent.
