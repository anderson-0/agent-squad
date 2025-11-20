"""
Branching Module (Stream E)

Workflow branching system for discovery-driven parallel tracks.
"""
from backend.agents.branching.branching_engine import (
    BranchingEngine,
    get_branching_engine,
)

__all__ = [
    "BranchingEngine",
    "get_branching_engine",
]

