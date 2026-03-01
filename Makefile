.PHONY: help install deploy test clean local-test

help:
	@echo "SDLC Automation Agent - Available Commands"
	@echo "==========================================="
	@echo "make install       - Install dependencies"
	@echo "make local-test    - Run orchestrator locally"
	@echo "make test          - Run unit tests"
	@echo "make deploy        - Deploy to AWS"
	@echo "make destroy       - Destroy AWS resources"
	@echo "make dashboard     - Open CloudWatch dashboard"
	@echo "make logs          - Tail Lambda logs"
	@echo "make clean         - Remove build artifacts"

install:
	pip install -r requirements.txt
	pip install aws-cdk-lib constructs
	echo "Installation complete!"

local-test:
	@echo "Running local test..."
	python orchestrator.py

test:
	@echo "Running unit tests..."
	pytest tests/ -v --cov=agents

deploy:
	@echo "Deploying to AWS..."
	cd infrastructure && cdk deploy --require-approval never
	@echo "Deployment complete!"
	@echo "Next: Configure GitHub webhook (see DEPLOYMENT.md)"

destroy:
	@echo "WARNING: This will delete all AWS resources!"
	@read -p "Continue? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd infrastructure && cdk destroy; \
	fi

dashboard:
	@echo "Opening CloudWatch dashboard..."
	@echo "Visit: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:dashboardName=sdlc-automation-dashboard"

logs:
	aws logs tail /aws/lambda/sdlc-automation-WebhookLambda --follow

synth:
	@echo "Synthesizing CloudFormation template..."
	cd infrastructure && cdk synth

clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist/
	rm -rf build/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"

env-setup:
	cp .env.example .env
	@echo "Created .env file - please fill in your values"

lint:
	black agents/ orchestrator.py
	flake8 agents/ orchestrator.py --max-line-length=120

format:
	black agents/ orchestrator.py lambda_functions/

requirements-update:
	pip list --outdated
	@echo "To update: pip install -U <package-name>"
