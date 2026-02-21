import json
import struct
import wave
from pathlib import Path

from meeting_summarizer.pipeline import run_pipeline


def test_smoke_pipeline(tmp_path: Path) -> None:
    # Input does not need to exist yet for the scaffold
    input_path = Path("data/raw/example.wav")
    output_dir = tmp_path / "out"

    result = run_pipeline(input_path=input_path, output_dir=output_dir, enable_engagement=False, run_asr=False)

    assert (output_dir / "stages.txt").exists()
    assert (output_dir / "summary.md").exists()
    assert (output_dir / "prosody.json").exists()

    prosody = json.loads((output_dir / "prosody.json").read_text(encoding="utf-8"))
    assert prosody["method"] == "rms_pause_v1"
    assert prosody["features"] == []

    assert "Meeting Summary (MVP)" in result.summary_text
    assert "No transcript segments available yet" in result.summary_text


def test_pipeline_writes_prosody_with_asr_enabled_using_stubbed_transcript(tmp_path: Path, monkeypatch) -> None:
    audio_path = tmp_path / "speech.wav"
    output_dir = tmp_path / "out"

    sample_rate = 16000
    one_second = [int(0.15 * 32767)] * sample_rate
    frames = struct.pack(f"<{len(one_second)}h", *one_second)
    with wave.open(str(audio_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)

    def _fake_transcribe(_audio_path: Path):
        return {
            "audio_path": str(audio_path),
            "model": "fake",
            "language": "en",
            "segments": [
                {"id": 0, "start": 0.0, "end": 1.0, "text": "hello team"},
            ],
        }

    monkeypatch.setattr("meeting_summarizer.pipeline.transcribe_audio", _fake_transcribe)

    run_pipeline(input_path=audio_path, output_dir=output_dir, enable_engagement=False, run_asr=True)

    prosody = json.loads((output_dir / "prosody.json").read_text(encoding="utf-8"))
    assert len(prosody["features"]) == 1
    assert prosody["audio_read_error"] is None
    assert prosody["features"][0]["rms_mean"] is not None