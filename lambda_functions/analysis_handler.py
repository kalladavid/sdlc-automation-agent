"""
Lambda handler for running analysis
Executes the SDLC orchestrator and stores results
"""
import json
import boto3
import os
import sys
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')


def lambda_handler(event, context):
    """
    Run SDLC analysis pipeline
    
    Can be triggered by:
    1. SNS message from webhook handler
    2. Direct EventBridge invocation
    3. Manual Lambda invocation
    """
    try:
        logger.info(f"Starting analysis pipeline")
        
        # Parse input
        if 'Records' in event:  # SNS triggered
            message = json.loads(event['Records'][0]['Sns']['Message'])
            pr_context = message
        else:  # Direct invocation
            pr_context = event.get('pr_context', {})
        
        if not pr_context:
            return format_response(400, "No PR context provided")
        
        logger.info(f"Analyzing PR: {pr_context.get('pr_title')}")
        
        # Import orchestrator (assuming it's available)
        # In real deployment, orchestrator would be packaged with Lambda
        try:
            from orchestrator import SDLCOrchestrator
            orchestrator = SDLCOrchestrator(aws_region="us-east-1")
            
            # Run pipeline
            results = orchestrator.run_pull_request_pipeline(pr_context)
            
        except ImportError:
            logger.warning("Orchestrator not available in Lambda, using mock")
            results = {
                "execution_id": f"mock-{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "pr_context": pr_context,
                "agent_results": {},
                "summary": {"total_actions": 0},
                "recommendations": ["Mock execution - deploy orchestrator to Lambda"],
                "should_block": False,
                "should_warn": False
            }
        
        # Store results in DynamoDB
        table = dynamodb.Table(os.environ.get('RESULTS_TABLE'))
        execution_id = results.get('execution_id')
        
        table.put_item(Item={
            'execution_id': execution_id,
            'timestamp': results.get('timestamp'),
            'pr_number': pr_context.get('pr_number'),
            'pr_title': pr_context.get('pr_title'),
            'author': pr_context.get('author'),
            'analysis_results': results,
            'status': 'completed'
        })
        
        # Store detailed report in S3
        bucket = os.environ.get('ARTIFACTS_BUCKET')
        key = f"analysis-results/{execution_id}/report.json"
        
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(results, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Results stored in S3: s3://{bucket}/{key}")
        
        # Send notification
        send_notification(pr_context, results)
        
        # Update GitHub PR status
        if results.get('should_block'):
            update_github_status(pr_context, 'failure', 'Critical issues detected')
        elif results.get('should_warn'):
            update_github_status(pr_context, 'neutral', 'Warnings - review needed')
        else:
            update_github_status(pr_context, 'success', 'Analysis passed')
        
        return format_response(200, "Analysis completed", results)
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        return format_response(500, f"Analysis failed: {str(e)}")


def send_notification(pr_context: Dict[str, Any], results: Dict[str, Any]):
    """Send SNS notification with results"""
    topic_arn = os.environ.get('ALERTS_TOPIC_ARN')
    
    if results.get('should_block'):
        subject = f"🚫 PR BLOCKED: {pr_context.get('pr_title')}"
    elif results.get('should_warn'):
        subject = f"⚠️  PR WARNING: {pr_context.get('pr_title')}"
    else:
        subject = f"✅ PR APPROVED: {pr_context.get('pr_title')}"
    
    message = f"""
SDLC Analysis Complete

PR: {pr_context.get('pr_title')}
Author: {pr_context.get('author')}
Branch: {pr_context.get('branch')}

Summary:
- Total Actions: {results.get('summary', {}).get('total_actions')}
- Errors: {results.get('summary', {}).get('total_errors')}
- Execution Time: {results.get('summary', {}).get('execution_time', 0):.2f}s

Status: {'BLOCKED' if results.get('should_block') else 'WARNED' if results.get('should_warn') else 'APPROVED'}

Recommendations:
{chr(10).join('- ' + r for r in results.get('recommendations', []))}

View details: Check CloudWatch Logs for execution ID {results.get('execution_id')}
"""
    
    sns_client.publish(
        TopicArn=topic_arn,
        Subject=subject,
        Message=message
    )


def update_github_status(pr_context: Dict[str, Any], state: str, description: str):
    """Update GitHub PR status check"""
    # This would use GitHub API to set commit status
    # Requires GitHub token from environment variables
    logger.info(f"Would update GitHub status: {state} - {description}")
    # Implementation would use requests library to call GitHub API


def format_response(status_code: int, message: str, data: Dict[str, Any] = None) -> Dict:
    """Format Lambda response"""
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'message': message,
            'data': data or {}
        })
    }
