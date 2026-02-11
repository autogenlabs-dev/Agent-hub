# OpenClaw/Moltbot Skills Catalog

## Overview
This document catalogs available skills across categories, with their **benefits** and **risk assessment** for installation.

> ⚠️ **General Warning**: All skills have system access. Only install from trusted sources.

---

## 📂 Category 1: System Control

### 1.1 Shell Executor
| Field | Details |
|-------|---------|
| **What it does** | Execute shell/terminal commands via natural language |
| **Benefits** | Automate system tasks, run scripts, manage processes, install packages |
| **Use Cases** | "Restart my server", "Check disk usage", "Kill process on port 3000" |
| **Risk Level** | 🔴 **CRITICAL** |
| **Risk Factors** | Full system command access. Malicious/incorrect commands can delete files, install malware, compromise security |
| **Mitigations** | Enable Approval Mode, run in Docker sandbox |

### 1.2 File Manager
| Field | Details |
|-------|---------|
| **What it does** | Create, read, edit, delete, and search local files |
| **Benefits** | Manage documents, organize folders, search for files by content |
| **Use Cases** | "Find all PDFs from last week", "Create a new project folder", "Back up my documents" |
| **Risk Level** | 🔴 **HIGH** |
| **Risk Factors** | Can read sensitive files (passwords, keys), accidentally delete important data |
| **Mitigations** | Restrict to specific directories, use read-only mode where possible |

### 1.3 Background Task Manager
| Field | Details |
|-------|---------|
| **What it does** | Run and monitor long-running processes in background |
| **Benefits** | Start servers, run builds, manage daemons without blocking |
| **Use Cases** | "Start my dev server in background", "Monitor the build process" |
| **Risk Level** | 🟠 **MEDIUM** |
| **Risk Factors** | Runaway processes can consume resources, zombie processes |
| **Mitigations** | Set timeouts, monitor resource usage |

---

## 📂 Category 2: Web Automation

### 2.1 Web Search (Brave/Tavily)
| Field | Details |
|-------|---------|
| **What it does** | Search the web and return summarized results |
| **Benefits** | Research topics, find documentation, check current events |
| **Use Cases** | "Search for Python async tutorials", "What's the latest on AI regulations?" |
| **Risk Level** | 🟢 **LOW** |
| **Risk Factors** | API key exposure, rate limiting, cost if using paid APIs |
| **Mitigations** | Use free tiers responsibly, protect API keys |

### 2.2 Web Page Capture/Snapshot
| Field | Details |
|-------|---------|
| **What it does** | Screenshot or capture full content of web pages |
| **Benefits** | Archive pages, extract content, visual verification |
| **Use Cases** | "Screenshot this webpage", "Save the article content" |
| **Risk Level** | 🟢 **LOW** |
| **Risk Factors** | May capture sensitive info if used on private pages |
| **Mitigations** | Be mindful of what pages you capture |

### 2.3 Form Auto-Fill / Browser Control
| Field | Details |
|-------|---------|
| **What it does** | Automatically fill forms and navigate websites |
| **Benefits** | Automate repetitive tasks, data entry, web scraping |
| **Use Cases** | "Fill out this job application", "Log into my dashboard and download report" |
| **Risk Level** | 🟠 **MEDIUM-HIGH** |
| **Risk Factors** | Can accidentally submit wrong data, expose credentials if not careful |
| **Mitigations** | Never store passwords in plain text, use approval for sensitive actions |

---

## 📂 Category 3: Developer Tools

### 3.1 GitHub Integration
| Field | Details |
|-------|---------|
| **What it does** | Manage repos, create PRs, review code, check CI/CD status |
| **Benefits** | Automate code reviews, merge PRs, monitor builds |
| **Use Cases** | "Create a PR for this branch", "Check if CI passed", "Review the latest commits" |
| **Risk Level** | 🟠 **MEDIUM** |
| **Risk Factors** | Can push code, merge branches, or delete repos if misconfigured |
| **Mitigations** | Use access tokens with minimal permissions, enable branch protection |

### 3.2 Code Analyzer / Bug Fixer
| Field | Details |
|-------|---------|
| **What it does** | Analyze code, find bugs, and suggest/apply fixes |
| **Benefits** | Faster debugging, automated code quality checks |
| **Use Cases** | "Find bugs in my Python script", "Fix the linting errors" |
| **Risk Level** | 🟢 **LOW-MEDIUM** |
| **Risk Factors** | May introduce new bugs with "fixes", could modify code incorrectly |
| **Mitigations** | Always review changes before committing, use version control |

### 3.3 CI/CD Monitor
| Field | Details |
|-------|---------|
| **What it does** | Monitor build pipelines, deployments, and alerts |
| **Benefits** | Stay informed on build status, get notified on failures |
| **Use Cases** | "Notify me when the build fails", "Check deployment status" |
| **Risk Level** | 🟢 **LOW** |
| **Risk Factors** | Read-only access is generally safe |
| **Mitigations** | Use read-only tokens |

---

## 📂 Category 4: Finance & Health

### 4.1 Expense Tracker
| Field | Details |
|-------|---------|
| **What it does** | Track daily expenses, categorize spending, generate reports |
| **Benefits** | Budget management, spending insights |
| **Use Cases** | "Add $50 for groceries", "Show my spending this month" |
| **Risk Level** | 🟢 **LOW** |
| **Risk Factors** | Stores personal financial data locally |
| **Mitigations** | Secure your device, don't share .env files |

### 4.2 Cryptocurrency Price Monitor
| Field | Details |
|-------|---------|
| **What it does** | Track crypto prices, set alerts, get market updates |
| **Benefits** | Real-time price monitoring, automated trading signals |
| **Use Cases** | "Alert me when BTC drops below $60k", "What's ETH price?" |
| **Risk Level** | 🟢 **LOW** |
| **Risk Factors** | API costs if using premium data, no trading risk (view only) |
| **Mitigations** | Use free API tiers |

### 4.3 Health Data Analyzer (WHOOP/Fitbit)
| Field | Details |
|-------|---------|
| **What it does** | Analyze sleep, heart rate, recovery data from wearables |
| **Benefits** | Health insights, sleep optimization |
| **Use Cases** | "How was my sleep last night?", "Show my recovery trend" |
| **Risk Level** | 🟠 **MEDIUM** |
| **Risk Factors** | Stores sensitive health data, requires API access to wearable |
| **Mitigations** | Protect API credentials, limit data retention |

---

## 📂 Category 5: Creative Media

### 5.1 Video Generator (Veo Integration)
| Field | Details |
|-------|---------|
| **What it does** | Generate AI videos from text prompts |
| **Benefits** | Create content, marketing videos, educational material |
| **Use Cases** | "Create a 30-second video about AI coding" |
| **Risk Level** | 🟢 **LOW** |
| **Risk Factors** | API costs, content moderation |
| **Mitigations** | Set spending limits on API |

### 5.2 PDF Processor
| Field | Details |
|-------|---------|
| **What it does** | Extract text, merge, split, and analyze PDF documents |
| **Benefits** | Document automation, data extraction |
| **Use Cases** | "Extract text from this PDF", "Merge these invoices" |
| **Risk Level** | 🟢 **LOW** |
| **Risk Factors** | Can access potentially sensitive documents |
| **Mitigations** | Be careful with confidential PDFs |

### 5.3 Voice Translator
| Field | Details |
|-------|---------|
| **What it does** | Transcribe and translate voice messages |
| **Benefits** | Multi-language support, accessibility |
| **Use Cases** | "Translate this voice note to English" |
| **Risk Level** | 🟢 **LOW** |
| **Risk Factors** | Sends audio to transcription API |
| **Mitigations** | Use trusted transcription services |

---

## 📂 Category 6: Productivity & Automation

### 6.1 Smart Home Control (Home Assistant)
| Field | Details |
|-------|---------|
| **What it does** | Control lights, thermostats, locks, and other smart devices |
| **Benefits** | Voice/text control of home, automation routines |
| **Use Cases** | "Turn off the living room lights", "Set thermostat to 72°F" |
| **Risk Level** | 🟠 **MEDIUM** |
| **Risk Factors** | Security risk if controlling locks/cameras, misconfiguration |
| **Mitigations** | Use strong authentication, limit to non-critical devices first |

### 6.2 Email Drafter
| Field | Details |
|-------|---------|
| **What it does** | Draft emails in your writing style, manage inbox |
| **Benefits** | Save time on email composition, maintain consistent tone |
| **Use Cases** | "Draft a reply to John's email", "Summarize my unread emails" |
| **Risk Level** | 🟠 **MEDIUM** |
| **Risk Factors** | Access to email content, potential for sending wrong emails |
| **Mitigations** | Always review before sending, use read-only mode initially |

### 6.3 Calendar & Schedule Manager
| Field | Details |
|-------|---------|
| **What it does** | Manage calendar events, set reminders, schedule meetings |
| **Benefits** | Automated scheduling, conflict detection |
| **Use Cases** | "Schedule a meeting with Sarah tomorrow at 2pm" |
| **Risk Level** | 🟢 **LOW** |
| **Risk Factors** | Accidental event creation/deletion |
| **Mitigations** | Enable confirmation before changes |

### 6.4 Morning Briefing (Proactive/Heartbeat)
| Field | Details |
|-------|---------|
| **What it does** | Automatically sends daily summaries (weather, schedule, news) |
| **Benefits** | Start day informed without asking, proactive notifications |
| **Use Cases** | Automatic morning message with schedule and weather |
| **Risk Level** | 🟢 **LOW** |
| **Risk Factors** | Requires always-on agent, potential for spam if misconfigured |
| **Mitigations** | Set frequency limits |

---

## 🔒 Risk Level Summary

| Level | Color | Meaning |
|-------|-------|---------|
| 🟢 LOW | Green | Minimal risk, mostly read-only or sandboxed |
| 🟠 MEDIUM | Orange | Some risk, can modify data or has external access |
| 🔴 HIGH/CRITICAL | Red | Full system access, can cause significant damage if misused |

---

## ✅ Recommended First Installs (Low Risk)

1. **Web Search** - Safe, useful for research
2. **Expense Tracker** - Local data, no system access
3. **PDF Processor** - Document utility
4. **Calendar Manager** - Productivity boost

## ⚠️ Install with Caution (Enable Approval Mode)

1. **Shell Executor** - Only if you need system automation
2. **GitHub Integration** - Use limited access tokens
3. **Smart Home Control** - Start with non-critical devices

---

*Last Updated: 2026-02-06*
