import json
import math
import struct
import wave
from pathlib import Path

from meeting_summarizer.prosody.extract_prosody import extract_prosody_features


def _write_test_wav(path: Path, sample_rate: int = 16000) -> None:
    # 0-1.0s: low-amplitude tone, 1.0-1.5s: silence, 1.5-2.5s: higher-amplitude tone
    samples = []
    total_seconds = 2.5
    total_samples = int(sample_rate * total_seconds)
    for i in range(total_samples):
        t = i / sample_rate
        if t < 1.0:
            amp = 0.10 * math.sin(2.0 * math.pi * 220.0 * t)
        elif t < 1.5:
            amp = 0.0
        else:
            amp = 0.20 * math.sin(2.0 * math.pi * 220.0 * t)
        int16_value = max(-32768, min(32767, int(amp * 32767.0)))
        samples.append(int16_value)

    frames = struct.pack(f"<{len(samples)}h", *samples)

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)


def test_extract_prosody_features_rms_and_pauses(tmp_path: Path) -> None:
    audio_path = tmp_path / "speech_like.wav"
    _write_test_wav(audio_path)

    aligned = {
        "segments": [
            {"id": 0, "start": 0.0, "end": 1.0, "speaker": "SPEAKER_0", "text": "part one"},
            {"id": 1, "start": 1.5, "end": 2.5, "speaker": "SPEAKER_1", "text": "part two"},
        ]
    }

    output_path = tmp_path / "prosody.json"
    result = extract_prosody_features(audio_path=audio_path, aligned=aligned, output_path=output_path)

    assert output_path.exists()
    assert result["method"] == "rms_pause_v1"
    assert result["audio_read_error"] is None
    assert result["sample_rate_hz"] == 16000

    features = result["features"]
    assert len(features) == 2

    first, second = features
    assert first["pause_before_s"] == 0.0
    assert first["pause_after_s"] == 0.5
    assert second["pause_before_s"] == 0.5
    assert second["pause_after_s"] == 0.0

    assert first["rms_mean"] is not None
    assert second["rms_mean"] is not None
    assert second["rms_mean"] > first["rms_mean"] > 0.0

    persisted = json.loads(output_path.read_text(encoding="utf-8"))
    assert persisted["features"][0]["segment_id"] == 0
    assert persisted["features"][1]["segment_id"] == 1


def test_extract_prosody_features_missing_audio(tmp_path: Path) -> None:
    aligned = {
        "segments": [
            {"id": 10, "start": 2.0, "end": 3.0, "speaker": "SPEAKER_0", "text": "hello"},
        ]
    }
    output_path = tmp_path / "prosody.json"

    result = extract_prosody_features(
        audio_path=tmp_path / "does_not_exist.wav",
        aligned=aligned,
        output_path=output_path,
    )

    assert output_path.exists()
    assert "Audio file not found" in (result["audio_read_error"] or "")
    assert len(result["features"]) == 1
    assert result["features"][0]["rms_mean"] is None
    assert result["features"][0]["rms_std"] is None
