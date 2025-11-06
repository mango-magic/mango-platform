"""
The Mangoes Management Dashboard
Beautiful interface to manage all AI agents, tasks, and workflows
"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio

app = FastAPI(title="The Mangoes Dashboard")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data directory
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
DATA_DIR.mkdir(exist_ok=True)

# ============================================================================
# DATA MODELS & HELPERS
# ============================================================================

def load_state() -> Dict:
    """Load current orchestrator state"""
    state_file = DATA_DIR / "state.json"
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return {
        "cycle_count": 0,
        "uptime_hours": 0,
        "agents_count": 39,
        "status": "initializing"
    }

def load_tasks() -> List[Dict]:
    """Load all tasks"""
    tasks_dir = DATA_DIR / "tasks"
    if not tasks_dir.exists():
        return []
    
    tasks = []
    for task_file in sorted(tasks_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        with open(task_file) as f:
            task = json.load(f)
            task['id'] = task_file.stem
            tasks.append(task)
    return tasks

def load_agents() -> List[Dict]:
    """Load all agents with their status"""
    # This would load from agent_definitions or a runtime state file
    # For now, returning a structured list
    agents = [
        {"id": "eng_manager_001", "name": "Marcus", "role": "Engineering Manager", "type": "developer", "status": "active", "emoji": "🎯"},
        {"id": "backend_001", "name": "Aria", "role": "Backend Engineer", "type": "developer", "status": "active", "emoji": "⚙️"},
        {"id": "backend_002", "name": "Kai", "role": "Backend Engineer", "type": "developer", "status": "active", "emoji": "⚙️"},
        {"id": "backend_003", "name": "Zara", "role": "LLM Engineer", "type": "developer", "status": "active", "emoji": "🤖"},
        {"id": "frontend_001", "name": "Luna", "role": "Frontend Engineer", "type": "developer", "status": "active", "emoji": "🎨"},
        {"id": "frontend_002", "name": "River", "role": "Frontend Engineer", "type": "developer", "status": "active", "emoji": "🎨"},
        {"id": "ml_001", "name": "Nova", "role": "ML Engineer", "type": "developer", "status": "active", "emoji": "🧠"},
        {"id": "ml_002", "name": "Sage", "role": "ML Engineer", "type": "developer", "status": "active", "emoji": "🧠"},
        {"id": "devops_001", "name": "Atlas", "role": "DevOps Engineer", "type": "developer", "status": "active", "emoji": "🚀"},
        {"id": "qa_001", "name": "Iris", "role": "QA Engineer", "type": "developer", "status": "active", "emoji": "🧪"},
        {"id": "pm_001", "name": "Jordan", "role": "Product Manager", "type": "developer", "status": "active", "emoji": "📋"},
        {"id": "designer_001", "name": "Mira", "role": "Designer", "type": "developer", "status": "active", "emoji": "✨"},
        {"id": "writer_001", "name": "Phoenix", "role": "Technical Writer", "type": "developer", "status": "active", "emoji": "📝"},
        {"id": "gtm_001", "name": "Blaze", "role": "GTM Lead", "type": "developer", "status": "active", "emoji": "📈"},
        {"id": "cs_001", "name": "Haven", "role": "Customer Success", "type": "developer", "status": "active", "emoji": "💬"},
        
        # 24 Mango Products
        {"id": "mango_data_001", "name": "Mango Data Entry", "role": "Data Entry Specialist", "type": "mango", "status": "active", "emoji": "📊"},
        {"id": "mango_ea_001", "name": "Mango EA", "role": "Executive Assistant", "type": "mango", "status": "active", "emoji": "💼"},
        {"id": "mango_sales_001", "name": "Mango Sales", "role": "Sales Representative", "type": "mango", "status": "active", "emoji": "💰"},
        {"id": "mango_support_001", "name": "Mango Support", "role": "Customer Support", "type": "mango", "status": "active", "emoji": "🎧"},
        {"id": "mango_marketing_001", "name": "Mango Marketing", "role": "Marketing Manager", "type": "mango", "status": "active", "emoji": "📱"},
        {"id": "mango_design_001", "name": "Mango Designer", "role": "Graphic Designer", "type": "mango", "status": "active", "emoji": "🎨"},
        {"id": "mango_recruiter_001", "name": "Mango Recruiter", "role": "Recruiter", "type": "mango", "status": "active", "emoji": "👥"},
        {"id": "mango_analyst_001", "name": "Mango Analyst", "role": "Business Analyst", "type": "mango", "status": "active", "emoji": "📊"},
        {"id": "mango_cfo_001", "name": "Mango CFO", "role": "Chief Financial Officer", "type": "mango", "status": "active", "emoji": "💵"},
        {"id": "mango_content_001", "name": "Mango Writer", "role": "Content Writer", "type": "mango", "status": "active", "emoji": "✍️"},
        {"id": "mango_legal_001", "name": "Mango Legal", "role": "Legal Assistant", "type": "mango", "status": "active", "emoji": "⚖️"},
        {"id": "mango_accountant_001", "name": "Mango Accountant", "role": "Accountant", "type": "mango", "status": "active", "emoji": "📚"},
        {"id": "mango_pm_001", "name": "Mango PM", "role": "Project Manager", "type": "mango", "status": "active", "emoji": "📋"},
        {"id": "mango_hr_001", "name": "Mango HR", "role": "HR Manager", "type": "mango", "status": "active", "emoji": "👔"},
        {"id": "mango_ops_001", "name": "Mango Operations", "role": "Operations Manager", "type": "mango", "status": "active", "emoji": "⚙️"},
        {"id": "mango_ba_001", "name": "Mango Business", "role": "Business Analyst", "type": "mango", "status": "active", "emoji": "📈"},
        {"id": "mango_social_001", "name": "Mango Social", "role": "Social Media Manager", "type": "mango", "status": "active", "emoji": "📱"},
        {"id": "mango_copy_001", "name": "Mango Copywriter", "role": "Copywriter", "type": "mango", "status": "active", "emoji": "✏️"},
        {"id": "mango_video_001", "name": "Mango Video", "role": "Video Editor", "type": "mango", "status": "active", "emoji": "🎬"},
        {"id": "mango_research_001", "name": "Mango Research", "role": "Researcher", "type": "mango", "status": "active", "emoji": "🔬"},
        {"id": "mango_translator_001", "name": "Mango Translator", "role": "Translator", "type": "mango", "status": "active", "emoji": "🌐"},
        {"id": "mango_transcribe_001", "name": "Mango Transcriber", "role": "Transcriptionist", "type": "mango", "status": "active", "emoji": "🎤"},
        {"id": "mango_receptionist_001", "name": "Mango Reception", "role": "Virtual Receptionist", "type": "mango", "status": "active", "emoji": "📞"},
        {"id": "mango_booking_001", "name": "Mango Booking", "role": "Booking Coordinator", "type": "mango", "status": "active", "emoji": "📅"},
    ]
    return agents

def get_analytics_data():
    """Generate analytics data for charts"""
    # In production, this would query actual metrics
    # For now, generate sample data
    tasks = load_tasks()
    state = load_state()
    
    # Last 30 days
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%b %d") for i in range(29, -1, -1)]
    
    return {
        "dates": dates,
        "tasks_completed": [12, 15, 18, 22, 25, 30, 28, 35, 40, 38, 42, 45, 50, 48, 52, 55, 58, 60, 62, 65, 68, 70, 72, 75, 78, 80, 82, 85, 88, 90],
        "agent_activity": [15, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 39, 39, 39, 39, 39, 39, 39, 39, 39, 39, 39, 39, 39, 39, 39, 39, 39, 39],
        "success_rate": [85, 87, 88, 90, 89, 91, 92, 93, 94, 93, 95, 96, 94, 95, 96, 97, 96, 97, 98, 97, 98, 99, 98, 97, 98, 99, 98, 99, 99, 100]
    }

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get main dashboard statistics"""
    state = load_state()
    tasks = load_tasks()
    agents = load_agents()
    
    completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
    pending_tasks = len([t for t in tasks if t.get('status') == 'pending'])
    in_progress_tasks = len([t for t in tasks if t.get('status') == 'in_progress'])
    
    active_agents = len([a for a in agents if a.get('status') == 'active'])
    
    return {
        "cycle_count": state.get('cycle_count', 0),
        "total_tasks": len(tasks),
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "in_progress_tasks": in_progress_tasks,
        "completion_rate": (completed_tasks / len(tasks) * 100) if len(tasks) > 0 else 0,
        "active_agents": active_agents,
        "total_agents": len(agents),
        "uptime_days": state.get('uptime_hours', 0) / 24,
        "uptime_hours": state.get('uptime_hours', 0),
        "status": state.get('status', 'running')
    }

@app.get("/api/agents")
async def get_agents(type: Optional[str] = None):
    """Get all agents, optionally filtered by type"""
    agents = load_agents()
    if type:
        agents = [a for a in agents if a['type'] == type]
    return agents

@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    agents = load_agents()
    agent = next((a for a in agents if a['id'] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@app.get("/api/tasks")
async def get_tasks(status: Optional[str] = None, limit: int = 100):
    """Get all tasks, optionally filtered by status"""
    tasks = load_tasks()[:limit]
    if status:
        tasks = [t for t in tasks if t.get('status') == status]
    return tasks

@app.post("/api/tasks/{task_id}/approve")
async def approve_task(task_id: str):
    """Approve a pending task"""
    tasks_dir = DATA_DIR / "tasks"
    task_file = tasks_dir / f"{task_id}.json"
    
    if not task_file.exists():
        raise HTTPException(status_code=404, detail="Task not found")
    
    with open(task_file) as f:
        task = json.load(f)
    
    task['status'] = 'approved'
    task['approved_at'] = datetime.now().isoformat()
    
    with open(task_file, 'w') as f:
        json.dump(task, f, indent=2)
    
    return {"message": "Task approved", "task": task}

@app.post("/api/tasks/{task_id}/reject")
async def reject_task(task_id: str, reason: str = ""):
    """Reject a pending task"""
    tasks_dir = DATA_DIR / "tasks"
    task_file = tasks_dir / f"{task_id}.json"
    
    if not task_file.exists():
        raise HTTPException(status_code=404, detail="Task not found")
    
    with open(task_file) as f:
        task = json.load(f)
    
    task['status'] = 'rejected'
    task['rejected_at'] = datetime.now().isoformat()
    task['rejection_reason'] = reason
    
    with open(task_file, 'w') as f:
        json.dump(task, f, indent=2)
    
    return {"message": "Task rejected", "task": task}

@app.get("/api/analytics")
async def get_analytics():
    """Get analytics data for charts"""
    return get_analytics_data()

@app.get("/api/activity")
async def get_recent_activity(limit: int = 20):
    """Get recent activity feed"""
    tasks = load_tasks()[:limit]
    
    activity = []
    for task in tasks:
        activity.append({
            "id": task.get('id'),
            "type": "task",
            "title": task.get('title', 'Untitled Task'),
            "agent": task.get('assigned_to', 'Unknown'),
            "status": task.get('status', 'unknown'),
            "timestamp": task.get('created_at', datetime.now().isoformat()),
            "message": task.get('description', '')[:100]
        })
    
    return activity

@app.get("/api/evaluations")
async def get_evaluations(limit: int = 10):
    """Get self-evaluation reports"""
    eval_dir = DATA_DIR / "evaluations"
    if not eval_dir.exists():
        return []
    
    evals = []
    for eval_file in sorted(eval_dir.glob("eval_*.json"), reverse=True)[:limit]:
        with open(eval_file) as f:
            eval_data = json.load(f)
            evals.append({
                "id": eval_file.stem,
                "timestamp": eval_data.get('timestamp'),
                "metrics": eval_data.get('metrics'),
                "evaluation": eval_data.get('evaluation'),
                "uptime_hours": eval_data.get('uptime_hours'),
                "cycle_count": eval_data.get('cycle_count')
            })
    
    return evals

@app.get("/api/evaluations/latest")
async def get_latest_evaluation():
    """Get the most recent self-evaluation"""
    eval_dir = DATA_DIR / "evaluations"
    if not eval_dir.exists():
        return {"error": "No evaluations found"}
    
    eval_files = sorted(eval_dir.glob("eval_*.json"), reverse=True)
    if not eval_files:
        return {"error": "No evaluations found"}
    
    with open(eval_files[0]) as f:
        return json.load(f)

@app.get("/api/improvements")
async def get_improvement_cycles(limit: int = 10):
    """Get self-improvement cycle history"""
    improvements_dir = DATA_DIR / "improvements"
    if not improvements_dir.exists():
        return []
    
    cycles = []
    for cycle_file in sorted(improvements_dir.glob("cycle_*.json"), reverse=True)[:limit]:
        with open(cycle_file) as f:
            cycle_data = json.load(f)
            cycles.append({
                "cycle_id": cycle_data.get('cycle_id'),
                "timestamp": cycle_data.get('timestamp'),
                "status": cycle_data.get('status'),
                "improvements_count": len(cycle_data.get('improvements_generated', {}).get('improvements', [])),
                "agent_approval_rate": cycle_data.get('test_analysis', {}).get('approval_rate', 0),
                "deployed": cycle_data.get('status') == 'deployed'
            })
    
    return cycles

@app.get("/api/improvements/{cycle_id}")
async def get_improvement_cycle(cycle_id: str):
    """Get detailed information about a specific improvement cycle"""
    cycle_file = DATA_DIR / "improvements" / f"cycle_{cycle_id}.json"
    if not cycle_file.exists():
        raise HTTPException(status_code=404, detail="Improvement cycle not found")
    
    with open(cycle_file) as f:
        return json.load(f)

@app.get("/")
async def dashboard():
    """Serve the main dashboard HTML"""
    html_file = Path(__file__).parent / "index.html"
    if html_file.exists():
        with open(html_file) as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Dashboard HTML not found</h1>")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

