"""
Risk Detection Agent: Identifies and flags potential risks in code and infrastructure
- Detects architectural risks
- Identifies performance issues
- Flags dependency vulnerabilities
- Detects deployment risks
"""
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent, AgentAction, AgentResult
import logging

logger = logging.getLogger(__name__)


class RiskDetectionAgent(BaseAgent):
    """Agent for detecting and flagging risks"""

    def __init__(self, aws_region: str = "us-east-1"):
        super().__init__("RiskDetectionAgent", aws_region)

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze for potential risks"""
        code = context.get("code", "")
        infrastructure = context.get("infrastructure", {})
        deployment = context.get("deployment", {})
        dependencies = context.get("dependencies", [])
        
        risks = {
            "architectural_risks": self._detect_architectural_risks(code),
            "performance_risks": self._detect_performance_risks(code),
            "dependency_risks": self._detect_dependency_risks(dependencies),
            "deployment_risks": self._detect_deployment_risks(deployment, infrastructure),
            "operational_risks": self._detect_operational_risks(infrastructure)
        }
        
        # Calculate risk scores
        all_risks = []
        for category_risks in risks.values():
            all_risks.extend(category_risks)
        
        return {
            "total_risks": len(all_risks),
            "risks_by_severity": self._categorize_by_severity(all_risks),
            "all_risks": risks,
            "risk_score": self._calculate_risk_score(all_risks),
            "requires_action": len(all_risks) > 0
        }

    def recommend_actions(self, analysis: Dict[str, Any]) -> List[AgentAction]:
        """Recommend risk mitigation actions"""
        actions = []
        
        if analysis["requires_action"]:
            critical_risks = analysis["risks_by_severity"].get("CRITICAL", [])
            high_risks = analysis["risks_by_severity"].get("HIGH", [])
            
            if critical_risks:
                action = AgentAction(
                    action_type="BLOCK_DEPLOYMENT",
                    description=f"Block deployment: {len(critical_risks)} critical risks detected",
                    payload={
                        "critical_risks_count": len(critical_risks),
                        "risks": [r.get("description", "Unknown") for r in critical_risks[:5]]
                    },
                    timestamp=datetime.now()
                )
                actions.append(action)
            
            if high_risks and not critical_risks:
                action = AgentAction(
                    action_type="WARN_DEPLOYMENT",
                    description=f"Warn before deployment: {len(high_risks)} high-risk issues found",
                    payload={
                        "high_risks_count": len(high_risks),
                        "requires_approval": True
                    },
                    timestamp=datetime.now()
                )
                actions.append(action)
            
            # Always create a risk report
            action = AgentAction(
                action_type="CREATE_RISK_REPORT",
                description=f"Generate risk assessment report ({analysis['risk_score']}/100 risk score)",
                payload={
                    "risk_score": analysis["risk_score"],
                    "total_risks": analysis["total_risks"],
                    "severity_breakdown": analysis["risks_by_severity"]
                },
                timestamp=datetime.now()
            )
            actions.append(action)
        
        return actions

    def execute(self, actions: List[AgentAction]) -> AgentResult:
        """Execute risk mitigation actions"""
        executed_actions = []
        errors = []
        
        for action in actions:
            try:
                if action.action_type == "BLOCK_DEPLOYMENT":
                    logger.error(f"DEPLOYMENT BLOCKED: {action.description}")
                    self.log_action(action)
                    executed_actions.append(action)
                    
                elif action.action_type == "WARN_DEPLOYMENT":
                    logger.warning(f"DEPLOYMENT WARNING: {action.description}")
                    self.log_action(action)
                    executed_actions.append(action)
                    
                elif action.action_type == "CREATE_RISK_REPORT":
                    logger.info(f"Generating risk report")
                    self.log_action(action)
                    executed_actions.append(action)
                    
            except Exception as e:
                errors.append(f"Error executing {action.action_type}: {str(e)}")
        
        return AgentResult(
            success=len(errors) == 0,
            message=f"Executed {len(executed_actions)} risk mitigation actions",
            actions=executed_actions,
            data={
                "deployments_blocked": len([a for a in executed_actions if a.action_type == "BLOCK_DEPLOYMENT"]),
                "warnings": len([a for a in executed_actions if a.action_type == "WARN_DEPLOYMENT"]),
                "reports": len([a for a in executed_actions if a.action_type == "CREATE_RISK_REPORT"])
            },
            errors=errors,
            duration_seconds=0
        )

    def _detect_architectural_risks(self, code: str) -> List[Dict[str, Any]]:
        """Detect architectural risks"""
        risks = []
        
        if "global " in code:
            risks.append({
                "type": "architectural",
                "severity": "HIGH",
                "description": "Global variables detected - violates best practices",
                "reccommendation": "Refactor to use dependency injection or class attributes"
            })
        
        if code.count("import *") > 0:
            risks.append({
                "type": "architectural",
                "severity": "MEDIUM",
                "description": "Wildcard imports can cause namespace pollution",
                "recommendation": "Use explicit imports"
            })
        
        return risks

    def _detect_performance_risks(self, code: str) -> List[Dict[str, Any]]:
        """Detect performance risks"""
        risks = []
        
        # Check for N+1 query patterns (simplified)
        if "for " in code and "query" in code:
            risks.append({
                "type": "performance",
                "severity": "MEDIUM",
                "description": "Potential N+1 query pattern detected in loop",
                "recommendation": "Use batch queries or eager loading"
            })
        
        # Check for large loops
        if code.count("for ") > 5:
            risks.append({
                "type": "performance",
                "severity": "LOW",
                "description": "Multiple nested loops detected",
                "recommendation": "Review loop complexity and optimize"
            })
        
        return risks

    def _detect_dependency_risks(self, dependencies: List[str]) -> List[Dict[str, Any]]:
        """Detect dependency vulnerabilities"""
        risks = []
        
        # Known vulnerable packages (simplified)
        vulnerable_packages = {
            "pyyaml": "Known deserialization vulnerability",
            "pickle": "Arbitrary code execution vulnerability",
            "eval": "Dynamic code evaluation risk"
        }
        
        for dep in dependencies:
            if dep in vulnerable_packages:
                risks.append({
                    "type": "dependency",
                    "severity": "HIGH",
                    "description": f"Vulnerable dependency: {dep}",
                    "recommendation": f"Update or replace {dep}"
                })
        
        return risks

    def _detect_deployment_risks(self, deployment: Dict, infrastructure: Dict) -> List[Dict[str, Any]]:
        """Detect deployment risks"""
        risks = []
        
        if not deployment:
            risks.append({
                "type": "deployment",
                "severity": "HIGH",
                "description": "No deployment strategy defined",
                "recommendation": "Define proper deployment process"
            })
        
        if deployment.get("strategy") == "all-at-once":
            risks.append({
                "type": "deployment",
                "severity": "HIGH",
                "description": "High-risk all-at-once deployment strategy",
                "recommendation": "Use blue-green or canary deployment"
            })
        
        return risks

    def _detect_operational_risks(self, infrastructure: Dict) -> List[Dict[str, Any]]:
        """Detect operational risks"""
        risks = []
        
        if not infrastructure.get("monitoring"):
            risks.append({
                "type": "operational",
                "severity": "HIGH",
                "description": "No monitoring configured",
                "recommendation": "Enable CloudWatch/operational monitoring"
            })
        
        if not infrastructure.get("backup"):
            risks.append({
                "type": "operational",
                "severity": "HIGH",
                "description": "No backup strategy",
                "recommendation": "Implement automated backups"
            })
        
        if not infrastructure.get("disaster_recovery"):
            risks.append({
                "type": "operational",
                "severity": "MEDIUM",
                "description": "No disaster recovery plan",
                "recommendation": "Establish disaster recovery procedures"
            })
        
        return risks

    def _categorize_by_severity(self, risks: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Categorize risks by severity"""
        categorized = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }
        
        for risk in risks:
            severity = risk.get("severity", "LOW")
            if severity in categorized:
                categorized[severity].append(risk)
        
        return categorized

    def _calculate_risk_score(self, risks: List[Dict[str, Any]]) -> int:
        """Calculate overall risk score (0-100, higher is worse)"""
        if not risks:
            return 0
        
        score = 0
        for risk in risks:
            severity = risk.get("severity", "LOW")
            if severity == "CRITICAL":
                score += 25
            elif severity == "HIGH":
                score += 15
            elif severity == "MEDIUM":
                score += 8
            elif severity == "LOW":
                score += 3
        
        return min(100, score)  # Cap at 100
