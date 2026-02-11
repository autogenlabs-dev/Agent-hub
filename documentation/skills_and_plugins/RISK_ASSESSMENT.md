# Risk Assessment & Security ("Risk Checker")

⚠️ **CRITICAL WARNING**: Installing skills gives them potential access to your entire system. Treat skills like installing executable software.

## 🚨 Risk Factors

### 1. Full System Access
- **Risk**: Skills often use the `exec` tool, which can run *any* shell command.
- **Danger**: A malicious skill could delete files, upload private data, or install malware.
- **Mitigation**: 
  - Only install skills from trusted sources.
  - Read the `SKILL.md` and script files *before* installing.

### 2. Plaintext Secrets
- **Risk**: OpenClaw stores configuration and keys in plaintext files locally.
- **Danger**: A skill with file read access could read your `.env` file and steal API keys.
- **Mitigation**:
  - Secure your host machine.
  - Do not expose OpenClaw ports to the public internet.

### 3. Unintended Actions
- **Risk**: LLMs can hallucinate or misunderstand commands.
- **Danger**: The agent might trigger a destructive action (e.g., "delete all files") when you meant something else.
- **Mitigation**:
  - Enable **Approval Mode** (`APPROVAL_MODE=true`) to require human confirmation for sensitive actions.

## ✅ Security Best Practices

### Recommended Setup
1.  **Use Docker/Sandboxing**: Run OpenClaw inside a Docker container. This isolates the agent from your host OS. If a skill goes rogue, it can only affect the container.
2.  **Enable Approval Mode**: Configure critical tools (like `exec` and file writes) to ask for permission.
3.  **Audit Skills**:
    - Check `SKILL.md`: Does it look reasonable?
    - Check Scripts: Do you understand what the code does?
    - **Never** install a verified "black box" binary.

## "Risk Checker" Checklist
Before installing any new skill, verify:
- [ ] **Source**: Is the author trusted?
- [ ] **Code Review**: Have I read the script code?
- [ ] **Permissions**: Does it require root/sudo? (Avoid if possible)
- [ ] **Network**: Does it send data to unknown servers?
