from pathlib import Path
from meeting_summarizer.diarization.diarize import baseline_diarize_from_transcript

def test_diarization_writes_turns(tmp_path: Path) -> None:
    transcript = {
        "audio_path": "data/raw/example.wav",
        "model": "small",
        "language": "en",
        "segments": [
            {"id": 0, "start": 0.0, "end": 1.0, "text": "Hi"},
            {"id": 1, "start": 1.0, "end": 2.5, "text": "Hello there"},
        ],
    }

    out = tmp_path / "diar.json"
    diar = baseline_diarize_from_transcript(transcript, out)

    assert "turns" in diar
    assert len(diar["turns"]) == 2
    assert diar["turns"][0]["speaker"] == "SPEAKER_0"
    assert out.exists()