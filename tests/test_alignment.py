from meeting_summarizer.diarization.align import align_transcript_with_diarization


def test_alignment_assigns_speaker_by_overlap():
    transcript = {
        "segments": [
            {"id": 0, "start": 0.0, "end": 2.0, "text": "Hi"},
            {"id": 1, "start": 2.0, "end": 4.0, "text": "Hello"},
        ]
    }
    diarization = {
        "turns": [
            {"id": 10, "speaker": "SPEAKER_0", "start": 0.0, "end": 3.0},
            {"id": 11, "speaker": "SPEAKER_1", "start": 3.0, "end": 5.0},
        ]
    }

    aligned = align_transcript_with_diarization(transcript, diarization)
    segs = aligned["segments"]

    assert segs[0]["speaker"] == "SPEAKER_0"
    assert segs[0]["turn_id"] == 10
    assert segs[1]["speaker"] == "SPEAKER_0"  # overlaps 2-3 (1s) vs 3-4 (1s) -> tie goes to first max found
    assert segs[1]["turn_id"] == 10