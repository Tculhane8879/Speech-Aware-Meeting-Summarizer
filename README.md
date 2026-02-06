# Speech-Aware Meeting Understanding and Summarization

This project explores how **speech information beyond words**—such as prosody, speaker behavior,
and acoustic cues—can improve understanding of recorded meetings.  
Rather than relying solely on transcripts, we build a **speech-aware pipeline** that produces
structured, enriched meeting summaries.

## Project Overview

Recorded meetings contain valuable information in _how_ things are said, not just _what_ is said.
This system analyzes Zoom-style meeting recordings and generates summaries enhanced with speech
features such as speaker turns, emphasis, pauses, and engagement cues.

## Pipeline

The system is organized as a modular pipeline:

1. **Speaker Diarization** — determine who spoke when
2. **Speech-to-Text (ASR)** — transcribe meeting audio
3. **Prosody Analysis** — extract pitch, pauses, and energy
4. **Engagement / Emotion (Optional)** — detect basic speaker engagement
5. **Topic Segmentation** — split the meeting into topical segments
6. **Speech-Aware Summarization** — generate an enriched meeting summary

## Example Output

Instead of:

> “They discussed deadlines and budgets.”

The system produces:

> “The budget discussion showed increased tension and longer pauses, while agreement was reached
> confidently during the deadline segment.”

## Repository Structure

```text
src/meeting_summarizer/   # Core pipeline modules
tests/                    # Tests
docs/                     # Project documentation
scripts/                  # Helper scripts
data/                     # Local data (ignored by git)
```
