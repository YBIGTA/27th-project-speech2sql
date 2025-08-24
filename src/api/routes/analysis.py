"""
Multi-agent analysis API routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from config.database import get_db
from src.database.models import Utterance, Meeting
from src.agents.orchestrator_agent import OrchestratorAgent
import time
import asyncio

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Analysis request model"""
    meeting_id: int
    analysis_type: Optional[str] = "comprehensive"  # comprehensive, speaker_only, agenda_only


class AnalysisResponse(BaseModel):
    """Analysis response model"""
    meeting_id: int
    analysis_type: str
    executive_summary: str
    insights: Dict[str, Any]
    comprehensive_analysis: Dict[str, Any]
    processing_time: float
    confidence: float


@router.post("/comprehensive", response_model=AnalysisResponse)
async def run_comprehensive_analysis(request: AnalysisRequest, db: Session = Depends(get_db)):
    """
    Run comprehensive multi-agent analysis on meeting data
    """
    start_time = time.perf_counter()
    
    try:
        # Fetch meeting data
        meeting = db.query(Meeting).filter(Meeting.id == request.meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Fetch utterances
        utterances = db.query(Utterance).filter(Utterance.meeting_id == request.meeting_id).all()
        if not utterances:
            raise HTTPException(status_code=404, detail="No utterances found for this meeting")
        
        # Convert to dict format for agents
        utterance_data = []
        for utterance in utterances:
            utterance_data.append({
                "id": utterance.id,
                "speaker": utterance.speaker,
                "timestamp": utterance.timestamp,
                "end_timestamp": utterance.end_timestamp,
                "text": utterance.text,
                "confidence": utterance.confidence,
                "language": utterance.language
            })
        
        # Prepare data for analysis
        analysis_data = {
            "meeting_id": request.meeting_id,
            "utterances": utterance_data
        }
        
        # Run orchestrator agent
        orchestrator = OrchestratorAgent()
        result = await orchestrator.execute(analysis_data)
        
        processing_time = round(time.perf_counter() - start_time, 4)
        
        return AnalysisResponse(
            meeting_id=request.meeting_id,
            analysis_type=request.analysis_type,
            executive_summary=result.result_data.get("executive_summary", ""),
            insights=result.result_data.get("insights", {}),
            comprehensive_analysis=result.result_data.get("comprehensive_analysis", {}),
            processing_time=processing_time,
            confidence=result.confidence_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/meeting/{meeting_id}/summary")
async def get_analysis_summary(meeting_id: int, db: Session = Depends(get_db)):
    """
    Get analysis summary for a specific meeting
    """
    try:
        # Check if meeting exists
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Check if utterances exist
        utterance_count = db.query(Utterance).filter(Utterance.meeting_id == meeting_id).count()
        if utterance_count == 0:
            raise HTTPException(status_code=404, detail="No utterances found for this meeting")
        
        # Get basic meeting stats
        speakers = db.query(Utterance.speaker).filter(Utterance.meeting_id == meeting_id).distinct().all()
        unique_speakers = len(speakers)
        
        # Get meeting duration
        first_utterance = db.query(Utterance).filter(Utterance.meeting_id == meeting_id).order_by(Utterance.timestamp).first()
        last_utterance = db.query(Utterance).filter(Utterance.meeting_id == meeting_id).order_by(Utterance.timestamp.desc()).first()
        
        duration = 0
        if first_utterance and last_utterance:
            duration = last_utterance.timestamp - first_utterance.timestamp
        
        return {
            "meeting_id": meeting_id,
            "meeting_title": meeting.title,
            "utterance_count": utterance_count,
            "unique_speakers": unique_speakers,
            "meeting_duration_minutes": round(duration / 60, 1) if duration > 0 else 0,
            "analysis_available": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/meeting/{meeting_id}/speakers")
async def get_speaker_analysis(meeting_id: int, db: Session = Depends(get_db)):
    """
    Get speaker-specific analysis for a meeting
    """
    try:
        # Fetch utterances
        utterances = db.query(Utterance).filter(Utterance.meeting_id == meeting_id).all()
        if not utterances:
            raise HTTPException(status_code=404, detail="No utterances found for this meeting")
        
        # Convert to dict format
        utterance_data = []
        for utterance in utterances:
            utterance_data.append({
                "id": utterance.id,
                "speaker": utterance.speaker,
                "timestamp": utterance.timestamp,
                "end_timestamp": utterance.end_timestamp,
                "text": utterance.text,
                "confidence": utterance.confidence,
                "language": utterance.language
            })
        
        # Run speaker analysis only
        from src.agents.speaker_analysis_agent import SpeakerAnalysisAgent
        speaker_agent = SpeakerAnalysisAgent()
        
        analysis_data = {
            "meeting_id": meeting_id,
            "utterances": utterance_data
        }
        
        result = await speaker_agent.execute(analysis_data)
        
        return {
            "meeting_id": meeting_id,
            "speaker_analysis": result.result_data,
            "confidence": result.confidence_score,
            "processing_time": result.processing_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speaker analysis failed: {str(e)}")


@router.get("/meeting/{meeting_id}/agendas")
async def get_agenda_analysis(meeting_id: int, db: Session = Depends(get_db)):
    """
    Get agenda-specific analysis for a meeting
    """
    try:
        # Fetch utterances
        utterances = db.query(Utterance).filter(Utterance.meeting_id == meeting_id).all()
        if not utterances:
            raise HTTPException(status_code=404, detail="No utterances found for this meeting")
        
        # Convert to dict format
        utterance_data = []
        for utterance in utterances:
            utterance_data.append({
                "id": utterance.id,
                "speaker": utterance.speaker,
                "timestamp": utterance.timestamp,
                "end_timestamp": utterance.end_timestamp,
                "text": utterance.text,
                "confidence": utterance.confidence,
                "language": utterance.language
            })
        
        # Run agenda analysis only
        from src.agents.agenda_analysis_agent import AgendaAnalysisAgent
        agenda_agent = AgendaAnalysisAgent()
        
        analysis_data = {
            "meeting_id": meeting_id,
            "utterances": utterance_data
        }
        
        result = await agenda_agent.execute(analysis_data)
        
        return {
            "meeting_id": meeting_id,
            "agenda_analysis": result.result_data,
            "confidence": result.confidence_score,
            "processing_time": result.processing_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agenda analysis failed: {str(e)}")


@router.get("/capabilities")
async def get_analysis_capabilities():
    """
    Get available analysis capabilities
    """
    orchestrator = OrchestratorAgent()
    
    return {
        "available_agents": [
            {
                "name": "OrchestratorAgent",
                "type": "orchestrator",
                "capabilities": orchestrator.get_capabilities(),
                "description": "조율 에이전트 - 모든 분석을 통합하고 종합 인사이트 생성"
            },
            {
                "name": "SpeakerAnalysisAgent", 
                "type": "speaker_analysis",
                "capabilities": [
                    "화자별 발화 패턴 분석",
                    "참여도 및 지배력 분석",
                    "의사소통 스타일 분석",
                    "주제별 관심도 분석",
                    "상호작용 패턴 분석"
                ],
                "description": "화자 분석 에이전트 - 개별 화자의 특성과 패턴 분석"
            },
            {
                "name": "AgendaAnalysisAgent",
                "type": "agenda_analysis", 
                "capabilities": [
                    "안건별 논의 패턴 분석",
                    "의견 및 입장 분석",
                    "결정사항 추출",
                    "합의 수준 분석",
                    "토론 품질 평가"
                ],
                "description": "안건 분석 에이전트 - 특정 안건에 대한 심도 있는 분석"
            }
        ],
        "analysis_types": [
            {
                "type": "comprehensive",
                "description": "종합 분석 - 모든 에이전트 실행 및 통합 결과 제공"
            },
            {
                "type": "speaker_only", 
                "description": "화자 분석만 - 화자별 특성 분석"
            },
            {
                "type": "agenda_only",
                "description": "안건 분석만 - 안건별 논의 패턴 분석"
            }
        ]
    } 