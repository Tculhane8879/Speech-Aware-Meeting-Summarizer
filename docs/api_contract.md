# Module API Contract (CS 582 Speech-Aware Meeting Summarizer)

This document defines the **inputs/outputs** for each pipeline module so team members can work independently
and integration stays smooth.

## Core idea

All modules read/write **simple files** inside a run directory:
`outputs/<run_name>/`

Each run should be reproducible from the original audio file + config.

---

## 0) Run Directory Layout (outputs/<run>/)

Expected files (some may be missing depending on flags/stage completion):

- `stages.txt` — list of pipeline stages
- `transcript.json` — ASR segments with timestamps
- `diarization.json` — speaker turns with timestamps
- `segments.json` — aligned segments combining ASR + speaker (optional but recommended)
- `prosody.json` — prosody features per segment or per speaker turn
- `topics.json` — topic segments and labels
- `summary.md` — final human-readable summary
- `metadata.json` — run metadata (audio path, model versions, parameters)

`data/` and `outputs/` are ignored by git.

---

## 1) ASR (Speech-to-Text) Output: transcript.json

### File: `transcript.json`

```json
{
  "audio_path": "data/raw/example.wav",
  "model": "small",
  "language": "en",
  "segments": [{ "id": 0, "start": 0.0, "end": 4.16, "text": "Hello..." }]
}
```

Rules:

- `start`/`end` are seconds (float)
- `segments` must be sorted by `start`
- `text` should be trimmed
- IDs are stable within a run

---

## 2) Diarization Output: diarization.json

### File: `diarization.json`

```json
{
  "audio_path": "data/raw/example.wav",
  "method": "pyannote|resemblyzer|baseline",
  "speakers": ["SPEAKER_0", "SPEAKER_1"],
  "turns": [
    { "id": 0, "speaker": "SPEAKER_0", "start": 0.2, "end": 2.8 },
    { "id": 1, "speaker": "SPEAKER_1", "start": 2.8, "end": 4.1 }
  ]
}
```

Rules:

- `turns` must be sorted by `start`
- speaker IDs must match `speakers`
- turns should not overlap (minor overlaps are allowed if algorithm produces them, but should be minimized)

---

## 3) Alignment Output: `segments.json`

### File: `segments.json`

```json
{
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 4.16,
      "speaker": "SPEAKER_0",
      "text": "Hello...",
      "asr_segment_id": 0,
      "turn_id": 0
    }
  ]
}
```

Rules:

- Choose speaker by maximum time overlap between the ASR segment and diarization turns
- If no diarization is available, use `"speaker": "UNKNOWN"` and omit `turn_id`

---

## 4) Prosody Output: `prosody.json`

Prosody can be computed per `segments.json` segment

### File: `prosody.json`

```json
{
  "audio_path": "data/raw/example.wav",
  "method": "rms_pause_v1",
  "sample_rate_hz": 16000,
  "audio_read_error": null,
  "features": [
    {
      "segment_id": 0,
      "start": 0.0,
      "end": 4.16,
      "speaker": "SPEAKER_0",
      "duration_s": 4.16,
      "pause_before_s": 0.35,
      "pause_after_s": 0.12,
      "rms_mean": 0.012,
      "rms_std": 0.004
    }
  ]
}
```

Rules:

- Features should reference `segment_id`
- `duration_s`, `pause_before_s`, and `pause_after_s` must be non-negative
- `rms_mean` and `rms_std` may be null when audio is unavailable or unreadable
- `audio_read_error` should be null on success; otherwise include a human-readable reason

---

## 5) Topic Segmentation Output: `topics.json`

### File: `topics.json`

```json
{
  "topics": [
    {
      "topic_id": 0,
      "start": 0.0,
      "end": 120.5,
      "label": "Budget discussion",
      "segment_ids": [0, 1, 2, 3]
    }
  ]
}
```

Rules:

- `segment_ids` reference `segments.json`
- `label` can be a simple keyword label for now

---

## 6) Summary Output: `summary.md`

### File: `summary.md`

A readable Markdown report that can include:

- overall summary
- per-topic bullet points
- speaker highlights (if diarization exists)
- prosody cues (if extracted)

---

## 7) Metadata: `metadata.json`

### File: `metadata.json`

```json
{
  "created_utc": "2026-02-14T00:00:00Z",
  "audio_path": "data/raw/example.wav",
  "pipeline_version": "0.1",
  "asr": { "model": "small" },
  "diarization": { "method": "baseline" }
}
```
