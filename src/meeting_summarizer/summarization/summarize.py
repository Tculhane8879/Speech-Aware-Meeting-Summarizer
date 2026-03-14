from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional


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


def _format_speaker_stats(prosody_model: Dict) -> List[str]:
    rows = prosody_model.get("speaker_stats", []) if isinstance(prosody_model, dict) else []
    if not rows:
        return ["- No speaker-level prosody statistics available."]

    lines: List[str] = []
    for row in rows:
        speaker = str(row.get("speaker", "UNKNOWN"))
        segment_count = int(row.get("segment_count", 0))
        avg_rms = row.get("avg_rms_mean")
        avg_pause_before = row.get("avg_pause_before_s")
        avg_pause_after = row.get("avg_pause_after_s")

        rms_text = "n/a" if avg_rms is None else f"{float(avg_rms):.4f}"
        pause_before_text = "n/a" if avg_pause_before is None else f"{float(avg_pause_before):.2f}s"
        pause_after_text = "n/a" if avg_pause_after is None else f"{float(avg_pause_after):.2f}s"

        lines.append(
            f"- {speaker}: segments={segment_count}, avg_rms={rms_text}, "
            f"avg_pause_before={pause_before_text}, avg_pause_after={pause_after_text}"
        )
    return lines


def _compute_sequence_signals(prosody_model: Optional[Dict]) -> Dict[str, float | int]:
    if not prosody_model:
        return {
            "sequence_length": 0,
            "reflective_pause_count": 0,
            "reflective_pause_ratio": 0.0,
            "max_active_run": 0,
            "abrupt_transition_count": 0,
        }

    observations = prosody_model.get("sequence", {}).get("observations", [])
    states = [str(obs.get("state_label", "UNKNOWN")) for obs in observations]
    sequence_length = len(states)

    reflective_pause_count = sum(1 for state in states if state == "REFLECTIVE_PAUSE")
    reflective_pause_ratio = reflective_pause_count / sequence_length if sequence_length > 0 else 0.0

    max_active_run = 0
    current_active_run = 0
    for state in states:
        if state == "ACTIVE_SPEECH":
            current_active_run += 1
            max_active_run = max(max_active_run, current_active_run)
        else:
            current_active_run = 0

    abrupt_transition_count = 0
    transition_rows = prosody_model.get("sequence", {}).get("state_transition_counts", [])
    for row in transition_rows:
        from_state = str(row.get("from", ""))
        to_state = str(row.get("to", ""))
        if {from_state, to_state} == {"ACTIVE_SPEECH", "REFLECTIVE_PAUSE"}:
            abrupt_transition_count += int(row.get("count", 0))

    return {
        "sequence_length": sequence_length,
        "reflective_pause_count": reflective_pause_count,
        "reflective_pause_ratio": reflective_pause_ratio,
        "max_active_run": max_active_run,
        "abrupt_transition_count": abrupt_transition_count,
    }


def _engagement_label(signals: Dict[str, float | int]) -> str:
    score = 0
    max_active_run = int(signals.get("max_active_run", 0))
    reflective_pause_ratio = float(signals.get("reflective_pause_ratio", 0.0))
    abrupt_transition_count = int(signals.get("abrupt_transition_count", 0))

    if max_active_run >= 3:
        score += 1
    if reflective_pause_ratio >= 0.35:
        score -= 1
    if abrupt_transition_count >= 2:
        score -= 1

    if score >= 1:
        return "moderate-to-high"
    if score == 0:
        return "moderate"
    return "low-to-moderate"


def summarize_segments(
    input_path: Path,
    aligned: Dict,
    prosody_model: Optional[Dict] = None,
    enable_engagement: bool = False,
) -> str:
    segments: List[Dict] = aligned.get("segments", [])

    if not segments:
        lines = [
            "Meeting Summary (MVP)",
            f"- Input: {input_path}",
            "- No transcript segments available yet (ASR skipped or produced no segments).",
        ]
        if enable_engagement:
            lines.append("- Engagement heuristic: unavailable (no segment sequence to analyze).")
        return "\n".join(lines) + "\n"

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

    lines.extend(["", "Speaker prosody profile:"])
    lines.extend(_format_speaker_stats(prosody_model or {}))

    signals = _compute_sequence_signals(prosody_model)
    if int(signals["sequence_length"]) > 0:
        lines.extend(
            [
                "",
                "Sequence dynamics:",
                f"- Sequence length: {int(signals['sequence_length'])}",
                f"- Long reflective-pause states: {int(signals['reflective_pause_count'])}",
                f"- Longest ACTIVE_SPEECH run: {int(signals['max_active_run'])}",
                f"- Abrupt ACTIVE↔REFLECTIVE transitions: {int(signals['abrupt_transition_count'])}",
            ]
        )

    if enable_engagement:
        lines.extend(
            [
                "",
                "Engagement heuristic (prototype):",
                f"- Estimated engagement level: {_engagement_label(signals)}",
                "- Basis: active speech runs, reflective-pause ratio, and abrupt state shifts.",
            ]
        )

    return "\n".join(lines) + "\n"
