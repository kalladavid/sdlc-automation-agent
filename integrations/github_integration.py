"""
GitHub Integration Module
Handles GitHub API interactions, webhook setup, and PR management
"""
import os
import requests
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GitHubIntegration:
    """Manages GitHub integration for SDLC automation"""

    def __init__(self, repo_owner: str, repo_name: str, github_token: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
        self.base_url = "https://api.github.com"
        self.repo_full_name = f"{repo_owner}/{repo_name}"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def setup_webhook(self, webhook_url: str, events: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Setup GitHub webhook for PR events
        
        Args:
            webhook_url: AWS Lambda webhook endpoint
            events: List of events to listen for (default: pull_request)
        
        Returns:
            Webhook configuration response
        """
        if events is None:
            events = ["pull_request"]
        
        webhook_config = {
            "name": "web",
            "active": True,
            "events": events,
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "insecure_ssl": "0"
            }
        }
        
        url = f"{self.base_url}/repos/{self.repo_full_name}/hooks"
        
        try:
            response = requests.post(url, headers=self.headers, json=webhook_config)
            response.raise_for_status()
            logger.info(f"Webhook created successfully: {webhook_url}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create webhook: {str(e)}")
            raise

    def add_pr_comment(self, pr_number: int, comment: str) -> Dict[str, Any]:
        """Add comment to PR"""
        url = f"{self.base_url}/repos/{self.repo_full_name}/issues/{pr_number}/comments"
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json={"body": comment}
            )
            response.raise_for_status()
            logger.info(f"Comment added to PR #{pr_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add comment: {str(e)}")
            raise

    def update_pr_status(self, commit_sha: str, state: str, description: str, 
                        context: str = "sdlc-automation") -> Dict[str, Any]:
        """
        Update GitHub PR status check
        
        Args:
            commit_sha: Commit SHA
            state: 'success', 'failure', 'pending', 'error'
            description: Status description
            context: Status context identifier
        """
        url = f"{self.base_url}/repos/{self.repo_full_name}/statuses/{commit_sha}"
        
        payload = {
            "state": state,
            "description": description,
            "context": context,
            "target_url": "https://github.com"  # Would link to analysis report
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"PR status updated: {state}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update status: {str(e)}")
            raise

    def get_pr_files(self, pr_number: int) -> List[Dict[str, Any]]:
        """Get list of files changed in PR"""
        url = f"{self.base_url}/repos/{self.repo_full_name}/pulls/{pr_number}/files"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Retrieved files for PR #{pr_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get PR files: {str(e)}")
            raise

    def get_pr_diff(self, pr_number: int) -> str:
        """Get the full diff for a PR"""
        url = f"{self.base_url}/repos/{self.repo_full_name}/pulls/{pr_number}"
        
        try:
            headers = self.headers.copy()
            headers["Accept"] = "application/vnd.github.v3.diff"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            logger.info(f"Retrieved diff for PR #{pr_number}")
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get PR diff: {str(e)}")
            raise

    def request_review(self, pr_number: int, reviewers: List[str]) -> Dict[str, Any]:
        """Request review from specific users"""
        url = f"{self.base_url}/repos/{self.repo_full_name}/pulls/{pr_number}/requested_reviewers"
        
        payload = {"reviewers": reviewers}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Requested reviews from {', '.join(reviewers)}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to request review: {str(e)}")
            raise

    def create_pr(self, title: str, body: str, head_branch: str, 
                  base_branch: str = "main", draft: bool = False) -> Dict[str, Any]:
        """Create a new pull request"""
        url = f"{self.base_url}/repos/{self.repo_full_name}/pulls"
        
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
            "draft": draft
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"PR created: {title}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create PR: {str(e)}")
            raise

    def get_repo_languages(self) -> Dict[str, int]:
        """Get primary languages in repository"""
        url = f"{self.base_url}/repos/{self.repo_full_name}/languages"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get languages: {str(e)}")
            raise

    def get_pr_details(self, pr_number: int) -> Dict[str, Any]:
        """Get detailed PR information"""
        url = f"{self.base_url}/repos/{self.repo_full_name}/pulls/{pr_number}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get PR details: {str(e)}")
            raise

    def create_check_run(self, head_sha: str, name: str, status: str, 
                    conclusion: Optional[str] = None, output: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a check run (modern alternative to commit status)
        
        Args:
            head_sha: Commit SHA
            name: Check name
            status: 'queued', 'in_progress', 'completed'
            conclusion: 'success', 'failure', 'neutral', 'cancelled', 'skipped', 'timed_out'
            output: Check output with title, summary, and annotations
        """
        url = f"{self.base_url}/repos/{self.repo_full_name}/check-runs"
        
        payload: Dict[str, Any] = {
            "name": name,
            "head_sha": head_sha,
            "status": status
        }
        
        if conclusion:
            payload["conclusion"] = conclusion
        
        if output:
            payload["output"] = output
        
        try:
            headers = self.headers.copy()
            headers["Accept"] = "application/vnd.github.v3+json"
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Check run created: {name}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create check run: {str(e)}")
            raise


class GitHubWebhookValidator:
    """Validates GitHub webhook signatures"""

    @staticmethod
    def validate_signature(payload_body: str, signature_header: str, 
                          secret: str) -> bool:
        """
        Validate GitHub webhook signature
        
        Args:
            payload_body: Raw request body
            signature_header: X-Hub-Signature-256 header
            secret: Webhook secret
        
        Returns:
            True if signature is valid
        """
        import hmac
        import hashlib
        
        # GitHub sends signature as "sha256=hexdigest"
        if not signature_header:
            return False
        
        hash_obj = hmac.new(
            secret.encode(),
            payload_body.encode(),
            hashlib.sha256
        )
        expected_signature = f"sha256={hash_obj.hexdigest()}"
        
        return hmac.compare_digest(signature_header, expected_signature)


def setup_github_integration(repo_owner: str, repo_name: str, 
                            webhook_url: str, github_token: str) -> GitHubIntegration:
    """
    Initialize GitHub integration and setup webhook
    
    Args:
        repo_owner: GitHub organization/user
        repo_name: Repository name
        webhook_url: AWS Lambda webhook endpoint
        github_token: GitHub PAT token
    
    Returns:
        Configured GitHubIntegration instance
    """
    integration = GitHubIntegration(repo_owner, repo_name, github_token)
    
    try:
        integration.setup_webhook(webhook_url)
        logger.info(f"GitHub integration ready for {repo_owner}/{repo_name}")
    except Exception as e:
        logger.error(f"Failed to setup webhook: {str(e)}")
        raise
    
    return integration
