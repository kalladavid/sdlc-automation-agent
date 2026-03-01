"""
Code Review Agent: Automated code quality analysis and review
- Analyzes code quality metrics
- Checks coding standards
- Suggests improvements
"""
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent, AgentAction, AgentResult
import logging

logger = logging.getLogger(__name__)


class CodeReviewAgent(BaseAgent):
    """Agent for automated code review and quality analysis"""

    def __init__(self, aws_region: str = "us-east-1"):
        super().__init__("CodeReviewAgent", aws_region)
        self.quality_thresholds = {
            "max_function_lines": 50,
            "max_cyclomatic_complexity": 10,
            "min_test_coverage": 80,
            "max_code_duplication": 5
        }

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code quality"""
        code_content = context.get("code", "")
        file_type = context.get("file_type", "")
        pr_title = context.get("pr_title", "")
        
        findings = {
            "code_quality_score": self._calculate_quality_score(code_content),
            "function_analysis": self._analyze_functions(code_content),
            "naming_violations": self._check_naming_conventions(code_content, file_type),
            "documentation_issues": self._check_documentation(code_content),
            "complexity_issues": self._analyze_complexity(code_content),
            "improvement_suggestions": [],
            "total_issues": 0
        }
        
        # Generate suggestions
        findings["improvement_suggestions"] = self._generate_suggestions(findings)
        findings["total_issues"] = (
            len(findings.get("naming_violations", [])) +
            len(findings.get("documentation_issues", [])) +
            len(findings.get("complexity_issues", []))
        )
        
        return findings

    def recommend_actions(self, analysis: Dict[str, Any]) -> List[AgentAction]:
        """Recommend code review actions"""
        actions = []
        
        if analysis["code_quality_score"] < 70:
            action = AgentAction(
                action_type="REQUEST_CHANGES",
                description=f"Code quality score is {analysis['code_quality_score']}%, below 70% threshold",
                payload={
                    "quality_score": analysis["code_quality_score"],
                    "blocking": True
                },
                timestamp=datetime.now()
            )
            actions.append(action)
        
        if analysis["total_issues"] > 0:
            action = AgentAction(
                action_type="ADD_REVIEW_COMMENT",
                description=f"Add review comments for {analysis['total_issues']} identified issues",
                payload={
                    "issues_count": analysis["total_issues"],
                    "suggestions": analysis["improvement_suggestions"][:5]
                },
                timestamp=datetime.now()
            )
            actions.append(action)
        
        if analysis["code_quality_score"] >= 80:
            action = AgentAction(
                action_type="APPROVE_PR",
                description="Code quality is sufficient, recommend approval",
                payload={
                    "quality_score": analysis["code_quality_score"],
                    "blocking": False
                },
                timestamp=datetime.now()
            )
            actions.append(action)
        
        return actions

    def execute(self, actions: List[AgentAction]) -> AgentResult:
        """Execute code review actions"""
        executed_actions = []
        errors = []
        
        for action in actions:
            try:
                logger.info(f"Executing: {action.action_type} - {action.description}")
                self.log_action(action)
                executed_actions.append(action)
            except Exception as e:
                errors.append(f"Error executing {action.action_type}: {str(e)}")
        
        return AgentResult(
            success=len(errors) == 0,
            message=f"Executed {len(executed_actions)} code review actions",
            actions=executed_actions,
            data={
                "review_comments": len([a for a in executed_actions if a.action_type == "ADD_REVIEW_COMMENT"]),
                "approvals": len([a for a in executed_actions if a.action_type == "APPROVE_PR"]),
                "rejections": len([a for a in executed_actions if a.action_type == "REQUEST_CHANGES"])
            },
            errors=errors,
            duration_seconds=0
        )

    def _calculate_quality_score(self, code: str) -> int:
        """Calculate code quality score"""
        score = 100
        
        # Deduct for various issues
        if len(code) < 50:
            score -= 10
        if code.count("TODO") > 5:
            score -= 5
        if code.count("FIXME") > 3:
            score -= 5
        if "commented code" in code.lower():
            score -= 5
        
        return max(0, score)

    def _analyze_functions(self, code: str) -> List[Dict[str, Any]]:
        """Analyze functions in code"""
        functions = []
        # Simplified function detection
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if 'def ' in line or 'function ' in line:
                functions.append({
                    "line": i + 1,
                    "definition": line.strip()
                })
        return functions

    def _check_naming_conventions(self, code: str, file_type: str) -> List[str]:
        """Check for naming convention violations"""
        violations = []
        
        if file_type in ["python", "py"]:
            # Check for camelCase (should be snake_case)
            import re
            camel_pattern = r'\b[a-z]+[A-Z][a-zA-Z]*\b'
            if re.search(camel_pattern, code):
                violations.append("Found camelCase variables (should use snake_case)")
        
        return violations

    def _check_documentation(self, code: str) -> List[str]:
        """Check for documentation issues"""
        issues = []
        
        lines = code.split('\n')
        for line in lines:
            if 'def ' in line or 'class ' in line:
                # Check if next line is a docstring
                if not ('"""' in code or "'''" in code):
                    issues.append("Missing docstring for function/class")
                    break
        
        return issues

    def _analyze_complexity(self, code: str) -> List[Dict[str, Any]]:
        """Analyze code complexity"""
        issues = []
        
        # Check for deeply nested code
        lines = code.split('\n')
        for i, line in enumerate(lines):
            indent = len(line) - len(line.lstrip())
            if indent > 24:  # More than 3 levels (assuming 8 spaces per level)
                issues.append({
                    "line": i + 1,
                    "type": "deep_nesting",
                    "message": "Code is deeply nested, consider refactoring"
                })
        
        return issues

    def _generate_suggestions(self, findings: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if len(findings["naming_violations"]) > 0:
            suggestions.append("Follow consistent naming conventions (snake_case for Python)")
        
        if len(findings["documentation_issues"]) > 0:
            suggestions.append("Add docstrings to all public functions and classes")
        
        if len(findings["complexity_issues"]) > 0:
            suggestions.append("Reduce code nesting and complexity")
        
        if findings["code_quality_score"] < 70:
            suggestions.append("Consider refactoring for better readability")
        
        return suggestions
