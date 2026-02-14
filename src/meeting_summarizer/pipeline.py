from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json

from meeting_summarizer.asr.transcribe import transcribe_audio
from meeting_summarizer.diarization.diarize import baseline_diarize_from_transcript

@dataclass
class PipelineResult:
    output_dir: Path
    summary_text: str


def run_pipeline(input_path: Path, output_dir: Path, enable_engagement: bool = False, run_asr: bool = True) -> PipelineResult:
    """
    Minimal scaffold for the meeting understanding pipeline.

    Later, each stage will call into:
      - diarization/
      - asr/
      - prosody/
      - topics/
      - summarization/
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # ASR stage
    if run_asr:
        transcript = transcribe_audio(input_path)
        
        # Diarization (baseline stub)
        diarization_path = output_dir / "diarization.json"
        
        # If transcript is available, pass it; otherwise create a minimal transcript dict
        transcript_data = transcript if 'transcript' not in locals() else transcript
        
        # (in case transcript variable name differs, ensure we use the returned transcript)
        diarization = baseline_diarize_from_transcript(transcript_data, diarization_path)
   
        transcript_path = output_dir / "transcript.json"
        transcript_path.write_text(json.dumps(transcript, indent=2), encoding="utf-8")

    stages = [
        "1) Speaker diarization",
        "2) Speech-to-text transcription (ASR)",
        "3) Prosody analysis (pitch/pauses/energy)",
        "4) Engagement / emotion detection" + (" (enabled)" if enable_engagement else " (skipped)"),
        "5) Topic segmentation",
        "6) Speech-aware summarization",
    ]

    # Placeholder summary
    summary_text = (
        "Placeholder summary:\n"
        f"- Input: {input_path}\n"
        "- TODO: diarization, ASR, prosody, topics, summarization\n"
    )

    (output_dir / "stages.txt").write_text("\n".join(stages) + "\n", encoding="utf-8")
    (output_dir / "summary.md").write_text(summary_text, encoding="utf-8")

    return PipelineResult(output_dir=output_dir, summary_text=summary_text)