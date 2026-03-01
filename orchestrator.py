"""
Main Agent Orchestrator: Coordinates all agents in the SDLC automation pipeline
Manages workflow, logging, and AWS integration
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from agents.base_agent import AgentResult
from agents.security_agent import SecurityAgent
from agents.code_review_agent import CodeReviewAgent
from agents.compliance_agent import ComplianceAgent
from agents.risk_detection_agent import RiskDetectionAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SDLCOrchestrator:
    """Orchestrates SDLC automation agents"""

    def __init__(self, aws_region: str = "us-east-1"):
        self.aws_region = aws_region
        self.execution_id = datetime.now().isoformat()
        
        # Initialize agents
        self.security_agent = SecurityAgent(aws_region)
        self.code_review_agent = CodeReviewAgent(aws_region)
        self.compliance_agent = ComplianceAgent(aws_region)
        self.risk_detection_agent = RiskDetectionAgent(aws_region)
        
        self.agents = [
            self.security_agent,
            self.code_review_agent,
            self.compliance_agent,
            self.risk_detection_agent
        ]
        
        self.results: Dict[str, AgentResult] = {}
        logger.info(f"SDLC Orchestrator initialized (Execution ID: {self.execution_id})")

    def run_pull_request_pipeline(self, pr_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full pipeline for a pull request"""
        logger.info("=" * 80)
        logger.info("🚀 STARTING PR PIPELINE")
        logger.info(f"PR: {pr_context.get('pr_title', 'Unknown')}")
        logger.info("=" * 80)
        
        pipeline_results = {
            "execution_id": self.execution_id,
            "timestamp": datetime.now().isoformat(),
            "pr_context": {
                "title": pr_context.get("pr_title"),
                "author": pr_context.get("author"),
                "branch": pr_context.get("branch")
            },
            "agent_results": {},
            "summary": {},
            "recommendations": [],
            "should_block": False,
            "should_warn": False
        }
        
        try:
            # Run security analysis
            logger.info("\n🔒 Running Security Analysis...")
            security_result = self.security_agent.run(pr_context)
            self.results["security"] = security_result
            pipeline_results["agent_results"]["security"] = self._serialize_result(security_result)
            
            # Run code review
            logger.info("\n📋 Running Code Review...")
            code_review_result = self.code_review_agent.run(pr_context)
            self.results["code_review"] = code_review_result
            pipeline_results["agent_results"]["code_review"] = self._serialize_result(code_review_result)
            
            # Run compliance check
            logger.info("\n✅ Running Compliance Check...")
            compliance_result = self.compliance_agent.run(pr_context)
            self.results["compliance"] = compliance_result
            pipeline_results["agent_results"]["compliance"] = self._serialize_result(compliance_result)
            
            # Run risk detection
            logger.info("\n⚠️  Running Risk Detection...")
            risk_result = self.risk_detection_agent.run(pr_context)
            self.results["risk"] = risk_result
            pipeline_results["agent_results"]["risk"] = self._serialize_result(risk_result)
            
            # Aggregate results
            pipeline_results["summary"] = self._aggregate_results()
            pipeline_results["recommendations"] = self._generate_recommendations()
            pipeline_results["should_block"] = self._should_block_pr()
            pipeline_results["should_warn"] = self._should_warn_pr()
            
            # Log summary
            self._log_summary(pipeline_results)
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}", exc_info=True)
            pipeline_results["error"] = str(e)
        
        return pipeline_results

    def _serialize_result(self, result: AgentResult) -> Dict[str, Any]:
        """Convert AgentResult to serializable dict"""
        return {
            "success": result.success,
            "message": result.message,
            "duration_seconds": result.duration_seconds,
            "actions_count": len(result.actions),
            "errors": result.errors,
            "data": result.data
        }

    def _aggregate_results(self) -> Dict[str, Any]:
        """Aggregate results from all agents"""
        summary = {
            "total_actions": sum(len(r.actions) for r in self.results.values()),
            "total_errors": sum(len(r.errors) for r in self.results.values()),
            "all_agents_successful": all(r.success for r in self.results.values()),
            "execution_time": sum(r.duration_seconds for r in self.results.values()),
            "agent_status": {
                name: "✓" if result.success else "✗"
                for name, result in self.results.items()
            }
        }
        return summary

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on agent findings"""
        recommendations = []
        
        # Analyze security findings
        security_result = self.results.get("security")
        if security_result and not security_result.success:
            recommendations.append("Address critical security vulnerabilities before merging")
        
        # Analyze code review findings
        code_review_result = self.results.get("code_review")
        if code_review_result and code_review_result.data.get("rejections", 0) > 0:
            recommendations.append("Resolve code quality issues flagged by review agent")
        
        # Analyze compliance findings
        compliance_result = self.results.get("compliance")
        if compliance_result and compliance_result.data.get("escalations", 0) > 0:
            recommendations.append("Review compliance escalations with security team")
        
        # Analyze risk findings
        risk_result = self.results.get("risk")
        if risk_result and risk_result.data.get("deployments_blocked", 0) > 0:
            recommendations.append("Critical risks must be resolved before deployment")
        
        return recommendations

    def _should_block_pr(self) -> bool:
        """Determine if PR should be blocked"""
        risk_result = self.results.get("risk")
        if risk_result and risk_result.data.get("deployments_blocked", 0) > 0:
            return True
        
        security_result = self.results.get("security")
        if security_result and security_result.data.get("fixes_applied", 0) > 5:
            return True
        
        return False

    def _should_warn_pr(self) -> bool:
        """Determine if PR should have warnings"""
        risk_result = self.results.get("risk")
        if risk_result and risk_result.data.get("warnings", 0) > 0:
            return True
        
        code_review_result = self.results.get("code_review")
        if code_review_result and code_review_result.data.get("issues", 0) > 0:
            return True
        
        return False

    def _log_summary(self, pipeline_results: Dict[str, Any]):
        """Log execution summary"""
        summary = pipeline_results["summary"]
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 PIPELINE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Actions Taken: {summary['total_actions']}")
        logger.info(f"Total Errors: {summary['total_errors']}")
        logger.info(f"All Agents Successful: {summary['all_agents_successful']}")
        logger.info(f"Execution Time: {summary['execution_time']:.2f}s")
        logger.info("\nAgent Status:")
        for agent, status in summary["agent_status"].items():
            logger.info(f"  {status} {agent}")
        
        if pipeline_results["recommendations"]:
            logger.info("\nRecommendations:")
            for rec in pipeline_results["recommendations"]:
                logger.info(f"  • {rec}")
        
        if pipeline_results["should_block"]:
            logger.warning("🚫 PR SHOULD BE BLOCKED")
        elif pipeline_results["should_warn"]:
            logger.warning("⚠️  PR HAS WARNINGS")
        else:
            logger.info("✅ PR READY FOR REVIEW")
        
        logger.info("=" * 80 + "\n")

    def export_results(self, format: str = "json") -> str:
        """Export results in specified format"""
        if format == "json":
            return json.dumps(
                {name: self._serialize_result(result) for name, result in self.results.items()},
                indent=2
            )
        return str(self.results)


def main():
    """Example usage"""
    
    # Sample PR context
    pr_context = {
        "pr_title": "Feature: Add user authentication",
        "author": "developer@company.com",
        "branch": "feature/auth",
        "code": """
def authenticate_user(username, password):
    # TODO: Add proper password hashing
    if username == "admin" and password == "admin123":
        return True
    return False

api_key = "sk_test_51234567890"
""",
        "file_type": "python",
        "infrastructure": {
            "logging": True,
            "monitoring": False,
            "backup": False
        },
        "deployment": {
            "strategy": "all-at-once"
        }
    }
    
    # Run orchestrator
    orchestrator = SDLCOrchestrator(aws_region="us-east-1")
    results = orchestrator.run_pull_request_pipeline(pr_context)
    
    # Export results
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    print(orchestrator.export_results("json"))


if __name__ == "__main__":
    main()
