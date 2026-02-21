from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _decode_pcm_mono(audio_path: Path) -> Tuple[List[float], int]:
    """Read a WAV file and return mono samples normalized to [-1, 1] and sample rate."""
    with wave.open(str(audio_path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        frames = wav_file.getnframes()
        raw = wav_file.readframes(frames)

    if sample_width == 1:
        ints = [byte - 128 for byte in raw]
        max_abs = 128.0
    elif sample_width == 2:
        count = len(raw) // 2
        ints = list(struct.unpack(f"<{count}h", raw))
        max_abs = 32768.0
    elif sample_width == 4:
        count = len(raw) // 4
        ints = list(struct.unpack(f"<{count}i", raw))
        max_abs = 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes")

    if channels <= 1:
        mono = [value / max_abs for value in ints]
    else:
        mono = []
        for idx in range(0, len(ints), channels):
            frame = ints[idx : idx + channels]
            mono.append((sum(frame) / len(frame)) / max_abs)

    return mono, int(sample_rate)


def _windowed_rms(samples: List[float], window_size: int) -> List[float]:
    if not samples:
        return []
    size = max(1, int(window_size))
    values: List[float] = []
    for i in range(0, len(samples), size):
        chunk = samples[i : i + size]
        if not chunk:
            continue
        mean_sq = sum(value * value for value in chunk) / len(chunk)
        values.append(math.sqrt(mean_sq))
    return values


def _mean_std(values: List[float]) -> Tuple[Optional[float], Optional[float]]:
    if not values:
        return None, None
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return mean, math.sqrt(variance)


def _segment_sample_bounds(start_s: float, end_s: float, sample_rate: int, total_samples: int) -> Tuple[int, int]:
    start_idx = max(0, min(total_samples, int(math.floor(start_s * sample_rate))))
    end_idx = max(start_idx, min(total_samples, int(math.ceil(end_s * sample_rate))))
    return start_idx, end_idx


def extract_prosody_features(audio_path: Path, aligned: Dict, output_path: Path) -> Dict:
    """
    Compute segment-level prosody features and write prosody.json.

    Features included per segment:
      - duration_s
      - pause_before_s / pause_after_s
      - rms_mean / rms_std (20ms windows)
    """
    segments = sorted(
        aligned.get("segments", []),
        key=lambda item: (float(item.get("start", 0.0)), float(item.get("end", 0.0))),
    )

    samples: List[float] = []
    sample_rate: Optional[int] = None
    audio_read_error: Optional[str] = None

    if audio_path.exists():
        try:
            samples, sample_rate = _decode_pcm_mono(audio_path)
        except (wave.Error, ValueError, OSError) as exc:
            audio_read_error = str(exc)
    else:
        audio_read_error = f"Audio file not found: {audio_path}"

    features: List[Dict] = []
    for idx, segment in enumerate(segments):
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", start))
        if end < start:
            end = start

        segment_id = int(segment.get("id", idx))
        speaker = str(segment.get("speaker", "UNKNOWN"))
        duration_s = max(0.0, end - start)

        if idx == 0:
            pause_before_s = 0.0
        else:
            prev_end = float(segments[idx - 1].get("end", start))
            pause_before_s = max(0.0, start - prev_end)

        if idx == len(segments) - 1:
            pause_after_s = 0.0
        else:
            next_start = float(segments[idx + 1].get("start", end))
            pause_after_s = max(0.0, next_start - end)

        rms_mean: Optional[float] = None
        rms_std: Optional[float] = None
        if sample_rate is not None and samples:
            left, right = _segment_sample_bounds(start, end, sample_rate, len(samples))
            segment_samples = samples[left:right]
            rms_values = _windowed_rms(segment_samples, window_size=int(sample_rate * 0.02))
            rms_mean, rms_std = _mean_std(rms_values)

        features.append(
            {
                "segment_id": segment_id,
                "start": start,
                "end": end,
                "speaker": speaker,
                "duration_s": duration_s,
                "pause_before_s": pause_before_s,
                "pause_after_s": pause_after_s,
                "rms_mean": rms_mean,
                "rms_std": rms_std,
            }
        )

    result = {
        "audio_path": str(audio_path),
        "method": "rms_pause_v1",
        "sample_rate_hz": sample_rate,
        "audio_read_error": audio_read_error,
        "features": features,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
