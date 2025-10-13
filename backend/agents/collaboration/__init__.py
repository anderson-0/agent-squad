"""
Collaboration Module

Enables agents to collaborate on tasks through structured patterns:
- Problem solving: Ask questions, get answers, synthesize solutions
- Code review: Request reviews, provide feedback, iterate
- Standup: Share progress, identify blockers, coordinate work
"""
from backend.agents.collaboration.patterns import CollaborationPatternManager
from backend.agents.collaboration.problem_solving import ProblemSolvingPattern
from backend.agents.collaboration.code_review import CodeReviewPattern
from backend.agents.collaboration.standup import StandupPattern

__all__ = [
    "CollaborationPatternManager",
    "ProblemSolvingPattern",
    "CodeReviewPattern",
    "StandupPattern",
]
