"""
Lambda handler for GitHub webhook events
Receives PR events and triggers the analysis pipeline
"""
import json
import boto3
import os
import logging
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')


def lambda_handler(event, context):
    """
    Handle GitHub webhook events
    
    Expected GitHub webhook payload:
    {
        "action": "opened|synchronize",
        "pull_request": {
            "id": "...",
            "title": "...",
            "body": "...",
            "head": {"sha": "...", "ref": "..."},
            "url": "..."
        }
    }
    """
    try:
        logger.info(f"Received webhook event: {json.dumps(event)}")
        
        # Parse GitHub event
        body = json.loads(event.get('body', '{}'))
        
        # Validate this is a PR event
        if 'pull_request' not in body:
            return format_response(400, "Not a pull request event")
        
        pr = body['pull_request']
        action = body.get('action', 'unknown')
        
        # We care about opened and synchronize actions
        if action not in ['opened', 'synchronize']:
            logger.info(f"Ignoring PR action: {action}")
            return format_response(200, "Event ignored")
        
        # Extract PR details
        pr_context = {
            "pr_id": pr.get('id'),
            "pr_number": pr.get('number'),
            "pr_title": pr.get('title'),
            "pr_body": pr.get('body'),
            "author": pr.get('user', {}).get('login'),
            "branch": pr.get('head', {}).get('ref'),
            "commit_sha": pr.get('head', {}).get('sha'),
            "repository": body.get('repository', {}).get('full_name'),
            "pr_url": pr.get('html_url'),
            "webhook_action": action
        }
        
        # Store event
        table = dynamodb.Table(os.environ.get('RESULTS_TABLE'))
        table.put_item(Item={
            'execution_id': f"webhook-{pr_context['pr_id']}",
            'timestamp': str(datetime.now().isoformat()),
            'event_type': 'webhook_received',
            'pr_context': pr_context,
            'status': 'pending_analysis'
        })
        
        # Publish SNS notification for analysis to pick up
        sns_client.publish(
            TopicArn=os.environ.get('ALERTS_TOPIC_ARN'),
            Subject=f"PR Analysis Triggered: {pr_context['pr_title']}",
            Message=json.dumps(pr_context)
        )
        
        logger.info(f"Successfully processed PR: {pr_context['pr_number']}")
        
        return format_response(200, "Webhook processed successfully", pr_context)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return format_response(500, f"Error: {str(e)}")


def format_response(status_code: int, message: str, data: Dict[str, Any] = None) -> Dict:
    """Format Lambda response"""
    response = {
        'statusCode': status_code,
        'body': json.dumps({
            'message': message,
            'data': data or {}
        })
    }
    return response


from datetime import datetime
