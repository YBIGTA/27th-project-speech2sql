"""
Audio processing API routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from sqlalchemy.orm import Session
import os
from datetime import datetime
from config.settings import settings
from config.database import get_db
from src.database.operations import MeetingOperations

router = APIRouter()


@router.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    title: str = None,
    participants: List[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload audio file for processing
    
    Args:
        file: Audio file (wav, mp3, m4a)
        title: Meeting title
        participants: List of participant names
    
    Returns:
        Upload response with file info
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.wav', '.mp3', '.m4a']:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Supported: {settings.supported_audio_formats}"
        )
    
    # Validate file size
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.max_audio_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.max_audio_size}"
        )
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.audio_upload_path, filename)
    
    os.makedirs(settings.audio_upload_path, exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create meeting in database
    try:
        meeting = MeetingOperations.create_meeting(
            db=db,
            title=title or f"Meeting {timestamp}",
            participants=participants or [],
            audio_path=file_path
        )
        
        # TODO: Process audio with Whisper STT and Speaker Diarization
        # This will be implemented by 팀원 A
        
        return JSONResponse({
            "message": "Audio file uploaded successfully",
            "meeting_id": meeting.id,
            "filename": filename,
            "file_path": file_path,
            "file_size": file_size,
            "title": meeting.title,
            "participants": meeting.participants,
            "status": "uploaded",
            "created_at": meeting.created_at.isoformat()
        })
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/status/{filename}")
async def get_processing_status(filename: str, db: Session = Depends(get_db)):
    """
    Get audio processing status
    
    Args:
        filename: Audio filename
    
    Returns:
        Processing status
    """
    meeting = MeetingOperations.get_meeting_by_filename(db, filename)
    if not meeting:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if audio file exists
    audio_exists = os.path.exists(meeting.audio_path) if meeting.audio_path else False
    
    # Simple status logic (can be enhanced later)
    if meeting.summary:
        status = "completed"
        progress = 1.0
        message = "Audio processing completed"
        stt_completed = True
        diarization_completed = True
        summary_completed = True
    elif audio_exists:
        status = "processing"
        progress = 0.5
        message = "Audio processing in progress"
        stt_completed = True
        diarization_completed = False
        summary_completed = False
    else:
        status = "failed"
        progress = 0.0
        message = "Audio file not found"
        stt_completed = False
        diarization_completed = False
        summary_completed = False
    
    return {
        "filename": filename,
        "status": status,
        "progress": progress,
        "stt_completed": stt_completed,
        "diarization_completed": diarization_completed,
        "summary_completed": summary_completed,
        "estimated_completion": meeting.updated_at.isoformat() if meeting.updated_at else None,
        "message": message
    }


@router.get("/files")
async def list_audio_files(
    skip: int = 0,
    limit: int = 100,
    title_search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all uploaded audio files
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        title_search: Optional title search filter
    
    Returns:
        List of audio files
    """
    meetings = MeetingOperations.get_meetings(
        db=db,
        skip=skip,
        limit=limit,
        title_search=title_search
    )
    
    files = []
    for meeting in meetings:
        # Check if audio file exists
        audio_exists = os.path.exists(meeting.audio_path) if meeting.audio_path else False
        filename = os.path.basename(meeting.audio_path) if meeting.audio_path else None
        
        if filename:  # Only include meetings with audio files
            files.append({
                "filename": filename,
                "title": meeting.title,
                "upload_date": meeting.created_at.isoformat(),
                "status": "completed" if meeting.summary else "processing",
                "duration": meeting.duration,
                "participants": meeting.participants
            })
    
    return {
        "files": files,
        "total": len(files),
        "skip": skip,
        "limit": limit
    }


@router.delete("/{filename}")
async def delete_audio_file(filename: str, db: Session = Depends(get_db)):
    """
    Delete audio file and meeting
    
    Args:
        filename: Audio filename
    
    Returns:
        Deletion confirmation
    """
    meeting = MeetingOperations.get_meeting_by_filename(db, filename)
    if not meeting:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete physical audio file if exists
    if meeting.audio_path and os.path.exists(meeting.audio_path):
        try:
            os.remove(meeting.audio_path)
        except OSError as e:
            # Log warning but continue with database deletion
            print(f"Warning: Could not delete audio file {meeting.audio_path}: {e}")
    
    # Delete from database using filename
    deleted_meeting = MeetingOperations.delete_meeting_by_filename(db, filename)
    if not deleted_meeting:
        raise HTTPException(status_code=500, detail="Failed to delete meeting from database")
    
    return {
        "message": "Audio file deleted successfully",
        "filename": filename
    } 