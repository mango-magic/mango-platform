# 🎛️ ManyMangoes Management Guide

## How to Manage Your AI Team

You have **three ways** to manage and interact with your 39 AI agents:

---

## 1. 📱 Telegram Bot (Recommended for Day-to-Day)

**Best for:** Quick commands, mobile access, approvals, talking to agents

### Setup (One-Time)

1. Get your Telegram Chat ID:
   ```bash
   # Message your bot first, then visit:
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   
   # Look for: "chat":{"id":123456789}
   # That number is your TELEGRAM_CHAT_ID
   ```

2. Add to Render environment variables:
   ```
   TELEGRAM_CHAT_ID=123456789
   ```

3. Start chatting with your bot on Telegram!

### Available Commands

#### **📊 Monitoring**
```
/status          - Team status summary
/agents          - List all 39 agents (who's active)
/tasks           - View current tasks
/deploy          - Deployment status (TEST/PROD)
/metrics         - Team performance metrics
/logs            - Recent log entries
```

#### **💬 Communication**
```
/talk marcus What's the status of Mango EA?
/talk aria How's the core framework?

# Or just type without /talk:
"Marcus, what are the top priorities today?"
```

#### **🎛️ Control**
```
/approve deploy_001    - Approve production deployment
/reject deploy_001     - Reject deployment
/activate mango_ea_001 - Activate tested Mango
/pause                 - Pause entire system
/resume                - Resume system
```

### Example Conversations

**Quick Status Check:**
```
You: /status

Bot: 📊 Team Status Report
     ⏰ Uptime: 12.3 hours
     🔄 Cycles: 370
     🌍 Environment: TEST
     
     👥 Agents: 15/39 active
     📋 Tasks: 45 completed (78%)
     
     Everything running smoothly! ✅
```

**Talk to Marcus:**
```
You: Marcus, what's blocking us right now?

Marcus: Hey! Great question. We have 2 blockers:
        
        1. Aria needs OAuth tokens for LinkedIn API
        2. Luna waiting for API endpoint from Aria
        
        I'm unblocking Aria now. Should be resolved 
        in next cycle (2 min).
        
        Overall: Day 3, core framework 40% complete.
        On track for first Mango by Day 7! 🚀
```

**Approve Deployment:**
```
You: /approve

Bot: 🔹 Pending Production Deployments:
     
     deploy_001
     Component: MangoBase Core
     Version: v1.0.0
     Gates: 10/10 ✅
     Coverage: 94.2%
     
     Use: /approve deploy_001

You: /approve deploy_001

Bot: ✅ Deployment approved and deployed to PRODUCTION!
```

**Activate Mango After Testing:**
```
You: /activate mango_data_001

Bot: 🚀 ACTIVATED: Mango Data Entry
     
     This Mango will now receive tasks from Marcus.
     Monitor closely for first few tasks!
```

---

## 2. 🖥️ Web Dashboard

**Best for:** Deep analysis, visual monitoring, detailed metrics

### Access

```
https://mango-dashboard-xxxxx.onrender.com
```

### What You See

1. **Real-Time Overview**
   - Current cycle number
   - Tasks completed
   - Active agents
   - System health

2. **Agent Grid**
   - All 39 agents with status
   - 🟢 Active | ⚪ Inactive
   - Real-time task assignments

3. **Task Timeline**
   - Recent tasks scrolling
   - Completion status
   - Who's working on what

4. **Environment Status**
   - TEST environment health
   - PRODUCTION environment health
   - Deployment history

5. **Team Metrics**
   - Tasks per agent per day
   - Completion rates
   - Velocity trends

### Dashboard Updates

- **Auto-refreshes every 10 seconds**
- No manual refresh needed
- Live data from orchestrator

### Dashboard Limitations

❌ Can't send commands (use Telegram for that)
❌ Can't approve deployments (use Telegram)
✅ Perfect for monitoring and analysis
✅ Great for presentations/demos

---

## 3. 🔧 Direct API Calls

**Best for:** Automation, scripts, external integrations

### Status Endpoint

```bash
curl https://mango-orchestrator-xxxxx.onrender.com/api/status
```

Response:
```json
{
  "status": "running",
  "cycle": 370,
  "agents_active": 15,
  "tasks_completed": 45,
  "uptime_hours": 12.3
}
```

### Create Task (For Marcus)

```bash
curl -X POST https://mango-orchestrator-xxxxx.onrender.com/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Investigate slow API response",
    "description": "Users reporting 2-3 second delays",
    "priority": "urgent",
    "assigned_to": "backend_001"
  }'
```

### Get Agent Status

```bash
curl https://mango-orchestrator-xxxxx.onrender.com/api/agents/eng_manager_001
```

---

## 🎯 Recommended Management Workflow

### **Daily (5 minutes)**

**Morning:**
```
1. Telegram: /status
2. Telegram: "Marcus, what are today's priorities?"
3. Dashboard: Check overnight progress
4. Telegram: /metrics (team performance)
```

**Evening:**
```
1. Telegram: "Marcus, summary of today's progress?"
2. Telegram: /deploy (check deployment status)
3. Dashboard: Review task completion
4. Telegram: /logs (scan for errors)
```

### **Weekly (30 minutes)**

**Monday:**
```
1. Talk to Marcus about week's goals
2. Review which Mangoes are ready for testing
3. Check TEST environment health
4. Set priorities for the week
```

**Friday:**
```
1. Review team metrics (velocity, quality)
2. Approve tested Mangoes for activation
3. Approve deployments to PRODUCTION
4. Give feedback to Marcus
```

### **Monthly (2 hours)**

**First of Month:**
```
1. Deep dive on dashboard metrics
2. Review all 24 Mango statuses
3. Plan next 4 Mangoes to build
4. Performance review with Marcus
5. Adjust priorities based on results
```

---

## 🚨 Emergency Controls

### Pause Everything

**Telegram:**
```
/pause
```

**When to use:**
- Production incident
- Need to investigate something
- Want to make manual changes

### Resume

**Telegram:**
```
/resume
```

### Emergency Rollback

**Telegram:**
```
/reject deploy_001
Marcus, rollback to previous version immediately
```

### View Logs in Real-Time

**Render Dashboard:**
1. Go to `mango-orchestrator` service
2. Click "Logs" tab
3. See real-time output

**Telegram:**
```
/logs
```

---

## 💡 Pro Tips

### 1. **Talk to Marcus Like a Real Manager**

❌ Bad: `/talk marcus status`
✅ Good: "Marcus, which engineers are blocked right now?"

❌ Bad: "Task update"
✅ Good: "What progress did we make on Mango EA today?"

### 2. **Use Telegram Notifications**

Marcus sends updates automatically:
- ✅ Major milestones ("Day 5: First Mango ready!")
- ⚠️ Blockers ("2 engineers waiting on API tokens")
- 🚀 Deployments ("MangoBase v1.0 deployed to TEST")
- ❌ Failures ("Production health check failed")

### 3. **Dashboard for Demos**

When showing investors/team:
- Open dashboard on screen share
- Shows live progress
- Updates every 10 seconds
- Looks professional

### 4. **Telegram for Real Work**

- Quick approvals on phone
- Talk to Marcus while commuting
- Get instant status
- Emergency controls

### 5. **Give Feedback Through Marcus**

```
You: "Marcus, the last deployment was too rushed. 
      From now on, run 200 tests before requesting 
      production approval."

Marcus: "Got it. Updating deployment checklist.
         Will run 200+ tests on all components
         before requesting approval. Thanks for
         the guidance! 🎯"
```

---

## 🔐 Security Best Practices

### 1. **Telegram Access**

- Keep your Telegram token secret
- Only your chat ID can send commands
- Bot won't respond to others

### 2. **Production Approvals**

- Always review /deploy before approving
- Check test coverage ≥ 90%
- Verify all 10 gates passed
- Have Marcus explain the change

### 3. **Emergency Access**

- Keep Render.com dashboard open in browser
- Can restart services manually if needed
- Can view logs directly

### 4. **Rate Limits**

Gemini API limits:
- 1500 requests/day
- 1M tokens/day

If exceeded:
- System auto-pauses
- Marcus sends Telegram alert
- Resumes next day automatically

---

## 📊 What to Monitor

### **Green Flags** ✅

```
✅ Cycle count increasing steadily
✅ Tasks completing regularly
✅ No error messages in logs
✅ Agents reporting status daily
✅ Test coverage ≥ 90%
✅ Deployments passing all gates
✅ Marcus responding to questions quickly
```

### **Yellow Flags** ⚠️

```
⚠️ Cycle count stuck (system paused?)
⚠️ Tasks piling up uncompleted
⚠️ Same agent blocked for multiple cycles
⚠️ Test coverage dropping below 90%
⚠️ Deployments failing gates repeatedly
⚠️ No status reports from agents

Action: Talk to Marcus, investigate
```

### **Red Flags** 🚨

```
🚨 Orchestrator crashed (Render service down)
🚨 API rate limits exceeded
🚨 Production deployment failed
🚨 Multiple critical bugs in logs
🚨 All agents inactive

Action: Pause system, check Render logs, investigate
```

---

## 🎭 Understanding Agent Behavior

### **Marcus (Engineering Manager)**

Embodies all 9 core values. Expect:
- Intellectual honesty: "I don't have data on that yet"
- Calm thinking: Never panics, always methodical
- Small ego: "You're right, let's use your approach"
- High ownership: "I'll handle this personally"

### **Developers (15 agents)**

- Report status daily
- Ask for help when blocked
- Give code review feedback
- Collaborate naturally
- Share knowledge

### **Mangoes (24 products)**

- Start INACTIVE (⚪)
- Activated after testing (🟢)
- Work on real user tasks
- Report back to Marcus

---

## 🚀 First Week Playbook

### **Day 1-2: Watch & Learn**

```
Goals:
- Marcus creates initial tasks
- Developers start building
- You monitor progress

Actions:
- /status every few hours
- Talk to Marcus once a day
- Watch dashboard for activity
```

### **Day 3-5: First Feedback**

```
Goals:
- Core framework taking shape
- First code reviews happening
- Give feedback to Marcus

Actions:
- "Marcus, what's our biggest risk?"
- Review test coverage
- Check team velocity
```

### **Day 6-7: First Mango**

```
Goals:
- First Mango (Data Entry) ready
- Run 100+ tests
- Activate if successful

Actions:
- "Marcus, is Mango Data Entry ready?"
- Review test results
- /activate mango_data_001 (if passes)
```

### **Day 8-14: Momentum**

```
Goals:
- 3-4 Mangoes ready
- Daily deployments to TEST
- First PRODUCTION deployment?

Actions:
- Daily check-ins with Marcus
- Approve tested components
- Monitor production health
```

---

## 🎯 Summary

### **Your Management Stack:**

1. **Telegram** (80% of time)
   - Quick commands
   - Talk to Marcus
   - Approvals
   - Mobile access

2. **Dashboard** (15% of time)
   - Deep analysis
   - Visual monitoring
   - Demos

3. **Render.com** (5% of time)
   - Check logs if issues
   - Restart services
   - Env var changes

### **Time Investment:**

- **Daily:** 5 minutes (Telegram check-ins)
- **Weekly:** 30 minutes (reviews, approvals)
- **Monthly:** 2 hours (deep analysis)

### **You Focus On:**

✅ Strategic decisions (priorities, goals)
✅ Production approvals (zero bugs)
✅ Feedback to Marcus (improve quality)
✅ Activating tested Mangoes

❌ NOT writing code
❌ NOT debugging issues
❌ NOT managing tasks
❌ NOT coordinating team

**Marcus and the dev team handle everything else!** 🎯

---

## 📞 Quick Reference

**Talk to Marcus:**
```
Just message your Telegram bot
```

**Check status:**
```
/status
```

**Approve deployment:**
```
/approve [id]
```

**Activate Mango:**
```
/activate [mango_id]
```

**Emergency pause:**
```
/pause
```

**View dashboard:**
```
https://mango-dashboard-xxxxx.onrender.com
```

**That's it!** You're now managing a 39-agent AI company. 🥭🚀

