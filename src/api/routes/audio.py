"""
Audio processing API routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
from datetime import datetime
from config.settings import settings
from config.database import get_db
from sqlalchemy.orm import Session
from src.database.models import Meeting, Utterance
from src.audio.whisper_stt import transcribe_audio

router = APIRouter()


def _parse_max_size(size_str: str) -> int:
    s = size_str.strip().upper()
    if s.endswith("MB"):
        return int(float(s[:-2]) * 1024 * 1024)
    if s.endswith("KB"):
        return int(float(s[:-2]) * 1024)
    if s.endswith("GB"):
        return int(float(s[:-2]) * 1024 * 1024 * 1024)
    return int(s)


@router.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    participants: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Upload audio file, run STT, and store results in DB
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.wav', '.mp3', '.m4a']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {settings.supported_formats}"
        )

    # Validate file size
    content = await file.read()
    file_size = len(content)
    max_size_bytes = _parse_max_size(settings.max_audio_size)

    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.max_audio_size}"
        )

    # Save file
    os.makedirs(settings.audio_upload_path, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.audio_upload_path, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Get or create Meeting
    meeting_title = title or os.path.splitext(file.filename)[0]
    meeting = db.query(Meeting).filter(Meeting.title == meeting_title).first()
    if not meeting:
        meeting = Meeting(
            title=meeting_title,
            participants=participants or [],
            summary="",
            audio_path=file_path,
        )
        db.add(meeting)
        db.flush()

    # Run Whisper STT (single speaker initial baseline)
    try:
        stt = transcribe_audio(file_path, model_name=settings.whisper_model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")

    # Store utterances
    inserted = 0
    for seg in stt.get("segments", []):
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start_ts = float(seg.get("start", 0.0))
        end_ts = float(seg.get("end", 0.0)) if seg.get("end") is not None else None

        # skip if exists
        exists = (
            db.query(Utterance.id)
            .filter(Utterance.meeting_id == meeting.id)
            .filter(Utterance.timestamp == start_ts)
            .filter(Utterance.text == text)
            .first()
        )
        if exists:
            continue

        utt = Utterance(
            meeting_id=meeting.id,
            speaker="SPEAKER_1",
            timestamp=start_ts,
            end_timestamp=end_ts,
            text=text,
            language=stt.get("language") or "ko",
        )
        db.add(utt)
        inserted += 1

    db.commit()

    return JSONResponse({
        "message": "Audio processed and stored successfully",
        "filename": filename,
        "file_path": file_path,
        "file_size": file_size,
        "title": meeting_title,
        "participants": participants or [],
        "segments": inserted,
        "status": "processed"
    })


@router.get("/status/{file_id}")
async def get_processing_status(file_id: str):
    return {
        "file_id": file_id,
        "status": "processing",
        "progress": 1.0,
        "message": "Processing completed (baseline)"
    }


@router.get("/files")
async def list_audio_files():
    return {"files": [], "total": 0}


@router.delete("/files/{file_id}")
async def delete_audio_file(file_id: str):
    return {"message": f"File {file_id} deleted successfully", "file_id": file_id} 