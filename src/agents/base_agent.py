"""
Base Agent class for all analysis agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent types enumeration"""
    SPEAKER_ANALYSIS = "speaker_analysis"
    AGENDA_ANALYSIS = "agenda_analysis"
    EMOTION_ANALYSIS = "emotion_analysis"
    LOGIC_ANALYSIS = "logic_analysis"
    EXPERTISE_ANALYSIS = "expertise_analysis"
    ORCHESTRATOR = "orchestrator"


@dataclass
class AgentResult:
    """Standard result format for all agents"""
    agent_type: AgentType
    meeting_id: int
    result_data: Dict[str, Any]
    confidence_score: float
    processing_time: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """Base class for all analysis agents"""
    
    def __init__(self, agent_type: AgentType, name: str):
        self.agent_type = agent_type
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
        
    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> AgentResult:
        """Main analysis method to be implemented by each agent"""
        pass
    
    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data format"""
        pass
    
    def preprocess(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess input data (can be overridden)"""
        return data
    
    def postprocess(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess result data (can be overridden)"""
        return result
    
    async def execute(self, data: Dict[str, Any]) -> AgentResult:
        """Execute the complete analysis pipeline"""
        start_time = datetime.now()
        
        try:
            # Validate input
            if not self.validate_input(data):
                raise ValueError(f"Invalid input data for agent {self.name}")
            
            # Preprocess
            processed_data = self.preprocess(data)
            
            # Analyze
            result_data = await self.analyze(processed_data)
            
            # Postprocess
            final_result = self.postprocess(result_data)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResult(
                agent_type=self.agent_type,
                meeting_id=data.get("meeting_id"),
                result_data=final_result,
                confidence_score=final_result.get("confidence", 0.0),
                processing_time=processing_time,
                timestamp=datetime.now(),
                metadata={"agent_name": self.name}
            )
            
        except Exception as e:
            self.logger.error(f"Error in agent {self.name}: {e}")
            raise
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return []
    
    def get_requirements(self) -> List[str]:
        """Return list of required input fields"""
        return [] 