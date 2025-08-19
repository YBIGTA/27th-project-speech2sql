"""
Speaker diarization wrapper
- If pyannote.audio is available and HUGGINGFACE_TOKEN is set: real diarization
- Else: fallback to single speaker
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

def diarize_segments_mvp(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # fallback: everyone is Speaker 1
    out = []
    for s in segments:
        out.append({
            **s,
            "speaker": "Speaker 1",
            "timestamp": float(s.get("start", 0.0)),
        })
    return out

def diarize_with_pyannote(audio_path: str) -> List[Dict[str, Any]]:
    try:
        from pyannote.audio import Pipeline
    except Exception as e:
        raise RuntimeError("pyannote.audio not installed. pip install pyannote.audio") from e

    token = os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        raise RuntimeError("HUGGINGFACE_TOKEN not set for pyannote diarization.")

    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=token)
    diarization = pipeline(audio_path)

    # Convert to [{start, end, speaker}]
    out: List[Dict[str, Any]] = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        out.append({
            "start": float(turn.start),
            "end": float(turn.end),
            "speaker": str(speaker),
        })
    return out

def assign_speakers(
    audio_path: str,
    stt_segments: List[Dict[str, Any]],
    prefer_pyannote: bool = True
) -> List[Dict[str, Any]]:
    """
    Align diarization turns to STT segments by simple overlap rule.
    If pyannote unavailable or failed → MVP fallback.
    """
    if prefer_pyannote:
        try:
            spk_turns = diarize_with_pyannote(audio_path)
        except Exception:
            spk_turns = None
    else:
        spk_turns = None

    if not spk_turns:
        return diarize_segments_mvp(stt_segments)

    # 간단한 매칭: STT 세그먼트 중심시간이 포함되는 diarization turn의 speaker를 라벨링
    def find_speaker(t: float) -> str:
        for tr in spk_turns:
            if tr["start"] <= t <= tr["end"]:
                return tr["speaker"]
        return "Speaker ?"

    labeled = []
    for s in stt_segments:
        center = (float(s.get("start", 0.0)) + float(s.get("end", 0.0))) / 2.0
        labeled.append({
            **s,
            "speaker": find_speaker(center),
            "timestamp": float(s.get("start", 0.0)),
        })
    return labeled