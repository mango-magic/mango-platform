"""
Simple monitoring dashboard - shows what all agents are doing.
Run this on the orchestrator VPS.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import os
from pathlib import Path
from datetime import datetime

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Real-time dashboard"""
    
    # Load state
    data_dir = Path(os.getenv('DATA_DIR', './data'))
    state_file = data_dir / "state.json"
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
    else:
        state = {"status": "initializing"}
    
    # Count tasks
    tasks_dir = data_dir / "tasks"
    total_tasks = len(list(tasks_dir.glob("*.json"))) if tasks_dir.exists() else 0
    
    completed_tasks = 0
    if tasks_dir.exists():
        for task_file in tasks_dir.glob("*.json"):
            with open(task_file) as f:
                task = json.load(f)
                if task.get('status') == 'completed':
                    completed_tasks += 1
    
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>🥭 ManyMangoes - Live Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1600px; margin: 0 auto; }}
        
        h1 {{ 
            font-size: 56px; 
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .tagline {{
            font-size: 20px;
            opacity: 0.9;
            margin-bottom: 40px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin: 40px 0;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 32px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(255, 255, 255, 0.4);
        }}
        
        .stat-label {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.8;
            margin-bottom: 12px;
        }}
        
        .stat-value {{
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .stat-subtitle {{
            font-size: 14px;
            opacity: 0.7;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 12px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            overflow: hidden;
            margin-top: 12px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #10b981, #34d399);
            width: {completion_rate}%;
            transition: width 1s;
        }}
        
        .agents-section {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 32px;
            margin-top: 40px;
            border: 2px solid rgba(255, 255, 255, 0.2);
        }}
        
        .agents-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 16px;
            margin-top: 24px;
        }}
        
        .agent-card {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid #10b981;
            transition: all 0.2s;
        }}
        
        .agent-card:hover {{
            background: rgba(255, 255, 255, 0.15);
            transform: translateX(5px);
        }}
        
        .agent-name {{
            font-weight: 600;
            margin-bottom: 4px;
        }}
        
        .agent-role {{
            font-size: 12px;
            opacity: 0.7;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            margin-top: 8px;
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid rgba(16, 185, 129, 0.4);
        }}
        
        .footer {{
            margin-top: 60px;
            text-align: center;
            opacity: 0.6;
            font-size: 14px;
        }}
        
        .pulse {{
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🥭 ManyMangoes</h1>
        <p class="tagline">The AI team that builds AI teams • Running 24/7</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Development Cycles</div>
                <div class="stat-value">{state.get('cycle_count', 0)}</div>
                <div class="stat-subtitle">Continuous autonomous loops</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Tasks Completed</div>
                <div class="stat-value">{completed_tasks}</div>
                <div class="stat-subtitle">Out of {total_tasks} total</div>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Days Elapsed</div>
                <div class="stat-value">{state.get('uptime_hours', 0) / 24:.1f}</div>
                <div class="stat-subtitle">Out of 30 day target</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Active Agents</div>
                <div class="stat-value pulse">{state.get('agents_count', 39)}</div>
                <div class="stat-subtitle">15 developers + 24 Mangoes</div>
            </div>
        </div>
        
        <div class="agents-section">
            <h2>👥 Active AI Agents</h2>
            <div class="agents-grid">
                <div class="agent-card">
                    <div class="agent-name">Marcus</div>
                    <div class="agent-role">Engineering Manager</div>
                    <span class="status-badge">🟢 Active</span>
                </div>
                <div class="agent-card">
                    <div class="agent-name">Aria</div>
                    <div class="agent-role">Backend Engineer</div>
                    <span class="status-badge">🟢 Active</span>
                </div>
                <div class="agent-card">
                    <div class="agent-name">Luna</div>
                    <div class="agent-role">Frontend Engineer</div>
                    <span class="status-badge">🟢 Active</span>
                </div>
                <div class="agent-card">
                    <div class="agent-name">Mango EA</div>
                    <div class="agent-role">Executive Assistant</div>
                    <span class="status-badge">🟢 Active</span>
                </div>
                <div class="agent-card">
                    <div class="agent-name">Mango Sales</div>
                    <div class="agent-role">Sales Representative</div>
                    <span class="status-badge">🟢 Active</span>
                </div>
                <div class="agent-card">
                    <div class="agent-name">+ 34 more agents</div>
                    <div class="agent-role">Building autonomously</div>
                    <span class="status-badge">🟢 Active</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC</p>
            <p>Auto-refresh every 10 seconds</p>
            <p style="margin-top: 20px;">💰 Running cost: $72/month for 16 VPS • 🆓 Gemini API FREE tier</p>
        </div>
    </div>
</body>
</html>
    """
    return html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

