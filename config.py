"""
Configuration and Environment Setup
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
    
    # GitHub Configuration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_REPO_OWNER = os.getenv('GITHUB_REPO_OWNER')
    GITHUB_REPO_NAME = os.getenv('GITHUB_REPO_NAME')
    GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
    
    # AWS Service Names (set during CDK deployment)
    RESULTS_TABLE_NAME = os.getenv('RESULTS_TABLE_NAME', 'sdlc-automation-results')
    ARTIFACTS_BUCKET_NAME = os.getenv('ARTIFACTS_BUCKET_NAME', 'sdlc-automation-artifacts')
    ALERTS_TOPIC_ARN = os.getenv('ALERTS_TOPIC_ARN')
    
    # Lambda Configuration
    WEBHOOK_LAMBDA_NAME = os.getenv('WEBHOOK_LAMBDA_NAME', 'sdlc-automation-webhook')
    ANALYSIS_LAMBDA_NAME = os.getenv('ANALYSIS_LAMBDA_NAME', 'sdlc-automation-analysis')
    
    # Agent Configuration
    SECURITY_ENABLED = os.getenv('SECURITY_ENABLED', 'true').lower() == 'true'
    CODE_REVIEW_ENABLED = os.getenv('CODE_REVIEW_ENABLED', 'true').lower() == 'true'
    COMPLIANCE_ENABLED = os.getenv('COMPLIANCE_ENABLED', 'true').lower() == 'true'
    RISK_DETECTION_ENABLED = os.getenv('RISK_DETECTION_ENABLED', 'true').lower() == 'true'
    
    # Compliance Frameworks
    COMPLIANCE_FRAMEWORKS = os.getenv(
        'COMPLIANCE_FRAMEWORKS',
        'SOC2,GDPR,HIPAA,PCI_DSS'
    ).split(',')
    
    # Thresholds
    MIN_CODE_QUALITY_SCORE = int(os.getenv('MIN_CODE_QUALITY_SCORE', '80'))
    MAX_RISK_SCORE = int(os.getenv('MAX_RISK_SCORE', '50'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def from_env_file(cls, env_file: str = '.env') -> None:
        """Load configuration from file"""
        if os.path.exists(env_file):
            load_dotenv(env_file)
        else:
            raise FileNotFoundError(f"Configuration file {env_file} not found")


def create_example_env() -> str:
    """Create example .env file content"""
    return """# SDLC Automation Agent Configuration
# Copy this to .env and fill in your values

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# GitHub Configuration
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_REPO_OWNER=your-org
GITHUB_REPO_NAME=your-repo
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# AWS Service Names (will be set during deployment)
RESULTS_TABLE_NAME=sdlc-automation-results
ARTIFACTS_BUCKET_NAME=sdlc-automation-artifacts
ALERTS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:alerts

# Agent Configuration
SECURITY_ENABLED=true
CODE_REVIEW_ENABLED=true
COMPLIANCE_ENABLED=true
RISK_DETECTION_ENABLED=true

# Compliance Frameworks (comma-separated)
COMPLIANCE_FRAMEWORKS=SOC2,GDPR,HIPAA,PCI_DSS

# Thresholds
MIN_CODE_QUALITY_SCORE=80
MAX_RISK_SCORE=50

# Logging
LOG_LEVEL=INFO
"""


if __name__ == "__main__":
    # Generate example .env file
    example_env = create_example_env()
    with open('.env.example', 'w') as f:
        f.write(example_env)
    print("Created .env.example")
