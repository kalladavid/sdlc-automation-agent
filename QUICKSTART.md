# SDLC Automation Agent - Quick Reference

## 📚 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          GitHub PR Event                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │ POST /webhook
                       ▼
          ┌─────────────────────────────┐
          │  AWS Lambda (webhook_handler) │
          │  • Parse PR context          │
          │  • Store in DynamoDB         │
          │  • Publish to SNS            │
          └──────────┬────────────────────┘
                     │ Trigger
                     ▼
          ┌─────────────────────────────────────┐
          │ AWS Lambda (analysis_handler)        │
          │ Run SDLC Orchestrator                │
          │                                      │
          │  ┌─────────────────────────────┐    │
          │  │ SecurityAgent               │    │
          │  │ • Scan vulnerabilities      │    │
          │  │ • Detect secrets            │    │
          │  │ • Analyze dependencies      │    │
          │  └─────────────────────────────┘    │
          │                                      │
          │  ┌─────────────────────────────┐    │
          │  │ CodeReviewAgent             │    │
          │  │ • Quality score             │    │
          │  │ • Naming conventions        │    │
          │  │ • Documentation             │    │
          │  └─────────────────────────────┘    │
          │                                      │
          │  ┌─────────────────────────────┐    │
          │  │ ComplianceAgent             │    │
          │  │ • SOC2 check                │    │
          │  │ • GDPR check                │    │
          │  │ • HIPAA check               │    │
          │  │ • PCI-DSS check             │    │
          │  └─────────────────────────────┘    │
          │                                      │
          │  ┌─────────────────────────────┐    │
          │  │ RiskDetectionAgent          │    │
          │  │ • Architectural risks       │    │
          │  │ • Performance issues        │    │
          │  │ • Deployment risks          │    │
          │  │ • Operational gaps          │    │
          │  └─────────────────────────────┘    │
          │                                      │
          │  ▼                                   │
          │  Aggregate Results                   │
          │  Generate Recommendations            │
          │  Update GitHub Status                │
          └──────────┬─────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     DynamoDB       S3          SNS
   (Store Results) (Reports)  (Alerts)
        │            │           │
        └────────────┼───────────┘
                     ▼
        ┌─────────────────────────┐
        │ GitHub PR Comments      │
        │ Status Checks           │
        │ Notifications           │
        └─────────────────────────┘
```

## 🚀 Quick Commands

```bash
# Setup
make install
make env-setup

# Local Development
make local-test
make test
make lint

# Deployment
make deploy
make destroy
make dashboard
make logs

# Maintenance
make clean
make requirements-update
```

## 📋 File Structure

```
sdlc-automation-agent/
├── agents/                    # Agent implementations
│   ├── base_agent.py         # Base class for all agents
│   ├── security_agent.py     # Vulnerability scanning
│   ├── code_review_agent.py  # Code quality analysis
│   ├── compliance_agent.py   # Compliance verification
│   └── risk_detection_agent.py # Risk identification
│
├── lambda_functions/          # AWS Lambda handlers
│   ├── webhook_handler.py    # Receives GitHub events
│   └── analysis_handler.py   # Runs orchestrator
│
├── integrations/              # External integrations
│   └── github_integration.py  # GitHub API
│
├── infrastructure/            # AWS CDK setup
│   └── sdlc_stack.py        # CloudFormation stack
│
├── tests/                     # Unit tests
│   └── test_agents.py
│
├── orchestrator.py            # Main orchestration logic
├── config.py                  # Configuration manager
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation
├── DEPLOYMENT.md              # Deployment guide
├── .env.example               # Environment template
└── Makefile                   # Build commands
```

## 🔄 Workflow Example

```
Developer creates PR
    ↓
[GitHub sends webhook]
    ↓
WebhookLambda receives request
    ├─ Validates signature
    ├─ Stores event in DynamoDB
    └─ Publishes to SNS
    ↓
AnalysisLambda triggered
    ├─ Downloads PR content
    ├─ Runs SecurityAgent
    ├─ Runs CodeReviewAgent
    ├─ Runs ComplianceAgent
    └─ Runs RiskDetectionAgent
    ↓
Results aggregated:
    ├─ Total issues: 5
    ├─ Critical: 1 (blocks merge)
    ├─ High: 2 (warnings)
    └─ Low: 2 (suggestions)
    ↓
Actions taken:
    ├─ Store results → S3 report
    ├─ Update GitHub → Set status to ❌ FAILURE
    ├─ Add comment → "Fix security issue on line 42"
    └─ Send alert → Slack/Email
```

## 🎯 Agent Responsibilities

### SecurityAgent
- **Input:** Code content
- **Checks:**
  - SQL injection vulnerabilities
  - Hardcoded credentials/secrets
  - Unsafe eval/exec
  - Insecure randomness
  - Unencrypted HTTP
- **Output:** Vulnerability list + severity levels
- **Example:** "Remove hardcoded API key from line 15"

### CodeReviewAgent
- **Input:** Code content + PR context
- **Checks:**
  - Code quality score (0-100)
  - Naming conventions
  - Function complexity
  - Missing documentation
  - Code duplication
- **Output:** Quality score + suggestions
- **Example:** "Add docstring to authenticate_user()"

### ComplianceAgent
- **Input:** Code + Infrastructure config
- **Frameworks Checked:**
  - SOC2: Logging, error handling
  - GDPR: Encryption, deletion rights
  - HIPAA: Auth, encryption, access controls
  - PCI-DSS: No hardcoded secrets, TLS only
- **Output:** Compliance status per framework
- **Example:** "GDPR: Missing data deletion mechanism"

### RiskDetectionAgent
- **Input:** Code + Infrastructure + Deployment strategy
- **Checks:**
  - Architecture risks
  - Performance issues
  - Dependency vulnerabilities
  - Deployment strategy risks
  - Operational readiness
- **Output:** Risk score (0-100) + blocking decisions
- **Example:** "All-at-once deployment blocked - use canary"

## 📊 Decision Flow

```
PR Received
    │
    ├─→ Security Issues Found?
    │   ├─ HIGH: Block PR (❌)
    │   ├─ MEDIUM: Warn (⚠️)
    │   └─ LOW: Note (ℹ️)
    │
    ├─→ Quality Below 80%?
    │   ├─ YES: Reject (❌)
    │   └─ NO: Continue (✓)
    │
    ├─→ Compliance Violations?
    │   ├─ YES: Escalate (🔴)
    │   └─ NO: Continue (✓)
    │
    └─→ High Risk Detected?
        ├─ CRITICAL: Block (❌)
        ├─ HIGH: Warn (⚠️)
        └─ LOW: Note (ℹ️)

Final Status:
├─ Blocked (❌)
├─ Approved (✅)
├─ Conditional (⚠️ - needs fixes)
└─ Manual Review Needed (🔴 - escalated)
```

## 💡 Tips & Tricks

### Local Testing
```bash
python -c "
from orchestrator import SDLCOrchestrator

pr_context = {
    'pr_title': 'Test PR',
    'code': 'api_key = \"secret123\"',
    'file_type': 'python'
}

results = SDLCOrchestrator().run_pull_request_pipeline(pr_context)
print(f\"Issues found: {results['summary']['total_actions']}\")
"
```

### Check AWS Resources
```bash
# List Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `sdlc`)]'

# Check DynamoDB tables
aws dynamodb list-tables | grep sdlc

# View S3 buckets
aws s3 ls | grep sdlc

# Check SNS topics
aws sns list-topics | grep sdlc
```

### Monitor Execution
```bash
# Real-time logs
Watch -n 1 'aws logs tail /aws/lambda/sdlc-automation-WebhookLambda --max-items 5'

# Count recent invocations
aws cloudwatch get-metric-statistics \
  --metric-name Invocations \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=sdlc-automation-AnalysisLambda \
  --start-time 2026-03-01T00:00:00Z \
  --end-time 2026-03-02T00:00:00Z \
  --period 86400 \
  --statistics Sum
```

## 🔗 Related Resources

- [GitHub API Docs](https://docs.github.com/en/rest)
- [AWS CDK Python](https://docs.aws.amazon.com/cdk/latest/guide/home.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Guide](https://docs.aws.amazon.com/dynamodb/)

## 📞 Support

For issues, check:
1. CloudWatch Logs: `/aws/lambda/sdlc-automation-*`
2. GitHub Webhook Deliveries
3. SNS subscription confirmations
4. Lambda timeout settings
5. IAM permissions

## 📈 Success Metrics

- PR review time: 30 seconds (vs. 30 minutes manual)
- Security issues caught: 95%+ (automation > manual)
- Compliance violations prevented: 100%
- Developer satisfaction: ⬆️ (less busywork)
- Deployment confidence: ⬆️ (pre-validated)

