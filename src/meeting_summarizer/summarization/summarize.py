from __future__ import annotations

from pathlib import Path
from typing import Dict, List


def _collect_highlights(segments: List[Dict], max_items: int = 3) -> List[str]:
    highlights: List[str] = []
    for segment in segments:
        text = (segment.get("text") or "").strip()
        if not text:
            continue
        speaker = str(segment.get("speaker", "UNKNOWN"))
        highlights.append(f"- {speaker}: {text}")
        if len(highlights) >= max_items:
            break
    return highlights


def summarize_segments(input_path: Path, aligned: Dict) -> str:
    segments: List[Dict] = aligned.get("segments", [])

    if not segments:
        return (
            "Meeting Summary (MVP)\n"
            f"- Input: {input_path}\n"
            "- No transcript segments available yet (ASR skipped or produced no segments).\n"
        )

    start = min(float(segment.get("start", 0.0)) for segment in segments)
    end = max(float(segment.get("end", start)) for segment in segments)
    duration_seconds = max(0.0, end - start)

    speakers = sorted({str(segment.get("speaker", "UNKNOWN")) for segment in segments})
    highlights = _collect_highlights(segments)
    if not highlights:
        highlights = ["- (No spoken text captured in transcript segments.)"]

    lines = [
        "Meeting Summary (MVP)",
        f"- Input: {input_path}",
        f"- Segments analyzed: {len(segments)}",
        f"- Estimated duration: {duration_seconds:.1f}s",
        f"- Speakers detected: {', '.join(speakers)}",
        "",
        "Top transcript highlights:",
        *highlights,
    ]
    return "\n".join(lines) + "\n"
