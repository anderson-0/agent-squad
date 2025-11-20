"""
ML-Enhanced Discovery Engine (Stream H Integration)

Integrates ML-based opportunity detection with the DiscoveryEngine.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.discovery.discovery_engine import DiscoveryEngine, WorkContext
from backend.agents.ml import OpportunityDetector, get_opportunity_detector, OptimizationOpportunity
from backend.agents.discovery.discovery_detector import Discovery
from backend.models.workflow import WorkflowPhase
from backend.core.logging import logger


class MLEnhancedDiscoveryEngine(DiscoveryEngine):
    """
    Enhanced Discovery Engine with ML-based opportunity detection.
    
    Extends DiscoveryEngine to use ML for:
    - Better opportunity detection
    - More accurate value prediction
    - Enhanced pattern recognition
    """
    
    def __init__(self):
        """Initialize ML-enhanced discovery engine"""
        super().__init__()
        self.ml_detector = get_opportunity_detector()
    
    async def analyze_work_context(
        self,
        db: AsyncSession,
        context: WorkContext,
    ) -> List[Discovery]:
        """
        Analyze work context with ML enhancement.
        
        Combines pattern-based and ML-based detection.
        """
        # Get pattern-based discoveries (from parent)
        pattern_discoveries = await super().analyze_work_context(db, context)
        
        # Get ML-based opportunities from work output
        ml_discoveries = []
        if context.work_output:
            try:
                opportunities = await self.ml_detector.detect_optimization_opportunities(
                    code_context=context.work_output,
                    execution_id=context.execution_id,
                )
                
                # Convert opportunities to discoveries
                for opp in opportunities:
                    ml_discoveries.append(Discovery(
                        type=opp.type,
                        description=opp.description,
                        value_score=opp.estimated_value,
                        suggested_phase=opp.suggested_phase,
                        confidence=opp.confidence,
                        context=opp.metadata,
                    ))
            except Exception as e:
                logger.debug(f"ML detection failed: {e}")
        
        # Combine and deduplicate
        all_discoveries = pattern_discoveries + ml_discoveries
        return self._deduplicate_discoveries(all_discoveries)
    
    async def evaluate_discovery_value(
        self,
        db: AsyncSession,
        discovery: Discovery,
        context: WorkContext,
    ) -> float:
        """
        Evaluate discovery value using ML prediction.
        """
        # Try ML-based value prediction first
        if self.ml_detector.use_ml:
            try:
                # Get similar historical tasks
                from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
                engine = PhaseBasedWorkflowEngine()
                all_tasks = await engine.get_tasks_for_execution(
                    db=db,
                    execution_id=context.execution_id,
                )
                
                # Predict value using ML
                predicted_value = await self.ml_detector.predict_task_value(
                    task_description=discovery.description,
                    historical_similar_tasks=all_tasks[:10],  # Use recent tasks
                    phase=discovery.suggested_phase,
                )
                
                # Combine with base value score
                combined_value = (discovery.value_score * 0.4) + (predicted_value * 0.6)
                return max(0.0, min(1.0, combined_value))
            except Exception as e:
                logger.debug(f"ML value prediction failed: {e}")
        
        # Fall back to parent implementation
        return await super().evaluate_discovery_value(db, discovery, context)
    
    def _deduplicate_discoveries(self, discoveries: List[Discovery]) -> List[Discovery]:
        """Remove duplicate discoveries"""
        seen = set()
        unique = []
        
        for discovery in discoveries:
            key = f"{discovery.type}:{discovery.description[:50]}"
            if key not in seen:
                seen.add(key)
                unique.append(discovery)
        
        return unique


def get_ml_enhanced_discovery_engine() -> MLEnhancedDiscoveryEngine:
    """Get ML-enhanced discovery engine instance"""
    return MLEnhancedDiscoveryEngine()

