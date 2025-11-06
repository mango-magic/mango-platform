"""
Team Communication System - Real world-class dev team collaboration
Agents communicate, report, review code, and work together like humans
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger('TeamComm')

@dataclass
class Message:
    """Inter-agent communication message"""
    id: str
    from_agent: str
    to_agent: str  # Can be "all" for broadcasts
    message_type: str  # "question", "code_review", "status_update", "blocker", "help_request"
    subject: str
    content: str
    timestamp: str
    priority: str  # "low", "normal", "high", "urgent"
    thread_id: Optional[str] = None  # For threading conversations
    attachments: Optional[Dict] = None  # Code snippets, test results, etc.

@dataclass
class StatusReport:
    """Agent status report - like daily standup"""
    agent_id: str
    agent_name: str
    timestamp: str
    completed_today: List[str]
    working_on: str
    blockers: List[str]
    needs_help_from: List[str]
    code_reviews_done: int
    tests_written: int
    bugs_fixed: int
    velocity_score: float  # Tasks completed per day

@dataclass
class CodeReviewRequest:
    """Code review request between agents"""
    id: str
    from_agent: str
    to_agent: str  # Usually Marcus or senior engineer
    pr_url: str
    files_changed: List[str]
    description: str
    test_coverage: float
    timestamp: str
    priority: str
    status: str  # "pending", "approved", "changes_requested", "merged"

class TeamCommunication:
    """Manages all team communication and collaboration"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.messages_dir = data_dir / "team_messages"
        self.reports_dir = data_dir / "status_reports"
        self.reviews_dir = data_dir / "code_reviews"
        
        # Create directories
        for dir_path in [self.messages_dir, self.reports_dir, self.reviews_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for recent messages
        self.recent_messages = []
        self.pending_reviews = {}
        
        logger.info("🤝 Team communication system initialized")
    
    async def send_message(self, message: Message):
        """Send message from one agent to another"""
        # Save to disk
        msg_file = self.messages_dir / f"{message.id}.json"
        with open(msg_file, 'w') as f:
            json.dump(asdict(message), f, indent=2)
        
        # Cache in memory
        self.recent_messages.append(message)
        if len(self.recent_messages) > 100:
            self.recent_messages.pop(0)
        
        logger.info(f"💬 {message.from_agent} → {message.to_agent}: {message.subject}")
        
        return message.id
    
    async def get_messages_for_agent(self, agent_id: str, unread_only: bool = True) -> List[Message]:
        """Get messages for a specific agent"""
        messages = []
        
        for msg_file in self.messages_dir.glob("*.json"):
            with open(msg_file) as f:
                data = json.load(f)
                if data['to_agent'] == agent_id or data['to_agent'] == "all":
                    messages.append(Message(**data))
        
        # Sort by timestamp, most recent first
        messages.sort(key=lambda x: x.timestamp, reverse=True)
        
        return messages[:20]  # Return last 20 messages
    
    async def submit_status_report(self, report: StatusReport):
        """Submit daily status report (like standup)"""
        report_file = self.reports_dir / f"{report.agent_id}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        
        logger.info(f"📊 {report.agent_name} submitted status report")
        
        # Broadcast to team
        await self.send_message(Message(
            id=f"status_{report.agent_id}_{datetime.now().timestamp()}",
            from_agent=report.agent_id,
            to_agent="all",
            message_type="status_update",
            subject=f"{report.agent_name} Daily Standup",
            content=f"""
**Completed Today:** {len(report.completed_today)} tasks
**Currently Working On:** {report.working_on}
**Blockers:** {', '.join(report.blockers) if report.blockers else 'None'}
**Velocity:** {report.velocity_score:.1f} tasks/day
            """.strip(),
            timestamp=report.timestamp,
            priority="normal"
        ))
    
    async def request_code_review(self, review: CodeReviewRequest):
        """Request code review from another agent"""
        review_file = self.reviews_dir / f"{review.id}.json"
        with open(review_file, 'w') as f:
            json.dump(asdict(review), f, indent=2)
        
        self.pending_reviews[review.id] = review
        
        logger.info(f"🔍 {review.from_agent} requested review from {review.to_agent}")
        
        # Send message
        await self.send_message(Message(
            id=f"review_req_{review.id}",
            from_agent=review.from_agent,
            to_agent=review.to_agent,
            message_type="code_review",
            subject=f"Code Review: {review.description}",
            content=f"""
**PR:** {review.pr_url}
**Files Changed:** {len(review.files_changed)}
**Test Coverage:** {review.test_coverage}%
**Priority:** {review.priority}

Please review and approve/request changes.
            """.strip(),
            timestamp=review.timestamp,
            priority=review.priority,
            attachments={"review_id": review.id}
        ))
    
    async def get_pending_reviews_for_agent(self, agent_id: str) -> List[CodeReviewRequest]:
        """Get pending code reviews assigned to agent"""
        pending = []
        
        for review_file in self.reviews_dir.glob("*.json"):
            with open(review_file) as f:
                data = json.load(f)
                if data['to_agent'] == agent_id and data['status'] == 'pending':
                    pending.append(CodeReviewRequest(**data))
        
        return pending
    
    async def approve_review(self, review_id: str, approver: str, comments: str = ""):
        """Approve a code review"""
        review_file = self.reviews_dir / f"{review_id}.json"
        
        if review_file.exists():
            with open(review_file) as f:
                review_data = json.load(f)
            
            review_data['status'] = 'approved'
            review_data['approved_by'] = approver
            review_data['approval_time'] = datetime.now().isoformat()
            review_data['comments'] = comments
            
            with open(review_file, 'w') as f:
                json.dump(review_data, f, indent=2)
            
            logger.info(f"✅ {approver} approved review {review_id}")
            
            # Notify submitter
            await self.send_message(Message(
                id=f"approval_{review_id}_{datetime.now().timestamp()}",
                from_agent=approver,
                to_agent=review_data['from_agent'],
                message_type="code_review",
                subject=f"✅ Code Review Approved: {review_data['description']}",
                content=f"Your code has been reviewed and approved.\n\n{comments}",
                timestamp=datetime.now().isoformat(),
                priority="normal"
            ))
            
            return True
        
        return False
    
    async def request_changes(self, review_id: str, reviewer: str, changes_needed: str):
        """Request changes on a code review"""
        review_file = self.reviews_dir / f"{review_id}.json"
        
        if review_file.exists():
            with open(review_file) as f:
                review_data = json.load(f)
            
            review_data['status'] = 'changes_requested'
            review_data['reviewed_by'] = reviewer
            review_data['changes_needed'] = changes_needed
            
            with open(review_file, 'w') as f:
                json.dump(review_data, f, indent=2)
            
            logger.info(f"🔄 {reviewer} requested changes on {review_id}")
            
            # Notify submitter
            await self.send_message(Message(
                id=f"changes_{review_id}_{datetime.now().timestamp()}",
                from_agent=reviewer,
                to_agent=review_data['from_agent'],
                message_type="code_review",
                subject=f"🔄 Changes Requested: {review_data['description']}",
                content=f"Changes needed:\n\n{changes_needed}",
                timestamp=datetime.now().isoformat(),
                priority="high"
            ))
            
            return True
        
        return False
    
    async def ask_for_help(self, from_agent: str, to_agent: str, question: str):
        """One agent asks another for help"""
        await self.send_message(Message(
            id=f"help_{from_agent}_{datetime.now().timestamp()}",
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="help_request",
            subject="Help Needed",
            content=question,
            timestamp=datetime.now().isoformat(),
            priority="high"
        ))
    
    async def report_blocker(self, agent_id: str, blocker_description: str):
        """Report a blocker to Marcus and team"""
        await self.send_message(Message(
            id=f"blocker_{agent_id}_{datetime.now().timestamp()}",
            from_agent=agent_id,
            to_agent="eng_manager_001",  # Marcus
            message_type="blocker",
            subject="⚠️ BLOCKER",
            content=blocker_description,
            timestamp=datetime.now().isoformat(),
            priority="urgent"
        ))
        
        logger.warning(f"⚠️ BLOCKER reported by {agent_id}: {blocker_description}")
    
    async def get_team_status_summary(self) -> Dict:
        """Get summary of entire team status - for Marcus"""
        today = datetime.now().strftime('%Y%m%d')
        
        summary = {
            "date": today,
            "agents_reporting": 0,
            "total_tasks_completed": 0,
            "total_blockers": 0,
            "pending_reviews": len(self.pending_reviews),
            "avg_velocity": 0.0,
            "agent_reports": []
        }
        
        velocities = []
        
        for report_file in self.reports_dir.glob(f"*_{today}.json"):
            with open(report_file) as f:
                report = json.load(f)
                summary["agents_reporting"] += 1
                summary["total_tasks_completed"] += len(report.get('completed_today', []))
                summary["total_blockers"] += len(report.get('blockers', []))
                velocities.append(report.get('velocity_score', 0.0))
                summary["agent_reports"].append(report)
        
        if velocities:
            summary["avg_velocity"] = sum(velocities) / len(velocities)
        
        return summary

class TeamChannel:
    """Slack-like channels for team communication"""
    
    def __init__(self, channel_name: str, data_dir: Path):
        self.channel_name = channel_name
        self.channel_dir = data_dir / "channels" / channel_name
        self.channel_dir.mkdir(parents=True, exist_ok=True)
        self.messages = []
    
    async def post(self, from_agent: str, message: str, attachments: Dict = None):
        """Post message to channel"""
        msg = {
            "from": from_agent,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "attachments": attachments
        }
        
        msg_file = self.channel_dir / f"{datetime.now().timestamp()}.json"
        with open(msg_file, 'w') as f:
            json.dump(msg, f, indent=2)
        
        logger.info(f"📣 #{self.channel_name}: {from_agent}: {message[:50]}...")
    
    async def get_recent(self, limit: int = 50) -> List[Dict]:
        """Get recent messages from channel"""
        messages = []
        
        for msg_file in sorted(self.channel_dir.glob("*.json"), reverse=True)[:limit]:
            with open(msg_file) as f:
                messages.append(json.load(f))
        
        return messages

