# 💬 Interactive Telegram Bot Guide

## Overview

Your AI team now has an **interactive Telegram bot** that responds to commands and questions in real-time!

You can ask it anything about your team's status, agents, tasks, evaluations, and more.

---

## 🚀 Getting Started

### 1. Find Your Bot

The bot is automatically active when the orchestrator is running. Just send a message to your Telegram chat!

### 2. Start the Conversation

Send `/start` to begin:

```
/start
```

You'll get a welcome message with quick commands.

---

## 📋 Available Commands

### Status & Overview

**`/status`** - Overall team health and status
```
/status
```
Shows:
- System uptime
- Task counts (completed, in progress, pending)
- Active agents
- Last update time

**`/uptime`** - System uptime and performance
```
/uptime
```
Shows:
- Days/hours running
- Total cycles completed
- Cycles per hour
- Performance metrics

**`/metrics`** - Detailed performance metrics
```
/metrics
```
Shows:
- Task completion rate
- Tasks per hour velocity
- Latest evaluation score
- System statistics

---

### Team Information

**`/agents`** - List all 39 agents
```
/agents
```
Shows:
- All developers (15)
- All Mangoes (24)
- Status of each agent
- Role and specialization

**`/team`** - Team breakdown by role
```
/team
```
Shows:
- Agents grouped by role
- Count per role
- Status indicators

---

### Tasks

**`/tasks`** - View all tasks
```
/tasks
```
Shows all tasks (pending, in progress, completed)

**`/tasks pending`** - Only pending tasks
```
/tasks pending
```

**`/tasks in progress`** - Only active tasks
```
/tasks in progress
```

**`/tasks completed`** - Only completed tasks
```
/tasks completed
```

---

### Evaluations & Improvements

**`/evaluation`** - Latest self-evaluation
```
/evaluation
```
Shows:
- Overall score (out of 100)
- Performance metrics
- Evaluation summary
- Timestamp

**`/improvements`** - Recent self-improvement cycles
```
/improvements
```
Shows:
- Recent improvement attempts
- Deployment status
- Agent approval rates
- Success/failure

---

### Help

**`/help`** - Full command list
```
/help
```
Shows all available commands and how to use them.

---

## 💬 Natural Language Questions

You don't need to remember commands! Just ask questions:

### Status Questions
- "What's happening?"
- "What is happening?"
- "How are things?"
- "Status?"

### Agent Questions
- "How are the agents doing?"
- "Show me the agents"
- "Who is working?"
- "List team members"

### Task Questions
- "What tasks are in progress?"
- "What are you working on?"
- "Show me pending tasks"
- "What's being done?"

### Evaluation Questions
- "How are we doing?"
- "What's the latest evaluation?"
- "Show me the score"
- "Performance?"

### Uptime Questions
- "How long has it been running?"
- "What's the uptime?"
- "How many cycles?"

---

## 📱 Example Conversations

### Example 1: Quick Status Check
```
You: /status

Bot: 📊 Team Status

Overall Health: 🟢 Operational
Uptime: 8.5 hours
Cycles Completed: 255

Tasks:
✅ Completed: 45
🔄 In Progress: 12
⏳ Pending: 8
📋 Total: 65

Agents:
👥 Total: 39
🟢 Active: 39

Last Update: 2025-11-06 12:30:00
```

### Example 2: Agent Inquiry
```
You: How are the agents doing?

Bot: 👥 All Agents (39 total)

Developers (15):
🟢 🎯 Marcus - Engineering Manager
🟢 ⚙️ Aria - Backend Engineer
🟢 ⚙️ Kai - Backend Engineer
🟢 🤖 Zara - LLM Engineer
🟢 🎨 Luna - Frontend Engineer
...

Mangoes (24):
🟢 📊 Mango Data Entry - Data Entry Specialist
🟢 💼 Mango EA - Executive Assistant
🟢 💰 Mango Sales - Sales Representative
...
```

### Example 3: Task Check
```
You: What tasks are pending?

Bot: ⏳ Pending Tasks (8)

⏳ Implement new feature X
   Agent: Marcus
   Status: pending

⏳ Fix bug in API endpoint
   Agent: Aria
   Status: pending

⏳ Update documentation
   Agent: Phoenix
   Status: pending
...
```

### Example 4: Evaluation Check
```
You: /evaluation

Bot: 📊 Latest Self-Evaluation

Score: 78/100
Time: 2025-11-06 12:00:00

Metrics:
• Tasks: 45/65 completed
• Velocity: 5.3 tasks/hour
• Uptime: 8.5 hours

Evaluation Summary:
OVERALL SCORE: 78/100

STRATEGIC FOCUS: 24/30
Good feature prioritization...

EXECUTION QUALITY: 22/25
Excellent code quality...
...
```

---

## 🎯 Quick Reference

| Want to know... | Command | Or ask... |
|----------------|---------|-----------|
| Overall status | `/status` | "What's happening?" |
| Agent list | `/agents` | "Show me the agents" |
| Task list | `/tasks` | "What's in progress?" |
| Latest score | `/evaluation` | "How are we doing?" |
| System uptime | `/uptime` | "How long running?" |
| Performance | `/metrics` | "Show metrics" |
| Team breakdown | `/team` | "Team status" |
| Improvements | `/improvements` | "Recent improvements" |
| Help | `/help` | "Help" |

---

## 🔔 Automatic Notifications

The bot also sends automatic notifications:

### Startup
```
🥭 ManyMangoes AI Team Started!
39 agents activated
Time: 2025-11-06 12:00:00

💬 Interactive bot active! Send /help to get started.
```

### Hourly Evaluations
```
🔍 Self-Evaluation Complete

📊 Metrics:
• Tasks: 45/65 completed
• Velocity: 5.3 tasks/hour
• Uptime: 8.5h

📝 Evaluation Summary:
[Preview of evaluation]
```

### Self-Improvements
```
🎉 Self-Improvement Deployed!

📊 Cycle: 20251106_143022
✅ Tests passed: 15/16 agents approved
🚀 Production deployment: SUCCESSFUL
```

---

## ⚙️ Setup

### Required Environment Variables

1. **`TELEGRAM_TOKEN`** - Your bot token from @BotFather
2. **`TELEGRAM_CHAT_ID`** - Your chat ID (optional, for notifications)

### Getting Your Bot Token

1. Open Telegram
2. Search for **@BotFather**
3. Send `/newbot`
4. Follow instructions to create bot
5. Copy the token
6. Add to Render environment variables

### Finding Your Chat ID

1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Look for `"chat":{"id":123456789}` in the response
4. That's your chat ID

---

## 🎨 Features

### ✅ Real-Time Updates
- Bot responds instantly
- Always has latest data
- No caching delays

### ✅ Natural Language
- Ask questions naturally
- No need to remember exact commands
- Understands variations

### ✅ Rich Formatting
- HTML formatting
- Emojis for visual clarity
- Organized sections
- Easy to read

### ✅ Comprehensive Coverage
- All team information
- Task status
- Evaluations
- Improvements
- Metrics

---

## 🚨 Troubleshooting

### Bot Not Responding?

**Check:**
1. Is orchestrator running?
2. Is `TELEGRAM_TOKEN` set correctly?
3. Check logs: `grep "Telegram bot" logs/orchestrator.log`
4. Did you send `/start` first?

### Commands Not Working?

**Try:**
1. Send `/start` to reset
2. Check spelling of command
3. Use natural language instead
4. Check `/help` for correct syntax

### Missing Information?

**Possible reasons:**
- System just started (no data yet)
- First evaluation hasn't run (needs 1 hour)
- No tasks created yet
- Check if orchestrator is fully initialized

---

## 💡 Tips

1. **Use natural language** - Don't worry about exact commands
2. **Check `/help`** - See all available commands
3. **Ask follow-ups** - Bot remembers context
4. **Use shortcuts** - `/s` works for `/status` (if you add it)
5. **Check regularly** - Bot updates in real-time

---

## 📚 Advanced Usage

### Query Specific Agents
```
You: Show me Marcus's status
Bot: [Shows Marcus-specific info]
```

### Get Detailed Metrics
```
You: /metrics
Bot: [Shows comprehensive performance data]
```

### Check Improvement History
```
You: /improvements
Bot: [Shows all recent improvement cycles]
```

---

## 🎉 Summary

You now have a **fully interactive AI team assistant** in Telegram!

**Just message your bot:**
- Ask questions naturally
- Get instant updates
- Monitor team status
- Track performance
- View evaluations
- Check improvements

**The bot is always listening and ready to help!** 💬🥭

---

**Questions?** Just ask the bot `/help` or send it a message!

