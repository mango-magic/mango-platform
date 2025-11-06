"""
Environment Management - TEST vs PRODUCTION separation
Strict deployment gates ensure zero bugs reach production
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger('Environments')

class Environment(Enum):
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"

class DeploymentStatus(Enum):
    PENDING = "pending"
    TESTING = "testing"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class DeploymentGate:
    """Requirements that must pass before TEST → PRODUCTION"""
    test_coverage_min: float = 90.0  # Minimum 90% test coverage
    tests_must_pass: bool = True  # All tests must pass
    code_review_required: bool = True  # Marcus or senior must approve
    security_scan_required: bool = True  # No vulnerabilities
    performance_benchmark: bool = True  # Must meet performance targets
    manual_approval_required: bool = True  # Human or Marcus must approve
    zero_critical_bugs: bool = True  # No P0/P1 bugs
    integration_tests_pass: bool = True  # All integration tests pass
    load_test_pass: bool = True  # Handle expected load
    documentation_complete: bool = True  # All docs written

@dataclass
class DeploymentRequest:
    """Request to deploy from TEST → PRODUCTION"""
    id: str
    requested_by: str  # Agent ID
    component: str  # What's being deployed
    version: str
    environment_from: Environment
    environment_to: Environment
    timestamp: str
    status: DeploymentStatus
    test_results: Dict
    code_review_status: str
    approvals: List[str]
    blockers: List[str]
    rollback_plan: str

class EnvironmentManager:
    """Manages TEST and PRODUCTION environments with strict gates"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.test_dir = data_dir / "environments" / "test"
        self.staging_dir = data_dir / "environments" / "staging"
        self.prod_dir = data_dir / "environments" / "production"
        self.deployments_dir = data_dir / "deployments"
        
        # Create directories
        for dir_path in [self.test_dir, self.staging_dir, self.prod_dir, self.deployments_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Deployment gates
        self.gates = DeploymentGate()
        
        # Track current state
        self.current_environment = Environment.TEST  # Start in TEST
        self.test_state = self._load_environment_state(Environment.TEST)
        self.prod_state = self._load_environment_state(Environment.PRODUCTION)
        
        logger.info("🏗️ Environment manager initialized")
        logger.info(f"📍 Current environment: {self.current_environment.value}")
    
    def _load_environment_state(self, env: Environment) -> Dict:
        """Load current state of an environment"""
        state_file = self._get_env_dir(env) / "state.json"
        
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
        
        return {
            "environment": env.value,
            "version": "0.0.0",
            "deployed_components": {},
            "last_deployment": None,
            "health_status": "unknown"
        }
    
    def _save_environment_state(self, env: Environment, state: Dict):
        """Save environment state"""
        state_file = self._get_env_dir(env) / "state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _get_env_dir(self, env: Environment) -> Path:
        """Get directory for environment"""
        if env == Environment.TEST:
            return self.test_dir
        elif env == Environment.STAGING:
            return self.staging_dir
        else:
            return self.prod_dir
    
    async def get_current_environment(self) -> Environment:
        """Get current active environment"""
        return self.current_environment
    
    async def deploy_to_test(self, component: str, version: str, deployed_by: str):
        """Deploy to TEST environment (no gates, fast iteration)"""
        logger.info(f"🧪 Deploying {component} v{version} to TEST by {deployed_by}")
        
        # Update TEST state
        self.test_state["deployed_components"][component] = {
            "version": version,
            "deployed_by": deployed_by,
            "deployed_at": datetime.now().isoformat(),
            "status": "active"
        }
        self.test_state["last_deployment"] = datetime.now().isoformat()
        
        self._save_environment_state(Environment.TEST, self.test_state)
        
        logger.info(f"✅ {component} v{version} deployed to TEST")
        return True
    
    async def request_production_deployment(
        self,
        component: str,
        version: str,
        requested_by: str,
        test_results: Dict,
        rollback_plan: str
    ) -> str:
        """Request deployment to PRODUCTION (requires passing all gates)"""
        
        deployment_id = f"deploy_{component}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        request = DeploymentRequest(
            id=deployment_id,
            requested_by=requested_by,
            component=component,
            version=version,
            environment_from=Environment.TEST,
            environment_to=Environment.PRODUCTION,
            timestamp=datetime.now().isoformat(),
            status=DeploymentStatus.PENDING,
            test_results=test_results,
            code_review_status="pending",
            approvals=[],
            blockers=[],
            rollback_plan=rollback_plan
        )
        
        # Save deployment request
        request_file = self.deployments_dir / f"{deployment_id}.json"
        with open(request_file, 'w') as f:
            json.dump(asdict(request), f, indent=2)
        
        logger.info(f"📋 Production deployment requested: {deployment_id}")
        
        # Check gates
        blockers = await self._check_deployment_gates(request, test_results)
        
        if blockers:
            request.status = DeploymentStatus.FAILED
            request.blockers = blockers
            
            with open(request_file, 'w') as f:
                json.dump(asdict(request), f, indent=2)
            
            logger.error(f"❌ Deployment {deployment_id} blocked: {blockers}")
            return deployment_id
        
        # All gates passed, waiting for approval
        request.status = DeploymentStatus.APPROVED
        
        with open(request_file, 'w') as f:
            json.dump(asdict(request), f, indent=2)
        
        logger.info(f"✅ Deployment {deployment_id} approved, ready for production")
        
        return deployment_id
    
    async def _check_deployment_gates(self, request: DeploymentRequest, test_results: Dict) -> List[str]:
        """Check all deployment gates - return list of blockers"""
        blockers = []
        
        # Gate 1: Test Coverage
        coverage = test_results.get('coverage', 0.0)
        if coverage < self.gates.test_coverage_min:
            blockers.append(f"Test coverage {coverage}% < required {self.gates.test_coverage_min}%")
        
        # Gate 2: All Tests Pass
        if self.gates.tests_must_pass:
            tests_passed = test_results.get('tests_passed', 0)
            tests_failed = test_results.get('tests_failed', 0)
            if tests_failed > 0:
                blockers.append(f"{tests_failed} tests failed")
        
        # Gate 3: Code Review
        if self.gates.code_review_required:
            if request.code_review_status != "approved":
                blockers.append("Code review not approved")
        
        # Gate 4: Security Scan
        if self.gates.security_scan_required:
            vulnerabilities = test_results.get('vulnerabilities', [])
            critical_vulns = [v for v in vulnerabilities if v.get('severity') in ['critical', 'high']]
            if critical_vulns:
                blockers.append(f"{len(critical_vulns)} critical/high vulnerabilities found")
        
        # Gate 5: Zero Critical Bugs
        if self.gates.zero_critical_bugs:
            critical_bugs = test_results.get('critical_bugs', 0)
            if critical_bugs > 0:
                blockers.append(f"{critical_bugs} critical bugs found")
        
        # Gate 6: Integration Tests
        if self.gates.integration_tests_pass:
            integration_passed = test_results.get('integration_tests_passed', False)
            if not integration_passed:
                blockers.append("Integration tests failed")
        
        # Gate 7: Performance Benchmark
        if self.gates.performance_benchmark:
            performance_ok = test_results.get('performance_benchmark_passed', False)
            if not performance_ok:
                blockers.append("Performance benchmark not met")
        
        # Gate 8: Documentation
        if self.gates.documentation_complete:
            docs_complete = test_results.get('documentation_complete', False)
            if not docs_complete:
                blockers.append("Documentation incomplete")
        
        return blockers
    
    async def approve_deployment(self, deployment_id: str, approver: str):
        """Approve a deployment (Marcus or human)"""
        request_file = self.deployments_dir / f"{deployment_id}.json"
        
        if not request_file.exists():
            logger.error(f"❌ Deployment {deployment_id} not found")
            return False
        
        with open(request_file) as f:
            request_data = json.load(f)
        
        request = DeploymentRequest(**request_data)
        
        if request.status != DeploymentStatus.APPROVED:
            logger.error(f"❌ Deployment {deployment_id} not in approved state")
            return False
        
        # Add approval
        if approver not in request.approvals:
            request.approvals.append(approver)
        
        # Check if we have required approvals (need Marcus or human)
        if "eng_manager_001" in request.approvals or "human" in request.approvals:
            # Deploy to production
            await self._execute_production_deployment(request)
            request.status = DeploymentStatus.DEPLOYED
            
            logger.info(f"🚀 {request.component} v{request.version} DEPLOYED TO PRODUCTION")
        
        # Save updated request
        with open(request_file, 'w') as f:
            json.dump(asdict(request), f, indent=2)
        
        return True
    
    async def _execute_production_deployment(self, request: DeploymentRequest):
        """Actually deploy to production"""
        logger.info(f"🚀 Deploying {request.component} to PRODUCTION")
        
        # Update PRODUCTION state
        self.prod_state["deployed_components"][request.component] = {
            "version": request.version,
            "deployed_by": request.requested_by,
            "deployed_at": datetime.now().isoformat(),
            "status": "active",
            "deployment_id": request.id
        }
        self.prod_state["last_deployment"] = datetime.now().isoformat()
        self.prod_state["version"] = request.version
        
        self._save_environment_state(Environment.PRODUCTION, self.prod_state)
        
        logger.info(f"✅ {request.component} v{request.version} live in PRODUCTION")
    
    async def rollback_production(self, component: str, reason: str, rolled_back_by: str):
        """Rollback production deployment"""
        logger.warning(f"🔄 Rolling back {component} in PRODUCTION: {reason}")
        
        if component not in self.prod_state["deployed_components"]:
            logger.error(f"❌ Component {component} not in production")
            return False
        
        # Get deployment history
        deployment_history = []
        for deploy_file in self.deployments_dir.glob(f"deploy_{component}_*.json"):
            with open(deploy_file) as f:
                deployment_history.append(json.load(f))
        
        # Sort by timestamp, get previous version
        deployment_history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        if len(deployment_history) < 2:
            logger.error(f"❌ No previous version to rollback to")
            return False
        
        previous = deployment_history[1]
        
        # Rollback
        self.prod_state["deployed_components"][component] = {
            "version": previous['version'],
            "deployed_by": rolled_back_by,
            "deployed_at": datetime.now().isoformat(),
            "status": "rolled_back",
            "rollback_reason": reason
        }
        
        self._save_environment_state(Environment.PRODUCTION, self.prod_state)
        
        logger.info(f"✅ Rolled back {component} to v{previous['version']}")
        return True
    
    async def get_environment_health(self, env: Environment) -> Dict:
        """Get health status of environment"""
        state = self._load_environment_state(env)
        
        health = {
            "environment": env.value,
            "status": "healthy",
            "components": len(state.get("deployed_components", {})),
            "last_deployment": state.get("last_deployment"),
            "issues": []
        }
        
        # Check each component
        for component, details in state.get("deployed_components", {}).items():
            if details.get("status") == "failed":
                health["status"] = "degraded"
                health["issues"].append(f"{component} in failed state")
        
        return health
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict]:
        """Get status of a deployment"""
        request_file = self.deployments_dir / f"{deployment_id}.json"
        
        if request_file.exists():
            with open(request_file) as f:
                return json.load(f)
        
        return None
    
    async def get_pending_deployments(self) -> List[Dict]:
        """Get all pending production deployments"""
        pending = []
        
        for deploy_file in self.deployments_dir.glob("deploy_*.json"):
            with open(deploy_file) as f:
                data = json.load(f)
                if data['status'] in ['pending', 'approved']:
                    pending.append(data)
        
        return pending

