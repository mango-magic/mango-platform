"""
Self-Improvement Cycle
After evaluation, the team rewrites its own code, tests it, and deploys to production.
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp

logger = logging.getLogger('SelfImprovement')

class SelfImprovementCycle:
    """
    Manages the complete self-improvement cycle:
    1. Receive evaluation results
    2. Generate code improvements with Gemini
    3. Deploy to test environment
    4. Get feedback from 16 agents
    5. Analyze test results
    6. If passed, deploy to production
    """
    
    def __init__(self, gemini_client, data_dir: Path, github_token: str):
        self.gemini = gemini_client
        self.data_dir = data_dir
        self.github_token = github_token
        self.improvements_dir = data_dir / "improvements"
        self.improvements_dir.mkdir(exist_ok=True)
        
        # GitHub configuration
        self.repo_owner = "mango-magic"
        self.repo_name = "mango-platform"
        self.test_branch = "test-improvements"
        self.main_branch = "main"
        
    async def run_improvement_cycle(self, evaluation: Dict):
        """
        Complete self-improvement cycle based on evaluation
        """
        cycle_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        logger.info(f"🔄 Starting self-improvement cycle: {cycle_id}")
        
        try:
            # Phase 1: Analyze evaluation and generate improvements
            logger.info("📝 Phase 1: Generating code improvements...")
            improvements = await self._generate_improvements(evaluation)
            
            if not improvements or improvements.get('skip'):
                logger.info("⏭️  No improvements needed at this time")
                return None
            
            # Phase 2: Apply improvements to test branch
            logger.info("🔧 Phase 2: Applying improvements to test branch...")
            test_deployment = await self._deploy_to_test(improvements, cycle_id)
            
            if not test_deployment:
                logger.error("❌ Failed to deploy to test environment")
                return None
            
            # Phase 3: Wait for test environment to stabilize
            logger.info("⏳ Phase 3: Waiting for test environment to stabilize...")
            await asyncio.sleep(120)  # 2 minutes for deployment
            
            # Phase 4: Collect feedback from agents
            logger.info("👥 Phase 4: Collecting feedback from 16 agents...")
            agent_feedback = await self._collect_agent_feedback(test_deployment)
            
            # Phase 5: Analyze test results and bugs
            logger.info("🔍 Phase 5: Analyzing test results...")
            test_analysis = await self._analyze_test_results(
                improvements, 
                agent_feedback,
                test_deployment
            )
            
            # Phase 6: Decision - deploy to production or rollback
            if test_analysis['passed']:
                logger.info("✅ Phase 6: All tests passed! Deploying to production...")
                production_deployment = await self._deploy_to_production(
                    improvements,
                    test_analysis,
                    cycle_id
                )
                
                # Save successful improvement
                await self._save_improvement_record(
                    cycle_id,
                    evaluation,
                    improvements,
                    agent_feedback,
                    test_analysis,
                    production_deployment,
                    status='deployed'
                )
                
                logger.info(f"🎉 Self-improvement cycle {cycle_id} SUCCESSFUL!")
                return {
                    'cycle_id': cycle_id,
                    'status': 'deployed',
                    'improvements': improvements,
                    'test_analysis': test_analysis,
                    'production_deployment': production_deployment
                }
                
            else:
                logger.warning("❌ Tests failed. Rolling back improvements...")
                await self._rollback_test_branch()
                
                # Save failed attempt for learning
                await self._save_improvement_record(
                    cycle_id,
                    evaluation,
                    improvements,
                    agent_feedback,
                    test_analysis,
                    None,
                    status='failed'
                )
                
                return {
                    'cycle_id': cycle_id,
                    'status': 'failed',
                    'reasons': test_analysis.get('failure_reasons', [])
                }
                
        except Exception as e:
            logger.error(f"❌ Self-improvement cycle failed: {e}")
            return None
    
    async def _generate_improvements(self, evaluation: Dict) -> Dict:
        """
        Use Gemini to generate specific code improvements based on evaluation
        """
        score = self._extract_score(evaluation.get('evaluation', ''))
        
        # Only improve if score is below 85
        if score >= 85:
            return {'skip': True, 'reason': 'Performance already excellent'}
        
        improvement_prompt = f"""
You are a world-class engineer tasked with improving an autonomous AI team system.

**Current Evaluation:**
Score: {score}/100
{evaluation.get('evaluation', '')}

**Current Metrics:**
{json.dumps(evaluation.get('metrics', {}), indent=2)}

**Your Task:**
Analyze the evaluation and generate SPECIFIC, ACTIONABLE code improvements.

For each improvement:
1. **File to modify** (exact path)
2. **What to change** (specific function/class)
3. **Why** (addresses which weakness)
4. **Expected impact** (how much score improvement)
5. **Risk level** (low/medium/high)

Focus on the TOP 3 weaknesses mentioned in the evaluation.

Provide improvements in this JSON format:
{{
  "improvements": [
    {{
      "file": "core/orchestrator.py",
      "function": "run_forever",
      "change_description": "Add proactive task generation every 5 cycles",
      "reasoning": "Addresses 'reactive rather than proactive' weakness",
      "expected_impact": "+8 points to Strategic Focus",
      "risk_level": "low",
      "code_snippet": "# New code here..."
    }}
  ],
  "priority": "high|medium|low",
  "estimated_improvement": "+12 points"
}}

Be conservative. Only suggest changes that:
- Are LOW RISK
- Address specific evaluation weaknesses
- Have clear expected benefits
- Won't break existing functionality

If improvements aren't necessary or safe, return: {{"skip": true}}
"""

        try:
            response = await self.gemini.generate(
                agent_id="self_improver",
                system="You are a cautious, world-class engineer who improves systems incrementally and safely.",
                prompt=improvement_prompt,
                temp=0.2  # Low temperature for conservative suggestions
            )
            
            # Parse JSON from response
            # (In production, would use more robust JSON extraction)
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                improvements = json.loads(json_match.group())
                return improvements
            
            return {'skip': True, 'reason': 'Could not parse improvements'}
            
        except Exception as e:
            logger.error(f"Error generating improvements: {e}")
            return {'skip': True, 'reason': str(e)}
    
    async def _deploy_to_test(self, improvements: Dict, cycle_id: str) -> Optional[Dict]:
        """
        Create test branch, apply improvements, push to GitHub
        """
        try:
            # In production, would use GitPython or GitHub API
            # For now, return mock deployment info
            
            logger.info(f"Creating test branch: {self.test_branch}-{cycle_id}")
            logger.info(f"Applying {len(improvements.get('improvements', []))} improvements")
            
            # Simulate deployment
            deployment_info = {
                'branch': f"{self.test_branch}-{cycle_id}",
                'commit_sha': f"test_{cycle_id}",
                'timestamp': datetime.now().isoformat(),
                'improvements_count': len(improvements.get('improvements', [])),
                'test_url': f"https://test-{cycle_id}.onrender.com"
            }
            
            logger.info(f"✅ Test deployment created: {deployment_info['test_url']}")
            return deployment_info
            
        except Exception as e:
            logger.error(f"Test deployment failed: {e}")
            return None
    
    async def _collect_agent_feedback(self, test_deployment: Dict) -> List[Dict]:
        """
        Have all 16 agents test the new code and provide feedback
        """
        logger.info("Collecting feedback from 16 agents...")
        
        # Define the 16 feedback agents
        feedback_agents = [
            {"id": "eng_manager_001", "name": "Marcus", "focus": "architecture"},
            {"id": "backend_001", "name": "Aria", "focus": "backend"},
            {"id": "backend_002", "name": "Kai", "focus": "api"},
            {"id": "backend_003", "name": "Zara", "focus": "llm"},
            {"id": "frontend_001", "name": "Luna", "focus": "ui"},
            {"id": "frontend_002", "name": "River", "focus": "ux"},
            {"id": "ml_001", "name": "Nova", "focus": "ml_models"},
            {"id": "ml_002", "name": "Sage", "focus": "ml_pipeline"},
            {"id": "devops_001", "name": "Atlas", "focus": "infrastructure"},
            {"id": "qa_001", "name": "Iris", "focus": "testing"},
            {"id": "pm_001", "name": "Jordan", "focus": "product"},
            {"id": "designer_001", "name": "Mira", "focus": "design"},
            {"id": "writer_001", "name": "Phoenix", "focus": "docs"},
            {"id": "gtm_001", "name": "Blaze", "focus": "marketing"},
            {"id": "cs_001", "name": "Haven", "focus": "customer"},
            {"id": "security_001", "name": "Shield", "focus": "security"}
        ]
        
        feedback_list = []
        
        for agent in feedback_agents:
            feedback_prompt = f"""
You are {agent['name']}, a {agent['focus']} specialist in an AI development team.

A new version of the system has been deployed to test environment:
{json.dumps(test_deployment, indent=2)}

**Your Task:**
Test the new system from your {agent['focus']} perspective and provide feedback.

Evaluate:
1. Does the new version work correctly?
2. Any bugs or issues you noticed?
3. Performance impact (better/worse/same)?
4. Specific to your domain: any concerns?
5. Should we deploy to production? (yes/no)

Provide concise, technical feedback. Be critical - we need to catch problems now.

Format:
{{
  "works": true/false,
  "bugs": ["list any bugs"],
  "performance": "better/worse/same",
  "concerns": ["domain-specific concerns"],
  "deploy_vote": "yes/no",
  "confidence": "high/medium/low",
  "notes": "additional observations"
}}
"""
            
            try:
                response = await self.gemini.generate(
                    agent_id=agent['id'],
                    system=f"You are {agent['name']}, an expert {agent['focus']} engineer. Be thorough and critical.",
                    prompt=feedback_prompt,
                    temp=0.3
                )
                
                # Parse feedback
                import re
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    feedback = json.loads(json_match.group())
                    feedback['agent'] = agent['name']
                    feedback['agent_id'] = agent['id']
                    feedback['focus_area'] = agent['focus']
                    feedback_list.append(feedback)
                    
                    logger.info(f"✓ {agent['name']}: {feedback.get('deploy_vote', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Error getting feedback from {agent['name']}: {e}")
                # Add negative feedback if agent failed to respond
                feedback_list.append({
                    'agent': agent['name'],
                    'agent_id': agent['id'],
                    'focus_area': agent['focus'],
                    'works': False,
                    'deploy_vote': 'no',
                    'confidence': 'high',
                    'notes': f'Agent failed to provide feedback: {e}'
                })
        
        return feedback_list
    
    async def _analyze_test_results(
        self, 
        improvements: Dict, 
        agent_feedback: List[Dict],
        test_deployment: Dict
    ) -> Dict:
        """
        Analyze all feedback and determine if tests passed
        """
        logger.info("Analyzing test results from 16 agents...")
        
        total_agents = len(agent_feedback)
        yes_votes = len([f for f in agent_feedback if f.get('deploy_vote') == 'yes'])
        no_votes = len([f for f in agent_feedback if f.get('deploy_vote') == 'no'])
        
        all_bugs = []
        all_concerns = []
        
        for feedback in agent_feedback:
            all_bugs.extend(feedback.get('bugs', []))
            all_concerns.extend(feedback.get('concerns', []))
        
        # Decision criteria
        approval_threshold = 0.80  # 80% must approve
        approval_rate = yes_votes / total_agents if total_agents > 0 else 0
        
        passed = (
            approval_rate >= approval_threshold and
            len(all_bugs) == 0 and
            no_votes <= 2  # Max 2 no votes allowed
        )
        
        analysis = {
            'passed': passed,
            'total_agents': total_agents,
            'yes_votes': yes_votes,
            'no_votes': no_votes,
            'approval_rate': approval_rate,
            'approval_threshold': approval_threshold,
            'bugs_found': all_bugs,
            'concerns_raised': all_concerns,
            'agent_feedback_summary': agent_feedback,
            'decision': 'DEPLOY' if passed else 'REJECT',
            'decision_reasoning': self._get_decision_reasoning(
                passed, approval_rate, all_bugs, all_concerns, no_votes
            )
        }
        
        if not passed:
            analysis['failure_reasons'] = []
            if approval_rate < approval_threshold:
                analysis['failure_reasons'].append(
                    f"Approval rate {approval_rate:.1%} below threshold {approval_threshold:.1%}"
                )
            if len(all_bugs) > 0:
                analysis['failure_reasons'].append(f"{len(all_bugs)} bugs found")
            if no_votes > 2:
                analysis['failure_reasons'].append(f"{no_votes} agents voted NO")
        
        logger.info(f"Analysis complete: {analysis['decision']}")
        logger.info(f"Approval rate: {approval_rate:.1%} ({yes_votes}/{total_agents})")
        
        return analysis
    
    def _get_decision_reasoning(
        self, 
        passed: bool, 
        approval_rate: float,
        bugs: List,
        concerns: List,
        no_votes: int
    ) -> str:
        """Generate human-readable decision reasoning"""
        if passed:
            return (
                f"✅ APPROVED FOR PRODUCTION\n"
                f"- {approval_rate:.1%} agent approval (threshold: 80%)\n"
                f"- Zero bugs found\n"
                f"- {len(concerns)} concerns raised but acceptable\n"
                f"- Only {no_votes} no votes\n"
                f"All criteria met for production deployment."
            )
        else:
            reasons = []
            if approval_rate < 0.80:
                reasons.append(f"❌ Low approval: {approval_rate:.1%} < 80%")
            if len(bugs) > 0:
                reasons.append(f"❌ {len(bugs)} bugs found")
            if no_votes > 2:
                reasons.append(f"❌ Too many no votes: {no_votes}")
            
            return (
                f"❌ REJECTED - NOT SAFE FOR PRODUCTION\n" +
                "\n".join(reasons)
            )
    
    async def _deploy_to_production(
        self,
        improvements: Dict,
        test_analysis: Dict,
        cycle_id: str
    ) -> Dict:
        """
        Merge test branch to main and deploy to production
        """
        logger.info("🚀 Deploying to production...")
        
        try:
            # In production, would:
            # 1. Create PR from test branch to main
            # 2. Wait for CI/CD tests
            # 3. Merge PR
            # 4. Trigger production deployment
            
            production_deployment = {
                'cycle_id': cycle_id,
                'deployed_at': datetime.now().isoformat(),
                'branch': 'main',
                'commit_message': f"Auto-improvement #{cycle_id}: {improvements.get('estimated_improvement', 'improvements')}",
                'improvements_applied': len(improvements.get('improvements', [])),
                'agent_approval_rate': test_analysis['approval_rate'],
                'production_url': 'https://mango-platform.onrender.com',
                'status': 'deployed'
            }
            
            logger.info("✅ Production deployment successful!")
            return production_deployment
            
        except Exception as e:
            logger.error(f"Production deployment failed: {e}")
            raise
    
    async def _rollback_test_branch(self):
        """Rollback/delete failed test branch"""
        logger.info("Rolling back test branch...")
        # In production: delete test branch, restore previous state
        pass
    
    async def _save_improvement_record(
        self,
        cycle_id: str,
        evaluation: Dict,
        improvements: Dict,
        agent_feedback: List[Dict],
        test_analysis: Dict,
        production_deployment: Optional[Dict],
        status: str
    ):
        """Save complete record of improvement cycle"""
        record = {
            'cycle_id': cycle_id,
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'evaluation': evaluation,
            'improvements_generated': improvements,
            'agent_feedback': agent_feedback,
            'test_analysis': test_analysis,
            'production_deployment': production_deployment
        }
        
        record_file = self.improvements_dir / f"cycle_{cycle_id}.json"
        with open(record_file, 'w') as f:
            json.dump(record, f, indent=2)
        
        logger.info(f"📝 Improvement record saved: {record_file}")
    
    def _extract_score(self, evaluation_text: str) -> int:
        """Extract numeric score from evaluation text"""
        import re
        match = re.search(r'OVERALL SCORE:?\s*(\d+)/100', evaluation_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 70  # Default middle score

