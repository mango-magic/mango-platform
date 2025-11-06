# ⚡ Cursor AI Setup - 2 Minute Guide

## What This Gives You

**Use Cursor AI (this tool!) to:**
- Analyze your AI team's performance
- Debug issues with AI assistance
- Optimize infrastructure based on metrics
- Query logs in natural language
- Get predictive insights

---

## 🚀 Setup (2 Minutes)

### Step 1: Create MCP Config File

**On Mac/Linux:**
```bash
mkdir -p ~/.cursor
nano ~/.cursor/mcp.json
```

**On Windows:**
```bash
mkdir %USERPROFILE%\.cursor
notepad %USERPROFILE%\.cursor\mcp.json
```

### Step 2: Paste This Configuration

```json
{
  "mcpServers": {
    "render": {
      "url": "https://mcp.render.com/mcp",
      "headers": {
        "Authorization": "Bearer rnd_CzMjLrxGNIiz258bWrU4Pe19E0E0"
      }
    }
  }
}
```

Save and close the file.

### Step 3: Restart Cursor

Close Cursor completely and reopen it.

### Step 4: Set Your Workspace

In Cursor's AI chat (Cmd/Ctrl + L), type:

```
Set my Render workspace to The Mangoes
```

Cursor will confirm:
```
✅ Render workspace set to "The Mangoes"
```

### Step 5: Test It!

Try these prompts:

```
List my Render services
```

```
Show me the status of mango-orchestrator
```

```
What errors occurred in the last hour?
```

**If you get responses, you're all set!** 🎉

---

## ✅ Quick Test Commands

Copy-paste these to verify everything works:

### Test 1: List Services
```
List all services in my Render workspace
```

**Expected:** List of your services (mango-orchestrator, mango-dashboard)

### Test 2: Check Logs
```
Pull the most recent 10 logs from mango-orchestrator
```

**Expected:** Recent log entries from your orchestrator

### Test 3: Get Metrics
```
What's the CPU usage for mango-orchestrator today?
```

**Expected:** CPU usage stats

### Test 4: Deploy History
```
Show me the deploy history for mango-orchestrator
```

**Expected:** List of recent deploys

---

## 🎯 Your First Real Analysis

After your services are running, try this:

```
Analyze my mango-orchestrator:
1. Current health status
2. Recent errors (if any)
3. Performance metrics (CPU, memory)
4. Any recommendations for optimization
```

Cursor will:
- Query Render for all relevant data
- Analyze the metrics
- Identify issues
- Suggest improvements

All in one response!

---

## 🔧 Troubleshooting

### "I don't see the Render MCP server"

**Fix:**
1. Check `~/.cursor/mcp.json` exists and has correct JSON
2. Restart Cursor completely (Cmd/Ctrl + Q, then reopen)
3. Look for MCP icon in bottom status bar
4. Try setting workspace again

### "Authorization failed"

**Fix:**
1. Verify API key in `~/.cursor/mcp.json` matches:
   ```
   rnd_CzMjLrxGNIiz258bWrU4Pe19E0E0
   ```
2. Ensure no extra spaces or quotes
3. Restart Cursor

### "Workspace not found"

**Fix:**
1. Check exact workspace name in Render Dashboard
2. Try: "List my Render workspaces"
3. Set to exact name shown

### "Command not working"

**Fix:**
Try more specific:
```
❌ "Show logs"
✅ "Show me the last 20 logs from mango-orchestrator service"

❌ "Check status"  
✅ "What's the current health status of mango-orchestrator?"
```

---

## 💡 Pro Tips

### 1. Be Specific with Service Names

```
✅ "Pull logs from mango-orchestrator"
❌ "Pull logs from orchestrator"
```

### 2. Combine Multiple Requests

```
"For mango-orchestrator:
1. Show recent errors
2. Check CPU usage
3. List recent deploys
4. Recommend optimizations"
```

### 3. Follow-Up Questions

```
You: "Show me today's errors"
[Cursor shows errors]

You: "Focus on the rate limit ones"
[Cursor filters]

You: "When did these start?"
[Cursor analyzes timeline]
```

### 4. Ask for Code Fixes

```
You: "I see rate limit errors. How do I fix this?"
[Cursor explains and writes code]

You: "Apply that fix to core/orchestrator.py"
[Cursor makes the changes]
```

---

## 🎯 Common Use Cases

### Morning Check-In
```
"What happened with my Render services overnight?"
```

### Weekly Review
```
"Analyze performance for mango-orchestrator over the last 7 days"
```

### Debug Issue
```
"My dashboard isn't loading. Investigate why."
```

### Optimize Performance
```
"Based on current metrics, how can I optimize my services?"
```

### Before Deployment
```
"Is my staging environment healthy? Should I deploy to production?"
```

---

## 🚀 Next Steps

1. ✅ **Setup complete** - You can now query Render from Cursor
2. 📚 **Read full guide** - See `CURSOR_AI_MANAGEMENT.md` for advanced usage
3. 🎯 **Start analyzing** - Try the example prompts above
4. 💬 **Combine with Telegram** - Use both for complete management

---

## 📊 Quick Reference

**Your Config File Location:**
- Mac/Linux: `~/.cursor/mcp.json`
- Windows: `%USERPROFILE%\.cursor\mcp.json`

**Your API Key:**
```
rnd_CzMjLrxGNIiz258bWrU4Pe19E0E0
```

**Your Workspace:**
```
The Mangoes
```

**Test Command:**
```
List my Render services
```

---

## ✅ You're Ready!

Cursor AI + Render MCP = **Intelligent infrastructure management**

Start with simple queries, then explore advanced analysis!

For comprehensive examples and strategies, see:
→ `CURSOR_AI_MANAGEMENT.md`

