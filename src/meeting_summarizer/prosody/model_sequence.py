from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def _energy_thresholds(values: List[float]) -> Tuple[float, float]:
    """Return lower/upper cut points for low/medium/high bucketing."""
    if not values:
        return 0.0, 0.0
    ordered = sorted(values)
    low_idx = max(0, len(ordered) // 3)
    high_idx = max(0, (2 * len(ordered)) // 3)
    return ordered[low_idx], ordered[min(high_idx, len(ordered) - 1)]


def _energy_bucket(value: Optional[float], low_cut: float, high_cut: float) -> str:
    if value is None:
        return "unknown"
    if value <= low_cut:
        return "low"
    if value <= high_cut:
        return "medium"
    return "high"


def _pause_bucket(pause_total: float) -> str:
    if pause_total < 0.15:
        return "short"
    if pause_total < 0.5:
        return "medium"
    return "long"


def _state_label(energy_bucket: str, pause_bucket: str) -> str:
    if energy_bucket == "unknown":
        return "UNKNOWN"
    if energy_bucket == "high" and pause_bucket in {"short", "medium"}:
        return "ACTIVE_SPEECH"
    if energy_bucket == "low" and pause_bucket == "long":
        return "REFLECTIVE_PAUSE"
    if energy_bucket == "medium" and pause_bucket == "short":
        return "STEADY_FLOW"
    return "TRANSITIONAL"


def build_prosody_sequence_model(prosody: Dict, output_path: Path) -> Dict:
    """
    Build speaker-level summaries and a prototype state sequence from prosody features.

    This is an HMM-inspired prototype using discretized observations and transition stats.
    """
    features: List[Dict] = sorted(
        prosody.get("features", []),
        key=lambda item: (float(item.get("start", 0.0)), float(item.get("end", 0.0))),
    )

    speaker_acc: Dict[str, Dict[str, List[float] | float | int]] = {}
    rms_values = [float(item["rms_mean"]) for item in features if item.get("rms_mean") is not None]
    low_cut, high_cut = _energy_thresholds(rms_values)

    observations: List[Dict] = []
    state_sequence: List[str] = []

    for item in features:
        speaker = str(item.get("speaker", "UNKNOWN"))
        duration = float(item.get("duration_s", 0.0))
        pause_before = float(item.get("pause_before_s", 0.0))
        pause_after = float(item.get("pause_after_s", 0.0))
        rms_mean = item.get("rms_mean")
        rms_value: Optional[float] = float(rms_mean) if rms_mean is not None else None

        if speaker not in speaker_acc:
            speaker_acc[speaker] = {
                "segment_count": 0,
                "total_duration_s": 0.0,
                "rms_values": [],
                "pause_before_values": [],
                "pause_after_values": [],
            }

        acc = speaker_acc[speaker]
        acc["segment_count"] = int(acc["segment_count"]) + 1
        acc["total_duration_s"] = float(acc["total_duration_s"]) + duration
        cast_rms_values = acc["rms_values"]
        cast_pause_before_values = acc["pause_before_values"]
        cast_pause_after_values = acc["pause_after_values"]
        if isinstance(cast_pause_before_values, list):
            cast_pause_before_values.append(pause_before)
        if isinstance(cast_pause_after_values, list):
            cast_pause_after_values.append(pause_after)
        if rms_value is not None and isinstance(cast_rms_values, list):
            cast_rms_values.append(rms_value)

        energy = _energy_bucket(rms_value, low_cut, high_cut)
        pause_total = pause_before + pause_after
        pause = _pause_bucket(pause_total)
        state = _state_label(energy, pause)
        state_sequence.append(state)

        observations.append(
            {
                "segment_id": int(item.get("segment_id", 0)),
                "speaker": speaker,
                "start": float(item.get("start", 0.0)),
                "end": float(item.get("end", 0.0)),
                "rms_mean": rms_value,
                "pause_before_s": pause_before,
                "pause_after_s": pause_after,
                "energy_bucket": energy,
                "pause_bucket": pause,
                "state_label": state,
            }
        )

    speaker_stats: List[Dict] = []
    for speaker, acc in sorted(speaker_acc.items()):
        rms_list = acc["rms_values"] if isinstance(acc["rms_values"], list) else []
        pause_before_list = acc["pause_before_values"] if isinstance(acc["pause_before_values"], list) else []
        pause_after_list = acc["pause_after_values"] if isinstance(acc["pause_after_values"], list) else []
        speaker_stats.append(
            {
                "speaker": speaker,
                "segment_count": int(acc["segment_count"]),
                "total_duration_s": float(acc["total_duration_s"]),
                "avg_rms_mean": _mean([float(v) for v in rms_list]),
                "avg_pause_before_s": _mean([float(v) for v in pause_before_list]),
                "avg_pause_after_s": _mean([float(v) for v in pause_after_list]),
            }
        )

    transition_counts: Dict[Tuple[str, str], int] = {}
    outgoing_totals: Dict[str, int] = {}
    for idx in range(len(state_sequence) - 1):
        key = (state_sequence[idx], state_sequence[idx + 1])
        transition_counts[key] = transition_counts.get(key, 0) + 1
        outgoing_totals[key[0]] = outgoing_totals.get(key[0], 0) + 1

    transition_count_rows = [
        {"from": start, "to": end, "count": count}
        for (start, end), count in sorted(transition_counts.items())
    ]
    transition_probability_rows = [
        {
            "from": row["from"],
            "to": row["to"],
            "probability": row["count"] / max(1, outgoing_totals.get(row["from"], 1)),
        }
        for row in transition_count_rows
    ]

    model = {
        "audio_path": prosody.get("audio_path"),
        "method": "prosody_sequence_v1",
        "source_prosody_method": prosody.get("method"),
        "speaker_stats": speaker_stats,
        "sequence": {
            "length": len(observations),
            "observations": observations,
            "state_transition_counts": transition_count_rows,
            "state_transition_probabilities": transition_probability_rows,
        },
        "notes": "Prototype HMM-style discretization over prosody observations (not a trained HMM).",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(model, indent=2), encoding="utf-8")
    return model
