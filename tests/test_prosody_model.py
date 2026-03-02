import json
from pathlib import Path

from meeting_summarizer.prosody.model_sequence import build_prosody_sequence_model


def test_build_prosody_sequence_model_with_features(tmp_path: Path) -> None:
    prosody = {
        "audio_path": "data/raw/sample.wav",
        "method": "rms_pause_v1",
        "features": [
            {
                "segment_id": 0,
                "start": 0.0,
                "end": 1.0,
                "speaker": "SPEAKER_0",
                "duration_s": 1.0,
                "pause_before_s": 0.4,
                "pause_after_s": 0.4,
                "rms_mean": 0.01,
            },
            {
                "segment_id": 1,
                "start": 1.0,
                "end": 2.0,
                "speaker": "SPEAKER_1",
                "duration_s": 1.0,
                "pause_before_s": 0.05,
                "pause_after_s": 0.05,
                "rms_mean": 0.2,
            },
            {
                "segment_id": 2,
                "start": 2.0,
                "end": 3.0,
                "speaker": "SPEAKER_1",
                "duration_s": 1.0,
                "pause_before_s": 0.05,
                "pause_after_s": 0.05,
                "rms_mean": 0.04,
            },
            {
                "segment_id": 3,
                "start": 3.0,
                "end": 4.0,
                "speaker": "SPEAKER_0",
                "duration_s": 1.0,
                "pause_before_s": 0.1,
                "pause_after_s": 0.1,
                "rms_mean": 0.08,
            },
        ],
    }

    output_path = tmp_path / "prosody_model.json"
    model = build_prosody_sequence_model(prosody=prosody, output_path=output_path)

    assert output_path.exists()
    assert model["method"] == "prosody_sequence_v1"
    assert model["source_prosody_method"] == "rms_pause_v1"

    assert len(model["speaker_stats"]) == 2
    speaker0 = next(item for item in model["speaker_stats"] if item["speaker"] == "SPEAKER_0")
    speaker1 = next(item for item in model["speaker_stats"] if item["speaker"] == "SPEAKER_1")

    assert speaker0["segment_count"] == 2
    assert speaker1["segment_count"] == 2
    assert speaker0["avg_rms_mean"] is not None
    assert speaker1["avg_rms_mean"] is not None
    assert speaker1["avg_rms_mean"] > speaker0["avg_rms_mean"]

    sequence = model["sequence"]
    assert sequence["length"] == 4
    assert len(sequence["observations"]) == 4

    states = [item["state_label"] for item in sequence["observations"]]
    assert states[0] == "REFLECTIVE_PAUSE"
    assert states[1] == "ACTIVE_SPEECH"

    transition_counts = {
        (item["from"], item["to"]): item["count"] for item in sequence["state_transition_counts"]
    }
    assert transition_counts[("REFLECTIVE_PAUSE", "ACTIVE_SPEECH")] == 1

    persisted = json.loads(output_path.read_text(encoding="utf-8"))
    assert persisted["sequence"]["length"] == 4


def test_build_prosody_sequence_model_empty_features(tmp_path: Path) -> None:
    model = build_prosody_sequence_model(
        prosody={"audio_path": "data/raw/example.wav", "method": "rms_pause_v1", "features": []},
        output_path=tmp_path / "prosody_model.json",
    )

    assert model["speaker_stats"] == []
    assert model["sequence"]["length"] == 0
    assert model["sequence"]["state_transition_counts"] == []
    assert model["sequence"]["state_transition_probabilities"] == []
