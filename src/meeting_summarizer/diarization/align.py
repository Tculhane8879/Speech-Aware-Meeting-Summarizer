from __future__ import annotations

from typing import Dict, List, Optional


def align_transcript_with_diarization(transcript: Dict, diarization: Dict) -> Dict:
    """
    Assign a speaker label to every transcript segment by finding the
    diarization turn that overlaps most with each segment's time range.

    Returns {"segments": [...]} where each segment has the original fields
    plus "speaker" and "turn_id" keys.
    """
    transcript_segments: List[Dict] = transcript.get("segments", [])
    turns: List[Dict] = diarization.get("turns", [])

    if not turns:
        aligned = []
        for seg in transcript_segments:
            aligned.append({**seg, "speaker": "SPEAKER_0", "turn_id": None})
        return {"segments": aligned}

    def _best_turn(start: float, end: float):
        best_turn_id: Optional[int] = None
        best_speaker = "SPEAKER_0"
        best_overlap = -1.0
        for turn in turns:
            t_start = float(turn.get("start", 0.0))
            t_end = float(turn.get("end", t_start))
            overlap = max(0.0, min(end, t_end) - max(start, t_start))
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = str(turn.get("speaker", "SPEAKER_0"))
                best_turn_id = turn.get("id")
        return best_speaker, best_turn_id

    aligned: List[Dict] = []
    for seg in transcript_segments:
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        speaker, turn_id = _best_turn(start, end)
        aligned.append({**seg, "speaker": speaker, "turn_id": turn_id})

    return {"segments": aligned}
