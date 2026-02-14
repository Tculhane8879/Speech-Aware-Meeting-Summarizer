from pathlib import Path
from typing import Dict, List

def baseline_diarize_from_transcript(transcript: Dict, output_path: Path) -> Dict:
    """
    Simple baseline diarization stub.
    - Assigns every ASR segment to SPEAKER_0
    - Produces a diarization.json structure and writes it to output_path
    """

    audio_path = transcript.get("audio_path", "")
    segments = transcript.get("segments", [])

    # build turns by copying ASR segments but adding speaker id and turn id
    turns: List[Dict] = []
    speakers = ["SPEAKER_0"]

    for i, seg in enumerate(segments):
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        turns.append(
            {
                "id": i,
                "speaker": "SPEAKER_0",
                "start": start,
                "end": end,
            }
        )

    diarization = {
        "audio_path": audio_path,
        "method": "baseline_stub",
        "speakers": speakers,
        "turns": turns,
    }

    # ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        __import__("json").dumps(diarization, indent=2), encoding="utf-8"
    )

    return diarization