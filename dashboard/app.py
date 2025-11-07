"""
The Mangoes Management Dashboard
Beautiful interface to manage all AI agents, tasks, and workflows
"""

from fastapi import FastAPI, WebSocket, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
import httpx

app = FastAPI(title="The Mangoes Dashboard")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Orchestrator URL - defaults to production URL
ORCHESTRATOR_URL = os.getenv('ORCHESTRATOR_URL', 'https://mango-platform.onrender.com')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def fetch_from_orchestrator(endpoint: str, params: Optional[Dict] = None):
    """Fetch data from orchestrator API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{ORCHESTRATOR_URL}{endpoint}"
            print(f"🔍 Fetching from orchestrator: {url} with params: {params}")
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Got response from {endpoint}: {len(data) if isinstance(data, list) else 'object'}")
            return data
    except httpx.HTTPError as e:
        print(f"❌ HTTP Error fetching from orchestrator {endpoint}: {e}")
        print(f"   URL was: {ORCHESTRATOR_URL}{endpoint}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error fetching from orchestrator {endpoint}: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get main dashboard statistics"""
    data = await fetch_from_orchestrator("/api/dashboard/stats")
    if data:
        return data
    # Fallback if orchestrator unavailable
    return {
        "cycle_count": 0,
        "total_tasks": 0,
        "completed_tasks": 0,
        "pending_tasks": 0,
        "in_progress_tasks": 0,
        "completion_rate": 0,
        "active_agents": 39,
        "total_agents": 39,
        "uptime_days": 0,
        "uptime_hours": 0,
        "status": "connecting"
    }

@app.get("/api/agents")
async def get_agents(type: Optional[str] = None):
    """Get all agents, optionally filtered by type"""
    params = {"type": type} if type else None
    data = await fetch_from_orchestrator("/api/agents", params)
    if data is not None:
        return data
    return []

@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    data = await fetch_from_orchestrator(f"/api/agents/{agent_id}")
    if data:
        return data
    raise HTTPException(status_code=404, detail="Agent not found")

@app.get("/api/tasks")
async def get_tasks(status: Optional[str] = None, limit: int = 100):
    """Get all tasks, optionally filtered by status"""
    params = {}
    if status:
        params["status"] = status
    if limit:
        params["limit"] = limit
    
    print(f"📋 Fetching tasks with status={status}, limit={limit}")
    data = await fetch_from_orchestrator("/api/tasks", params)
    
    if data is not None:
        print(f"✅ Returning {len(data)} tasks")
        return data
    
    print("⚠️ No data from orchestrator, returning empty list")
    return []

@app.post("/api/tasks/{task_id}/approve")
async def approve_task(task_id: str):
    """Approve a pending task"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{ORCHESTRATOR_URL}/api/tasks/{task_id}/approve"
            response = await client.post(url)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving task: {str(e)}")

@app.post("/api/tasks/{task_id}/reject")
async def reject_task(task_id: str, reason: str = ""):
    """Reject a pending task"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{ORCHESTRATOR_URL}/api/tasks/{task_id}/reject"
            response = await client.post(url, params={"reason": reason} if reason else None)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rejecting task: {str(e)}")

@app.get("/api/analytics")
async def get_analytics():
    """Get analytics data for charts"""
    data = await fetch_from_orchestrator("/api/analytics")
    if data:
        return data
    # Fallback empty data
    return {
        "dates": [],
        "tasks_completed": [],
        "agent_activity": [],
        "success_rate": []
    }

@app.get("/api/activity/live")
async def get_live_activity():
    """Get current agent activity (what each agent is working on right now)"""
    data = await fetch_from_orchestrator("/api/activity/live")
    if data:
        return data
    return {"agents_working": []}

@app.get("/api/activity")
async def get_recent_activity(limit: int = 20):
    """Get recent activity feed"""
    params = {"limit": limit}
    data = await fetch_from_orchestrator("/api/activity", params)
    if data is not None:
        return data
    return []

@app.get("/api/evaluations")
async def get_evaluations(limit: int = 10):
    """Get self-evaluation reports"""
    params = {"limit": limit}
    data = await fetch_from_orchestrator("/api/evaluations", params)
    if data is not None:
        return data
    return []

@app.get("/api/evaluations/latest")
async def get_latest_evaluation():
    """Get the most recent self-evaluation"""
    data = await fetch_from_orchestrator("/api/evaluations/latest")
    if data:
        return data
    return {"error": "No evaluations found"}


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

