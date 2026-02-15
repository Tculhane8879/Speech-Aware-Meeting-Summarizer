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


def test_summarize_segments_without_content() -> None:
    summary = summarize_segments(input_path=Path("data/raw/example.wav"), aligned={"segments": []})

    assert "Meeting Summary (MVP)" in summary
    assert "No transcript segments available yet" in summary
