from pathlib import Path

from meeting_summarizer.pipeline import run_pipeline


def test_smoke_pipeline(tmp_path: Path) -> None:
    # Input does not need to exist yet for the scaffold
    input_path = Path("data/raw/example.wav")
    output_dir = tmp_path / "out"

    result = run_pipeline(input_path=input_path, output_dir=output_dir, enable_engagement=False, run_asr=False)

    assert (output_dir / "stages.txt").exists()
    assert (output_dir / "summary.md").exists()
    assert "Meeting Summary (MVP)" in result.summary_text
    assert "No transcript segments available yet" in result.summary_text