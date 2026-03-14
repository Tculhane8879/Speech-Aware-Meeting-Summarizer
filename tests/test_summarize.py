from pathlib import Path

from meeting_summarizer.summarization.summarize import summarize_segments


def test_summarize_segments_with_content() -> None:
    aligned = {
        "segments": [
            {"id": 0, "start": 0.0, "end": 1.2, "speaker": "SPEAKER_0", "text": "Let's review the budget."},
            {"id": 1, "start": 1.2, "end": 2.8, "speaker": "SPEAKER_1", "text": "We can cut nonessential costs."},
        ]
    }

    summary = summarize_segments(input_path=Path("data/raw/example.wav"), aligned=aligned)

    assert "Meeting Summary (MVP)" in summary
    assert "Segments analyzed: 2" in summary
    assert "Speakers detected: SPEAKER_0, SPEAKER_1" in summary
    assert "Top transcript highlights:" in summary
    assert "Speaker prosody profile:" in summary


def test_summarize_segments_without_content() -> None:
    summary = summarize_segments(input_path=Path("data/raw/example.wav"), aligned={"segments": []})

    assert "Meeting Summary (MVP)" in summary
    assert "No transcript segments available yet" in summary


def test_summarize_segments_with_sequence_and_engagement() -> None:
    aligned = {
        "segments": [
            {"id": 0, "start": 0.0, "end": 1.0, "speaker": "SPEAKER_0", "text": "Let's start now."},
            {"id": 1, "start": 1.0, "end": 2.0, "speaker": "SPEAKER_1", "text": "Agreed."},
            {"id": 2, "start": 2.0, "end": 3.0, "speaker": "SPEAKER_0", "text": "Thanks."},
        ]
    }
    prosody_model = {
        "speaker_stats": [
            {
                "speaker": "SPEAKER_0",
                "segment_count": 2,
                "avg_rms_mean": 0.08,
                "avg_pause_before_s": 0.10,
                "avg_pause_after_s": 0.09,
            },
            {
                "speaker": "SPEAKER_1",
                "segment_count": 1,
                "avg_rms_mean": 0.05,
                "avg_pause_before_s": 0.12,
                "avg_pause_after_s": 0.12,
            },
        ],
        "sequence": {
            "observations": [
                {"state_label": "ACTIVE_SPEECH"},
                {"state_label": "ACTIVE_SPEECH"},
                {"state_label": "ACTIVE_SPEECH"},
            ],
            "state_transition_counts": [
                {"from": "ACTIVE_SPEECH", "to": "ACTIVE_SPEECH", "count": 2},
            ],
        },
    }

    summary = summarize_segments(
        input_path=Path("data/raw/example.wav"),
        aligned=aligned,
        prosody_model=prosody_model,
        enable_engagement=True,
    )

    assert "Speaker prosody profile:" in summary
    assert "SPEAKER_0: segments=2" in summary
    assert "Sequence dynamics:" in summary
    assert "Longest ACTIVE_SPEECH run: 3" in summary
    assert "Engagement heuristic (prototype):" in summary
    assert "Estimated engagement level: moderate-to-high" in summary
