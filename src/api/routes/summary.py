"""
Summary generation API routes
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from config.database import get_db
from src.database.operations import MeetingOperations, ActionOperations, AnalyticsOperations

router = APIRouter()


class SummaryRequest(BaseModel):
    """Summary generation request model"""
    meeting_id: int
    summary_type: str = "general"  # general, action_items, decisions
    language: str = "ko"


class SummaryResponse(BaseModel):
    """Summary response model"""
    meeting_id: int
    summary_type: str
    summary_text: str
    key_points: List[str]
    action_items: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]
    generated_at: str


@router.post("/generate", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest, db: Session = Depends(get_db)):
    """
    Generate meeting summary
    
    Args:
        request: Summary generation request
    
    Returns:
        Generated summary
    """
    # Check if meeting exists
    meeting = MeetingOperations.get_meeting(db, request.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get existing actions for this meeting
    actions = ActionOperations.get_actions_by_meeting(db, request.meeting_id)
    
    # TODO: Implement actual summary generation with LLM
    # This will be implemented by 팀원 B
    # For now, update meeting with mock summary
    
    mock_summary = f"회의 '{meeting.title}'에서 논의된 주요 내용을 요약합니다."
    
    # Update meeting with generated summary
    MeetingOperations.update_meeting(
        db=db,
        meeting_id=request.meeting_id,
        summary=mock_summary
    )
    
    # Format action items
    action_items = [
        {
            "id": action.id,
            "description": action.description,
            "assignee": action.assignee,
            "due_date": action.due_date.isoformat() if action.due_date else None,
            "status": action.status,
            "priority": action.priority
        }
        for action in actions if action.action_type == "assignment"
    ]
    
    # Format decisions
    decisions = [
        {
            "id": action.id,
            "topic": action.description,
            "decision": action.description,
            "decided_at": action.created_at.isoformat()
        }
        for action in actions if action.action_type == "decision"
    ]
    
    return SummaryResponse(
        meeting_id=request.meeting_id,
        summary_type=request.summary_type,
        summary_text=mock_summary,
        key_points=[
            f"회의 제목: {meeting.title}",
            f"참가자: {', '.join(meeting.participants) if meeting.participants else '미정'}",
            f"액션 아이템: {len(action_items)}개",
            f"결정사항: {len(decisions)}개"
        ],
        action_items=action_items,
        decisions=decisions,
        generated_at=datetime.utcnow().isoformat()
    )


@router.get("/meeting/{meeting_id}")
async def get_meeting_summary(meeting_id: int, db: Session = Depends(get_db)):
    """
    Get existing meeting summary
    
    Args:
        meeting_id: Meeting identifier
    
    Returns:
        Meeting summary
    """
    meeting = MeetingOperations.get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get actions for this meeting
    actions = ActionOperations.get_actions_by_meeting(db, meeting_id)
    
    return {
        "meeting_id": meeting.id,
        "title": meeting.title,
        "date": meeting.date.isoformat(),
        "duration": meeting.duration,
        "participants": meeting.participants,
        "summary": meeting.summary or "요약이 아직 생성되지 않았습니다.",
        "action_count": len([a for a in actions if a.action_type == "assignment"]),
        "decision_count": len([a for a in actions if a.action_type == "decision"]),
        "status": "completed" if meeting.summary else "pending"
    }


@router.post("/pdf/{meeting_id}")
async def generate_pdf_summary(meeting_id: int):
    """
    Generate PDF summary for meeting
    
    Args:
        meeting_id: Meeting identifier
    
    Returns:
        PDF file response
    """
    # TODO: Implement PDF generation
    # This will be implemented by 팀원 D
    
    # Mock response
    return {
        "message": "PDF generation started",
        "meeting_id": meeting_id,
        "status": "processing"
    }


@router.get("/pdf/{meeting_id}/download")
async def download_pdf_summary(meeting_id: int):
    """
    Download PDF summary
    
    Args:
        meeting_id: Meeting identifier
    
    Returns:
        PDF file
    """
    # TODO: Implement PDF download
    # Mock file path
    file_path = f"temp/summary_{meeting_id}.pdf"
    
    return FileResponse(
        path=file_path,
        filename=f"meeting_summary_{meeting_id}.pdf",
        media_type="application/pdf"
    )


@router.get("/analytics")
async def get_summary_analytics(db: Session = Depends(get_db)):
    """
    Get summary generation analytics
    
    Returns:
        Analytics data
    """
    stats = AnalyticsOperations.get_meeting_statistics(db)
    
    # Count meetings with summaries
    meetings_with_summaries = len([
        m for m in MeetingOperations.get_meetings(db, limit=1000) 
        if m.summary
    ])
    
    return {
        "total_meetings": stats["total_meetings"],
        "total_summaries": meetings_with_summaries,
        "total_actions": stats["total_actions"],
        "average_duration_minutes": stats["average_duration_minutes"],
        "summary_completion_rate": round(
            meetings_with_summaries / max(stats["total_meetings"], 1) * 100, 2
        ),
        "monthly_meetings": stats["monthly_meetings"]
    } 