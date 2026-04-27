from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


def _load_audio(audio_path: Path) -> Tuple[Optional[np.ndarray], int, Optional[str]]:
    """
    Load audio file into a mono float32 numpy array using PyAV.
    Handles WAV, MP3, M4A, and any format supported by ffmpeg.
    Returns (samples, sample_rate, error_message).
    """
    if not audio_path.exists():
        return None, 0, f"Audio file not found: {audio_path}"

    try:
        import av  # type: ignore
    except ImportError:
        return None, 0, "PyAV not installed (pip install av)"

    try:
        container = av.open(str(audio_path))
        audio_streams = [s for s in container.streams if s.type == "audio"]
        if not audio_streams:
            container.close()
            return None, 0, "no audio stream found"

        audio_stream = audio_streams[0]
        sample_rate: int = audio_stream.sample_rate or 16000

        chunks: List[np.ndarray] = []
        for frame in container.decode(audio=0):
            arr = frame.to_ndarray()
            # arr shape: (channels, samples) for planar formats — mix to mono
            if arr.ndim > 1:
                arr = arr.mean(axis=0)
            # normalize to float32 in [-1, 1]
            if arr.dtype == np.int16:
                arr = arr.astype(np.float32) / 32768.0
            elif arr.dtype == np.int32:
                arr = arr.astype(np.float32) / 2_147_483_648.0
            else:
                arr = arr.astype(np.float32)
            chunks.append(arr)

        container.close()

        if not chunks:
            return None, sample_rate, "no audio frames decoded"

        samples = np.concatenate(chunks)
        return samples, sample_rate, None

    except Exception as exc:  # noqa: BLE001
        return None, 0, str(exc)


def _rms_stats(
    samples: np.ndarray,
    start: float,
    end: float,
    sample_rate: int,
) -> Tuple[Optional[float], Optional[float]]:
    """Return (rms_mean, rms_std) for the slice [start, end] seconds."""
    i0 = int(start * sample_rate)
    i1 = int(end * sample_rate)
    i0 = max(0, min(i0, len(samples)))
    i1 = max(i0, min(i1, len(samples)))
    if i1 <= i0:
        return None, None
    chunk = samples[i0:i1]
    if chunk.size == 0:
        return None, None
    # Frame-level RMS with 10ms frames
    frame_len = max(1, int(0.01 * sample_rate))
    n_frames = len(chunk) // frame_len
    if n_frames == 0:
        rms_val = float(np.sqrt(np.mean(chunk ** 2)))
        return rms_val, 0.0
    frames = chunk[: n_frames * frame_len].reshape(n_frames, frame_len)
    frame_rms = np.sqrt(np.mean(frames ** 2, axis=1))
    return float(frame_rms.mean()), float(frame_rms.std())


def extract_prosody_features(
    audio_path: Path,
    aligned: Dict,
    output_path: Path,
) -> Dict:
    """
    Extract per-segment prosody features: RMS energy and pause durations.

    Uses PyAV to decode audio so it works with MP3, WAV, M4A, and other
    formats supported by ffmpeg — not just WAV.
    """
    segments: List[Dict] = aligned.get("segments", [])

    samples, sample_rate, audio_error = _load_audio(audio_path)

    features: List[Dict] = []
    for idx, seg in enumerate(segments):
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        speaker = str(seg.get("speaker", "UNKNOWN"))
        duration_s = max(0.0, end - start)

        # Pause = gap between adjacent segments (clamped to 0)
        if idx > 0:
            prev_end = float(segments[idx - 1].get("end", start))
            pause_before_s = max(0.0, start - prev_end)
        else:
            pause_before_s = 0.0

        if idx < len(segments) - 1:
            next_start = float(segments[idx + 1].get("start", end))
            pause_after_s = max(0.0, next_start - end)
        else:
            pause_after_s = 0.0

        rms_mean: Optional[float] = None
        rms_std: Optional[float] = None
        if samples is not None and len(samples) > 0:
            rms_mean, rms_std = _rms_stats(samples, start, end, sample_rate)

        features.append(
            {
                "segment_id": int(seg.get("id", idx)),
                "speaker": speaker,
                "start": start,
                "end": end,
                "duration_s": duration_s,
                "rms_mean": rms_mean,
                "rms_std": rms_std,
                "pause_before_s": pause_before_s,
                "pause_after_s": pause_after_s,
            }
        )

    result = {
        "audio_path": str(audio_path),
        "method": "rms_pause_v1",
        "sample_rate_hz": sample_rate if sample_rate else None,
        "audio_read_error": audio_error,
        "features": features,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
