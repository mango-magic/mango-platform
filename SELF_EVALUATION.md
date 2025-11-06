# 🔍 Self-Evaluation System

## Overview

The Mangoes AI Team now includes a **self-evaluation system** that automatically analyzes team performance every hour against world-class standards. This ensures continuous improvement and accountability.

---

## How It Works

### 1. Automatic Evaluation (Every Hour)
- **Frequency:** Every 60 minutes
- **Trigger:** Automatic during the orchestrator's main loop
- **Duration:** ~30 seconds per evaluation
- **Storage:** All evaluations saved to `data/evaluations/`

### 2. What Gets Evaluated

The system analyzes:

#### Performance Metrics
- ✅ Total tasks completed
- ✅ Tasks in progress
- ✅ Failed tasks
- ✅ Tasks per hour velocity
- ✅ Cycles per hour
- ✅ Uptime and consistency

#### Qualitative Analysis
The AI evaluator examines recent completed tasks and scores the team across **5 key dimensions:**

**1. Strategic Focus (30 points)**
- Are tasks aligned with high-impact goals?
- Is there a clear product vision?
- Building features that matter?
- Balance between innovation and maintenance?

**2. Execution Quality (25 points)**
- Task completion rate and velocity
- Technical excellence
- Testing and validation
- Documentation quality

**3. Team Collaboration (20 points)**
- Communication between agents
- Knowledge sharing
- Coordinated efforts
- Cross-functional work

**4. Innovation & Learning (15 points)**
- Exploring new technologies
- Learning from failures
- Adapting strategies
- Creative problem-solving

**5. Operational Excellence (10 points)**
- Consistent delivery rhythm
- Proper prioritization
- Resource utilization
- System reliability

### 3. Evaluation Output

Each evaluation provides:

✅ **Overall Score** out of 100  
✅ **Top 3 Strengths** - What's working well  
✅ **Top 3 Weaknesses** - Critical issues to address  
✅ **3 Action Items** - Immediate improvements to make  
✅ **Ambitious Goal** - Target for next evaluation  

---

## Where to View Evaluations

### Option 1: Management Dashboard (Recommended)
1. Go to: https://mangoes-dashboard.onrender.com
2. Click **"Self-Evaluations"** in the sidebar
3. View:
   - Latest evaluation with full details
   - Historical performance trends
   - Metrics over time

### Option 2: Raw Files
- Location: `data/evaluations/`
- Format: JSON files named `eval_YYYYMMDD_HHMMSS.json`
- Each file contains:
  - Timestamp
  - Performance metrics
  - Full evaluation text
  - Cycle count and uptime

### Option 3: Telegram Notifications
- Summary sent to Telegram after each evaluation
- Includes key metrics and preview
- Full report link provided

---

## Evaluation Schedule

| Time | Action |
|------|--------|
| Every hour | Full self-evaluation |
| Immediate | Results saved to disk |
| Immediate | Telegram notification sent |
| Ongoing | Available in dashboard |

---

## Example Evaluation Output

```
🔍 Self-Evaluation Complete

📊 Metrics:
• Tasks: 45/120 completed
• Velocity: 5.2 tasks/hour
• Uptime: 8.7h

📝 Evaluation Summary:

OVERALL SCORE: 67/100

STRATEGIC FOCUS: 18/30
The team is working on various features but lacks a clear 
prioritization framework. Many tasks are maintenance-focused 
rather than high-impact innovations.

EXECUTION QUALITY: 22/25
Strong technical execution. Tasks are completed with good code 
quality and proper testing.

TEAM COLLABORATION: 14/20
Communication between agents is functional but could be more 
proactive. Limited knowledge sharing.

[... full report continues ...]

TOP 3 STRENGTHS:
1. Consistent delivery rhythm
2. High code quality
3. Good testing coverage

TOP 3 WEAKNESSES:
1. Lack of strategic focus
2. Limited innovation
3. Reactive rather than proactive

IMMEDIATE ACTION ITEMS:
1. Define clear product priorities
2. Allocate 20% time to innovation
3. Implement daily standups

AMBITIOUS GOAL:
Ship one major feature that demonstrates world-class innovation 
by next evaluation.
```

---

## Customizing Evaluations

### Adjust Evaluation Frequency

Edit `core/orchestrator.py`:

```python
# Change from 1.0 (hourly) to your preference
if time_since_eval >= 1.0:  # Every hour
    await self._self_evaluate()

# Examples:
# 0.5 = Every 30 minutes
# 2.0 = Every 2 hours
# 24.0 = Once per day
```

### Modify Evaluation Criteria

Edit the `evaluation_prompt` in `_self_evaluate()` method to:
- Add new scoring dimensions
- Change point allocations
- Adjust evaluation strictness
- Focus on specific aspects

### Change Notification Frequency

By default, notifications are sent after every evaluation. To change:

```python
# Send only if score drops below threshold
if score < 70:
    await self.telegram.send_message(...)
```

---

## Interpreting Scores

| Score | Performance Level | Action Required |
|-------|-------------------|-----------------|
| 90-100 | World-class | Maintain momentum |
| 75-89 | Strong | Minor optimizations |
| 60-74 | Adequate | Address weaknesses |
| 45-59 | Concerning | Major improvements needed |
| <45 | Critical | Urgent intervention |

---

## Benefits

### 1. Continuous Improvement
- Identifies issues before they become problems
- Tracks performance trends over time
- Provides objective feedback

### 2. Accountability
- Team holds itself to high standards
- Clear metrics for success
- Documented progress

### 3. Strategic Alignment
- Ensures work aligns with goals
- Highlights misallocated effort
- Guides prioritization

### 4. Learning & Adaptation
- Learn from past evaluations
- Adapt strategies based on feedback
- Build institutional knowledge

---

## Troubleshooting

### No Evaluations Appearing?

**Check:**
1. Has 1 hour passed since startup?
2. Is Gemini API key valid?
3. Check logs for errors: `grep "Self-evaluation" logs/orchestrator.log`
4. Verify `data/evaluations/` directory exists

### Evaluations Too Harsh?

This is intentional! World-class teams don't accept mediocrity. Use the criticism to improve.

**But if needed:**
- Adjust the system prompt to be more encouraging
- Focus on specific dimensions you care about
- Change evaluation frequency to reduce pressure

### Want More Detail?

Add additional metrics to track:
- Code coverage percentages
- Bug counts
- Customer satisfaction
- Response times
- Innovation metrics

---

## API Endpoints

### Get Latest Evaluation
```bash
GET /api/evaluations/latest
```

### Get Evaluation History
```bash
GET /api/evaluations?limit=10
```

### Response Format
```json
{
  "timestamp": "2025-11-06T11:30:00Z",
  "uptime_hours": 8.5,
  "cycle_count": 255,
  "metrics": {
    "total_tasks": 120,
    "completed": 45,
    "in_progress": 12,
    "failed": 2,
    "tasks_per_hour": 5.3,
    "cycles_per_hour": 30.0
  },
  "evaluation": "OVERALL SCORE: 72/100...",
  "recent_tasks_analyzed": 20
}
```

---

## Future Enhancements

Potential improvements:
- [ ] Trend analysis across evaluations
- [ ] Automated action item tracking
- [ ] Performance prediction
- [ ] Comparison to industry benchmarks
- [ ] A/B testing of strategies
- [ ] Integration with external metrics
- [ ] Custom evaluation templates
- [ ] Slack/Discord integration

---

## Summary

✅ **Automatic:** Runs every hour without intervention  
✅ **Comprehensive:** Evaluates 5 key dimensions  
✅ **Actionable:** Provides specific improvement suggestions  
✅ **Tracked:** Full history stored and accessible  
✅ **Visible:** Available in dashboard and notifications  

**This system ensures your AI team continuously strives for world-class performance!** 🥭

