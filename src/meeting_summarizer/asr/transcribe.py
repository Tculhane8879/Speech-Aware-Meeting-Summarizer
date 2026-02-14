from pathlib import Path
from typing import Dict, List

from faster_whisper import WhisperModel


def transcribe_audio(audio_path: Path, model_size: str = "small") -> Dict:
    """
    Transcribe an audio file using faster-whisper.

    Returns a dictionary with:
        - audio_path
        - model
        - segments (list of {start, end, text})
    """

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments_generator, info = model.transcribe(str(audio_path))

    segments: List[Dict] = []

    for i, segment in enumerate(segments_generator):
        segments.append(
            {
                "id": i,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
            }
        )

    return {
        "audio_path": str(audio_path),
        "model": model_size,
        "language": info.language,
        "segments": segments,
    }