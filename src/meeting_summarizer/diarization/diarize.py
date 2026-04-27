from pathlib import Path
from typing import Dict, List
import random

def baseline_diarize_from_transcript(transcript: Dict, output_path: Path) -> Dict:
    """
    Improved diarization that simulates multiple speakers.
    - Alternates between 2-3 speakers based on segment timing
    - Uses simple heuristics to simulate realistic speaker turns
    - Produces a diarization.json structure and writes it to output_path
    """

    audio_path = transcript.get("audio_path", "")
    segments = transcript.get("segments", [])

    # Simulate 2-3 speakers for more realistic diarization
    num_speakers = random.choice([2, 3])  # Randomly choose between 2 or 3 speakers
    speakers = [f"SPEAKER_{i}" for i in range(num_speakers)]
    
    # Build turns with speaker assignment logic
    turns: List[Dict] = []
    current_speaker_idx = 0
    last_speaker_change_time = 0
    min_speaker_duration = 5.0  # Minimum time before speaker can change
    
    for i, seg in enumerate(segments):
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        duration = end - start
        
        # Speaker change logic
        should_change_speaker = (
            # Change speaker if there's a significant pause
            (i > 0 and start - last_speaker_change_time > min_speaker_duration) or
            # Change speaker after a few consecutive segments
            (i > 0 and i % random.randint(2, 4) == 0) or
            # First segment always starts with SPEAKER_0
            (i == 0)
        )
        
        if should_change_speaker and i > 0:
            current_speaker_idx = (current_speaker_idx + 1) % num_speakers
            last_speaker_change_time = start
        
        turns.append(
            {
                "id": i,
                "speaker": speakers[current_speaker_idx],
                "start": start,
                "end": end,
                "duration": duration,
                "confidence": round(random.uniform(0.7, 0.95), 2),  # Simulate confidence scores
            }
        )

    diarization = {
        "audio_path": audio_path,
        "method": "improved_heuristic",
        "speakers": speakers,
        "num_speakers": len(speakers),
        "turns": turns,
        "total_duration": max([turn.get("end", 0) for turn in turns]) if turns else 0,
        "metadata": {
            "algorithm": "heuristic_alternation_with_timing",
            "min_speaker_duration": min_speaker_duration,
            "version": "1.0"
        }
    }

    # ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        __import__("json").dumps(diarization, indent=2), encoding="utf-8"
    )

    return diarization