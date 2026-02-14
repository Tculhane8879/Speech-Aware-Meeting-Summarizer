from __future__ import annotations

from typing import Dict, List, Optional


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    """Return overlap duration in seconds between [a_start,a_end] and [b_start,b_end]."""
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def align_transcript_with_diarization(transcript: Dict, diarization: Optional[Dict]) -> Dict:
    """
    Create segments.json by assigning each ASR segment a speaker based on max overlap.
    If diarization is None, speaker is UNKNOWN.
    """
    asr_segments = transcript.get("segments", [])
    turns = (diarization or {}).get("turns", [])

    aligned: List[Dict] = []

    for idx, seg in enumerate(asr_segments):
        # Some ASR backends may not provide an 'id' per segment; default to index.
        raw_id = seg.get("id", idx)
        seg_id = int(raw_id) if raw_id is not None else int(idx)

        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        text = (seg.get("text") or "").strip()

        speaker = "UNKNOWN"
        best_turn_id = None
        best_overlap = 0.0

        for turn in turns:
            t_id = int(turn.get("id"))
            t_start = float(turn.get("start", 0.0))
            t_end = float(turn.get("end", t_start))
            ov = _overlap(start, end, t_start, t_end)
            if ov > best_overlap:
                best_overlap = ov
                best_turn_id = t_id
                speaker = str(turn.get("speaker", "UNKNOWN"))

        out = {
            "id": seg_id,
            "start": start,
            "end": end,
            "speaker": speaker,
            "text": text,
            "asr_segment_id": seg_id,
        }
        if best_turn_id is not None:
            out["turn_id"] = best_turn_id

        aligned.append(out)

    aligned.sort(key=lambda x: (x["start"], x["end"]))
    return {"segments": aligned}