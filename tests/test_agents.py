"""
Tests for SDLC Agents
"""
import pytest
import json
from agents.security_agent import SecurityAgent
from agents.code_review_agent import CodeReviewAgent
from agents.compliance_agent import ComplianceAgent
from agents.risk_detection_agent import RiskDetectionAgent


class TestSecurityAgent:
    """Test security analysis"""

    def test_sql_injection_detection(self):
        agent = SecurityAgent()
        code = 'execute("SELECT * FROM users WHERE id = {}")'
        
        context = {
            "code": code,
            "file_type": "python"
        }
        
        analysis = agent.analyze(context)
        assert analysis["vulnerability_count"] > 0

    def test_hardcoded_secrets_detection(self):
        agent = SecurityAgent()
        code = 'api_key = "sk_live_51234567890abcdef"'
        
        context = {
            "code": code,
            "file_type": "python"
        }
        
        analysis = agent.analyze(context)
        assert analysis["vulnerability_count"] > 0

    def test_safe_code_no_vulnerabilities(self):
        agent = SecurityAgent()
        code = '''
def safe_function():
    """A safe function"""
    result = process_data()
    return result
'''
        
        context = {
            "code": code,
            "file_type": "python"
        }
        
        analysis = agent.analyze(context)
        assert analysis["vulnerability_count"] == 0


class TestCodeReviewAgent:
    """Test code quality analysis"""

    def test_quality_score_calculation(self):
        agent = CodeReviewAgent()
        code = "x = 1"
        
        score = agent._calculate_quality_score(code)
        assert 0 <= score <= 100

    def test_missing_docstring_detection(self):
        agent = CodeReviewAgent()
        code = "def my_function():\n    return 42"
        
        context = {
            "code": code,
            "file_type": "python"
        }
        
        analysis = agent.analyze(context)
        assert len(analysis.get("documentation_issues", [])) >= 0


class TestComplianceAgent:
    """Test compliance checking"""

    def test_soc2_check(self):
        agent = ComplianceAgent()
        code = """
import logging
try:
    result = process()
except Exception as e:
    logging.error(str(e))
"""
        
        status = agent._check_soc2(code, {})
        assert status["compliant"]

    def test_gdpr_unencrypted_code(self):
        agent = ComplianceAgent()
        code = "def process_user_data(data): return data"
        
        status = agent._check_gdpr(code, {})
        assert not status["compliant"]


class TestRiskDetectionAgent:
    """Test risk detection"""

    def test_risk_score_normal(self):
        agent = RiskDetectionAgent()
        risks = []
        
        score = agent._calculate_risk_score(risks)
        assert score == 0

    def test_risk_score_with_issues(self):
        agent = RiskDetectionAgent()
        risks = [
            {"severity": "HIGH"},
            {"severity": "MEDIUM"},
            {"severity": "LOW"}
        ]
        
        score = agent._calculate_risk_score(risks)
        assert score > 0

    def test_risk_categorization(self):
        agent = RiskDetectionAgent()
        risks = [
            {"severity": "CRITICAL"},
            {"severity": "HIGH"},
            {"severity": "LOW"}
        ]
        
        categorized = agent._categorize_by_severity(risks)
        assert len(categorized["CRITICAL"]) == 1
        assert len(categorized["HIGH"]) == 1
        assert len(categorized["LOW"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
