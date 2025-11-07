"""
Tool executor for agents - actually executes actions
"""
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging
import asyncio

logger = logging.getLogger('ToolExecutor')

class ToolExecutor:
    """Executes actual tool actions for agents"""
    
    def __init__(self, agent_id: str, workspace_root: str = "/tmp/mango-platform"):
        self.agent_id = agent_id
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
    
    async def execute_action(self, action_type: str, action_data: Dict) -> Dict:
        """Execute a single action"""
        try:
            if action_type == "write_file":
                return await self.write_file(action_data)
            elif action_type == "run_command":
                return await self.run_command(action_data)
            elif action_type == "run_test":
                return await self.run_test(action_data)
            elif action_type == "git_commit":
                return await self.git_commit(action_data)
            elif action_type == "git_push":
                return await self.git_push(action_data)
            else:
                return {"success": False, "error": f"Unknown action type: {action_type}"}
        except Exception as e:
            logger.error(f"Error executing {action_type}: {e}")
            return {"success": False, "error": str(e)}
    
    async def write_file(self, data: Dict) -> Dict:
        """Write code to a file"""
        file_path = self.workspace_root / data.get('path', '')
        content = data.get('content', '')
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        file_path.write_text(content, encoding='utf-8')
        
        logger.info(f"📝 {self.agent_id} wrote {file_path} ({len(content)} chars)")
        return {
            "success": True,
            "file_path": str(file_path),
            "bytes_written": len(content.encode('utf-8'))
        }
    
    async def run_command(self, data: Dict) -> Dict:
        """Run a shell command"""
        command = data.get('command', '')
        cwd = data.get('cwd', str(self.workspace_root))
        
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        logger.info(f"🔧 {self.agent_id} ran: {command[:50]}...")
        
        return {
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout.decode('utf-8'),
            "stderr": stderr.decode('utf-8')
        }
    
    async def run_test(self, data: Dict) -> Dict:
        """Run tests"""
        test_path = data.get('path', '.')
        test_command = data.get('command', 'pytest')
        
        # Run pytest
        command = f"{test_command} {test_path} --json-report --json-report-file=/tmp/test_results.json"
        
        result = await self.run_command({
            "command": command,
            "cwd": str(self.workspace_root)
        })
        
        # Parse test results if available
        test_results = {}
        test_results_file = Path("/tmp/test_results.json")
        if test_results_file.exists():
            try:
                test_results = json.loads(test_results_file.read_text())
            except:
                pass
        
        return {
            **result,
            "test_results": test_results
        }
    
    async def git_commit(self, data: Dict) -> Dict:
        """Commit changes to git"""
        message = data.get('message', f'Work by {self.agent_id}')
        files = data.get('files', [])
        
        # Stage files
        if files:
            for file in files:
                await self.run_command({
                    "command": f"git add {file}",
                    "cwd": str(self.workspace_root)
                })
        else:
            await self.run_command({
                "command": "git add -A",
                "cwd": str(self.workspace_root)
            })
        
        # Commit
        result = await self.run_command({
            "command": f'git commit -m "{message}"',
            "cwd": str(self.workspace_root)
        })
        
        if result["success"]:
            # Get commit hash
            hash_result = await self.run_command({
                "command": "git rev-parse HEAD",
                "cwd": str(self.workspace_root)
            })
            commit_hash = hash_result["stdout"].strip() if hash_result["success"] else None
            
            logger.info(f"✅ {self.agent_id} committed: {commit_hash}")
            return {
                **result,
                "commit_hash": commit_hash
            }
        
        return result
    
    async def git_push(self, data: Dict) -> Dict:
        """Push to git remote"""
        branch = data.get('branch', 'main')
        
        result = await self.run_command({
            "command": f"git push origin {branch}",
            "cwd": str(self.workspace_root)
        })
        
        logger.info(f"🚀 {self.agent_id} pushed to {branch}")
        return result

