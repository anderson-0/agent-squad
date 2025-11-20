"""
ML-Based Opportunity Detector (Stream H)

Uses machine learning to detect optimization opportunities and predict task value.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from backend.models.workflow import WorkflowPhase, DynamicTask
from backend.models.project import TaskExecution
from backend.agents.discovery.discovery_detector import Discovery, get_discovery_detector
from backend.core.logging import logger

# Try to import ML libraries (optional dependencies)
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. ML features will use pattern matching fallback.")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not available. Some ML features may be limited.")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Classification will use pattern matching fallback.")


class OptimizationOpportunity(BaseModel):
    """
    Detected optimization opportunity.
    """
    type: str  # "optimization", "bug", "refactoring", "performance", etc.
    description: str
    code_context: Optional[str] = None
    confidence: float  # 0.0-1.0
    estimated_value: float  # 0.0-1.0
    suggested_phase: WorkflowPhase
    metadata: Dict[str, Any] = {}


class ModelMetrics(BaseModel):
    """Metrics from model training"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    validation_samples: int
    trained_at: datetime


class OpportunityDetector:
    """
    ML-powered opportunity and issue detection.
    
    Uses embeddings and classification to detect:
    - Optimization opportunities
    - Performance issues
    - Code quality improvements
    - Refactoring needs
    
    Falls back to pattern matching if ML libraries are unavailable.
    """
    
    def __init__(self, use_ml: bool = True):
        """
        Initialize opportunity detector.
        
        Args:
            use_ml: Whether to use ML models (True) or pattern matching (False)
        """
        self.use_ml = use_ml and (OPENAI_AVAILABLE or SKLEARN_AVAILABLE)
        self.discovery_detector = get_discovery_detector()
        
        # ML components (initialized lazily)
        self._embedding_client: Optional[Any] = None
        self._classifier: Optional[Any] = None
        self._vectorizer: Optional[Any] = None
        
        # In-memory model storage (for simple models)
        self._simple_classifier = None
        self._training_data: List[Dict[str, Any]] = []
    
    async def detect_optimization_opportunities(
        self,
        code_context: str,
        performance_metrics: Optional[Dict[str, float]] = None,
        execution_id: Optional[UUID] = None,
    ) -> List[OptimizationOpportunity]:
        """
        Detect optimization opportunities using ML.
        
        Args:
            code_context: Code or context to analyze
            performance_metrics: Optional performance metrics
            execution_id: Optional execution ID for context
            
        Returns:
            List of detected optimization opportunities
        """
        opportunities = []
        
        if self.use_ml:
            # Use ML-based detection
            try:
                ml_opportunities = await self._detect_with_ml(
                    code_context=code_context,
                    performance_metrics=performance_metrics,
                )
                opportunities.extend(ml_opportunities)
            except Exception as e:
                logger.warning(f"ML detection failed, falling back to pattern matching: {e}")
                # Fall back to pattern matching
                opportunities.extend(
                    self._detect_with_patterns(code_context=code_context)
                )
        else:
            # Use pattern matching
            opportunities.extend(
                self._detect_with_patterns(code_context=code_context)
            )
        
        # Filter by confidence and value
        filtered = [
            opp for opp in opportunities
            if opp.confidence >= 0.5 and opp.estimated_value >= 0.5
        ]
        
        # Sort by estimated value
        filtered.sort(key=lambda x: x.estimated_value, reverse=True)
        
        return filtered
    
    async def predict_task_value(
        self,
        task_description: str,
        historical_similar_tasks: Optional[List[DynamicTask]] = None,
        phase: Optional[WorkflowPhase] = None,
    ) -> float:
        """
        Predict value of a potential task.
        
        Args:
            task_description: Description of the task
            historical_similar_tasks: Optional similar tasks for comparison
            phase: Optional workflow phase
            
        Returns:
            Predicted value (0.0-1.0)
        """
        base_value = 0.5  # Default value
        
        if self.use_ml and historical_similar_tasks:
            # Use ML to predict based on historical data
            try:
                predicted_value = await self._predict_value_with_ml(
                    task_description=task_description,
                    historical_tasks=historical_similar_tasks,
                )
                return max(0.0, min(1.0, predicted_value))
            except Exception as e:
                logger.debug(f"ML value prediction failed: {e}")
        
        # Pattern-based heuristics
        value_factors = []
        
        # High-value keywords
        high_value_keywords = [
            "optimize", "improve", "refactor", "fix", "resolve",
            "enhance", "performance", "efficiency", "bug", "critical",
        ]
        value_factors.append(
            0.2 if any(keyword in task_description.lower() for keyword in high_value_keywords)
            else 0.1
        )
        
        # Description length (longer descriptions often indicate more thought)
        description_length_factor = min(len(task_description) / 200.0, 0.3)
        value_factors.append(description_length_factor)
        
        # Phase-based adjustments
        if phase == WorkflowPhase.VALIDATION:
            value_factors.append(0.2)  # Validation tasks are often high value
        
        predicted_value = sum(value_factors)
        return max(0.0, min(1.0, predicted_value))
    
    async def train_model(
        self,
        historical_data: List[Dict[str, Any]],
        validation_split: float = 0.2,
    ) -> ModelMetrics:
        """
        Train model on historical data.
        
        Args:
            historical_data: List of historical task/discovery data
            validation_split: Fraction of data to use for validation
            
        Returns:
            ModelMetrics with training results
        """
        if not SKLEARN_AVAILABLE:
            raise ValueError("scikit-learn is required for model training")
        
        if len(historical_data) < 10:
            raise ValueError("Need at least 10 training samples")
        
        # Prepare training data
        X = [item.get("text", "") for item in historical_data]
        y = [item.get("label", "other") for item in historical_data]
        
        # Simple text classification pipeline
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.pipeline import Pipeline
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        # Train simple classifier
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=1000)),
            ("classifier", MultinomialNB()),
        ])
        
        pipeline.fit(X_train, y_train)
        
        # Evaluate
        y_pred = pipeline.predict(X_val)
        
        accuracy = accuracy_score(y_val, y_pred)
        precision = precision_score(y_val, y_pred, average="weighted", zero_division=0)
        recall = recall_score(y_val, y_pred, average="weighted", zero_division=0)
        f1 = f1_score(y_val, y_pred, average="weighted", zero_division=0)
        
        # Store model
        self._simple_classifier = pipeline
        self._training_data = historical_data
        
        return ModelMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            training_samples=len(X_train),
            validation_samples=len(X_val),
            trained_at=datetime.utcnow(),
        )
    
    # Private helper methods
    
    async def _detect_with_ml(
        self,
        code_context: str,
        performance_metrics: Optional[Dict[str, float]] = None,
    ) -> List[OptimizationOpportunity]:
        """Use ML to detect opportunities"""
        opportunities = []
        
        # Simple heuristic-based detection for now
        # In production, this would use trained models
        
        # Check for performance patterns
        if "slow" in code_context.lower() or "bottleneck" in code_context.lower():
            opportunities.append(OptimizationOpportunity(
                type="performance",
                description="Potential performance issue detected",
                code_context=code_context[:500],  # First 500 chars
                confidence=0.7,
                estimated_value=0.8,
                suggested_phase=WorkflowPhase.INVESTIGATION,
                metadata={"pattern": "performance_keyword"},
            ))
        
        # Check for code quality patterns
        if "duplicate" in code_context.lower() or "repeated" in code_context.lower():
            opportunities.append(OptimizationOpportunity(
                type="refactoring",
                description="Code duplication detected",
                code_context=code_context[:500],
                confidence=0.6,
                estimated_value=0.7,
                suggested_phase=WorkflowPhase.BUILDING,
                metadata={"pattern": "duplication_keyword"},
            ))
        
        return opportunities
    
    def _detect_with_patterns(
        self,
        code_context: str,
    ) -> List[OptimizationOpportunity]:
        """Use pattern matching to detect opportunities"""
        opportunities = []
        
        # Simple pattern-based detection (doesn't require message)
        # Check for common optimization keywords
        optimization_keywords = {
            "optimization": ["slow", "bottleneck", "performance", "optimize", "speed up"],
            "refactoring": ["duplicate", "repeated", "refactor", "clean up"],
            "bug": ["bug", "error", "fix", "issue", "problem"],
            "performance": ["slow", "latency", "timeout", "heavy"],
        }
        
        code_lower = code_context.lower()
        
        for opp_type, keywords in optimization_keywords.items():
            if any(keyword in code_lower for keyword in keywords):
                # Determine phase based on type
                if opp_type == "optimization":
                    phase = WorkflowPhase.INVESTIGATION
                elif opp_type == "bug":
                    phase = WorkflowPhase.VALIDATION
                else:
                    phase = WorkflowPhase.BUILDING
                
                opportunities.append(OptimizationOpportunity(
                    type=opp_type,
                    description=f"{opp_type.title()} opportunity detected in code context",
                    code_context=code_context[:500],
                    confidence=0.6,
                    estimated_value=0.7,
                    suggested_phase=phase,
                    metadata={"detection_method": "pattern_matching"},
                ))
        
        return opportunities
    
    async def _predict_value_with_ml(
        self,
        task_description: str,
        historical_tasks: List[DynamicTask],
    ) -> float:
        """Use ML to predict task value"""
        # Simple heuristic: average value of similar tasks
        if not historical_tasks:
            return 0.5
        
        # Count completed tasks (completed = high value)
        completed_count = sum(1 for t in historical_tasks if t.status == "completed")
        completion_rate = completed_count / len(historical_tasks) if historical_tasks else 0
        
        # Base value on completion rate
        predicted_value = 0.3 + (completion_rate * 0.5)
        
        return predicted_value
    
    def _initialize_embedding_client(self):
        """Initialize embedding client (lazy)"""
        if self._embedding_client is None and OPENAI_AVAILABLE:
            from backend.core.config import settings
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                self._embedding_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            else:
                logger.warning("OpenAI API key not configured")
    
    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text"""
        self._initialize_embedding_client()
        
        if not self._embedding_client:
            return None
        
        try:
            response = await self._embedding_client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000],  # Limit length
            )
            return response.data[0].embedding
        except Exception as e:
            logger.debug(f"Embedding generation failed: {e}")
            return None


# Singleton instance
_opportunity_detector_instance: Optional[OpportunityDetector] = None


def get_opportunity_detector() -> OpportunityDetector:
    """Get singleton OpportunityDetector instance"""
    global _opportunity_detector_instance
    if _opportunity_detector_instance is None:
        _opportunity_detector_instance = OpportunityDetector()
    return _opportunity_detector_instance

