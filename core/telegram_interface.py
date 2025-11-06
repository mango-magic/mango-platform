"""
Interactive Telegram Bot Interface - Manage your AI team from Telegram
Talk to agents, approve deployments, control the system
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
import os
import json
from pathlib import Path

logger = logging.getLogger('TelegramInterface')

class TelegramCommandHandler:
    """Handle interactive commands from Telegram"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.authorized_users = []  # Will be populated from env
        
    async def handle_command(self, message: dict) -> str:
        """Process incoming Telegram command"""
        text = message.get('text', '').strip()
        user_id = message.get('from', {}).get('id')
        
        # Command routing
        if text.startswith('/'):
            command = text.split()[0].lower()
            args = text.split()[1:] if len(text.split()) > 1 else []
            
            commands = {
                '/start': self.cmd_start,
                '/status': self.cmd_status,
                '/talk': self.cmd_talk_to_agent,
                '/approve': self.cmd_approve_deployment,
                '/reject': self.cmd_reject_deployment,
                '/pause': self.cmd_pause_system,
                '/resume': self.cmd_resume_system,
                '/activate': self.cmd_activate_mango,
                '/tasks': self.cmd_list_tasks,
                '/agents': self.cmd_list_agents,
                '/help': self.cmd_help,
                '/deploy': self.cmd_deployment_status,
                '/logs': self.cmd_recent_logs,
                '/metrics': self.cmd_team_metrics,
            }
            
            handler = commands.get(command)
            if handler:
                return await handler(args, user_id)
            else:
                return f"Unknown command: {command}\nType /help for available commands"
        
        # If not a command, assume it's a message to Marcus
        return await self.cmd_talk_to_agent(['marcus', text], user_id)
    
    async def cmd_start(self, args, user_id) -> str:
        """Welcome message"""
        return """
🥭 <b>Welcome to ManyMangoes Control Center!</b>

I'm your AI team management interface.

<b>Quick Commands:</b>
/status - Team status summary
/talk marcus [message] - Talk to Marcus
/agents - List all agents
/tasks - View current tasks
/deploy - Deployment status
/approve [id] - Approve production deployment
/activate [mango_id] - Activate a tested Mango

Type /help for full command list.

<b>Tip:</b> Just type a message to talk directly to Marcus!
        """
    
    async def cmd_status(self, args, user_id) -> str:
        """Get team status"""
        state = self.orchestrator._load_state()
        
        # Get task stats
        total_tasks = len(self.orchestrator.task_manager.tasks)
        completed = len([t for t in self.orchestrator.task_manager.tasks.values() 
                        if t.get('status') == 'completed'])
        pending = len([t for t in self.orchestrator.task_manager.tasks.values() 
                      if t.get('status') == 'pending'])
        
        # Get active agents
        active_agents = len([a for a in self.orchestrator.agents.values() if a.active])
        
        # Get environment
        env = await self.orchestrator.env_manager.get_current_environment()
        
        return f"""
📊 <b>Team Status Report</b>

⏰ <b>Uptime:</b> {state.get('uptime_hours', 0):.1f} hours
🔄 <b>Cycles:</b> {state.get('cycle_count', 0)}
🌍 <b>Environment:</b> {env.value.upper()}

👥 <b>Agents:</b>
  • Active: {active_agents}/39
  • Developers: 15 (all active)
  • Mangoes: 24 ({active_agents - 15} active)

📋 <b>Tasks:</b>
  • Total: {total_tasks}
  • Completed: {completed} ({(completed/total_tasks*100) if total_tasks > 0 else 0:.1f}%)
  • Pending: {pending}

Use /agents or /tasks for details.
        """
    
    async def cmd_talk_to_agent(self, args, user_id) -> str:
        """Send message to an agent"""
        if len(args) < 2:
            return "Usage: /talk [agent_name] [message]\nExample: /talk marcus What's the status of Mango EA?"
        
        agent_name = args[0].lower()
        message = ' '.join(args[1:])
        
        # Map common names to agent IDs
        name_map = {
            'marcus': 'eng_manager_001',
            'aria': 'backend_001',
            'kai': 'backend_002',
            'zara': 'backend_003',
            'luna': 'frontend_001',
            'river': 'frontend_002',
            'nova': 'ml_001',
            'sage': 'ml_002',
            'atlas': 'devops_001',
            'iris': 'qa_001',
        }
        
        agent_id = name_map.get(agent_name, agent_name)
        
        if agent_id not in self.orchestrator.agents:
            return f"❌ Agent '{agent_name}' not found.\n\nAvailable: marcus, aria, kai, zara, luna, river, nova, sage, atlas, iris"
        
        agent = self.orchestrator.agents[agent_id]
        
        # Send message via team communication
        from core.team_communication import Message
        await self.orchestrator.team_comm.send_message(Message(
            id=f"human_{datetime.now().timestamp()}",
            from_agent="human",
            to_agent=agent_id,
            message_type="question",
            subject="Message from Human",
            content=message,
            timestamp=datetime.now().isoformat(),
            priority="high"
        ))
        
        # Get AI response (in next cycle)
        prompt = f"""You received a message from your human manager:

"{message}"

Respond directly, professionally, and concisely. Use your core values (intellectual honesty, calm thinking, etc.)."""
        
        try:
            response = await self.orchestrator.gemini.generate(
                agent_id=agent_id,
                system=agent.system_prompt,
                prompt=prompt,
                temp=agent.temperature
            )
            
            return f"""
💬 <b>{agent.name} ({agent.role.value}):</b>

{response[:1000]}
            """
        except Exception as e:
            return f"❌ Error getting response from {agent.name}: {str(e)}"
    
    async def cmd_approve_deployment(self, args, user_id) -> str:
        """Approve production deployment"""
        if not args:
            # List pending deployments
            pending = await self.orchestrator.env_manager.get_pending_deployments()
            
            if not pending:
                return "✅ No pending deployments"
            
            msg = "<b>Pending Production Deployments:</b>\n\n"
            for deploy in pending:
                msg += f"🔹 <code>{deploy['id']}</code>\n"
                msg += f"   Component: {deploy['component']}\n"
                msg += f"   Version: {deploy['version']}\n"
                msg += f"   Status: {deploy['status']}\n\n"
            
            msg += "\nUse: /approve [deployment_id]"
            return msg
        
        deployment_id = args[0]
        
        # Approve deployment
        success = await self.orchestrator.env_manager.approve_deployment(deployment_id, "human")
        
        if success:
            return f"✅ Deployment {deployment_id} approved and deployed to PRODUCTION!"
        else:
            return f"❌ Failed to approve deployment {deployment_id}"
    
    async def cmd_reject_deployment(self, args, user_id) -> str:
        """Reject production deployment"""
        if not args:
            return "Usage: /reject [deployment_id] [reason]"
        
        deployment_id = args[0]
        reason = ' '.join(args[1:]) if len(args) > 1 else "Rejected by human"
        
        # Mark as failed
        deploy_file = self.orchestrator.env_manager.deployments_dir / f"{deployment_id}.json"
        if deploy_file.exists():
            with open(deploy_file) as f:
                deploy_data = json.load(f)
            
            deploy_data['status'] = 'failed'
            deploy_data['rejection_reason'] = reason
            
            with open(deploy_file, 'w') as f:
                json.dump(deploy_data, f, indent=2)
            
            return f"❌ Deployment {deployment_id} rejected.\nReason: {reason}"
        
        return f"❌ Deployment {deployment_id} not found"
    
    async def cmd_pause_system(self, args, user_id) -> str:
        """Pause the orchestrator"""
        self.orchestrator.paused = True
        return "⏸️ System PAUSED. No new cycles will start.\nUse /resume to continue."
    
    async def cmd_resume_system(self, args, user_id) -> str:
        """Resume the orchestrator"""
        self.orchestrator.paused = False
        return "▶️ System RESUMED. Cycles will continue."
    
    async def cmd_activate_mango(self, args, user_id) -> str:
        """Activate a Mango agent after testing"""
        if not args:
            return "Usage: /activate [mango_id]\nExample: /activate mango_data_001"
        
        mango_id = args[0]
        
        if mango_id not in self.orchestrator.agents:
            return f"❌ Mango '{mango_id}' not found"
        
        agent = self.orchestrator.agents[mango_id]
        
        if agent.type.value != 'mango':
            return f"❌ {mango_id} is not a Mango (it's a developer agent)"
        
        if agent.active:
            return f"✅ {agent.name} is already active"
        
        # Activate the Mango
        agent.active = True
        
        return f"""
🚀 <b>ACTIVATED: {agent.name}</b>

Agent ID: {mango_id}
Role: {agent.role.value}

This Mango will now receive tasks from Marcus.
Monitor closely for first few tasks!

Use /status to see updated agent count.
        """
    
    async def cmd_list_tasks(self, args, user_id) -> str:
        """List current tasks"""
        tasks = list(self.orchestrator.task_manager.tasks.values())
        
        if not tasks:
            return "📋 No tasks yet. Marcus will create them in the next cycle."
        
        # Group by status
        pending = [t for t in tasks if t.get('status') == 'pending']
        in_progress = [t for t in tasks if t.get('status') == 'in_progress']
        completed = [t for t in tasks if t.get('status') == 'completed']
        
        msg = "<b>📋 Task Summary:</b>\n\n"
        msg += f"⏳ Pending: {len(pending)}\n"
        msg += f"⚙️ In Progress: {len(in_progress)}\n"
        msg += f"✅ Completed: {len(completed)}\n\n"
        
        # Show recent 5 tasks
        recent = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
        msg += "<b>Recent Tasks:</b>\n\n"
        for task in recent:
            status_emoji = {'pending': '⏳', 'in_progress': '⚙️', 'completed': '✅', 'failed': '❌'}.get(task.get('status'), '❓')
            msg += f"{status_emoji} {task.get('title', 'Unknown')[:50]}\n"
            msg += f"   Assigned to: {task.get('assigned_to', 'Unknown')}\n\n"
        
        return msg
    
    async def cmd_list_agents(self, args, user_id) -> str:
        """List all agents"""
        developers = [a for a in self.orchestrator.agents.values() if a.type.value == 'developer']
        mangoes = [a for a in self.orchestrator.agents.values() if a.type.value == 'mango']
        
        msg = "<b>👥 Agent Roster:</b>\n\n"
        
        msg += "<b>DEVELOPERS (15):</b>\n"
        for agent in developers:
            status = "🟢" if agent.active else "⏸️"
            msg += f"{status} {agent.name} ({agent.role.value})\n"
        
        msg += f"\n<b>MANGOES ({len([m for m in mangoes if m.active])}/24 active):</b>\n"
        for agent in mangoes[:10]:  # Show first 10
            status = "🟢" if agent.active else "⚪"
            msg += f"{status} {agent.name}\n"
        
        if len(mangoes) > 10:
            msg += f"\n... and {len(mangoes) - 10} more Mangoes\n"
        
        return msg
    
    async def cmd_deployment_status(self, args, user_id) -> str:
        """Check deployment status"""
        test_health = await self.orchestrator.env_manager.get_environment_health('test')
        prod_health = await self.orchestrator.env_manager.get_environment_health('production')
        
        msg = "<b>🚀 Deployment Status:</b>\n\n"
        
        msg += f"<b>TEST Environment:</b>\n"
        msg += f"  Status: {test_health['status']}\n"
        msg += f"  Components: {test_health['components']}\n"
        msg += f"  Last Deploy: {test_health.get('last_deployment', 'Never')}\n\n"
        
        msg += f"<b>PRODUCTION Environment:</b>\n"
        msg += f"  Status: {prod_health['status']}\n"
        msg += f"  Components: {prod_health['components']}\n"
        msg += f"  Last Deploy: {prod_health.get('last_deployment', 'Never')}\n\n"
        
        # Pending deployments
        pending = await self.orchestrator.env_manager.get_pending_deployments()
        if pending:
            msg += f"\n⏳ <b>Pending Approvals:</b> {len(pending)}\n"
            msg += "Use /approve to review"
        
        return msg
    
    async def cmd_recent_logs(self, args, user_id) -> str:
        """Get recent log entries"""
        log_file = Path(os.getenv('LOG_DIR', './logs')) / 'orchestrator.log'
        
        if not log_file.exists():
            return "📋 No logs yet"
        
        # Read last 20 lines
        with open(log_file) as f:
            lines = f.readlines()[-20:]
        
        msg = "<b>📋 Recent Logs:</b>\n\n<code>"
        msg += ''.join(lines[-10:])  # Last 10 lines
        msg += "</code>"
        
        return msg[:4000]  # Telegram message limit
    
    async def cmd_team_metrics(self, args, user_id) -> str:
        """Get team performance metrics"""
        summary = await self.orchestrator.team_comm.get_team_status_summary()
        
        msg = "<b>📊 Team Performance Metrics:</b>\n\n"
        msg += f"📅 Date: {summary['date']}\n"
        msg += f"👥 Agents Reporting: {summary['agents_reporting']}\n"
        msg += f"✅ Tasks Completed: {summary['total_tasks_completed']}\n"
        msg += f"⚠️ Blockers: {summary['total_blockers']}\n"
        msg += f"🔍 Pending Reviews: {summary['pending_reviews']}\n"
        msg += f"⚡ Avg Velocity: {summary['avg_velocity']:.1f} tasks/agent/day\n"
        
        return msg
    
    async def cmd_help(self, args, user_id) -> str:
        """Show help"""
        return """
<b>🥭 ManyMangoes Command Reference:</b>

<b>📊 Monitoring:</b>
/status - Overall team status
/agents - List all agents
/tasks - View current tasks
/deploy - Deployment status
/metrics - Team performance
/logs - Recent log entries

<b>💬 Communication:</b>
/talk [agent] [message] - Talk to an agent
Just type a message - talks to Marcus

<b>🎛️ Control:</b>
/approve [id] - Approve production deploy
/reject [id] - Reject production deploy
/activate [mango_id] - Activate tested Mango
/pause - Pause system
/resume - Resume system

<b>Examples:</b>
• "What's the status of Mango EA?"
• /talk aria How's the core framework coming?
• /approve deploy_001
• /activate mango_data_001

<b>Tip:</b> Most commands work without arguments and show you options!
        """

async def start_telegram_listener(orchestrator):
    """Start listening for Telegram commands"""
    handler = TelegramCommandHandler(orchestrator)
    
    # Simple polling implementation
    # In production, use python-telegram-bot library
    logger.info("📱 Telegram command interface started")
    
    # For now, this is a placeholder
    # Actual implementation would use webhooks or polling
    pass

