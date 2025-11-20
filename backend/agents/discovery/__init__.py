"""
Discovery Detection Module

Detects opportunities in agent messages and work output.
"""
from backend.agents.discovery.discovery_detector import (
    Discovery,
    DiscoveryDetector,
    get_discovery_detector,
)
from backend.agents.discovery.discovery_engine import (
    DiscoveryEngine,
    TaskSuggestion,
    WorkContext,
    get_discovery_engine,
)

__all__ = [
    "Discovery",
    "DiscoveryDetector",
    "get_discovery_detector",
    "DiscoveryEngine",
    "TaskSuggestion",
    "WorkContext",
    "get_discovery_engine",
]

