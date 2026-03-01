# Deployment Guide - AWS Infrastructure Setup

## Prerequisites

1. **AWS Account** with appropriate permissions (Admin or full Lambda, DynamoDB, S3, SNS access)
2. **AWS CLI** configured with credentials
3. **Python 3.11+** installed
4. **AWS CDK** installed
5. **GitHub token** with repo admin access
6. **Docker** (optional, for local testing)

## Step 1: Local Development

### Install Dependencies

```bash
# Navigate to project directory
cd "c:\Users\daveedu.k\Documents\Devops projects\sdlc-automation-agent"

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install AWS CDK dependencies
pip install aws-cdk-lib constructs
```

### Test Locally

```bash
# Run the orchestrator
python orchestrator.py

# Run tests
pytest tests/ -v
```

## Step 2: Prepare AWS Environment

### Configure AWS CLI

```bash
# Configure credentials
aws configure

# Enter:
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret access key]
# Default region: us-east-1
# Default output format: json
```

### Create S3 Bucket for CDK Assets

```bash
# CDK needs a bootstrap bucket
aws s3 mb s3://sdlc-automation-cdk-assets-$(date +%s) --region us-east-1
```

### Bootstrap CDK

```bash
cd infrastructure

cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1

# Example:
cdk bootstrap aws://123456789012/us-east-1
```

## Step 3: Deploy Infrastructure

### Synthesize CDK

```bash
cd infrastructure

# Generate CloudFormation template
cdk synth

# View the template
cat cdk.out/SDLCAutomationStack.template.json
```

### Deploy Stack

```bash
# Deploy (requires approval for each resource)
cdk deploy

# Or deploy without approval
cdk deploy --require-approval never

# Or deploy specific resources
cdk deploy SDLCAutomationStack
```

**Expected Output:**
```
✓ SDLCAutomationStack
  ArtifactsBucket: arn:aws:s3:::sdlc-automation-artifacts-xxx
  ResultsTable: sdlc-automation-results-xxx
  AlertsTopic: arn:aws:sns:us-east-1:xxx:alerts-topic
  WebhookLambda: arn:aws:lambda:us-east-1:xxx:function:webhook
  AnalysisLambda: arn:aws:lambda:us-east-1:xxx:function:analysis
```

### Get Deployment Outputs

```bash
# List stack resources
aws cloudformation list-stack-resources \
  --stack-name SDLCAutomationStack \
  --region us-east-1

# Get specific resource
aws lambda list-functions \
  --region us-east-1 \
  --query 'Functions[?contains(FunctionName, `WebhookLambda`)]'
```

## Step 4: Get Lambda Webhook URL

```bash
# Option 1: AWS Console
# Go to Lambda → WebhookLambda → Function URL

# Option 2: AWS CLI
aws lambda get-function-url-config \
  --function-name sdlc-automation-WebhookLambda \
  --region us-east-1

# Save the FunctionUrl
```

## Step 5: Setup GitHub Integration

### Create GitHub Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Create new token with scopes:
   - `repo` (full repository access)
   - `admin:repo_hook` (for webhooks)
   - `workflow` (for actions)
3. Copy token (you won't see it again!)

### Setup Webhook Using Script

```python
# Create setup_github.py
import os
from integrations.github_integration import setup_github_integration

# Configuration
REPO_OWNER = "your-org"
REPO_NAME = "your-repo"
WEBHOOK_URL = "https://your-lambda-function.execute-api.us-east-1.amazonaws.com"
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']

# Setup
try:
    integration = setup_github_integration(
        REPO_OWNER,
        REPO_NAME,
        WEBHOOK_URL,
        GITHUB_TOKEN
    )
    print("✓ Webhook setup successful!")
except Exception as e:
    print(f"✗ Setup failed: {e}")

# Run:
# GITHUB_TOKEN=ghp_xxxxxxxxxxxx python setup_github.py
```

### Manual Webhook Setup

1. Go to GitHub repo → Settings → Webhooks
2. Click "Add webhook"
3. Fill in:
   - **Payload URL:** (Your Lambda Function URL)
   - **Content type:** application/json
   - **Events:** Let me select individual events
     - ✓ Pull requests
     - ✓ Push
   - ✓ Active
4. Click "Add webhook"

## Step 6: Configure Monitoring

### Create CloudWatch Alarms

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name sdlc-lambda-errors \
  --alarm-description "Alert on high Lambda error rate" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1

# DynamoDB throttling alarm
aws cloudwatch put-metric-alarm \
  --alarm-name sdlc-dynamodb-throttle \
  --metric-name UserErrors \
  --namespace AWS/DynamoDB \
  --statistic Sum \
  --period 60 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

### View Dashboard

```bash
# Navigate to CloudWatch → Dashboards → sdlc-automation-dashboard
# Or use CLI:
aws cloudwatch describe-dashboards \
  --dashboard-name-prefix sdlc
```

## Step 7: Test the Pipeline

### Create a Test PR

```bash
# In your repository
git checkout -b test/automated-analysis

# Create a test Python file with intentional issues
cat > test_bad_code.py << 'EOF'
# This code has security and quality issues
api_key = "sk_live_1234567890abcdef"
password = "admin123"

def authenticate(user, pwd):
    if user == "admin" and pwd == password:
        return True
    return False

global_counter = 0
for i in range(100):
    for j in range(100):
        global_counter += i * j
EOF

# Commit and push
git add test_bad_code.py
git commit -m "Test: Automated analysis pipeline"
git push origin test/automated-analysis

# Create PR in GitHub UI
```

### Monitor Execution

```bash
# Watch Lambda logs
aws logs tail /aws/lambda/sdlc-automation-WebhookLambda --follow

# Check DynamoDB for results
aws dynamodb scan \
  --table-name sdlc-automation-ResultsTable \
  --limit 10
```

### Check Results

```bash
# View S3 artifacts
aws s3 ls s3://sdlc-automation-artifacts-xxx/analysis-results/

# Download report
aws s3 cp \
  s3://sdlc-automation-artifacts-xxx/analysis-results/*/report.json \
  ./last-report.json

# View report
cat last-report.json | jq .
```

## Step 8: Production Configuration

### Enable Logging

```bash
# Set log retention
aws logs put-retention-policy \
  --log-group-name /aws/lambda/sdlc-automation-WebhookLambda \
  --retention-in-days 30
```

### Setup SNS Notifications

```bash
# Subscribe to alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:xxx:sdlc-alerts \
  --protocol email \
  --notification-endpoint your-email@company.com

# Confirm subscription via email
```

### Enable Backups

```bash
# Enable DynamoDB backups
aws dynamodb update-continuous-backups \
  --table-name sdlc-automation-ResultsTable \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

### Configure S3 Lifecycle

```bash
# Archive old reports
aws s3api put-bucket-lifecycle-configuration \
  --bucket sdlc-automation-artifacts-xxx \
  --lifecycle-configuration file://lifecycle.json
```

**lifecycle.json:**
```json
{
  "Rules": [
    {
      "Id": "Archive old analyses",
      "Status": "Enabled",
      "Prefix": "analysis-results/",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 730
      }
    }
  ]
}
```

## Step 9: Cost Optimization

### Estimate Costs

```bash
# At scale (100 PRs/day):
# Lambda: ~$0.20/day (1M requests free tier)
# DynamoDB: $1/day (on-demand)
# S3: $0.50/day (storage)
# SNS: $0.50/day (notifications)
# Total: ~$2.20/day = $66/month
```

### Cost Controls

```bash
# Set Lambda reserved concurrency
aws lambda put-function-concurrency \
  --function-name sdlc-automation-WebhookLambda \
  --reserved-concurrent-executions 100

# Monitor costs
aws ce get-cost-and-usage \
  --time-period Start=2026-03-01,End=2026-03-02 \
  --granularity DAILY \
  --metrics BlendedCost
```

## Step 10: Cleanup (if needed)

```bash
# Delete all AWS resources
cd infrastructure
cdk destroy --force

# Or manually delete via Console
# This will remove all Lambda, DynamoDB, S3, SNS resources
```

## Troubleshooting

### Lambda Timeout

```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name sdlc-automation-AnalysisLambda \
  --timeout 600
```

### DynamoDB Throttling

```bash
# Switch to on-demand billing
aws dynamodb update-billing-mode \
  --table-name sdlc-automation-ResultsTable \
  --billing-mode PAY_PER_REQUEST
```

### Webhook Not Triggering

```bash
# Verify webhook in GitHub Settings → Webhooks
# Check "Recent Deliveries" tab for error responses
# Verify Lambda Function URL is accessible

# Test manually:
curl -X POST https://your-lambda-function.amazonaws.com \
  -H 'Content-Type: application/json' \
  -d '{"action":"opened","pull_request":{"id":1,"title":"Test"}}'
```

### Permission Denied Errors

```bash
# Check Lambda role permissions
aws iam get-role-policy \
  --role-name SDLCAutomationStack-LambdaExecutionRole \
  --policy-name inline-policy

# Grant additional permissions if needed
aws iam put-role-policy \
  --role-name SDLCAutomationStack-LambdaExecutionRole \
  --policy-name additional-policy \
  --policy-document file://policy.json
```

## Next Steps

1. ✅ Deploy infrastructure
2. ✅ Configure GitHub webhook
3. ✅ Test with sample PR
4. ✅ Setup notifications
5. ✅ Monitor performance
6. ✅ Optimize costs
7. ✅ Document custom rules
8. ✅ Train team on results interpretation

## Support

For issues:
1. Check CloudWatch Logs
2. Review Lambda error messages
3. Verify GitHub webhook payloads
4. Check DynamoDB for stored events
5. Monitor SNS notifications

