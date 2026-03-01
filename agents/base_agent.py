"""
Base Agent Framework for SDLC Automation
Provides the foundation for all specialized agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentAction:
    """Represents an action the agent performs"""
    action_type: str
    description: str
    payload: Dict[str, Any]
    timestamp: datetime


@dataclass
class AgentResult:
    """Result of agent execution"""
    success: bool
    message: str
    actions: List[AgentAction]
    data: Dict[str, Any]
    errors: List[str]
    duration_seconds: float


class BaseAgent(ABC):
    """Abstract base class for all SDLC agents"""

    def __init__(self, agent_name: str, aws_region: str = "us-east-1"):
        self.agent_name = agent_name
        self.aws_region = aws_region
        self.actions: List[AgentAction] = []
        self.logger = logging.getLogger(agent_name)

    @abstractmethod
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the provided context and return findings"""
        pass

    @abstractmethod
    def recommend_actions(self, analysis: Dict[str, Any]) -> List[AgentAction]:
        """Based on analysis, recommend actions to take"""
        pass

    @abstractmethod
    def execute(self, actions: List[AgentAction]) -> AgentResult:
        """Execute the recommended actions"""
        pass

    def run(self, context: Dict[str, Any]) -> AgentResult:
        """Execute full agent workflow"""
        start_time = datetime.now()
        try:
            self.logger.info(f"[{self.agent_name}] Starting analysis...")
            
            # Step 1: Analyze
            analysis = self.analyze(context)
            
            # Step 2: Recommend
            self.actions = self.recommend_actions(analysis)
            
            # Step 3: Execute
            result = self.execute(self.actions)
            
            duration = (datetime.now() - start_time).total_seconds()
            result.duration_seconds = duration
            
            self.logger.info(
                f"[{self.agent_name}] Completed in {duration:.2f}s. "
                f"Actions: {len(self.actions)}, Success: {result.success}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"[{self.agent_name}] Error: {str(e)}", exc_info=True)
            duration = (datetime.now() - start_time).total_seconds()
            return AgentResult(
                success=False,
                message=f"Agent execution failed: {str(e)}",
                actions=self.actions,
                data={},
                errors=[str(e)],
                duration_seconds=duration
            )

    def log_action(self, action: AgentAction):
        """Log and track an action"""
        self.actions.append(action)
        self.logger.info(
            f"[{self.agent_name}] Action: {action.action_type} - {action.description}"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent state to dictionary"""
        return {
            "agent_name": self.agent_name,
            "aws_region": self.aws_region,
            "actions_count": len(self.actions),
            "actions": [
                {
                    "type": a.action_type,
                    "description": a.description,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in self.actions
            ]
        }
