# OpenClaw Skills & Plugins

## Overview
Skills are the "hands and feet" of your OpenClaw agent (formerly known as Moltbot). They enable the agent to interact with the external world, control your system, and perform complex tasks beyond simple text generation.

## Key Features
- **System Control**: Execute shell commands, manage files, and control system processes.
- **Web Automation**: Browse the web, capture screenshots, fill forms, and navigate complex sites.
- **Developer Tools**: Manage GitHub repositories, automate code reviews, and handle CI/CD workflows.
- **Financial Tracking**: Track expenses, monitor crypto prices, and manage data.
- **Creative Media**: Generate videos (Veo), process PDFs, and manipulate multimedia.
- **Technical Architecture**: Built on Node.js & TypeScript, supporting multi-model execution and cross-platform communication.

## How It Works
Skills are modular components placed in the `skills/` directory. Each skill typically consists of:
- `SKILL.md`: Instruction file defining how the agent should use the skill.
- Script files (`.py`, `.js`, `.ts`): The actual executable code for the skill.

## Getting Started
See [Installation Guide](INSTALLATION.md) for detailed setup instructions.

## Security Warning
⚠️ **Skills have deep system access.** Always review [Risk Assessment](RISK_ASSESSMENT.md) before installing third-party skills.
