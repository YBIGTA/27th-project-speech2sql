"""
Whisper STT wrapper
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, TypedDict
import os
import torch
import numpy as np
import librosa
import whisper

class Segment(TypedDict, total=False):
    start: float
    end: float
    text: str
    avg_logprob: float
    no_speech_prob: float
    compression_ratio: float

class STTResult(TypedDict):
    text: str
    language: Optional[str]
    segments: List[Segment]

# --- model cache ---
_MODEL_CACHE: dict[str, whisper.Whisper] = {}

def _get_model(model_name: str) -> whisper.Whisper:
    """
    Load and cache the Whisper model.
    Args:
        model_name (str): Name of the Whisper model to load (e.g., "base", "small", "medium", "large").
    Returns:
        whisper.Whisper: Loaded Whisper model.
    """
    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = whisper.load_model(model_name)
    return _MODEL_CACHE[model_name]

def transcribe_audio(
    file_path: str,
    model_name: str = "base",
    language: Optional[str] = None,
    initial_prompt: Optional[str] = None,
) -> STTResult:
    """
    Transcribe an audio file using OpenAI Whisper.

    Args:
        file_path (str): Path to the audio file (WAV, MP3, M4A, etc.).
        model_name (str): Whisper model name (e.g., "base", "small", "medium", "large").
        language (Optional[str]): Language code for transcription (e.g., "en", "ko"). If None, auto-detect.
        initial_prompt (Optional[str]): Initial text prompt to guide transcription.
    Returns:
        {
          "text": str,
          "language": Optional[str],
          "segments": [
             {"start": float, "end": float, "text": str,
              "avg_logprob": float, "no_speech_prob": float, "compression_ratio": float}
          ]
        }
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    model = _get_model(model_name)

    # device/fp16 policy
    use_cuda = torch.cuda.is_available()
    fp16 = bool(use_cuda)

    def _run_transcribe(input_audio: Any) -> Dict[str, Any]:
        return model.transcribe(
            input_audio,
            task="transcribe",
            language=language,             # None이면 자동 감지
            fp16=fp16,                    # GPU면 fp16 사용
            verbose=False,
            temperature=(0.0, 0.2, 0.4),  # fallback for unstable parts
            condition_on_previous_text=True,
            initial_prompt=initial_prompt,
            logprob_threshold=-1.0,       # 더 유연하게
            no_speech_threshold=0.6,
            compression_ratio_threshold=2.4,
        )

    try:
        # Prefer WAV → numpy float32 16k mono
        if file_path.lower().endswith(".wav"):
            audio, _sr = librosa.load(file_path, sr=16000, mono=True)
            # Whisper expects float32 in [-1, 1]
            audio = audio.astype(np.float32)
            result = _run_transcribe(audio)
        else:
            # mp3/m4a 등은 ffmpeg 필요
            result = _run_transcribe(file_path)
    except FileNotFoundError as e:
        raise RuntimeError(
            "ffmpeg/decoder not found. Install ffmpeg (macOS: brew install ffmpeg, Ubuntu: apt-get install ffmpeg). "
            "Or supply WAV files."
        ) from e
    except OSError as e:
        # 디코더/경로 문제
        raise RuntimeError(f"Audio decoding failed: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}") from e

    segments: List[Segment] = []
    for seg in result.get("segments", []):
        segments.append({
            "start": float(seg.get("start", 0.0)),
            "end": float(seg.get("end", 0.0)),
            "text": str(seg.get("text", "")).strip(),
            "avg_logprob": float(seg.get("avg_logprob", 0.0)),
            "no_speech_prob": float(seg.get("no_speech_prob", 0.0)),
            "compression_ratio": float(seg.get("compression_ratio", 0.0)),
        })

    return {
        "text": str(result.get("text", "")).strip(),
        "language": result.get("language"),
        "segments": segments,
    }