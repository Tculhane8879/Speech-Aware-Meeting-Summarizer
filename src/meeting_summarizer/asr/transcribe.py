from __future__ import annotations

from pathlib import Path
from typing import Dict, List


def transcribe_audio(audio_path: Path) -> Dict:
    """
    Transcribe audio using faster-whisper.

    Returns a dict matching the project transcript schema:
    {
        "audio_path": str,
        "model": str,
        "language": str,
        "segments": [{"id": int, "start": float, "end": float, "text": str}, ...]
    }
    """
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        ) from exc

    model = WhisperModel("base", device="cpu", compute_type="int8")

    raw_segments, info = model.transcribe(str(audio_path), beam_size=5)

    segments: List[Dict] = []
    for i, seg in enumerate(raw_segments):
        segments.append(
            {
                "id": i,
                "start": float(seg.start),
                "end": float(seg.end),
                "text": seg.text.strip(),
            }
        )

    return {
        "audio_path": str(audio_path),
        "model": "base",
        "language": info.language,
        "segments": segments,
    }
