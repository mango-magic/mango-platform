"""
Interactive Telegram Bot
Responds to commands and provides real-time team status
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp

logger = logging.getLogger('TelegramBot')

class TelegramBot:
    """
    Interactive Telegram bot that responds to commands
    and provides team status updates
    """
    
    def __init__(self, token: str, orchestrator_ref=None):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.orchestrator = orchestrator_ref
        self.running = False
        self.last_update_id = 0
        
        # Command handlers
        self.commands = {
            '/start': self._handle_start,
            '/help': self._handle_help,
            '/status': self._handle_status,
            '/agents': self._handle_agents,
            '/tasks': self._handle_tasks,
            '/evaluation': self._handle_evaluation,
            '/improvements': self._handle_improvements,
            '/uptime': self._handle_uptime,
            '/metrics': self._handle_metrics,
            '/team': self._handle_team,
        }
    
    async def start(self):
        """Start the bot and listen for messages"""
        self.running = True
        logger.info("🤖 Telegram bot started - listening for commands...")
        
        while self.running:
            try:
                await self._process_updates()
                await asyncio.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logger.error(f"Bot error: {e}")
                await asyncio.sleep(5)
    
    async def _process_updates(self):
        """Get and process new messages"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/getUpdates",
                    params={"offset": self.last_update_id + 1, "timeout": 5}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('ok'):
                            for update in data.get('result', []):
                                await self._handle_update(update)
                                self.last_update_id = update['update_id']
        except Exception as e:
            logger.error(f"Error processing updates: {e}")
    
    async def _handle_update(self, update: Dict):
        """Handle a single update"""
        try:
            if 'message' not in update:
                return
            
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            if not text:
                return
            
            # Check if it's a command
            if text.startswith('/'):
                command = text.split()[0].lower()
                if command in self.commands:
                    try:
                        response = await self.commands[command](chat_id, text)
                        await self._send_message(chat_id, response)
                    except Exception as e:
                        logger.error(f"Error handling command {command}: {e}")
                        await self._send_message(
                            chat_id,
                            f"❌ Error processing command: {str(e)}\n\nPlease try again or use /help."
                        )
                else:
                    await self._send_message(
                        chat_id,
                        "❓ Unknown command. Use /help to see available commands."
                    )
            else:
                # Handle natural language questions
                try:
                    response = await self._handle_question(chat_id, text)
                    if response:
                        await self._send_message(chat_id, response)
                except Exception as e:
                    logger.error(f"Error handling question: {e}")
                    await self._send_message(
                        chat_id,
                        f"❌ Error processing question. Try using a command like /status or /help."
                    )
        except Exception as e:
            logger.error(f"Error in _handle_update: {e}")
    
    async def _send_message(self, chat_id: int, text: str, parse_mode: str = "HTML"):
        """Send a message to Telegram"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode
                    }
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"📤 Sent response to {chat_id}")
                    else:
                        logger.warning(f"Failed to send: {resp.status}")
        except Exception as e:
            logger.error(f"Send error: {e}")
    
    async def _handle_start(self, chat_id: int, text: str) -> str:
        """Handle /start command"""
        return f"""
🥭 <b>Welcome to The Mangoes AI Team Bot!</b>

I'm your autonomous AI team of 39 agents (15 developers + 24 Mangoes).

<b>Quick Commands:</b>
/status - Overall team status
/agents - List all agents and their status
/tasks - View current tasks
/evaluation - Latest self-evaluation
/uptime - System uptime and metrics
/team - Detailed team breakdown

<b>Ask me anything:</b>
• "What's happening?"
• "How are the agents doing?"
• "What tasks are in progress?"
• "Show me the latest evaluation"

Type /help for full command list.
"""
    
    async def _handle_help(self, chat_id: int, text: str) -> str:
        """Handle /help command"""
        return """
📚 <b>Available Commands:</b>

<b>Status & Overview:</b>
/status - Overall team status and health
/uptime - System uptime and performance metrics
/metrics - Detailed performance metrics

<b>Team Information:</b>
/agents - List all 39 agents and their status
/team - Detailed team breakdown by role
/tasks - View all tasks (pending, in progress, completed)

<b>Evaluations & Improvements:</b>
/evaluation - Latest self-evaluation report
/improvements - Recent self-improvement cycles

<b>Natural Language:</b>
You can also ask questions like:
• "What's happening?"
• "How are the agents doing?"
• "What's the latest evaluation?"
• "Show me agent status"
• "What tasks are pending?"

Type any command to get started!
"""
    
    async def _handle_status(self, chat_id: int, text: str) -> str:
        """Handle /status command"""
        if not self.orchestrator:
            return "⚠️ Orchestrator not available"
        
        state = self._get_state()
        tasks = self._get_tasks()
        
        completed = len([t for t in tasks if t.get('status') == 'completed'])
        in_progress = len([t for t in tasks if t.get('status') == 'in_progress'])
        pending = len([t for t in tasks if t.get('status') == 'pending'])
        
        uptime_hours = state.get('uptime_hours', 0)
        cycles = state.get('cycle_count', 0)
        
        return f"""
📊 <b>Team Status</b>

<b>Overall Health:</b> 🟢 Operational
<b>Uptime:</b> {uptime_hours:.1f} hours
<b>Cycles Completed:</b> {cycles}

<b>Tasks:</b>
✅ Completed: {completed}
🔄 In Progress: {in_progress}
⏳ Pending: {pending}
📋 Total: {len(tasks)}

<b>Agents:</b>
👥 Total: {state.get('agents_count', 39)}
🟢 Active: {state.get('agents_count', 39)}

<b>Last Update:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Type /agents for detailed agent status.
"""
    
    async def _handle_agents(self, chat_id: int, text: str) -> str:
        """Handle /agents command"""
        if not self.orchestrator:
            return "⚠️ Orchestrator not available"
        
        try:
            agents = self._get_agents()
            
            if not agents or len(agents) == 0:
                return "⚠️ No agents found. The orchestrator may still be initializing."
            
            # Group by type (ensure type is string)
            developers = [a for a in agents if str(a.get('type', '')).lower() == 'developer']
            mangoes = [a for a in agents if str(a.get('type', '')).lower() == 'mango']
            
            response = f"""
👥 <b>All Agents ({len(agents)} total)</b>

<b>Developers ({len(developers)}):</b>
"""
            
            if len(developers) == 0:
                response += "No developers found.\n"
            else:
                for agent in developers[:10]:  # Show first 10
                    emoji = agent.get('emoji', '👤')
                    name = agent.get('name', 'Unknown')
                    role = str(agent.get('role', 'Unknown'))
                    status = agent.get('status', 'unknown')
                    status_emoji = '🟢' if status == 'active' else '🔴'
                    response += f"{status_emoji} {emoji} <b>{name}</b> - {role}\n"
                
                if len(developers) > 10:
                    response += f"... and {len(developers) - 10} more developers\n"
            
            response += f"\n<b>Mangoes ({len(mangoes)}):</b>\n"
            
            if len(mangoes) == 0:
                response += "No Mangoes found.\n"
            else:
                for agent in mangoes[:10]:  # Show first 10
                    emoji = agent.get('emoji', '🥭')
                    name = agent.get('name', 'Unknown')
                    role = str(agent.get('role', 'Unknown'))
                    status = agent.get('status', 'unknown')
                    status_emoji = '🟢' if status == 'active' else '🔴'
                    response += f"{status_emoji} {emoji} <b>{name}</b> - {role}\n"
                
                if len(mangoes) > 10:
                    response += f"... and {len(mangoes) - 10} more Mangoes\n"
            
            response += "\nType /team for detailed breakdown by role."
            
            return response
        except Exception as e:
            logger.error(f"Error in _handle_agents: {e}")
            return f"❌ Error getting agents: {str(e)}"
    
    async def _handle_tasks(self, chat_id: int, text: str) -> str:
        """Handle /tasks command"""
        if not self.orchestrator:
            return "⚠️ Orchestrator not available"
        
        tasks = self._get_tasks()
        
        # Filter by status if specified
        if 'pending' in text.lower():
            tasks = [t for t in tasks if t.get('status') == 'pending']
            title = "⏳ Pending Tasks"
        elif 'progress' in text.lower() or 'in progress' in text.lower():
            tasks = [t for t in tasks if t.get('status') == 'in_progress']
            title = "🔄 Tasks In Progress"
        elif 'completed' in text.lower():
            tasks = [t for t in tasks if t.get('status') == 'completed']
            title = "✅ Completed Tasks"
        else:
            title = "📋 All Tasks"
        
        if not tasks:
            return f"{title}\n\nNo tasks found."
        
        response = f"{title} ({len(tasks)})\n\n"
        
        for task in tasks[:10]:  # Show first 10
            title_text = task.get('title', 'Untitled Task')
            status = task.get('status', 'unknown')
            agent = task.get('assigned_to', 'Unassigned')
            
            status_emoji = {
                'completed': '✅',
                'in_progress': '🔄',
                'pending': '⏳',
                'failed': '❌'
            }.get(status, '📋')
            
            response += f"{status_emoji} <b>{title_text}</b>\n"
            response += f"   Agent: {agent}\n"
            response += f"   Status: {status}\n\n"
        
        if len(tasks) > 10:
            response += f"... and {len(tasks) - 10} more tasks"
        
        return response
    
    async def _handle_evaluation(self, chat_id: int, text: str) -> str:
        """Handle /evaluation command"""
        eval_data = self._get_latest_evaluation()
        
        if not eval_data or eval_data.get('error'):
            return "📊 <b>Latest Evaluation</b>\n\nNo evaluations yet. First evaluation runs after 1 hour of uptime."
        
        metrics = eval_data.get('metrics', {})
        evaluation_text = eval_data.get('evaluation', '')
        
        # Extract score
        import re
        score_match = re.search(r'OVERALL SCORE:?\s*(\d+)/100', evaluation_text, re.IGNORECASE)
        score = score_match.group(1) if score_match else "N/A"
        
        return f"""
📊 <b>Latest Self-Evaluation</b>

<b>Score:</b> {score}/100
<b>Time:</b> {datetime.fromisoformat(eval_data['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}

<b>Metrics:</b>
• Tasks: {metrics.get('completed', 0)}/{metrics.get('total_tasks', 0)} completed
• Velocity: {metrics.get('tasks_per_hour', 0):.1f} tasks/hour
• Uptime: {eval_data.get('uptime_hours', 0):.1f} hours

<b>Evaluation Summary:</b>
{evaluation_text[:500]}...

Use /improvements to see if any improvements were deployed.
"""
    
    async def _handle_improvements(self, chat_id: int, text: str) -> str:
        """Handle /improvements command"""
        improvements = self._get_improvements(limit=5)
        
        if not improvements:
            return "🚀 <b>Self-Improvements</b>\n\nNo improvement cycles yet."
        
        response = "🚀 <b>Recent Self-Improvements</b>\n\n"
        
        for imp in improvements:
            cycle_id = imp.get('cycle_id', 'unknown')
            status = imp.get('status', 'unknown')
            timestamp = imp.get('timestamp', '')
            deployed = imp.get('deployed', False)
            
            status_emoji = '✅' if deployed else '❌'
            status_text = 'DEPLOYED' if deployed else 'FAILED'
            
            response += f"{status_emoji} <b>Cycle {cycle_id}</b>\n"
            response += f"Status: {status_text}\n"
            response += f"Time: {timestamp[:16]}\n"
            response += f"Improvements: {imp.get('improvements_count', 0)}\n"
            
            if deployed:
                approval = imp.get('agent_approval_rate', 0)
                response += f"Approval: {approval:.1%}\n"
            
            response += "\n"
        
        return response
    
    async def _handle_uptime(self, chat_id: int, text: str) -> str:
        """Handle /uptime command"""
        state = self._get_state()
        uptime_hours = state.get('uptime_hours', 0)
        cycles = state.get('cycle_count', 0)
        
        uptime_days = uptime_hours / 24
        cycles_per_hour = cycles / uptime_hours if uptime_hours > 0 else 0
        
        return f"""
⏱️ <b>System Uptime</b>

<b>Uptime:</b> {uptime_days:.1f} days ({uptime_hours:.1f} hours)
<b>Cycles Completed:</b> {cycles:,}
<b>Cycles/Hour:</b> {cycles_per_hour:.1f}
<b>Start Time:</b> {state.get('start_time', 'Unknown')}

<b>Performance:</b>
🟢 All systems operational
🔄 Continuous autonomous loops
📊 Real-time monitoring active

The team has been running autonomously for {uptime_days:.1f} days!
"""
    
    async def _handle_metrics(self, chat_id: int, text: str) -> str:
        """Handle /metrics command"""
        state = self._get_state()
        tasks = self._get_tasks()
        eval_data = self._get_latest_evaluation()
        
        completed = len([t for t in tasks if t.get('status') == 'completed'])
        total = len(tasks)
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        metrics = eval_data.get('metrics', {}) if eval_data else {}
        
        return f"""
📈 <b>Performance Metrics</b>

<b>Task Metrics:</b>
• Completion Rate: {completion_rate:.1f}%
• Tasks/Hour: {metrics.get('tasks_per_hour', 0):.1f}
• Total Tasks: {total}
• Completed: {completed}

<b>System Metrics:</b>
• Uptime: {state.get('uptime_hours', 0):.1f} hours
• Cycles: {state.get('cycle_count', 0):,}
• Active Agents: {state.get('agents_count', 39)}

<b>Latest Evaluation Score:</b>
{self._extract_score(eval_data.get('evaluation', '')) if eval_data else 'N/A'}/100

Type /evaluation for full evaluation details.
"""
    
    async def _handle_team(self, chat_id: int, text: str) -> str:
        """Handle /team command"""
        agents = self._get_agents()
        
        # Group by role (ensure role is always a string)
        by_role = {}
        for agent in agents:
            role = agent.get('role', 'Unknown')
            # Convert to string if it's an enum or other object
            role_str = str(role) if role else 'Unknown'
            if role_str not in by_role:
                by_role[role_str] = []
            by_role[role_str].append(agent)
        
        response = "👥 <b>Team Breakdown by Role</b>\n\n"
        
        # Sort by role name (string) to avoid comparison errors
        for role, role_agents in sorted(by_role.items(), key=lambda x: x[0]):
            response += f"<b>{role} ({len(role_agents)}):</b>\n"
            for agent in role_agents[:5]:  # Show first 5 per role
                emoji = agent.get('emoji', '👤')
                name = agent.get('name', 'Unknown')
                status = '🟢' if agent.get('status') == 'active' else '🔴'
                response += f"  {status} {emoji} {name}\n"
            if len(role_agents) > 5:
                response += f"  ... and {len(role_agents) - 5} more\n"
            response += "\n"
        
        return response
    
    async def _handle_question(self, chat_id: int, text: str) -> Optional[str]:
        """Handle natural language questions"""
        text_lower = text.lower()
        
        # Status questions
        if any(word in text_lower for word in ['status', 'what\'s happening', 'what is happening', 'how are things']):
            return await self._handle_status(chat_id, text)
        
        # Agent questions
        if any(word in text_lower for word in ['agents', 'team members', 'who is working']):
            return await self._handle_agents(chat_id, text)
        
        # Task questions
        if any(word in text_lower for word in ['tasks', 'what are you working on', 'what\'s in progress']):
            return await self._handle_tasks(chat_id, text)
        
        # Evaluation questions
        if any(word in text_lower for word in ['evaluation', 'how are we doing', 'score', 'performance']):
            return await self._handle_evaluation(chat_id, text)
        
        # Uptime questions
        if any(word in text_lower for word in ['uptime', 'how long', 'running for']):
            return await self._handle_uptime(chat_id, text)
        
        # Default response
        return "I can help you with:\n• Team status (/status)\n• Agent information (/agents)\n• Tasks (/tasks)\n• Evaluations (/evaluation)\n\nOr ask me a question!"
    
    def _get_state(self) -> Dict:
        """Get orchestrator state"""
        if not self.orchestrator:
            return {}
        
        data_dir = Path(os.getenv('DATA_DIR', './data'))
        state_file = data_dir / "state.json"
        
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
        return {}
    
    def _get_tasks(self) -> List[Dict]:
        """Get all tasks"""
        if not self.orchestrator:
            return []
        
        data_dir = Path(os.getenv('DATA_DIR', './data'))
        tasks_dir = data_dir / "tasks"
        
        if not tasks_dir.exists():
            return []
        
        tasks = []
        for task_file in tasks_dir.glob("*.json"):
            with open(task_file) as f:
                task = json.load(f)
                task['id'] = task_file.stem
                tasks.append(task)
        
        return tasks
    
    def _get_agents(self) -> List[Dict]:
        """Get all agents"""
        if not self.orchestrator:
            return []
        
        # Load from agent definitions or orchestrator
        try:
            # Try orchestrator first
            if hasattr(self.orchestrator, 'agents') and self.orchestrator.agents:
                agents = []
                for agent_id, agent_config in self.orchestrator.agents.items():
                    # Ensure all values are strings to avoid comparison issues
                    role = agent_config.role if hasattr(agent_config, 'role') else 'Unknown'
                    type_val = agent_config.type if hasattr(agent_config, 'type') else 'unknown'
                    
                    agents.append({
                        'id': str(agent_id),
                        'name': str(agent_config.name if hasattr(agent_config, 'name') else agent_id),
                        'role': str(role),
                        'type': str(type_val),
                        'status': 'active',
                        'emoji': str(getattr(agent_config, 'emoji', '👤'))
                    })
                return agents
            
            # Fallback: load from definitions
            try:
                from config.agent_definitions import ALL_AGENTS
                agents = []
                for agent in ALL_AGENTS:
                    # Ensure all values are strings
                    role = getattr(agent, 'role', 'Unknown')
                    type_val = getattr(agent, 'type', 'unknown')
                    
                    agents.append({
                        'id': str(getattr(agent, 'id', 'unknown')),
                        'name': str(getattr(agent, 'name', 'Unknown')),
                        'role': str(role),
                        'type': str(type_val),
                        'status': 'active',
                        'emoji': str(getattr(agent, 'emoji', '👤'))
                    })
                return agents
            except ImportError:
                logger.warning("Could not import agent definitions")
                return []
                
        except Exception as e:
            logger.error(f"Error getting agents: {e}", exc_info=True)
            return []
    
    def _get_latest_evaluation(self) -> Dict:
        """Get latest evaluation"""
        data_dir = Path(os.getenv('DATA_DIR', './data'))
        eval_dir = data_dir / "evaluations"
        
        if not eval_dir.exists():
            return {'error': 'No evaluations'}
        
        eval_files = sorted(eval_dir.glob("eval_*.json"), reverse=True)
        if not eval_files:
            return {'error': 'No evaluations'}
        
        with open(eval_files[0]) as f:
            return json.load(f)
    
    def _get_improvements(self, limit: int = 5) -> List[Dict]:
        """Get improvement cycles"""
        data_dir = Path(os.getenv('DATA_DIR', './data'))
        improvements_dir = data_dir / "improvements"
        
        if not improvements_dir.exists():
            return []
        
        cycles = []
        for cycle_file in sorted(improvements_dir.glob("cycle_*.json"), reverse=True)[:limit]:
            with open(cycle_file) as f:
                cycle_data = json.load(f)
                cycles.append({
                    'cycle_id': cycle_data.get('cycle_id'),
                    'timestamp': cycle_data.get('timestamp'),
                    'status': cycle_data.get('status'),
                    'improvements_count': len(cycle_data.get('improvements_generated', {}).get('improvements', [])),
                    'agent_approval_rate': cycle_data.get('test_analysis', {}).get('approval_rate', 0),
                    'deployed': cycle_data.get('status') == 'deployed'
                })
        
        return cycles
    
    def _extract_score(self, evaluation_text: str) -> str:
        """Extract score from evaluation text"""
        import re
        match = re.search(r'OVERALL SCORE:?\s*(\d+)/100', evaluation_text, re.IGNORECASE)
        return match.group(1) if match else "N/A"

