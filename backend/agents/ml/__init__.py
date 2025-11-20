"""
ML-Based Opportunity Detection Module (Stream H)

Machine learning models for detecting optimization opportunities and predicting task value.
"""
from backend.agents.ml.opportunity_detector import (
    OpportunityDetector,
    OptimizationOpportunity,
    ModelMetrics,
    get_opportunity_detector,
)

__all__ = [
    "OpportunityDetector",
    "OptimizationOpportunity",
    "ModelMetrics",
    "get_opportunity_detector",
]

