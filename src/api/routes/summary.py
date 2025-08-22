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
from config.settings import settings

router = APIRouter()


def _generate_llm_summary(text: str, title: str, language: str = "ko", summary_type: str = "general") -> str:
    """
    Generate comprehensive summary using LLM
    
    Args:
        text: Combined text from all utterances
        title: Meeting title  
        language: Target language (ko/en)
    
    Returns:
        Generated summary
    """
    # Clean and preprocess text
    import re
    text = re.sub(r'\s+', ' ', text).strip()
    
    if len(text) < 50:
        if language == "ko":
            return f"회의 '{title}'에 대한 충분한 내용이 없어 요약을 생성할 수 없습니다."
        else:
            return f"Insufficient content to generate summary for meeting '{title}'."
    
    # Try LLM summary first
    try:
        llm_summary = _call_upstage_summarization(text, title, language, summary_type)
        if llm_summary and len(llm_summary.strip()) > 20:
            return llm_summary
    except Exception as e:
        print(f"LLM summarization failed: {e}")
    
    # Fallback to extractive summary
    return _generate_extractive_fallback(text, title, language)


def _call_upstage_summarization(text: str, title: str, language: str, summary_type: str = "general") -> str:
    """Call Upstage API for summarization"""
    if not settings.upstage_api_key:
        raise Exception("Upstage API key not configured")
    
    import requests
    
    # Prepare prompt based on language and summary type
    if language == "ko":
        if summary_type == "general":
            system_prompt = """당신은 회의록 요약 전문가입니다. 주어진 회의 내용을 분석해서 핵심적이고 구체적인 요약을 생성해주세요.

요약 규칙:
1. 실제 논의된 구체적인 내용을 포함하세요
2. 주요 주제별로 3-5개의 섹션으로 나누어 정리하세요
3. 각 섹션은 "1. [주제명]" 형태로 시작하세요
4. 불필요한 인사말이나 형식적인 내용은 제외하세요
5. 한국어로 자연스럽게 작성하세요"""
            
        elif summary_type == "meeting":
            system_prompt = """당신은 회의록 전문가입니다. 주어진 회의 내용에서 액션 아이템과 결정사항을 중심으로 요약을 생성해주세요.

요약 규칙:
1. 액션 아이템(할 일)과 결정사항을 우선적으로 추출하세요
2. 액션 아이템은 "담당자: ~, 마감일: ~, 내용: ~" 형태로 명시하세요
3. 결정사항은 "~로 결정했다", "~하기로 했다" 형태로 명확하게 표현하세요
4. 액션 아이템이나 결정사항이 없는 경우 "해당 사항이 없습니다"라고 표시하세요
5. 한국어로 자연스럽게 작성하세요"""
        
        user_prompt = f"""회의 제목: {title}

회의 내용:
{text[:3000]}  

위 회의 내용을 바탕으로 요약을 작성해주세요."""
    else:
        if summary_type == "general":
            system_prompt = """You are a meeting summary expert. Analyze the given meeting content and generate a comprehensive and specific summary.

Summary rules:
1. Include specific content that was actually discussed
2. Organize into 3-5 sections by main topics
3. Start each section with "1. [Topic Name]" format
4. Exclude unnecessary greetings or formal content
5. Write naturally in English"""
            
        elif summary_type == "meeting":
            system_prompt = """You are a meeting expert. Generate a summary focused on action items and decisions from the given meeting content.

Summary rules:
1. Prioritize action items (tasks to be done) and decisions made
2. For action items, specify "Assignee: ~, Due Date: ~, Content: ~"
3. For decisions, use clear expressions like "decided to", "agreed to"
4. If no action items or decisions, state "No relevant items found"
5. Write naturally in English"""
        
        user_prompt = f"""Meeting Title: {title}

Meeting Content:
{text[:3000]}

Based on the above meeting content, please write a summary."""
    
    try:
        # Call Upstage Chat API
        headers = {
            "Authorization": f"Bearer {settings.upstage_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "solar-1-mini-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        response = requests.post(
            f"{settings.upstage_base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result["choices"][0]["message"]["content"].strip()
            print(f"LLM summary generated: {len(summary)} characters")
            return summary
        else:
            print(f"Upstage API error: {response.status_code} {response.text}")
            raise Exception(f"API call failed: {response.status_code}")
            
    except Exception as e:
        print(f"Upstage API call failed: {e}")
        raise e


def _generate_extractive_fallback(text: str, title: str, language: str) -> str:
    """Fallback extractive summary when LLM fails"""
    import re
    sentences = re.split(r'[.!?]\s*', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    if len(sentences) < 3:
        if language == "ko":
            return f"회의 '{title}'의 내용을 요약하기에 충분한 문장이 없습니다."
        else:
            return f"Insufficient sentences to summarize meeting '{title}'."
    
    # Extract key sentences (simplified)
    import random
    key_sentences = sentences[:5] if len(sentences) >= 5 else sentences
    
    if language == "ko":
        summary_parts = [
            "이 회의에서 논의된 주요 내용:",
            ""
        ]
        for i, sentence in enumerate(key_sentences, 1):
            summary_parts.append(f"{i}. {sentence}")
        return "\n".join(summary_parts)
    else:
        summary_parts = [
            "Main topics discussed in this meeting:",
            ""
        ]
        for i, sentence in enumerate(key_sentences, 1):
            summary_parts.append(f"{i}. {sentence}")
        return "\n".join(summary_parts)





class SummaryRequest(BaseModel):
    """Summary generation request model"""
    meeting_id: int
    summary_type: str = "general"  # general, meeting
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
    
    # Generate actual summary from utterances
    from src.database.operations import UtteranceOperations
    
    # Get utterances for this meeting
    utterances = UtteranceOperations.get_utterances_by_meeting(db, request.meeting_id)
    
    # Create a comprehensive summary from utterances
    if utterances:
        # Combine all utterances into a text corpus
        all_text = []
        speakers = set()
        for utterance in utterances:
            all_text.append(utterance.text)
            speakers.add(utterance.speaker)
        
        combined_text = " ".join(all_text)
        
        # Generate content-based summary using LLM with type-specific prompts
        generated_summary = _generate_llm_summary(
            combined_text, 
            meeting.title, 
            request.language,
            request.summary_type
        )
        
    else:
        generated_summary = f"회의 '{meeting.title}'의 음성 인식 결과를 바탕으로 요약을 생성할 수 없습니다."
    
    # Update meeting with generated summary and type
    MeetingOperations.update_meeting(
        db=db,
        meeting_id=request.meeting_id,
        summary=generated_summary,
        summary_type=request.summary_type
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
        summary_text=generated_summary,
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
async def generate_pdf_summary(meeting_id: int, db: Session = Depends(get_db)):
    """
    Generate PDF summary for meeting
    
    Args:
        meeting_id: Meeting identifier
    
    Returns:
        PDF file response
    """
    from src.utils.pdf_generator import generate_meeting_pdf
    from src.database.operations import UtteranceOperations
    
    # Check if meeting exists
    meeting = MeetingOperations.get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get meeting data
    meeting_data = {
        "id": meeting.id,
        "title": meeting.title,
        "date": meeting.date.isoformat() if meeting.date else "",
        "duration": meeting.duration or 0,
        "participants": meeting.participants or [],
        "summary": meeting.summary or "요약이 아직 생성되지 않았습니다."
    }
    
    # Get utterances for this meeting
    utterances_data = []
    try:
        utterances = UtteranceOperations.get_utterances_by_meeting(db, meeting_id)
        utterances_data = [
            {
                "speaker": u.speaker,
                "timestamp": u.timestamp,
                "text": u.text,
                "confidence": u.confidence
            }
            for u in utterances
        ]
    except Exception as e:
        print(f"Error fetching utterances: {e}")
        # Continue without utterances
    
    # Get actions for this meeting
    actions = ActionOperations.get_actions_by_meeting(db, meeting_id)
    actions_data = [
        {
            "id": action.id,
            "action_type": action.action_type,
            "description": action.description,
            "assignee": action.assignee,
            "due_date": action.due_date.isoformat() if action.due_date else None,
            "status": action.status,
            "priority": action.priority
        }
        for action in actions
    ]
    
    try:
        # Generate PDF with saved summary type
        pdf_path = generate_meeting_pdf(meeting_data, utterances_data, actions_data, meeting.summary_type or "general")
        
        return {
            "message": "PDF generation completed",
            "meeting_id": meeting_id,
            "status": "completed",
            "pdf_path": pdf_path,
            "download_url": f"/api/v1/summary/pdf/{meeting_id}/download"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/pdf/{meeting_id}/download")
async def download_pdf_summary(meeting_id: int, db: Session = Depends(get_db)):
    """
    Download PDF summary
    
    Args:
        meeting_id: Meeting identifier
    
    Returns:
        PDF file
    """
    import glob
    import os
    
    # Check if meeting exists
    meeting = MeetingOperations.get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Look for existing PDF files for this meeting
    temp_dir = os.path.join("temp", "summaries")
    pattern = os.path.join(temp_dir, f"meeting_summary_{meeting_id}_*.pdf")
    pdf_files = glob.glob(pattern)
    
    if not pdf_files:
        # Generate PDF if it doesn't exist
        try:
            from src.utils.pdf_generator import generate_meeting_pdf
            from src.database.operations import UtteranceOperations
            
            # Get meeting data
            meeting_data = {
                "id": meeting.id,
                "title": meeting.title,
                "date": meeting.date.isoformat() if meeting.date else "",
                "duration": meeting.duration or 0,
                "participants": meeting.participants or [],
                "summary": meeting.summary or "요약이 아직 생성되지 않았습니다."
            }
            
            # Get utterances and actions
            utterances_data = []
            try:
                utterances = UtteranceOperations.get_utterances_by_meeting(db, meeting_id)
                utterances_data = [
                    {
                        "speaker": u.speaker,
                        "timestamp": u.timestamp,
                        "text": u.text,
                        "confidence": u.confidence
                    }
                    for u in utterances
                ]
            except Exception:
                pass
            
            actions = ActionOperations.get_actions_by_meeting(db, meeting_id)
            actions_data = [
                {
                    "id": action.id,
                    "action_type": action.action_type,
                    "description": action.description,
                    "assignee": action.assignee,
                    "due_date": action.due_date.isoformat() if action.due_date else None,
                    "status": action.status,
                    "priority": action.priority
                }
                for action in actions
            ]
            
            file_path = generate_meeting_pdf(meeting_data, utterances_data, actions_data, meeting.summary_type or "general")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    else:
        # Use the most recent PDF file
        file_path = max(pdf_files, key=os.path.getctime)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
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