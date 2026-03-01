"""
Compliance Agent: Automated compliance checking and report generation
- Verifies compliance with standards (SOC2, HIPAA, GDPR, PCI-DSS)
- Generates compliance reports
- Flags non-compliant configurations
"""
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent, AgentAction, AgentResult
import logging
import json

logger = logging.getLogger(__name__)


class ComplianceAgent(BaseAgent):
    """Agent for compliance checking and report generation"""

    def __init__(self, aws_region: str = "us-east-1"):
        super().__init__("ComplianceAgent", aws_region)
        self.compliance_frameworks = {
            "SOC2": self._check_soc2,
            "GDPR": self._check_gdpr,
            "HIPAA": self._check_hipaa,
            "PCI_DSS": self._check_pci_dss
        }

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code/infrastructure for compliance"""
        code_content = context.get("code", "")
        infrastructure = context.get("infrastructure", {})
        frameworks = context.get("frameworks", list(self.compliance_frameworks.keys()))
        
        compliance_status = {}
        total_findings = 0
        
        for framework in frameworks:
            if framework in self.compliance_frameworks:
                status = self.compliance_frameworks[framework](code_content, infrastructure)
                compliance_status[framework] = status
                total_findings += status.get("findings_count", 0)
        
        return {
            "compliance_frameworks": compliance_status,
            "total_findings": total_findings,
            "overall_compliance": self._calculate_overall_compliance(compliance_status),
            "risk_level": self._calculate_risk_level(total_findings),
            "requires_remediation": total_findings > 0
        }

    def recommend_actions(self, analysis: Dict[str, Any]) -> List[AgentAction]:
        """Recommend compliance remediation actions"""
        actions = []
        
        if analysis["requires_remediation"]:
            action = AgentAction(
                action_type="GENERATE_COMPLIANCE_REPORT",
                description=f"Generate compliance report for {analysis['total_findings']} findings",
                payload={
                    "frameworks": list(analysis["compliance_frameworks"].keys()),
                    "findings_count": analysis["total_findings"],
                    "risk_level": analysis["risk_level"]
                },
                timestamp=datetime.now()
            )
            actions.append(action)
            
            if analysis["risk_level"] in ["HIGH", "CRITICAL"]:
                escalation_action = AgentAction(
                    action_type="ESCALATE_TO_SECURITY_TEAM",
                    description=f"Escalate {analysis['risk_level']} risk compliance issues",
                    payload={
                        "risk_level": analysis["risk_level"],
                        "frameworks_affected": [f for f, s in analysis["compliance_frameworks"].items() 
                                               if not s.get("compliant", True)]
                    },
                    timestamp=datetime.now()
                )
                actions.append(escalation_action)
        
        return actions

    def execute(self, actions: List[AgentAction]) -> AgentResult:
        """Execute compliance actions"""
        executed_actions = []
        errors = []
        
        for action in actions:
            try:
                if action.action_type == "GENERATE_COMPLIANCE_REPORT":
                    report = self._generate_report(action.payload)
                    logger.info(f"Generated compliance report")
                    self.log_action(action)
                    executed_actions.append(action)
                    
                elif action.action_type == "ESCALATE_TO_SECURITY_TEAM":
                    logger.warning(f"Escalating: {action.payload['risk_level']} compliance risk")
                    self.log_action(action)
                    executed_actions.append(action)
                    
            except Exception as e:
                errors.append(f"Error executing {action.action_type}: {str(e)}")
        
        return AgentResult(
            success=len(errors) == 0,
            message=f"Executed {len(executed_actions)} compliance actions",
            actions=executed_actions,
            data={
                "reports_generated": len([a for a in executed_actions if a.action_type == "GENERATE_COMPLIANCE_REPORT"]),
                "escalations": len([a for a in executed_actions if a.action_type == "ESCALATE_TO_SECURITY_TEAM"])
            },
            errors=errors,
            duration_seconds=0
        )

    def _check_soc2(self, code: str, infrastructure: Dict) -> Dict[str, Any]:
        """Check SOC2 compliance"""
        findings = []
        
        # Check for logging
        if "logging" not in code.lower():
            findings.append("Missing logging implementation (SOC2 requirement)")
        
        # Check for error handling
        if "try" not in code and "except" not in code:
            findings.append("Missing error handling (SOC2 requirement)")
        
        return {
            "compliant": len(findings) == 0,
            "findings": findings,
            "findings_count": len(findings)
        }

    def _check_gdpr(self, code: str, infrastructure: Dict) -> Dict[str, Any]:
        """Check GDPR compliance"""
        findings = []
        
        # Check for data privacy
        if "encrypt" not in code.lower() and "hash" not in code.lower():
            findings.append("No data encryption/hashing detected (GDPR requires data protection)")
        
        if "delete" not in code.lower():
            findings.append("No data deletion mechanism found (GDPR requires right to be forgotten)")
        
        return {
            "compliant": len(findings) == 0,
            "findings": findings,
            "findings_count": len(findings)
        }

    def _check_hipaa(self, code: str, infrastructure: Dict) -> Dict[str, Any]:
        """Check HIPAA compliance"""
        findings = []
        
        # Check for encryption at rest and in transit
        if "https" not in code and "ssl" not in code:
            findings.append("HTTPS/SSL not enforced (HIPAA requires encryption in transit)")
        
        if "encrypt" not in code.lower():
            findings.append("Encryption at rest not implemented (HIPAA requirement)")
        
        # Check for access controls
        if "auth" not in code.lower():
            findings.append("No authentication mechanism found (HIPAA requires access controls)")
        
        return {
            "compliant": len(findings) == 0,
            "findings": findings,
            "findings_count": len(findings)
        }

    def _check_pci_dss(self, code: str, infrastructure: Dict) -> Dict[str, Any]:
        """Check PCI-DSS compliance"""
        findings = []
        
        # Check for hardcoded credentials
        if "password" in code or "api_key" in code or "secret" in code:
            findings.append("Potential hardcoded credentials (PCI-DSS violation)")
        
        # Check for secure communication
        if "http://" in code:
            findings.append("Insecure HTTP communication detected (PCI-DSS requires TLS)")
        
        return {
            "compliant": len(findings) == 0,
            "findings": findings,
            "findings_count": len(findings)
        }

    def _calculate_overall_compliance(self, compliance_status: Dict[str, Any]) -> int:
        """Calculate overall compliance percentage"""
        if not compliance_status:
            return 100
        
        compliant_count = sum(1 for status in compliance_status.values() if status.get("compliant", False))
        return int((compliant_count / len(compliance_status)) * 100)

    def _calculate_risk_level(self, findings_count: int) -> str:
        """Calculate risk level based on findings"""
        if findings_count == 0:
            return "NONE"
        elif findings_count <= 3:
            return "LOW"
        elif findings_count <= 8:
            return "MEDIUM"
        elif findings_count <= 15:
            return "HIGH"
        else:
            return "CRITICAL"

    def _generate_report(self, payload: Dict[str, Any]) -> str:
        """Generate compliance report"""
        report = f"""
# Compliance Report - {datetime.now().isoformat()}

## Summary
- **Total Findings**: {payload['findings_count']}
- **Risk Level**: {payload['risk_level']}
- **Frameworks Checked**: {', '.join(payload['frameworks'])}

## Findings by Framework
[Detailed findings would be listed here]

## Recommendations
1. Review all identified compliance gaps
2. Implement required controls
3. Schedule follow-up audit

**Generated by ComplianceAgent** 🤖
"""
        return report
