"""
Workflow Intelligence Module (Stream I)

AI-powered workflow recommendations and predictions.
"""
from backend.agents.intelligence.workflow_intelligence import (
    WorkflowIntelligence,
    TaskSuggestion,
    WorkflowPrediction,
    get_workflow_intelligence,
)

__all__ = [
    "WorkflowIntelligence",
    "TaskSuggestion",
    "WorkflowPrediction",
    "get_workflow_intelligence",
]

