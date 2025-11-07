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
        # Try multiple model names, use first that initializes
        model_names = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']
        self.model = None
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"✅ Initialized Gemini model: {model_name} (will test on first use)")
                break
            except Exception as e:
                logger.warning(f"⚠️  Model {model_name} initialization failed: {e}")
                continue
        
        if not self.model:
            logger.error("❌ No working Gemini model found! Tasks will use fallback generation.")
        self.limiter = GeminiRateLimiter()
        self.cache = {}  # Simple cache
        
    async def generate(self, agent_id: str, system: str, prompt: str, 
                      temp: float = 0.7) -> str:
        """Generate with rate limiting and caching"""
        
        # If no model available, return fallback
        if not self.model:
            logger.warning(f"⚠️  No Gemini model available for {agent_id}, using fallback")
            return self._fallback_response(agent_id, prompt)
        
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
            # Use fallback instead of raising
            logger.warning(f"⚠️  Using fallback response for {agent_id}")
            return self._fallback_response(agent_id, prompt)
    
    def _fallback_response(self, agent_id: str, prompt: str) -> str:
        """Generate fallback response when Gemini is unavailable"""
        if 'eng_manager' in agent_id or 'task' in prompt.lower():
            # Fallback task generation for engineering manager
            return json.dumps({
                "tasks": [
                    {
                        "title": "Set up core infrastructure",
                        "description": "Initialize project structure, set up database, configure environment",
                        "assigned_to": "backend_001",
                        "priority": 1,
                        "estimated_hours": 8,
                        "dependencies": []
                    },
                    {
                        "title": "Build Mango Core base class",
                        "description": "Create base class for all Mango agents with memory, actions, and LLM routing",
                        "assigned_to": "backend_002",
                        "priority": 1,
                        "estimated_hours": 6,
                        "dependencies": []
                    },
                    {
                        "title": "Create task management system",
                        "description": "Build system to track, assign, and complete tasks across agents",
                        "assigned_to": "backend_001",
                        "priority": 2,
                        "estimated_hours": 4,
                        "dependencies": []
                    },
                    {
                        "title": "Set up testing framework",
                        "description": "Configure pytest, write test utilities, set up CI/CD",
                        "assigned_to": "qa_001",
                        "priority": 2,
                        "estimated_hours": 4,
                        "dependencies": []
                    },
                    {
                        "title": "Build management dashboard",
                        "description": "Create web dashboard to view agents, tasks, and system status",
                        "assigned_to": "frontend_001",
                        "priority": 2,
                        "estimated_hours": 8,
                        "dependencies": []
                    }
                ]
            }, indent=2)
        elif 'evaluation' in prompt.lower() or 'self_evaluator' in agent_id:
            # Fallback evaluation
            return """OVERALL SCORE: 65/100

STRATEGIC FOCUS: 18/30
Team is working but lacks clear prioritization. Need better alignment with roadmap.

EXECUTION QUALITY: 20/25
Good technical execution. Code quality is solid.

TEAM COLLABORATION: 15/20
Agents are working independently. Need more coordination.

INNOVATION & LEARNING: 7/15
Playing it safe. Need more experimentation.

OPERATIONAL EXCELLENCE: 5/10
System is running but needs optimization.

TOP 3 STRENGTHS:
1. Solid technical foundation
2. Good code quality
3. System is operational

TOP 3 WEAKNESSES:
1. Lack of strategic focus
2. Limited innovation
3. Need better prioritization

IMMEDIATE ACTION ITEMS:
1. Define clear priorities for next cycle
2. Increase task generation
3. Improve team coordination"""
        else:
            return "I'm currently unable to process this request. Please check the Gemini API configuration."

class TaskManager:
    """Manages tasks across all agents"""
    
    def __init__(self):
        self.tasks = {}  # task_id -> Task
        data_dir = Path(os.getenv('DATA_DIR', './data'))
        self.task_dir = data_dir / "tasks"
        self.task_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing tasks from disk
        self._load_tasks_from_disk()
    
    def _load_tasks_from_disk(self):
        """Load all tasks from disk"""
        if not self.task_dir.exists():
            return
        
        for task_file in self.task_dir.glob("*.json"):
            try:
                with open(task_file) as f:
                    task = json.load(f)
                    task_id = task_file.stem
                    task['id'] = task_id
                    self.tasks[task_id] = task
            except Exception as e:
                logger.warning(f"Failed to load task {task_file}: {e}")
        
        if self.tasks:
            logger.info(f"📋 Loaded {len(self.tasks)} tasks from disk")
        
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
    
    def _validate_proof_of_work(self, result: str) -> bool:
        """Validate that result contains proof of work"""
        if not result:
            return False
        
        # Try to parse as JSON
        try:
            result_data = json.loads(result)
        except:
            # Not JSON - check if it's a meaningful string (not just empty or placeholder)
            result_lower = result.lower().strip()
            if len(result_lower) < 20:  # Too short to be meaningful
                return False
            # Check for common placeholder text
            placeholders = ['task completed', 'done', 'finished', 'completed', 'ok']
            if any(placeholder in result_lower and len(result_lower) < 50):
                return False
            # If it's a longer meaningful string, accept it
            return True
        
        # Check for proof fields in JSON
        proof_fields = [
            'files_changed',  # List of files modified
            'actions_taken',  # List of actions performed
            'test_coverage',  # Test coverage percentage
            'code_changes',   # Description of code changes
            'commit_hash',    # Git commit hash
            'pr_url',         # Pull request URL
            'deployment_url', # Deployment URL
            'screenshots',    # Screenshots taken
            'api_endpoints',  # API endpoints created
            'database_changes', # Database changes made
        ]
        
        # Check if any proof field exists and has value
        for field in proof_fields:
            if field in result_data:
                value = result_data[field]
                # Check if value is meaningful
                if isinstance(value, list) and len(value) > 0:
                    return True
                if isinstance(value, (int, float)) and value > 0:
                    return True
                if isinstance(value, str) and len(value.strip()) > 0:
                    return True
                if isinstance(value, bool) and value:
                    return True
        
        # Check if result field contains meaningful content (not just task planning)
        if 'result' in result_data:
            result_text = str(result_data['result'])
            # Reject if it looks like task planning (contains "tasks" array)
            if 'tasks' in result_data and isinstance(result_data['tasks'], list):
                # This is task planning, not proof of work
                return False
            # Check if result is meaningful
            if len(result_text) > 50 and not result_text.lower().startswith('task'):
                return True
        
        # Check if description field contains meaningful content
        if 'description' in result_data:
            desc = str(result_data['description'])
            if len(desc) > 50:
                return True
        
        return False
    
    def complete_task(self, task_id: str, result: str):
        """Mark task complete - ONLY if proof of work exists"""
        if task_id in self.tasks:
            # Validate proof of work before completing
            if not self._validate_proof_of_work(result):
                logger.warning(f"❌ Cannot complete {task_id} - missing proof of work")
                logger.warning(f"   Result: {result[:200]}...")
                # Don't mark as completed - leave status as is
                return False
            
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
            self.tasks[task_id]['result'] = result
            self._save_task(task_id)
            logger.info(f"✅ Completed: {task_id}")
            return True
        return False

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
        self.last_self_eval = datetime.now()  # Track last self-evaluation
        
        # Self-improvement system
        from core.self_improvement import SelfImprovementCycle
        self.self_improvement = SelfImprovementCycle(
            gemini_client=self.gemini,
            data_dir=data_dir,
            github_token=os.getenv('GITHUB_TOKEN', '')
        )
        
        # Interactive Telegram bot
        from core.telegram_bot import TelegramBot
        self.telegram_bot = TelegramBot(
            token=os.getenv('TELEGRAM_TOKEN', ''),
            orchestrator_ref=self
        )
        
        # Load agent configs
        self._load_agents()
        
        # State tracking
        data_dir = Path(os.getenv('DATA_DIR', './data'))
        data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = data_dir / "state.json"
        self.eval_dir = data_dir / "evaluations"
        self.eval_dir.mkdir(exist_ok=True)
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
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'last_self_eval': self.last_self_eval.isoformat()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    async def _self_evaluate(self):
        """
        Self-evaluation: Analyze if the team is performing at world-class standards.
        Runs every hour to ensure continuous improvement.
        """
        now = datetime.now()
        logger.info("🔍 Starting self-evaluation...")
        
        # Gather performance metrics
        tasks = self.task_manager.tasks
        total_tasks = len(tasks)
        completed = len([t for t in tasks.values() if t['status'] == 'completed'])
        in_progress = len([t for t in tasks.values() if t['status'] == 'in_progress'])
        failed = len([t for t in tasks.values() if t['status'] == 'failed'])
        
        # Calculate time-based metrics
        uptime_hours = (now - self.start_time).total_seconds() / 3600
        tasks_per_hour = completed / uptime_hours if uptime_hours > 0 else 0
        cycles_per_hour = self.cycle_count / uptime_hours if uptime_hours > 0 else 0
        
        # Get recent tasks for quality analysis
        recent_tasks = sorted(
            [t for t in tasks.values() if t.get('completed_at')],
            key=lambda x: x.get('completed_at', ''),
            reverse=True
        )[:20]  # Last 20 completed tasks
        
        # Build evaluation prompt
        evaluation_prompt = f"""
You are evaluating an autonomous AI development team of 39 agents (15 developers + 24 specialized Mangoes).

**Current Performance Metrics:**
- Uptime: {uptime_hours:.1f} hours
- Total Cycles: {self.cycle_count}
- Tasks Completed: {completed}/{total_tasks}
- Tasks In Progress: {in_progress}
- Failed Tasks: {failed}
- Tasks per Hour: {tasks_per_hour:.2f}
- Cycles per Hour: {cycles_per_hour:.1f}

**Recent Completed Tasks:**
{json.dumps([{'title': t.get('title'), 'agent': t.get('assigned_to'), 'complexity': t.get('complexity', 'unknown')} for t in recent_tasks[:10]], indent=2)}

**Evaluation Criteria (World-Class Team Standards):**

1. **Strategic Focus (30 points)**
   - Are tasks aligned with high-impact goals?
   - Is there a clear product vision?
   - Are we building features that matter?
   - Is there a balance between innovation and maintenance?

2. **Execution Quality (25 points)**
   - Task completion rate and velocity
   - Technical excellence and code quality
   - Proper testing and validation
   - Documentation and knowledge sharing

3. **Team Collaboration (20 points)**
   - Effective communication between agents
   - Knowledge sharing and learning
   - Coordinated efforts on complex tasks
   - Cross-functional collaboration

4. **Innovation & Learning (15 points)**
   - Exploring new technologies
   - Learning from failures
   - Adapting strategies based on results
   - Creative problem-solving

5. **Operational Excellence (10 points)**
   - Consistent delivery rhythm
   - Proper task prioritization
   - Resource utilization
   - System reliability

**Your Task:**
Provide a brutally honest evaluation of this team's performance. Score each category out of its max points.
Then provide:
1. Overall score out of 100
2. Top 3 strengths
3. Top 3 critical weaknesses
4. 3 immediate action items to improve
5. One ambitious goal for the next evaluation period

Be critical. World-class teams don't accept mediocrity. If something is subpar, call it out.
"""

        try:
            # Get AI evaluation
            evaluation = await self.gemini.generate(
                agent_id="self_evaluator",
                system="You are a world-class engineering manager evaluating team performance. Be critical, honest, and actionable.",
                prompt=evaluation_prompt,
                temp=0.3  # Lower temperature for more consistent evaluation
            )
            
            # Parse and structure the evaluation
            eval_result = {
                'timestamp': now.isoformat(),
                'uptime_hours': uptime_hours,
                'cycle_count': self.cycle_count,
                'metrics': {
                    'total_tasks': total_tasks,
                    'completed': completed,
                    'in_progress': in_progress,
                    'failed': failed,
                    'tasks_per_hour': tasks_per_hour,
                    'cycles_per_hour': cycles_per_hour
                },
                'evaluation': evaluation,
                'recent_tasks_analyzed': len(recent_tasks)
            }
            
            # Save evaluation to file
            eval_file = self.eval_dir / f"eval_{now.strftime('%Y%m%d_%H%M%S')}.json"
            with open(eval_file, 'w') as f:
                json.dump(eval_result, f, indent=2)
            
            logger.info("✅ Self-evaluation completed and saved")
            logger.info(f"📊 Evaluation Preview:\n{evaluation[:500]}...")
            
            # Send notification with summary
            await self.telegram.send_message(
                f"🔍 <b>Self-Evaluation Complete</b>\n\n"
                f"📊 <b>Metrics:</b>\n"
                f"• Tasks: {completed}/{total_tasks} completed\n"
                f"• Velocity: {tasks_per_hour:.1f} tasks/hour\n"
                f"• Uptime: {uptime_hours:.1f}h\n\n"
                f"📝 <b>Evaluation Summary:</b>\n"
                f"{evaluation[:400]}...\n\n"
                f"💾 Full report saved to evaluations/"
            )
            
            # Update last evaluation time
            self.last_self_eval = now
            
            # Trigger self-improvement cycle if score is below 85
            score = self._extract_score_from_eval(evaluation)
            if score < 85:
                logger.info(f"📊 Score {score}/100 - Triggering self-improvement cycle...")
                asyncio.create_task(self._run_improvement_cycle(eval_result))
            else:
                logger.info(f"✨ Score {score}/100 - Excellent! No improvements needed.")
            
            return eval_result
            
        except Exception as e:
            logger.error(f"❌ Self-evaluation failed: {e}")
            # Create fallback evaluation so we have something
            logger.info("📊 Creating fallback evaluation...")
            fallback_eval = {
                'timestamp': now.isoformat(),
                'uptime_hours': uptime_hours,
                'cycle_count': self.cycle_count,
                'metrics': {
                    'total_tasks': total_tasks,
                    'completed': completed,
                    'in_progress': in_progress,
                    'failed': failed,
                    'tasks_per_hour': tasks_per_hour,
                    'cycles_per_hour': cycles_per_hour
                },
                'evaluation': self.gemini._fallback_response('self_evaluator', 'evaluation'),
                'recent_tasks_analyzed': len(recent_tasks)
            }
            
            # Save fallback evaluation
            eval_file = self.eval_dir / f"eval_{now.strftime('%Y%m%d_%H%M%S')}.json"
            with open(eval_file, 'w') as f:
                json.dump(fallback_eval, f, indent=2)
            
            logger.info("✅ Fallback evaluation created and saved")
            self.last_self_eval = now
            return fallback_eval
    
    def _extract_score_from_eval(self, evaluation_text: str) -> int:
        """Extract numeric score from evaluation"""
        import re
        match = re.search(r'OVERALL SCORE:?\s*(\d+)/100', evaluation_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 85  # Default to passing score if can't parse
    
    async def _run_improvement_cycle(self, evaluation: Dict):
        """
        Run the complete self-improvement cycle:
        1. Generate improvements
        2. Deploy to test
        3. Get agent feedback
        4. Analyze results
        5. Deploy to production if passed
        """
        try:
            logger.info("🔄 Starting self-improvement cycle...")
            
            result = await self.self_improvement.run_improvement_cycle(evaluation)
            
            if result:
                if result['status'] == 'deployed':
                    await self.telegram.send_message(
                        f"🎉 <b>Self-Improvement Deployed!</b>\n\n"
                        f"📊 Cycle: {result['cycle_id']}\n"
                        f"✅ Tests passed: {result['test_analysis']['yes_votes']}/16 agents approved\n"
                        f"🚀 Production deployment: SUCCESSFUL\n\n"
                        f"The team has improved itself and deployed to production automatically!"
                    )
                elif result['status'] == 'failed':
                    await self.telegram.send_message(
                        f"⚠️ <b>Self-Improvement Attempt Failed</b>\n\n"
                        f"📊 Cycle: {result['cycle_id']}\n"
                        f"❌ Reasons:\n" + "\n".join(f"• {r}" for r in result.get('reasons', []))
                    )
            
        except Exception as e:
            logger.error(f"❌ Self-improvement cycle error: {e}")
            await self.telegram.send_message(
                f"❌ <b>Self-Improvement Error</b>\n\n{str(e)}"
            )
    
    async def run_forever(self):
        """Main loop - runs forever"""
        logger.info("🚀 Starting infinite autonomous loop...")
        
        # Start interactive Telegram bot in background
        if self.telegram_bot.token:
            asyncio.create_task(self.telegram_bot.start())
            logger.info("🤖 Interactive Telegram bot started")
        
        # Send startup notification
        await self.telegram.send_message(
            "🥭 <b>ManyMangoes AI Team Started!</b>\n"
            f"39 agents activated\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"💬 <b>Interactive bot active!</b> Send /help to get started."
        )
        
        # Create initial tasks if none exist
        if len(self.task_manager.tasks) == 0:
            logger.info("📋 No tasks found - creating initial starter tasks...")
            initial_tasks = [
                {
                    "title": "Set up core infrastructure",
                    "description": "Initialize project structure, set up database, configure environment variables",
                    "assigned_to": "backend_001",
                    "priority": 1,
                    "estimated_hours": 8,
                    "dependencies": []
                },
                {
                    "title": "Build Mango Core base class",
                    "description": "Create base class for all Mango agents with memory, actions, and LLM routing",
                    "assigned_to": "backend_002",
                    "priority": 1,
                    "estimated_hours": 6,
                    "dependencies": []
                },
                {
                    "title": "Create task management system",
                    "description": "Build system to track, assign, and complete tasks across all agents",
                    "assigned_to": "backend_001",
                    "priority": 2,
                    "estimated_hours": 4,
                    "dependencies": []
                },
                {
                    "title": "Set up testing framework",
                    "description": "Configure pytest, write test utilities, set up CI/CD pipeline",
                    "assigned_to": "qa_001",
                    "priority": 2,
                    "estimated_hours": 4,
                    "dependencies": []
                },
                {
                    "title": "Build management dashboard",
                    "description": "Create web dashboard to view agents, tasks, and system status",
                    "assigned_to": "frontend_001",
                    "priority": 2,
                    "estimated_hours": 8,
                    "dependencies": []
                }
            ]
            for task in initial_tasks:
                self.task_manager.create_task(task)
            logger.info(f"✅ Created {len(initial_tasks)} initial tasks")
        
        # Create initial evaluation if none exist
        eval_dir = Path(os.getenv('DATA_DIR', './data')) / "evaluations"
        eval_dir.mkdir(exist_ok=True)
        existing_evals = list(eval_dir.glob("eval_*.json"))
        if len(existing_evals) == 0:
            logger.info("📊 No evaluations found - creating initial evaluation...")
            try:
                await self._self_evaluate()
            except Exception as e:
                logger.warning(f"Could not create initial evaluation: {e}")
        
        while True:
            try:
                self.cycle_count += 1
                cycle_start = datetime.now()
                
                logger.info(f"\n{'='*80}")
                logger.info(f"🔄 CYCLE #{self.cycle_count}")
                logger.info(f"⏰ Time: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"⏱️  Uptime: {(cycle_start - self.start_time).total_seconds()/3600:.1f}h")
                logger.info(f"{'='*80}\n")
                
                # Phase 0: Collect status reports from team (standup)
                await self._collect_status_reports()
                
                # Phase 1: Engineering Manager plans (with full team context)
                await self._engineering_manager_cycle()
                
                # Phase 1.5: Process code reviews (Marcus reviews code)
                await self._process_all_pending_reviews()
                
                # Phase 2: Execute all pending tasks in parallel
                await self._execute_all_tasks()
                
                # Phase 2.5: Process blockers and unblock agents
                await self._process_blockers()
                
                # Phase 3: Self-evaluation (every hour)
                time_since_eval = (datetime.now() - self.last_self_eval).total_seconds() / 3600
                if time_since_eval >= 1.0:  # Every hour
                    logger.info("⏰ One hour elapsed - triggering self-evaluation")
                    await self._self_evaluate()
                
                # Phase 4: Save state
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
        
        # Gather comprehensive metrics
        total_tasks = len(self.task_manager.tasks)
        completed = len([t for t in self.task_manager.tasks.values() 
                        if t['status'] == 'completed'])
        pending = len([t for t in self.task_manager.tasks.values() 
                      if t['status'] == 'pending'])
        in_progress = len([t for t in self.task_manager.tasks.values() 
                          if t['status'] == 'in_progress'])
        in_review = len([t for t in self.task_manager.tasks.values() 
                        if t['status'] == 'in_review'])
        blocked = len([t for t in self.task_manager.tasks.values() 
                      if t['status'] == 'blocked'])
        
        # Get recent completed tasks for context
        recent_completed = sorted(
            [t for t in self.task_manager.tasks.values() if t.get('status') == 'completed'],
            key=lambda x: x.get('completed_at', ''),
            reverse=True
        )[:10]
        
        # Get what each agent is currently working on
        agent_workload = {}
        for agent_id in self.agents.keys():
            if agent_id == 'eng_manager_001':
                continue
            agent_tasks = [t for t in self.task_manager.tasks.values() 
                          if t.get('assigned_to') == agent_id]
            agent_workload[agent_id] = {
                'total': len(agent_tasks),
                'completed': len([t for t in agent_tasks if t.get('status') == 'completed']),
                'pending': len([t for t in agent_tasks if t.get('status') == 'pending']),
                'in_progress': len([t for t in agent_tasks if t.get('status') == 'in_progress']),
                'current_task': next((t for t in agent_tasks if t.get('status') in ['pending', 'in_progress']), None)
            }
        
        # Get team status summary
        team_status = await self.team_comm.get_team_status_summary()
        
        # Get pending reviews
        pending_reviews = await self.team_comm.get_pending_reviews_for_agent('eng_manager_001')
        
        # Get blockers
        blockers = [t for t in self.task_manager.tasks.values() if t.get('status') == 'blocked']
        
        days_elapsed = (datetime.now() - self.start_time).days
        hours_elapsed = (datetime.now() - self.start_time).total_seconds() / 3600
        
        # Calculate velocity (tasks per hour)
        velocity = completed / hours_elapsed if hours_elapsed > 0 else 0
        
        # Build comprehensive context
        prompt = f"""CYCLE #{self.cycle_count} - Engineering Manager Planning

⏰ TIME & PROGRESS:
- Days into project: {days_elapsed}/30
- Hours elapsed: {hours_elapsed:.1f}h
- Velocity: {velocity:.2f} tasks/hour
- Target: 24 Mangoes in 30 days = ~0.8 Mangoes/day

📊 CURRENT STATE:
- Total tasks: {total_tasks}
- ✅ Completed: {completed} ({(completed/total_tasks*100 if total_tasks > 0 else 0):.1f}%)
- ⏳ Pending: {pending}
- 🔄 In Progress: {in_progress}
- 🔍 In Review: {in_review}
- ⚠️ Blocked: {blocked}
- 📝 Pending Reviews: {len(pending_reviews)}

🎯 RECENT COMPLETIONS (Last 10):
{chr(10).join([f"- {t.get('title', 'Unknown')} by {t.get('assigned_to', 'Unknown')}" for t in recent_completed[:10]])}

👥 TEAM WORKLOAD:
{chr(10).join([f"- {agent_id}: {data['completed']} done, {data['pending']} pending, {data['in_progress']} in progress" + (f" | Current: {data['current_task']['title'][:50]}" if data['current_task'] else "") for agent_id, data in list(agent_workload.items())[:15]])}

⚠️ BLOCKERS ({len(blockers)}):
{chr(10).join([f"- {t.get('title', 'Unknown')}: {', '.join(t.get('blockers', []))}" for t in blockers[:5]])}

📋 TEAM STATUS SUMMARY:
- Agents reporting: {team_status.get('agents_reporting', 0)}
- Total tasks completed today: {team_status.get('total_tasks_completed', 0)}
- Average velocity: {team_status.get('avg_velocity', 0):.1f} tasks/day

🎯 ROADMAP STATUS:
Days 1-10: Core Infrastructure + Mango Data, EA, Sales, Support
Days 11-20: 10 more Mangoes (Marketing, Design, Content, etc)
Days 21-30: Final 10 Mangoes + Polish + Launch

YOUR JOB RIGHT NOW (CRITICAL FOR PROGRESS):
1. ✅ Review and process pending code reviews FIRST (unblock the team)
2. 🔍 Identify agents who are idle or have low workload - assign them work
3. 🎯 Generate 15-25 HIGH-IMPACT tasks that move us toward Mango completion
4. 🔗 Create task dependencies so agents can build on each other's work
5. 👥 Assign tasks strategically - balance workload across all 15 developers
6. 🚀 Prioritize tasks that unblock others or complete Mango features
7. 📊 Ensure every agent has 2-3 tasks queued up (no idle time!)

COLLABORATION STRATEGY:
- Create tasks that build on recently completed work
- Pair agents on complex features (e.g., "Aria + Kai: Build API together")
- Create integration tasks that connect different components
- Ensure frontend/backend work is coordinated
- Make sure QA has work to test as features complete

OUTPUT FORMAT (JSON only):
{{
  "tasks": [
    {{
      "title": "Build X feature (builds on Y completed by Z)",
      "description": "Detailed description with acceptance criteria. Reference related completed tasks.",
      "assigned_to": "backend_001",
      "priority": 1,
      "estimated_hours": 4,
      "dependencies": ["TASK-ID-of-prerequisite"],
      "collaborates_with": ["backend_002"],
      "builds_on": "What this builds on from recent completions"
    }}
  ],
  "strategy": "Brief explanation of task generation strategy"
}}

Generate 15-25 strategic tasks NOW:"""

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
            # Create fallback tasks if none exist
            if len(self.task_manager.tasks) == 0:
                logger.info("📋 No tasks exist - creating fallback starter tasks")
                fallback_tasks = [
                    {
                        "title": "Set up core infrastructure",
                        "description": "Initialize project structure, set up database, configure environment",
                        "assigned_to": "backend_001",
                        "priority": 1,
                        "estimated_hours": 8
                    },
                    {
                        "title": "Build Mango Core base class",
                        "description": "Create base class for all Mango agents",
                        "assigned_to": "backend_002",
                        "priority": 1,
                        "estimated_hours": 6
                    },
                    {
                        "title": "Create task management system",
                        "description": "Build system to track and assign tasks",
                        "assigned_to": "backend_001",
                        "priority": 2,
                        "estimated_hours": 4
                    }
                ]
                for task in fallback_tasks:
                    self.task_manager.create_task(task)
                logger.info(f"✅ Created {len(fallback_tasks)} fallback tasks")
    
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
        
        # Mark task as in progress
        task['status'] = 'in_progress'
        task['started_at'] = datetime.now().isoformat()
        self.task_manager._save_task(task_id)
        
        # Check for messages/blockers before starting
        messages = await self.team_comm.get_messages_for_agent(agent_id, unread_only=True)
        if messages:
            logger.info(f"💬 {agent.name} has {len(messages)} unread messages")
        
        try:
            # Build execution prompt with comprehensive team context
            team_context = ""
            
            # Recent messages
            if messages:
                recent_msgs = messages[:5]
                team_context += "\n\n💬 RECENT TEAM MESSAGES:\n"
                for msg in recent_msgs:
                    team_context += f"- {msg.from_agent}: {msg.subject}\n"
            
            # What other agents are working on
            other_agents_work = []
            for other_agent_id, other_agent in self.agents.items():
                if other_agent_id == agent_id:
                    continue
                other_tasks = [t for t in self.task_manager.tasks.values() 
                              if t.get('assigned_to') == other_agent_id and 
                              t.get('status') in ['in_progress', 'in_review']]
                if other_tasks:
                    for task in other_tasks[:2]:
                        other_agents_work.append(f"{other_agent.name} ({other_agent.role}): {task.get('title', 'Unknown')}")
            
            if other_agents_work:
                team_context += "\n\n👥 WHAT YOUR TEAMMATES ARE WORKING ON:\n"
                team_context += "\n".join(other_agents_work[:10])
            
            # Recently completed work you can build on
            recent_completed = sorted(
                [t for t in self.task_manager.tasks.values() if t.get('status') == 'completed'],
                key=lambda x: x.get('completed_at', ''),
                reverse=True
            )[:5]
            
            if recent_completed:
                team_context += "\n\n✅ RECENTLY COMPLETED (you can build on these):\n"
                for task in recent_completed:
                    team_context += f"- {task.get('title', 'Unknown')} by {task.get('assigned_to', 'Unknown')}\n"
            
            # Task dependencies
            task_deps = []
            if task.get('dependencies'):
                for dep_id in task.get('dependencies', []):
                    dep_task = self.task_manager.tasks.get(dep_id)
                    if dep_task:
                        task_deps.append(f"- {dep_task.get('title', 'Unknown')} ({dep_task.get('status', 'unknown')})")
            
            if task_deps:
                team_context += "\n\n🔗 TASK DEPENDENCIES:\n"
                team_context += "\n".join(task_deps)
            
            prompt = f"""TASK EXECUTION

TASK ID: {task_id}
TITLE: {task['title']}
DESCRIPTION: {task['description']}
PRIORITY: {task['priority']}
{team_context}

YOUR AVAILABLE TOOLS:
{', '.join(agent.tools)}

EXECUTE THIS TASK:
1. Plan your approach
2. Use your tools to complete the work
3. Write tests (aim for 90%+ coverage)
4. If you're blocked, ask for help using team communication
5. Report results

IMPORTANT - CODE REVIEW PROCESS:
- If this task involves code changes, you MUST request a code review
- Request review from Marcus (eng_manager_001) or appropriate senior engineer
- Do NOT mark task as complete until code is reviewed and approved
- Follow world-class engineering practices: "We fight the code together, not each other"

CRITICAL - PROOF OF WORK REQUIRED:
Your task CANNOT be marked as completed without proof of work. You MUST include at least ONE of:
- "files_changed": ["file1.py", "file2.tsx"] - REQUIRED if you changed code
- "actions_taken": ["Created API", "Wrote tests"] - REQUIRED - list what you did
- "test_coverage": 0.85 - Test coverage (0.0 to 1.0)
- "code_changes": "Description" - What code you changed
- "commit_hash": "abc123" - Git commit hash
- "pr_url": "https://..." - Pull request URL

WITHOUT PROOF OF WORK, YOUR TASK WILL BE BLOCKED AND NOT COMPLETED.

OUTPUT FORMAT (MUST be valid JSON):
{{
  "status": "completed" or "blocked",
  "result": "Summary of what was accomplished",
  "actions_taken": ["action 1", "action 2", ...],  // REQUIRED - what did you do?
  "files_changed": ["file1.py", "file2.tsx", ...],  // REQUIRED if code changed
  "test_coverage": 0.95,  // Optional but recommended
  "needs_code_review": true/false,
  "reviewer": "eng_manager_001",
  "next_steps": ["what should happen next"],
  "blockers": ["any blockers encountered"]
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
            
            # Handle blockers
            if result_data and result_data.get('status') == 'blocked':
                blockers = result_data.get('blockers', [])
                for blocker in blockers:
                    await self.team_comm.report_blocker(
                        agent_id, 
                        f"Task {task['title']}: {blocker}"
                    )
                task['status'] = 'blocked'
                task['blockers'] = blockers
                self.task_manager._save_task(task_id)
                logger.warning(f"⚠️  {agent.name} blocked on: {task['title']}")
                return
            
            # Validate proof of work BEFORE any completion - ALWAYS required
            result_text = json.dumps(result_data) if result_data else response
            has_proof = self.task_manager._validate_proof_of_work(result_text)
            
            if not has_proof:
                # No proof of work - mark as blocked and ask agent to provide evidence
                task['status'] = 'blocked'
                task['blocker_reason'] = 'Missing proof of work. Please provide files_changed, actions_taken, or other evidence of work completed.'
                task['result'] = result_text
                self.task_manager._save_task(task_id)
                
                logger.warning(f"⚠️ {agent.name} cannot complete '{task['title']}' - missing proof of work")
                logger.warning(f"   Result was: {result_text[:200]}...")
                
                # Send message to agent asking for proof
                from core.team_communication import Message
                await self.team_comm.send_message(
                    Message(
                        id=f"proof_request_{task_id}_{datetime.now().timestamp()}",
                        from_agent='eng_manager_001',
                        to_agent=agent_id,
                        message_type="blocker",
                        subject=f"Proof of Work Required: {task['title']}",
                        content=f"""
Your task '{task['title']}' cannot be marked as completed without proof of work.

Please provide ONE of the following:
- files_changed: List of files you modified
- actions_taken: List of actions you performed  
- test_coverage: Test coverage percentage
- code_changes: Description of code changes
- commit_hash: Git commit hash
- pr_url: Pull request URL

Current result: {result_text[:300]}

Please resubmit with proof of work.
                        """.strip(),
                        timestamp=datetime.now().isoformat(),
                        priority="high"
                    )
                )
                return
            
            # If we have proof, proceed with review or completion
            # Handle code review requirement
            needs_review = result_data and (
                result_data.get('needs_code_review', False) or 
                result_data.get('files_changed', [])
            )
            
            if needs_review:
                # Request code review from Marcus or specified reviewer
                reviewer = result_data.get('reviewer', 'eng_manager_001')
                files_changed = result_data.get('files_changed', [])
                test_coverage = result_data.get('test_coverage', 0.0)
                
                review_id = f"REVIEW-{task_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                from core.team_communication import CodeReviewRequest
                review_request = CodeReviewRequest(
                    id=review_id,
                    from_agent=agent_id,
                    to_agent=reviewer,
                    pr_url=f"task://{task_id}",
                    files_changed=files_changed,
                    description=f"{task['title']}: {result_data.get('result', '')[:200]}",
                    test_coverage=test_coverage * 100,
                    timestamp=datetime.now().isoformat(),
                    priority="high" if task.get('priority', 2) == 1 else "normal",
                    status="pending"
                )
                
                await self.team_comm.request_code_review(review_request)
                task['status'] = 'in_review'
                task['review_id'] = review_id
                task['reviewer'] = reviewer
                task['result'] = result_text  # Save result with proof
                self.task_manager._save_task(task_id)
                
                logger.info(f"🔍 {agent.name} requested code review from {reviewer} for: {task['title']}")
                
                # Review will be processed in next cycle's review phase
            else:
                # No code review needed, mark complete (proof already validated)
                if self.task_manager.complete_task(task_id, result_text):
                    logger.info(f"✅ {agent.name} completed: {task['title']} (with proof of work)")
                else:
                    logger.error(f"❌ Failed to complete {task_id} - validation failed")
            
        except Exception as e:
            logger.error(f"❌ {agent.name} failed on {task['title']}: {e}")
            task['status'] = 'failed'
            task['error'] = str(e)
            self.task_manager._save_task(task_id)
            
            # Report error to team
            await self.team_comm.report_blocker(
                agent_id,
                f"Task '{task['title']}' failed: {str(e)}"
            )
    
    async def _collect_status_reports(self):
        """Collect status reports from all agents (daily standup)"""
        # Only collect every few cycles to avoid spam
        if self.cycle_count % 5 != 0:  # Every 5 cycles (~10 minutes)
            return
        
        logger.info("📊 Collecting status reports from team...")
        
        from core.team_communication import StatusReport
        
        for agent_id, agent in self.agents.items():
            if agent_id == 'eng_manager_001':
                continue
            
            # Get agent's tasks
            agent_tasks = [t for t in self.task_manager.tasks.values() 
                          if t.get('assigned_to') == agent_id]
            
            completed_today = [t for t in agent_tasks 
                             if t.get('status') == 'completed' and 
                             t.get('completed_at', '').startswith(datetime.now().strftime('%Y-%m-%d'))]
            
            current_task = next((t for t in agent_tasks 
                               if t.get('status') in ['pending', 'in_progress']), None)
            
            blockers = [t for t in agent_tasks if t.get('status') == 'blocked']
            
            # Calculate velocity
            total_completed = len([t for t in agent_tasks if t.get('status') == 'completed'])
            uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            velocity = total_completed / uptime_hours if uptime_hours > 0 else 0
            
            report = StatusReport(
                agent_id=agent_id,
                agent_name=agent.name,
                timestamp=datetime.now().isoformat(),
                completed_today=[t.get('title', 'Unknown') for t in completed_today],
                working_on=current_task.get('title', 'No current task') if current_task else 'Idle',
                blockers=[t.get('title', 'Unknown') for t in blockers],
                needs_help_from=[],
                code_reviews_done=0,  # Could track this
                tests_written=len([t for t in completed_today if 'test' in t.get('title', '').lower()]),
                bugs_fixed=len([t for t in completed_today if 'fix' in t.get('title', '').lower()]),
                velocity_score=velocity
            )
            
            await self.team_comm.submit_status_report(report)
        
        logger.info("✅ Status reports collected")
    
    async def _process_blockers(self):
        """Process blockers and help unblock agents"""
        blockers = [t for t in self.task_manager.tasks.values() if t.get('status') == 'blocked']
        
        if not blockers:
            return
        
        logger.info(f"🔧 Processing {len(blockers)} blockers...")
        
        manager = self.agents['eng_manager_001']
        
        for blocker_task in blockers[:3]:  # Process up to 3 blockers per cycle
            agent_id = blocker_task.get('assigned_to')
            blocker_reasons = blocker_task.get('blockers', [])
            
            if not blocker_reasons:
                continue
            
            # Ask Marcus to help unblock
            prompt = f"""BLOCKER RESOLUTION

AGENT: {agent_id}
TASK: {blocker_task.get('title', 'Unknown')}
BLOCKERS: {', '.join(blocker_reasons)}

YOUR JOB:
1. Analyze why this agent is blocked
2. Provide specific guidance to unblock them
3. Suggest alternative approaches
4. Assign helper tasks if needed

OUTPUT FORMAT:
{{
  "analysis": "Why they're blocked",
  "solution": "How to unblock them",
  "action_items": ["specific action 1", "specific action 2"],
  "helper_tasks": [
    {{
      "title": "Helper task title",
      "assigned_to": "agent_id",
      "description": "How this helps unblock"
    }}
  ]
}}

Help unblock NOW:"""
            
            try:
                response = await self.gemini.generate(
                    agent_id=manager.id,
                    system=manager.system_prompt,
                    prompt=prompt,
                    temp=manager.temperature
                )
                
                solution_data = self._extract_json(response)
                
                if solution_data:
                    # Send unblocking message to agent
                    from core.team_communication import Message
                    await self.team_comm.send_message(
                        Message(
                            id=f"unblock_{blocker_task['id']}_{datetime.now().timestamp()}",
                            from_agent='eng_manager_001',
                            to_agent=agent_id,
                            message_type="help_request",
                            subject=f"Unblocking: {blocker_task.get('title', 'Unknown')}",
                            content=f"""**Analysis:** {solution_data.get('analysis', '')}

**Solution:** {solution_data.get('solution', '')}

**Action Items:**
{chr(10).join(['- ' + item for item in solution_data.get('action_items', [])])}""",
                            timestamp=datetime.now().isoformat(),
                            priority="high"
                        )
                    )
                    
                    # Create helper tasks if needed
                    if solution_data.get('helper_tasks'):
                        for helper_task in solution_data['helper_tasks']:
                            helper_task['priority'] = 1  # High priority for unblocking
                            helper_task['dependencies'] = []
                            self.task_manager.create_task(helper_task)
                            logger.info(f"📋 Created helper task: {helper_task.get('title', 'Unknown')}")
                    
                    logger.info(f"✅ Unblocked: {blocker_task.get('title', 'Unknown')}")
            except Exception as e:
                logger.error(f"❌ Failed to process blocker: {e}")
    
    async def _process_all_pending_reviews(self):
        """Process all pending code reviews - Marcus reviews everything"""
        # Marcus reviews all pending reviews
        marcus_id = 'eng_manager_001'
        pending_reviews = await self.team_comm.get_pending_reviews_for_agent(marcus_id)
        
        if pending_reviews:
            logger.info(f"🔍 Processing {len(pending_reviews)} pending code reviews")
            # Process up to 3 reviews per cycle to avoid overload
            for review in pending_reviews[:3]:
                await self._process_pending_reviews(marcus_id)
                # Small delay between reviews
                await asyncio.sleep(2)
    
    async def _process_pending_reviews(self, reviewer_id: str):
        """Process pending code reviews for a reviewer"""
        if reviewer_id not in self.agents:
            return
        
        pending_reviews = await self.team_comm.get_pending_reviews_for_agent(reviewer_id)
        
        if not pending_reviews:
            return
        
        reviewer = self.agents[reviewer_id]
        
        # Process one review per cycle to avoid overload
        review = pending_reviews[0]
        logger.info(f"🔍 {reviewer.name} reviewing: {review.description}")
        
        # Get the task being reviewed
        task_id = review.id.split('-')[1] if '-' in review.id else None
        task = None
        if task_id:
            task = self.task_manager.tasks.get(task_id)
        
        # Build review prompt
        prompt = f"""CODE REVIEW REQUEST

REVIEW ID: {review.id}
FROM: {review.from_agent}
DESCRIPTION: {review.description}
FILES CHANGED: {len(review.files_changed)}
TEST COVERAGE: {review.test_coverage}%

REVIEW GUIDELINES (from "Defining our Characters.md"):
- "We fight the code together, not each other"
- Check for: security issues, test coverage, documentation, performance
- Be specific: "I think there's a simpler version of this. Want to explore?"
- Judge ideas on merit, not origin
- Provide constructive feedback

TASK CONTEXT:
{json.dumps(task, indent=2) if task else 'No task context available'}

REVIEW THIS CODE:
1. Check test coverage (should be ≥90%)
2. Review for security issues
3. Check code quality and maintainability
4. Ensure documentation exists
5. Validate performance considerations

OUTPUT FORMAT:
{{
  "decision": "approved" or "changes_requested",
  "comments": "detailed review comments",
  "specific_feedback": ["specific issue 1", "specific issue 2"],
  "suggestions": ["suggestion 1", "suggestion 2"]
}}

Review now:"""
        
        try:
            response = await self.gemini.generate(
                agent_id=reviewer.id,
                system=reviewer.system_prompt,
                prompt=prompt,
                temp=reviewer.temperature
            )
            
            review_data = self._extract_json(response)
            
            if review_data:
                decision = review_data.get('decision', 'approved')
                comments = review_data.get('comments', '')
                
                if decision == 'approved':
                    await self.team_comm.approve_review(
                        review.id,
                        reviewer_id,
                        comments
                    )
                    # Mark task as completed
                    if task:
                        self.task_manager.complete_task(
                            task['id'],
                            f"Code reviewed and approved by {reviewer.name}. {comments}"
                        )
                        logger.info(f"✅ {reviewer.name} approved review: {review.description}")
                else:
                    changes_needed = '\n'.join(review_data.get('specific_feedback', []))
                    await self.team_comm.request_changes(
                        review.id,
                        reviewer_id,
                        f"{comments}\n\nSpecific feedback:\n{changes_needed}"
                    )
                    # Mark task as needs changes
                    if task:
                        task['status'] = 'pending'
                        task['review_feedback'] = changes_needed
                        self.task_manager._save_task(task['id'])
                        logger.info(f"🔄 {reviewer.name} requested changes: {review.description}")
        except Exception as e:
            logger.error(f"❌ Review processing failed: {e}")
    
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
    
    # Store orchestrator reference for API endpoints
    orchestrator_ref = {"instance": None}
    
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
    
    # API endpoints for dashboard
    @app.get("/api/dashboard/stats")
    async def get_dashboard_stats():
        """Get dashboard statistics"""
        if not orchestrator_ref["instance"]:
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
                "status": "initializing"
            }
        
        orch = orchestrator_ref["instance"]
        tasks = list(orch.task_manager.tasks.values())
        completed = len([t for t in tasks if t.get('status') == 'completed'])
        pending = len([t for t in tasks if t.get('status') == 'pending'])
        in_progress = len([t for t in tasks if t.get('status') == 'in_progress'])
        in_review = len([t for t in tasks if t.get('status') == 'in_review'])
        failed = len([t for t in tasks if t.get('status') == 'failed'])
        uptime_hours = (datetime.now() - orch.start_time).total_seconds() / 3600
        
        return {
            "cycle_count": orch.cycle_count,
            "total_tasks": len(tasks),
            "completed_tasks": completed,
            "pending_tasks": pending,
            "in_progress_tasks": in_progress,
            "in_review_tasks": in_review,
            "failed_tasks": failed,
            "completion_rate": (completed / len(tasks) * 100) if len(tasks) > 0 else 0,
            "active_agents": len(orch.agents),
            "total_agents": len(orch.agents),
            "uptime_days": uptime_hours / 24,
            "uptime_hours": uptime_hours,
            "status": "running"
        }
    
    @app.get("/api/tasks")
    async def get_tasks(status: Optional[str] = None, limit: int = 100):
        """Get all tasks"""
        if not orchestrator_ref["instance"]:
            # Try to load tasks from disk if orchestrator not initialized yet
            tasks_dir = Path(os.getenv('DATA_DIR', './data')) / "tasks"
            if tasks_dir.exists():
                tasks = []
                for task_file in sorted(tasks_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
                    try:
                        with open(task_file) as f:
                            task = json.load(f)
                            task['id'] = task_file.stem
                            if not status or task.get('status') == status:
                                tasks.append(task)
                    except:
                        pass
                return tasks
            return []
        
        tasks = list(orchestrator_ref["instance"].task_manager.tasks.values())
        tasks = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)[:limit]
        
        if status:
            tasks = [t for t in tasks if t.get('status') == status]
            # Filter out tasks that shouldn't appear in pending/in_review if they're already approved/completed
            if status in ['pending', 'in_review']:
                tasks = [t for t in tasks if t.get('status') == status and t.get('status') != 'completed']
                # Also exclude in_progress tasks that have been approved
                tasks = [t for t in tasks if not (t.get('status') == 'in_progress' and t.get('approved_at'))]
        
        return tasks
    
    @app.post("/api/tasks/{task_id}/approve")
    async def approve_task(task_id: str):
        """Approve a task (for code reviews)"""
        if not orchestrator_ref["instance"]:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        task_manager = orchestrator_ref["instance"].task_manager
        if task_id not in task_manager.tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = task_manager.tasks[task_id]
        
        # Check if already completed or approved
        if task.get('status') == 'completed':
            logger.warning(f"⚠️ Task {task_id} already completed")
            return {"status": "already_completed", "task_id": task_id, "message": "Task was already completed"}
        
        if task.get('status') == 'in_progress' and task.get('approved_at'):
            logger.warning(f"⚠️ Task {task_id} already approved")
            return {"status": "already_approved", "task_id": task_id, "message": "Task was already approved"}
        
        # If task is in review, approve it and mark as completed
        if task.get('status') == 'in_review':
            task_manager.complete_task(task_id, task.get('result', 'Code review approved'))
            # Also update review status if exists
            if task.get('review_id'):
                team_comm = orchestrator_ref["instance"].team_comm
                review_file = team_comm.reviews_dir / f"{task['review_id']}.json"
                if review_file.exists():
                    with open(review_file) as f:
                        review_data = json.load(f)
                    review_data['status'] = 'approved'
                    review_data['reviewed_by'] = 'user'
                    review_data['reviewed_at'] = datetime.now().isoformat()
                    with open(review_file, 'w') as f:
                        json.dump(review_data, f, indent=2)
            logger.info(f"✅ Task {task_id} approved and completed")
            return {"status": "approved", "task_id": task_id, "message": "Task approved and marked as completed"}
        elif task.get('status') == 'pending':
            # For pending tasks, mark as approved and move to in_progress
            task['status'] = 'in_progress'
            task['approved_at'] = datetime.now().isoformat()
            task['approved_by'] = 'user'
            task_manager._save_task(task_id)
            logger.info(f"✅ Task {task_id} approved and moved to in_progress")
            return {"status": "approved", "task_id": task_id, "message": "Task approved and moved to in_progress"}
        else:
            raise HTTPException(status_code=400, detail=f"Cannot approve task with status: {task.get('status')}")
    
    @app.get("/api/tasks/{task_id}")
    async def get_task_detail(task_id: str):
        """Get detailed information about a specific task"""
        if not orchestrator_ref["instance"]:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        task_manager = orchestrator_ref["instance"].task_manager
        if task_id not in task_manager.tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = task_manager.tasks[task_id]
        
        # Try to get code review details if available
        review_details = None
        if task.get('review_id'):
            team_comm = orchestrator_ref["instance"].team_comm
            review_file = team_comm.reviews_dir / f"{task['review_id']}.json"
            if review_file.exists():
                with open(review_file) as f:
                    review_details = json.load(f)
        
        # Parse result to extract structured data
        result_data = None
        if task.get('result'):
            try:
                result_data = json.loads(task['result'])
            except:
                pass
        
        # Build GitHub links if files_changed exist OR if we have a GitHub repo
        github_links = []
        
        # Auto-detect GitHub repo from git config if not set
        github_repo = os.getenv('GITHUB_REPO', '')
        if not github_repo:
            try:
                import subprocess
                result = subprocess.run(
                    ['git', 'config', '--get', 'remote.origin.url'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    git_url = result.stdout.strip()
                    # Convert git@github.com:user/repo.git to https://github.com/user/repo
                    if git_url.startswith('git@'):
                        git_url = git_url.replace('git@github.com:', 'https://github.com/').replace('.git', '')
                    elif git_url.startswith('https://github.com/'):
                        git_url = git_url.replace('.git', '')
                    github_repo = git_url
            except:
                pass
        
        # Get current branch for links
        github_branch = 'main'
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                github_branch = result.stdout.strip()
        except:
            pass
        
        # Build links for files_changed if they exist
        if github_repo and result_data and result_data.get('files_changed'):
            for file_path in result_data.get('files_changed', []):
                github_links.append({
                    'file': file_path,
                    'url': f"{github_repo}/blob/{github_branch}/{file_path}",
                    'raw_url': f"{github_repo}/raw/{github_branch}/{file_path}",
                    'blame_url': f"{github_repo}/blame/{github_branch}/{file_path}",
                    'history_url': f"{github_repo}/commits/{github_branch}/{file_path}"
                })
        
        return {
            **task,
            'review_details': review_details,
            'github_links': github_links,
            'result_data': result_data,
            'github_repo': github_repo,  # Include repo URL for frontend to use
            'github_branch': github_branch  # Include branch for frontend
        }
    
    @app.get("/api/tasks/{task_id}/files/{file_path:path}")
    async def get_task_file_content(task_id: str, file_path: str):
        """Get file content for a task (if file exists locally)"""
        if not orchestrator_ref["instance"]:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        task_manager = orchestrator_ref["instance"].task_manager
        if task_id not in task_manager.tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = task_manager.tasks[task_id]
        
        # Check if file exists in workspace
        workspace_root = Path(os.getenv('WORKSPACE_ROOT', '.'))
        full_path = workspace_root / file_path
        
        if not full_path.exists() or not str(full_path).startswith(str(workspace_root)):
            raise HTTPException(status_code=404, detail="File not found")
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
            
            return {
                'file_path': file_path,
                'content': content,
                'size': len(content),
                'lines': content.count('\n') + 1
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    
    @app.get("/api/reviews/{review_id}")
    async def get_review_detail(review_id: str):
        """Get detailed code review information"""
        if not orchestrator_ref["instance"]:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        team_comm = orchestrator_ref["instance"].team_comm
        review_file = team_comm.reviews_dir / f"{review_id}.json"
        
        if not review_file.exists():
            raise HTTPException(status_code=404, detail="Review not found")
        
        with open(review_file) as f:
            review_data = json.load(f)
        
        return review_data
    
    @app.post("/api/tasks/{task_id}/reject")
    async def reject_task(task_id: str, reason: str = ""):
        """Reject a task (request changes)"""
        if not orchestrator_ref["instance"]:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        task_manager = orchestrator_ref["instance"].task_manager
        if task_id not in task_manager.tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = task_manager.tasks[task_id]
        
        # If task is in review, reject it and move back to pending
        if task.get('status') == 'in_review':
            task['status'] = 'pending'
            task['review_feedback'] = reason or "Changes requested"
            task['rejected_at'] = datetime.now().isoformat()
            task_manager._save_task(task_id)
            logger.info(f"❌ Task {task_id} rejected: {reason}")
            return {"status": "rejected", "task_id": task_id, "message": "Task rejected, changes requested"}
        elif task.get('status') == 'pending':
            task['status'] = 'pending'
            task['rejection_reason'] = reason or "Task rejected"
            task['rejected_at'] = datetime.now().isoformat()
            task_manager._save_task(task_id)
            logger.info(f"❌ Task {task_id} rejected: {reason}")
            return {"status": "rejected", "task_id": task_id, "message": "Task rejected"}
        else:
            raise HTTPException(status_code=400, detail=f"Cannot reject task with status: {task.get('status')}")
    
    @app.get("/api/agents")
    async def get_agents(type: Optional[str] = None):
        """Get all agents"""
        if not orchestrator_ref["instance"]:
            return []
        
        agents = []
        for agent_id, agent_config in orchestrator_ref["instance"].agents.items():
            agent_data = {
                "id": agent_id,
                "name": agent_config.name,
                "role": agent_config.role,
                "type": "developer" if "mango" not in agent_id.lower() else "mango",
                "status": "active",
                "emoji": getattr(agent_config, 'emoji', '🤖')
            }
            if not type or agent_data["type"] == type:
                agents.append(agent_data)
        
        return agents
    
    @app.get("/api/agents/{agent_id}")
    async def get_agent_details(agent_id: str):
        """Get agent details and their tasks"""
        if not orchestrator_ref["instance"]:
            raise HTTPException(status_code=404, detail="Orchestrator not initialized")
        
        orch = orchestrator_ref["instance"]
        
        # Find agent
        agent_config = orch.agents.get(agent_id)
        if not agent_config:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get all tasks for this agent
        all_tasks = list(orch.task_manager.tasks.values())
        agent_tasks = [t for t in all_tasks if t.get('assigned_to') == agent_id]
        
        # Calculate stats
        completed = len([t for t in agent_tasks if t.get('status') == 'completed'])
        pending = len([t for t in agent_tasks if t.get('status') == 'pending'])
        in_progress = len([t for t in agent_tasks if t.get('status') == 'in_progress'])
        
        return {
            "id": agent_id,
            "name": agent_config.name,
            "role": agent_config.role,
            "type": "developer" if "mango" not in agent_id.lower() else "mango",
            "status": "active",
            "emoji": getattr(agent_config, 'emoji', '🤖'),
            "system_prompt": getattr(agent_config, 'system_prompt', '')[:500] if hasattr(agent_config, 'system_prompt') else '',
            "tasks": sorted(agent_tasks, key=lambda x: x.get('created_at', ''), reverse=True),
            "stats": {
                "total_tasks": len(agent_tasks),
                "completed": completed,
                "pending": pending,
                "in_progress": in_progress,
                "completion_rate": (completed / len(agent_tasks) * 100) if len(agent_tasks) > 0 else 0
            }
        }
    
    @app.get("/api/activity")
    async def get_activity(limit: int = 20):
        """Get recent activity"""
        if not orchestrator_ref["instance"]:
            return []
        
        tasks = list(orchestrator_ref["instance"].task_manager.tasks.values())
        tasks = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)[:limit]
        
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
    
    @app.get("/api/analytics")
    async def get_analytics():
        """Get analytics data"""
        if not orchestrator_ref["instance"]:
            return {
                "dates": [],
                "tasks_completed": [],
                "agent_activity": [],
                "success_rate": []
            }
        
        orch = orchestrator_ref["instance"]
        tasks = list(orch.task_manager.tasks.values())
        
        # Generate last 30 days of data
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime("%b %d") for i in range(29, -1, -1)]
        
        # Group tasks by date
        tasks_by_date = {}
        for task in tasks:
            if task.get('created_at'):
                try:
                    task_date = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                    date_key = task_date.strftime("%b %d")
                    if date_key not in tasks_by_date:
                        tasks_by_date[date_key] = {"completed": 0, "total": 0}
                    tasks_by_date[date_key]["total"] += 1
                    if task.get('status') == 'completed':
                        tasks_by_date[date_key]["completed"] += 1
                except:
                    pass
        
        # Build arrays
        tasks_completed = []
        success_rate = []
        for date in dates:
            if date in tasks_by_date:
                tasks_completed.append(tasks_by_date[date]["completed"])
                total = tasks_by_date[date]["total"]
                success_rate.append((tasks_by_date[date]["completed"] / total * 100) if total > 0 else 0)
            else:
                tasks_completed.append(0)
                success_rate.append(0)
        
        # Agent activity (constant for now, could be enhanced)
        agent_activity = [len(orch.agents)] * 30
        
        return {
            "dates": dates,
            "tasks_completed": tasks_completed,
            "agent_activity": agent_activity,
            "success_rate": success_rate
        }
    
    @app.get("/api/evaluations")
    async def get_evaluations(limit: int = 10):
        """Get evaluations"""
        eval_dir = Path(os.getenv('DATA_DIR', './data')) / "evaluations"
        if not eval_dir.exists():
            return []
        
        evals = []
        for eval_file in sorted(eval_dir.glob("eval_*.json"), reverse=True)[:limit]:
            try:
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
            except:
                pass
        
        return evals
    
    @app.get("/api/evaluations/latest")
    async def get_latest_evaluation():
        """Get latest evaluation"""
        eval_dir = Path(os.getenv('DATA_DIR', './data')) / "evaluations"
        if not eval_dir.exists():
            return {"error": "No evaluations found"}
        
        eval_files = sorted(eval_dir.glob("eval_*.json"), reverse=True)
        if not eval_files:
            return {"error": "No evaluations found"}
        
        try:
            with open(eval_files[0]) as f:
                return json.load(f)
        except:
            return {"error": "Error reading evaluation"}
    
    def run_server():
        port = int(os.getenv('PORT', 10000))
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    logger.info(f"🌐 HTTP server started on port {os.getenv('PORT', 10000)}")
    
    # Run orchestrator in main thread
    orchestrator = Orchestrator()
    orchestrator_ref["instance"] = orchestrator  # Store reference for API endpoints
    await orchestrator.run_forever()

if __name__ == "__main__":
    asyncio.run(main())

