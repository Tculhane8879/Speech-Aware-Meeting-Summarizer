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

## Current Implementation Status

Implemented now:

- ASR via `faster-whisper`
- Baseline diarization stub
- Alignment (`segments.json`)
- Prosody features (`prosody.json`) with:
  - `duration_s`
  - `pause_before_s`, `pause_after_s`
  - `rms_mean`, `rms_std`
- MVP summary generation (`summary.md`)

## Quick Start (CLI)

### 1) Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 2) Run fast smoke pipeline (no ASR)

Windows PowerShell:

```bash
$env:PYTHONPATH="src"
python src\cli.py --no-asr --output outputs\smoke_test
```

MacOS/Linux:

```bash
PYTHONPATH=src python src/cli.py --no-asr --output outputs/smoke_test
```

### 3) Run tests

```bash
python -m pytest -q
```

## Run the Local Web App (manual testing)

The project includes a lightweight web interface to run the pipeline and inspect summary/prosody outputs.

### Start web app

Windows PowerShell:

```bash
$env:PYTHONPATH="src"
python -m meeting_summarizer.web_app
```

Then open:

```text
http://127.0.0.1:8000
```

In the UI you can:

- Set audio input and output folder
- Toggle ASR on/off
- Run pipeline from browser
- Inspect summary and prosody table

Tip: keep **Run ASR** unchecked for quick manual checks.

## Example Output

Instead of:

> “They discussed deadlines and budgets.”

The system produces:

> “The budget discussion showed increased tension and longer pauses, while agreement was reached
> confidently during the deadline segment.”

## Repository Structure

```text
src/meeting_summarizer/   # Core pipeline modules
  web_app.py              # Flask app entry for local UI
  webui/                  # HTML/CSS/JS for manual testing UI
tests/                    # Tests
docs/                     # Project documentation
scripts/                  # Helper scripts
data/                     # Local data (ignored by git)
```
