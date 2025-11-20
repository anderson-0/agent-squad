"""
Discovery Detection System

Analyzes agent messages and work to detect opportunities:
- Optimization opportunities
- Bugs or issues
- Refactoring needs
- Performance improvements
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
import re

from pydantic import BaseModel

from backend.models.workflow import WorkflowPhase
from backend.schemas.agent_message import AgentMessageResponse

logger = logging.getLogger(__name__)


class Discovery(BaseModel):
    """Represents a discovery made by an agent"""
    type: str  # "optimization", "bug", "refactoring", "performance", "feature", etc.
    description: str
    value_score: float  # 0.0-1.0 (how valuable is this discovery)
    suggested_phase: WorkflowPhase
    confidence: float  # 0.0-1.0 (how confident in this discovery)
    context: Dict[str, Any]  # Additional context about the discovery


class DiscoveryDetector:
    """
    Detects discoveries in agent messages and work output.
    
    Uses pattern matching and heuristics to identify opportunities.
    Can be enhanced with LLM-based detection in the future.
    """
    
    def __init__(self):
        """Initialize discovery detector with patterns"""
        self._initialize_patterns()
    
    def _initialize_patterns(self) -> None:
        """Initialize detection patterns"""
        # Optimization patterns
        self.optimization_patterns = [
            r"could.*apply.*(?:to|for|across).*\d+.*(?:route|endpoint|function|method)",
            r"(?:speedup|performance|optimize|improve|faster).*\d+%",
            r"reduce.*(?:time|latency|memory|cpu).*\d+%",
            r"cache.*(?:could|should|can).*apply",
            r"optimization.*opportunity",
            r"could.*optimize",
            r"performance.*improvement",
        ]
        
        # Bug patterns
        self.bug_patterns = [
            r"bug.*found",
            r"error.*detected",
            r"issue.*discovered",
            r"problem.*identified",
            r"failing.*test",
            r"exception.*occurs",
            r"incorrect.*behavior",
        ]
        
        # Refactoring patterns
        self.refactoring_patterns = [
            r"refactor.*(?:would|could|should)",
            r"code.*duplication",
            r"technical.*debt",
            r"clean.*up",
            r"improve.*structure",
            r"simplify.*code",
        ]
        
        # Performance patterns
        self.performance_patterns = [
            r"slow.*performance",
            r"bottleneck.*detected",
            r"latency.*issue",
            r"memory.*leak",
            r"scalability.*concern",
            r"high.*cpu.*usage",
        ]
        
        # Feature patterns
        self.feature_patterns = [
            r"missing.*feature",
            r"would.*benefit.*from",
            r"could.*add.*feature",
            r"enhancement.*opportunity",
            r"new.*capability.*needed",
        ]
    
    def analyze_agent_message(
        self,
        message: AgentMessageResponse,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Discovery]:
        """
        Detect if message contains a discovery.
        
        Args:
            message: Agent message to analyze
            context: Optional context (execution_id, phase, etc.)
            
        Returns:
            Discovery if opportunity found, None otherwise
        """
        if not message.content:
            return None
        
        content = message.content.lower()
        
        # Check each discovery type
        discoveries = []
        
        # Optimization
        if self._matches_patterns(content, self.optimization_patterns):
            value_score = self._calculate_optimization_value(content)
            discoveries.append(Discovery(
                type="optimization",
                description=self._extract_description(content, "optimization"),
                value_score=value_score,
                suggested_phase=WorkflowPhase.INVESTIGATION,
                confidence=0.7,
                context={"source": "message", "message_id": str(message.id)},
            ))
        
        # Bug
        if self._matches_patterns(content, self.bug_patterns):
            discoveries.append(Discovery(
                type="bug",
                description=self._extract_description(content, "bug"),
                value_score=0.9,  # Bugs are high value
                suggested_phase=WorkflowPhase.INVESTIGATION,
                confidence=0.8,
                context={"source": "message", "message_id": str(message.id)},
            ))
        
        # Refactoring
        if self._matches_patterns(content, self.refactoring_patterns):
            discoveries.append(Discovery(
                type="refactoring",
                description=self._extract_description(content, "refactoring"),
                value_score=0.6,
                suggested_phase=WorkflowPhase.INVESTIGATION,
                confidence=0.7,
                context={"source": "message", "message_id": str(message.id)},
            ))
        
        # Performance
        if self._matches_patterns(content, self.performance_patterns):
            discoveries.append(Discovery(
                type="performance",
                description=self._extract_description(content, "performance"),
                value_score=0.8,
                suggested_phase=WorkflowPhase.INVESTIGATION,
                confidence=0.75,
                context={"source": "message", "message_id": str(message.id)},
            ))
        
        # Return highest value discovery
        if discoveries:
            return max(discoveries, key=lambda d: d.value_score)
        
        return None
    
    def analyze_agent_work(
        self,
        work_output: str,
        phase: WorkflowPhase,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Discovery]:
        """
        Analyze agent's work output for discoveries.
        
        Args:
            work_output: Agent's work output (code, test results, etc.)
            phase: Current workflow phase
            context: Optional context
            
        Returns:
            List of discovered opportunities
        """
        if not work_output:
            return []
        
        discoveries = []
        work_lower = work_output.lower()
        
        # Analyze work for all discovery types
        # Optimization opportunities
        if self._matches_patterns(work_lower, self.optimization_patterns):
            value_score = self._calculate_optimization_value(work_lower)
            discoveries.append(Discovery(
                type="optimization",
                description=self._extract_description(work_output, "optimization"),
                value_score=value_score,
                suggested_phase=WorkflowPhase.INVESTIGATION,
                confidence=0.7,
                context={"source": "work_output", "phase": phase.value},
            ))
        
        # Bugs found
        if self._matches_patterns(work_lower, self.bug_patterns):
            discoveries.append(Discovery(
                type="bug",
                description=self._extract_description(work_output, "bug"),
                value_score=0.9,
                suggested_phase=WorkflowPhase.INVESTIGATION,
                confidence=0.8,
                context={"source": "work_output", "phase": phase.value},
            ))
        
        return discoveries
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the patterns"""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _calculate_optimization_value(self, text: str) -> float:
        """
        Calculate value score for optimization discoveries.
        
        Higher value for:
        - Higher percentage improvements
        - More routes/endpoints affected
        - Clear performance benefits
        """
        # Extract percentage if mentioned
        percent_match = re.search(r'(\d+)%', text)
        if percent_match:
            percent = int(percent_match.group(1))
            # Normalize to 0.0-1.0 (0% = 0.0, 100% = 1.0)
            value_score = min(percent / 100.0, 1.0)
        else:
            value_score = 0.6  # Default for optimizations without percentage
        
        # Boost value if multiple routes/endpoints mentioned
        count_match = re.search(r'(\d+).*(?:route|endpoint|function|method)', text)
        if count_match:
            count = int(count_match.group(1))
            # Boost: 1 route = +0.0, 10 routes = +0.2, 20+ routes = +0.3
            boost = min(count / 50.0, 0.3)
            value_score = min(value_score + boost, 1.0)
        
        return value_score
    
    def _extract_description(self, text: str, discovery_type: str) -> str:
        """
        Extract a description of the discovery from text.
        
        For now, returns first sentence containing discovery keywords.
        Can be enhanced with LLM extraction later.
        """
        # Find sentences with discovery keywords
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in [
                discovery_type,
                "optimization", "optimize",
                "bug", "error", "issue",
                "refactor", "refactoring",
                "performance", "slow", "bottleneck",
            ]):
                # Clean up and return
                description = sentence.strip()
                if len(description) > 200:
                    description = description[:197] + "..."
                return description
        
        # Fallback: return first 100 chars
        return text[:100].strip() + ("..." if len(text) > 100 else "")


# Singleton instance
_discovery_detector: Optional[DiscoveryDetector] = None


def get_discovery_detector() -> DiscoveryDetector:
    """Get or create discovery detector instance"""
    global _discovery_detector
    if _discovery_detector is None:
        _discovery_detector = DiscoveryDetector()
    return _discovery_detector

