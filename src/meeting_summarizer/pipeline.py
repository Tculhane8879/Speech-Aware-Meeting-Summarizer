from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from meeting_summarizer.asr.transcribe import transcribe_audio
from meeting_summarizer.diarization.diarize import baseline_diarize_from_transcript
from meeting_summarizer.diarization.align import align_transcript_with_diarization
from meeting_summarizer.prosody.extract_prosody import extract_prosody_features
from meeting_summarizer.summarization.summarize import summarize_segments

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
    aligned = {"segments": []}

    # ASR stage
    if run_asr:
        transcript = transcribe_audio(input_path)

        # Write transcript.json
        transcript_path = output_dir / "transcript.json"
        transcript_path.write_text(json.dumps(transcript, indent=2), encoding="utf-8")

        # Diarization (baseline stub)
        diarization_path = output_dir / "diarization.json"
        diarization = baseline_diarize_from_transcript(transcript, diarization_path)

        # Alignment: ASR segments + diarization turns -> segments.json
        aligned = align_transcript_with_diarization(transcript, diarization)
        (output_dir / "segments.json").write_text(
            json.dumps(aligned, indent=2),
            encoding="utf-8",
        )

    stages = [
        "1) Speaker diarization",
        "2) Speech-to-text transcription (ASR)",
        "3) Prosody analysis (pitch/pauses/energy)",
        "4) Engagement / emotion detection" + (" (enabled)" if enable_engagement else " (skipped)"),
        "5) Topic segmentation",
        "6) Speech-aware summarization",
    ]

    extract_prosody_features(
        audio_path=input_path,
        aligned=aligned,
        output_path=output_dir / "prosody.json",
    )

    summary_text = summarize_segments(input_path=input_path, aligned=aligned)

    (output_dir / "stages.txt").write_text("\n".join(stages) + "\n", encoding="utf-8")
    (output_dir / "summary.md").write_text(summary_text, encoding="utf-8")

    return PipelineResult(output_dir=output_dir, summary_text=summary_text)