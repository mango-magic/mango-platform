# 🥭 The Mangoes - Management Hub

## Quick Access Links

### 🎯 Main Dashboard
**URL:** https://dashboard.render.com  
The central hub for all your services.

---

## Your Services

### 1. Orchestrator (Main AI Team)
- **Live URL:** https://mango-platform.onrender.com
- **Dashboard:** https://dashboard.render.com/web/srv-d45vrkqdbo4c7386mfug
- **Health Check:** https://mango-platform.onrender.com/health
- **Status:** https://mango-platform.onrender.com/status

**What it does:** Runs your 39 AI agents autonomously 24/7

### 2. Mangoes Dashboard (Management UI)  
- **Live URL:** https://mangoes-dashboard.onrender.com *(deploying)*
- **Dashboard:** https://dashboard.render.com/web/srv-d46886a4d50c73cfa930
- **Status:** Building

**What it does:** Beautiful UI to manage agents, tasks, and approvals

### 3. Basic Monitor  
- **Live URL:** https://mango-platform-1.onrender.com
- **Dashboard:** https://dashboard.render.com/web/srv-d45vseq4d50c73ca2ej0

**What it does:** Simple real-time monitoring

---

## How to Manage Everything

### View All Services
1. Go to https://dashboard.render.com
2. You'll see all 3 services listed
3. Click any service to open its control panel

### View Logs
1. Open a service dashboard
2. Click **"Logs"** tab
3. See real-time logs, errors, and activity
4. Filter by type: app logs, build logs, request logs

### View Deployments
1. Open a service dashboard
2. Click **"Events"** tab
3. See all deployment history
4. Each deployment shows:
   - Commit message
   - Status (live, building, failed)
   - Duration
   - Logs

### Manual Actions

**Deploy Latest Code:**
1. Open service dashboard
2. Click **"Manual Deploy"** button
3. Confirm

**Restart Service:**
1. Open service dashboard
2. Go to **"Events"** tab
3. Click on latest deployment
4. Click **"Restart"** button

**View Environment Variables:**
1. Open service dashboard
2. Click **"Environment"** tab
3. See all env vars
4. Add/edit/delete variables

**Suspend Service:**
1. Open service dashboard
2. Go to **"Settings"** tab
3. Click **"Suspend"**
4. Service stops running (saves money)

**Resume Service:**
1. Open service dashboard
2. Click **"Resume"** button

---

## Monitoring & Metrics

### View Performance Metrics
1. Open service dashboard
2. Click **"Metrics"** tab
3. See:
   - CPU usage
   - Memory usage
   - Request counts
   - Response times
   - Bandwidth

### Set Up Alerts
1. Open service dashboard
2. Go to **"Settings"**
3. Scroll to **"Notifications"**
4. Enable email/Slack/Discord alerts for:
   - Deploy failures
   - Service crashes
   - High CPU/memory

---

## Common Tasks

### Check if Everything is Working
```bash
# Test Orchestrator health
curl https://mango-platform.onrender.com/health

# Should return:
{
  "status": "running",
  "service": "mango-orchestrator",
  "agents": 39
}
```

### View Agent Status
```bash
curl https://mango-platform.onrender.com/status

# Returns current state of all agents
```

### Force New Deployment
1. Go to https://dashboard.render.com/web/srv-d45vrkqdbo4c7386mfug
2. Click **"Manual Deploy"**
3. Select **"Deploy latest commit"**
4. Click **"Deploy"**

### Rollback to Previous Version
1. Go to service dashboard
2. Click **"Events"** tab
3. Find a previous successful deployment
4. Click **"Rollback to this deploy"**

---

## Troubleshooting

### Service Shows "Failed"
1. Click on the service
2. Go to **"Logs"** tab
3. Look for ERROR messages
4. Common fixes:
   - Check environment variables
   - Verify build command
   - Check dependencies

### Service is Slow
1. Go to **"Metrics"** tab
2. Check CPU/Memory usage
3. If maxed out:
   - Upgrade to larger plan
   - Or optimize code

### Can't Access Service
1. Check if service is **"Live"**
2. Check if it's **"Suspended"**
3. Try restarting it
4. Check logs for errors

---

## Cost Management

### Current Setup
- **Orchestrator:** Starter plan ($7/month)
- **Dashboard:** Starter plan ($7/month) 
- **Monitor:** Starter plan ($7/month)
- **Total:** ~$21/month

### Free Options
- All services have free tiers
- Free tier limitations:
  - 750 hours/month
  - Spins down after 15 min inactivity
  - Slower cold starts

### Upgrade When Needed
1. Go to service dashboard
2. Click **"Settings"**
3. Scroll to **"Instance Type"**
4. Choose plan:
   - **Starter** ($7/mo): 0.5 GB RAM
   - **Standard** ($25/mo): 2 GB RAM
   - **Pro** ($85/mo): 4 GB RAM

---

## Quick Commands

### SSH into Service
```bash
# Get SSH address from service dashboard
ssh srv-XXXXX@ssh.oregon.render.com
```

### View Recent Logs (Terminal)
```bash
# Install Render CLI
brew tap render-oss/render
brew install render

# Login
render login

# View logs
render logs -s srv-d45vrkqdbo4c7386mfug
```

---

## Mobile Management

### Render Mobile App
- **iOS:** https://apps.apple.com/app/render/id1563621206
- **Android:** https://play.google.com/store/apps/details?id=com.render.mobile

**Features:**
- View all services
- See logs
- Deploy services
- Get alerts
- Manage settings

---

## Support Resources

- **Render Docs:** https://render.com/docs
- **Status Page:** https://status.render.com
- **Community:** https://community.render.com
- **Support:** support@render.com

---

## Summary: What You Can Do

✅ **View Everything:** https://dashboard.render.com  
✅ **Check Health:** https://mango-platform.onrender.com/health  
✅ **View Logs:** Service Dashboard → Logs tab  
✅ **Deploy Updates:** Service Dashboard → Manual Deploy  
✅ **Monitor Metrics:** Service Dashboard → Metrics tab  
✅ **Get Alerts:** Service Dashboard → Settings → Notifications  
✅ **Mobile App:** Download from App Store/Play Store

---

**Last Updated:** November 6, 2025  
**Services:** 3 active  
**Status:** Orchestrator live, Dashboard deploying  
**Next Steps:** Wait for auto-deploy or manually trigger deployment

