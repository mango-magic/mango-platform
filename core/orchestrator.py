"""
Autonomous Orchestrator - The brain that never stops.
Coordinates all 39 agents (15 developers + 24 Mangoes) continuously.
"""

import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import aiohttp
import google.generativeai as genai

# Setup logging
log_dir = Path(os.getenv('LOG_DIR', './logs'))
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Orchestrator')

class GeminiRateLimiter:
    """Stay within FREE tier: 1500 req/day, 1M tokens/day"""
    
    def __init__(self):
        self.requests_today = 0
        self.tokens_today = 0
        self.last_reset = datetime.now().date()
        self.MAX_REQUESTS = 1400  # Buffer
        self.MAX_TOKENS = 900000  # Buffer
        
    def reset_if_new_day(self):
        today = datetime.now().date()
        if today != self.last_reset:
            logger.info("🔄 Daily rate limits reset")
            self.requests_today = 0
            self.tokens_today = 0
            self.last_reset = today
    
    def can_make_request(self, estimated_tokens: int = 3000) -> bool:
        self.reset_if_new_day()
        return (self.requests_today < self.MAX_REQUESTS and 
                self.tokens_today + estimated_tokens < self.MAX_TOKENS)
    
    def record_usage(self, tokens: int):
        self.requests_today += 1
        self.tokens_today += tokens
        logger.info(f"📊 Usage: {self.requests_today}/{self.MAX_REQUESTS} req, "
                   f"{self.tokens_today:,}/{self.MAX_TOKENS:,} tokens")
    
    def seconds_until_reset(self) -> int:
        tomorrow = (datetime.now() + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return int((tomorrow - datetime.now()).total_seconds())

class TelegramNotifier:
    """Send notifications via Telegram"""
    
    def __init__(self, token: str, chat_id: str = None):
        self.token = token
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{token}"
        
    async def send_message(self, message: str, parse_mode: str = "HTML"):
        """Send message to Telegram"""
        if not self.chat_id:
            logger.warning("No Telegram chat_id configured")
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": parse_mode
                    }
                ) as resp:
                    if resp.status == 200:
                        logger.info("📱 Sent Telegram notification")
                    else:
                        logger.warning(f"Telegram send failed: {resp.status}")
        except Exception as e:
            logger.error(f"❌ Telegram error: {e}")

class GeminiClient:
    """Optimized Gemini client with caching and rate limiting"""
    
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        # Use gemini-pro for free tier (stable, reliable, available)
        self.model = genai.GenerativeModel('gemini-pro')
        self.limiter = GeminiRateLimiter()
        self.cache = {}  # Simple cache
        
    async def generate(self, agent_id: str, system: str, prompt: str, 
                      temp: float = 0.7) -> str:
        """Generate with rate limiting and caching"""
        
        # Check cache
        cache_key = f"{agent_id}:{hash(prompt)}"
        if cache_key in self.cache:
            logger.info(f"💾 Cache hit: {agent_id}")
            return self.cache[cache_key]
        
        # Wait if rate limited
        if not self.limiter.can_make_request():
            wait = self.limiter.seconds_until_reset()
            logger.warning(f"⏸️  Rate limited. Waiting {wait}s")
            await asyncio.sleep(wait)
        
        # Make request
        try:
            full_prompt = f"{system}\n\n{prompt}"
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temp,
                    max_output_tokens=4096,
                )
            )
            
            result = response.text
            tokens = response.usage_metadata.total_token_count
            self.limiter.record_usage(tokens)
            
            # Cache result
            if len(self.cache) > 1000:
                self.cache.pop(next(iter(self.cache)))
            self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Gemini error for {agent_id}: {e}")
            if "429" in str(e) or "quota" in str(e).lower():
                await asyncio.sleep(60)
                return await self.generate(agent_id, system, prompt, temp)
            raise

class TaskManager:
    """Manages tasks across all agents"""
    
    def __init__(self):
        self.tasks = {}  # task_id -> Task
        data_dir = Path(os.getenv('DATA_DIR', './data'))
        self.task_dir = data_dir / "tasks"
        self.task_dir.mkdir(parents=True, exist_ok=True)
        
    def create_task(self, task_data: dict) -> str:
        """Create new task"""
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(self.tasks)}"
        task_data['id'] = task_id
        task_data['status'] = 'pending'
        task_data['created_at'] = datetime.now().isoformat()
        
        self.tasks[task_id] = task_data
        self._save_task(task_id)
        
        logger.info(f"📋 Created: {task_id} → {task_data['assigned_to']}")
        return task_id
    
    def _save_task(self, task_id: str):
        """Persist task to disk"""
        task_file = self.task_dir / f"{task_id}.json"
        with open(task_file, 'w') as f:
            json.dump(self.tasks[task_id], f, indent=2)
    
    def get_pending_tasks(self, agent_id: str) -> List[dict]:
        """Get pending tasks for an agent"""
        return [t for t in self.tasks.values() 
                if t['assigned_to'] == agent_id and t['status'] == 'pending']
    
    def complete_task(self, task_id: str, result: str):
        """Mark task complete"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
            self.tasks[task_id]['result'] = result
            self._save_task(task_id)
            logger.info(f"✅ Completed: {task_id}")

class Orchestrator:
    """The autonomous system that coordinates everything"""
    
    def __init__(self):
        self.gemini = GeminiClient()
        self.task_manager = TaskManager()
        self.telegram = TelegramNotifier(os.getenv('TELEGRAM_TOKEN'))
        
        # Team collaboration systems
        data_dir = Path(os.getenv('DATA_DIR', './data'))
        from core.team_communication import TeamCommunication
        from core.environments import EnvironmentManager
        
        self.team_comm = TeamCommunication(data_dir)
        self.env_manager = EnvironmentManager(data_dir)
        
        self.agents = {}  # agent_id -> AgentConfig (loaded from definitions)
        self.cycle_count = 0
        self.start_time = datetime.now()
        
        # Load agent configs
        self._load_agents()
        
        # State tracking
        data_dir = Path(os.getenv('DATA_DIR', './data'))
        data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = data_dir / "state.json"
        self._load_state()
        
        logger.info("🥭 Orchestrator initialized with 39 agents")
        
    def _load_agents(self):
        """Load all agent configurations"""
        from config.agent_definitions import ALL_AGENTS
        for agent in ALL_AGENTS:
            self.agents[agent.id] = agent
            logger.info(f"Loaded agent: {agent.id} ({agent.name})")
    
    def _load_state(self):
        """Load persistent state"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                state = json.load(f)
                self.cycle_count = state.get('cycle_count', 0)
        else:
            self._save_state()
    
    def _save_state(self):
        """Save persistent state"""
        state = {
            'cycle_count': self.cycle_count,
            'start_time': self.start_time.isoformat(),
            'agents_count': len(self.agents),
            'tasks_completed': len([t for t in self.task_manager.tasks.values() 
                                   if t['status'] == 'completed']),
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    async def run_forever(self):
        """Main loop - runs forever"""
        logger.info("🚀 Starting infinite autonomous loop...")
        
        # Send startup notification
        await self.telegram.send_message(
            "🥭 <b>ManyMangoes AI Team Started!</b>\n"
            f"39 agents activated\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        while True:
            try:
                self.cycle_count += 1
                cycle_start = datetime.now()
                
                logger.info(f"\n{'='*80}")
                logger.info(f"🔄 CYCLE #{self.cycle_count}")
                logger.info(f"⏰ Time: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"⏱️  Uptime: {(cycle_start - self.start_time).total_seconds()/3600:.1f}h")
                logger.info(f"{'='*80}\n")
                
                # Phase 1: Engineering Manager plans
                await self._engineering_manager_cycle()
                
                # Phase 2: Execute all pending tasks in parallel
                await self._execute_all_tasks()
                
                # Phase 3: Save state
                self._save_state()
                
                # Calculate cycle duration
                duration = (datetime.now() - cycle_start).total_seconds()
                logger.info(f"✅ Cycle #{self.cycle_count} completed in {duration:.1f}s")
                
                # Send progress update every 10 cycles
                if self.cycle_count % 10 == 0:
                    completed = len([t for t in self.task_manager.tasks.values() 
                                    if t['status'] == 'completed'])
                    total = len(self.task_manager.tasks)
                    await self.telegram.send_message(
                        f"📊 <b>Cycle #{self.cycle_count} Complete</b>\n"
                        f"✅ Tasks: {completed}/{total}\n"
                        f"⏱️ Uptime: {(datetime.now() - self.start_time).total_seconds()/3600:.1f}h"
                    )
                
                # Wait before next cycle (adaptive based on rate limits)
                if self.gemini.limiter.requests_today > 1200:
                    await asyncio.sleep(300)  # 5 min if approaching limit
                else:
                    await asyncio.sleep(120)  # 2 min normally
                
            except Exception as e:
                logger.error(f"❌ Cycle error: {e}", exc_info=True)
                await self.telegram.send_message(
                    f"⚠️ <b>Cycle Error</b>\n{str(e)[:500]}"
                )
                await asyncio.sleep(60)
    
    async def _engineering_manager_cycle(self):
        """Engineering Manager creates tasks for the team"""
        manager = self.agents['eng_manager_001']
        
        # Gather metrics
        total_tasks = len(self.task_manager.tasks)
        completed = len([t for t in self.task_manager.tasks.values() 
                        if t['status'] == 'completed'])
        pending = len([t for t in self.task_manager.tasks.values() 
                      if t['status'] == 'pending'])
        
        days_elapsed = (datetime.now() - self.start_time).days
        
        # Build context
        prompt = f"""CYCLE #{self.cycle_count} - Engineering Manager Planning

CURRENT STATE:
- Days into project: {days_elapsed}/30
- Total tasks created: {total_tasks}
- Completed tasks: {completed}
- Pending tasks: {pending}
- Completion rate: {(completed/total_tasks*100 if total_tasks > 0 else 0):.1f}%

ROADMAP STATUS:
Days 1-10: Core Infrastructure + Mango Data, EA, Sales, Support
Days 11-20: 10 more Mangoes (Marketing, Design, Content, etc)
Days 21-30: Final 10 Mangoes + Polish + Launch

YOUR JOB RIGHT NOW:
1. Assess what's been completed
2. Identify blockers
3. Generate 10-20 high-priority tasks
4. Assign to appropriate team members
5. Ensure we're on track for 24 Mangoes in 30 days

OUTPUT FORMAT (JSON only):
{{
  "tasks": [
    {{
      "title": "Build X feature",
      "description": "Detailed description with acceptance criteria",
      "assigned_to": "backend_001",
      "priority": 1,
      "estimated_hours": 4,
      "dependencies": []
    }}
  ]
}}

Generate tasks NOW:"""

        try:
            response = await self.gemini.generate(
                agent_id=manager.id,
                system=manager.system_prompt,
                prompt=prompt,
                temp=manager.temperature
            )
            
            # Parse tasks from response
            tasks_data = self._extract_json(response)
            if tasks_data and 'tasks' in tasks_data:
                for task in tasks_data['tasks']:
                    self.task_manager.create_task(task)
                    
                logger.info(f"📋 Marcus created {len(tasks_data['tasks'])} new tasks")
            else:
                logger.warning("⚠️  No valid tasks in response")
                
        except Exception as e:
            logger.error(f"❌ Engineering Manager cycle failed: {e}")
    
    async def _execute_all_tasks(self):
        """Execute all pending tasks in parallel (one per agent)"""
        
        # Group pending tasks by agent
        agent_tasks = {}
        for task in self.task_manager.tasks.values():
            if task['status'] == 'pending':
                agent_id = task['assigned_to']
                
                # Skip if agent is not active (inactive Mangoes)
                if agent_id in self.agents and not self.agents[agent_id].active:
                    logger.info(f"⏸️  Skipping task for inactive agent: {agent_id}")
                    continue
                
                if agent_id not in agent_tasks:
                    agent_tasks[agent_id] = []
                agent_tasks[agent_id].append(task)
        
        if not agent_tasks:
            logger.info("⏸️  No pending tasks to execute")
            return
        
        logger.info(f"🔄 Executing tasks for {len(agent_tasks)} agents")
        
        # Execute one task per agent in parallel
        tasks = []
        for agent_id, agent_task_list in agent_tasks.items():
            # Take first pending task for this agent
            task = agent_task_list[0]
            tasks.append(self._execute_single_task(agent_id, task))
        
        # Run all in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_single_task(self, agent_id: str, task: dict):
        """Execute one task for one agent"""
        
        if agent_id not in self.agents:
            logger.error(f"❌ Unknown agent: {agent_id}")
            return
        
        agent = self.agents[agent_id]
        task_id = task['id']
        
        logger.info(f"▶️  {agent.name} starting: {task['title']}")
        
        try:
            # Build execution prompt
            prompt = f"""TASK EXECUTION

TASK ID: {task_id}
TITLE: {task['title']}
DESCRIPTION: {task['description']}
PRIORITY: {task['priority']}

YOUR AVAILABLE TOOLS:
{', '.join(agent.tools)}

EXECUTE THIS TASK:
1. Plan your approach
2. Use your tools to complete the work
3. Test your work
4. Report results

OUTPUT FORMAT:
{{
  "actions_taken": ["action 1", "action 2", ...],
  "files_changed": ["file1.py", "file2.tsx", ...],
  "result": "description of what was accomplished",
  "status": "completed" or "blocked",
  "next_steps": ["what should happen next"]
}}

Execute now:"""

            response = await self.gemini.generate(
                agent_id=agent.id,
                system=agent.system_prompt,
                prompt=prompt,
                temp=agent.temperature
            )
            
            # Extract result
            result_data = self._extract_json(response)
            
            # If agent needs browser/tools, execute those actions
            if agent.browser_enabled and result_data:
                await self._execute_agent_actions(agent, result_data)
            
            # Mark complete
            result_text = json.dumps(result_data) if result_data else response
            self.task_manager.complete_task(task_id, result_text)
            
            logger.info(f"✅ {agent.name} completed: {task['title']}")
            
        except Exception as e:
            logger.error(f"❌ {agent.name} failed on {task['title']}: {e}")
            task['status'] = 'failed'
            task['error'] = str(e)
    
    async def _execute_agent_actions(self, agent, result_data: dict):
        """Execute browser/tool actions for an agent"""
        actions = result_data.get('actions_taken', [])
        
        for action in actions:
            # Parse action and execute with tools
            # This is where browser automation, API calls, etc. happen
            logger.info(f"🔧 {agent.name} executing: {action}")
            
            # Tool execution happens here (see tools.py)
            # For now, just log
    
    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from LLM response"""
        try:
            # Find JSON in markdown code blocks
            if '```json' in text:
                start = text.find('```json') + 7
                end = text.find('```', start)
                json_str = text[start:end].strip()
            elif '{' in text and '}' in text:
                start = text.find('{')
                end = text.rfind('}') + 1
                json_str = text[start:end]
            else:
                return None
            
            return json.loads(json_str)
        except:
            return None

async def main():
    """Entry point"""
    # Start HTTP health check server in background for Render port requirement
    import threading
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI()
    
    @app.get("/")
    @app.get("/health")
    async def health():
        return {
            "status": "running",
            "service": "mango-orchestrator",
            "agents": 39
        }
    
    @app.get("/status")
    async def status():
        return {
            "status": "operational",
            "agents_loaded": 39,
            "service": "The Mangoes AI Team"
        }
    
    def run_server():
        port = int(os.getenv('PORT', 10000))
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    logger.info(f"🌐 HTTP server started on port {os.getenv('PORT', 10000)}")
    
    # Run orchestrator in main thread
    orchestrator = Orchestrator()
    await orchestrator.run_forever()

if __name__ == "__main__":
    asyncio.run(main())

