"""
Topic segmentation for meeting transcripts.

This module implements a simple but effective approach to segmenting meeting transcripts
into coherent topics based on speaker turns and content similarity.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import re
from collections import defaultdict


def segment_topics(aligned_segments: List[Dict], min_segment_size: int = 3) -> Dict:
    """
    Segment aligned transcript segments into topics.
    
    Uses a combination of:
    - Speaker turn boundaries
    - Temporal gaps (pauses)
    - Simple keyword-based topic detection
    
    Args:
        aligned_segments: List of segments with speaker, text, start, end times
        min_segment_size: Minimum number of segments per topic
        
    Returns:
        Dictionary with topics structure
    """
    if not aligned_segments or len(aligned_segments) < min_segment_size:
        return {
            "method": "simple_topic_segmentation",
            "num_topics": 0,
            "topics": []
        }
    
    # Group segments by temporal gaps and speaker changes
    topics = []
    current_topic_segments = []
    last_end_time = 0
    last_speaker = None
    
    for i, segment in enumerate(aligned_segments):
        current_time = segment.get("start", 0)
        current_speaker = segment.get("speaker", "UNKNOWN")
        text = segment.get("text", "").strip()
        
        # Calculate gap from previous segment
        gap = current_time - last_end_time if last_end_time > 0 else 0
        
        # Decision points for topic boundary:
        # 1. Large temporal gap (> 10 seconds)
        # 2. Speaker change after substantial content
        # 3. Explicit transition phrases
        has_large_gap = gap > 10.0
        speaker_changed = current_speaker != last_speaker and last_speaker is not None
        has_transition = _has_transition_phrase(text)
        
        should_start_new_topic = (
            has_large_gap or 
            (speaker_changed and len(current_topic_segments) >= min_segment_size) or
            has_transition
        )
        
        if should_start_new_topic and current_topic_segments:
            # Save current topic
            topic = _create_topic_from_segments(current_topic_segments, len(topics))
            topics.append(topic)
            current_topic_segments = []
        
        # Add current segment to topic
        current_topic_segments.append(segment)
        last_end_time = segment.get("end", current_time)
        last_speaker = current_speaker
    
    # Don't forget the last topic
    if current_topic_segments:
        topic = _create_topic_from_segments(current_topic_segments, len(topics))
        topics.append(topic)
    
    # Merge very small topics with neighbors
    topics = _merge_small_topics(topics, min_segment_size)
    
    return {
        "method": "simple_topic_segmentation",
        "num_topics": len(topics),
        "topics": topics
    }


def _has_transition_phrase(text: str) -> bool:
    """Check if text contains transition/topic change indicators."""
    transition_phrases = [
        "moving on", "next topic", "let's talk about", "changing subject",
        "another point", "regarding", "concerning", "as for", "now let's",
        "okay so", "alright", "anyway", "so", "well", "actually"
    ]
    
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in transition_phrases)


def _create_topic_from_segments(segments: List[Dict], topic_id: int) -> Dict:
    """Create a topic structure from a list of segments."""
    if not segments:
        return {}
    
    # Calculate topic timing
    start_time = min(seg.get("start", 0) for seg in segments)
    end_time = max(seg.get("end", 0) for seg in segments)
    duration = end_time - start_time
    
    # Get all speakers in this topic
    speakers = list(set(seg.get("speaker", "UNKNOWN") for seg in segments))
    
    # Combine text
    full_text = " ".join(seg.get("text", "") for seg in segments).strip()
    
    # Extract key terms (simple frequency-based)
    words = re.findall(r'\b\w+\b', full_text.lower())
    word_freq = defaultdict(int)
    for word in words:
        if len(word) > 3:  # Ignore very short words
            word_freq[word] += 1
    
    # Get top keywords (excluding common words)
    common_words = {"that", "this", "with", "from", "they", "have", "been", "were", "said", "will", "would", "could", "should"}
    keywords = [
        word for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        if word not in common_words and count > 1
    ]
    
    # Generate a simple topic label
    topic_label = _generate_topic_label(speakers, keywords, topic_id)
    
    return {
        "id": topic_id,
        "label": topic_label,
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "speakers": speakers,
        "num_segments": len(segments),
        "segments": segments,
        "keywords": keywords,
        "full_text": full_text
    }


def _generate_topic_label(speakers: List[str], keywords: List[str], topic_id: int) -> str:
    """Generate a human-readable topic label."""
    if keywords:
        main_keyword = keywords[0].title()
        if len(speakers) == 1:
            return f"{speakers[0]} discusses {main_keyword}"
        else:
            return f"Discussion about {main_keyword}"
    else:
        return f"Topic {topic_id + 1}"


def _merge_small_topics(topics: List[Dict], min_size: int) -> List[Dict]:
    """Merge topics that are too small with neighboring topics."""
    if len(topics) <= 1:
        return topics
    
    merged = []
    i = 0
    
    while i < len(topics):
        current = topics[i]
        
        if current.get("num_segments", 0) < min_size:
            # Try to merge with next topic
            if i + 1 < len(topics):
                next_topic = topics[i + 1]
                merged_topic = _merge_two_topics(current, next_topic)
                merged.append(merged_topic)
                i += 2  # Skip the next topic since we merged it
            else:
                # Last topic, merge with previous
                if merged:
                    merged[-1] = _merge_two_topics(merged[-1], current)
                else:
                    merged.append(current)
                i += 1
        else:
            merged.append(current)
            i += 1
    
    return merged


def _merge_two_topics(topic1: Dict, topic2: Dict) -> Dict:
    """Merge two topics into one."""
    segments = topic1.get("segments", []) + topic2.get("segments", [])
    
    # Recalculate timing
    start_time = min(topic1.get("start_time", 0), topic2.get("start_time", 0))
    end_time = max(topic1.get("end_time", 0), topic2.get("end_time", 0))
    
    # Merge speakers and keywords
    speakers = list(set(
        topic1.get("speakers", []) + topic2.get("speakers", [])
    ))
    
    keywords = list(set(
        topic1.get("keywords", []) + topic2.get("keywords", [])
    ))
    
    # Generate new label
    topic_label = f"Merged: {topic1.get('label', '')} + {topic2.get('label', '')}"
    
    return {
        "id": topic1.get("id", 0),
        "label": topic_label,
        "start_time": start_time,
        "end_time": end_time,
        "duration": end_time - start_time,
        "speakers": speakers,
        "num_segments": len(segments),
        "segments": segments,
        "keywords": keywords,
        "full_text": (topic1.get("full_text", "") + " " + topic2.get("full_text", "")).strip()
    }


def extract_topic_summary(topics: List[Dict], max_summary_length: int = 100) -> List[str]:
    """
    Extract brief summaries for each topic.
    
    Args:
        topics: List of topic dictionaries
        max_summary_length: Maximum length of each summary
        
    Returns:
        List of topic summary strings
    """
    summaries = []
    
    for topic in topics:
        speakers = topic.get("speakers", [])
        keywords = topic.get("keywords", [])
        duration = topic.get("duration", 0)
        
        # Create a concise summary
        if keywords:
            keyword_str = ", ".join(keywords[:3])
            speaker_str = f" ({', '.join(speakers)})" if speakers else ""
            summary = f"Discussion about {keyword_str}{speaker_str} ({duration:.1f}s)"
        else:
            speaker_str = f" by {', '.join(speakers)}" if speakers else ""
            summary = f"Topic discussion{speaker_str} ({duration:.1f}s)"
        
        # Truncate if too long
        if len(summary) > max_summary_length:
            summary = summary[:max_summary_length-3] + "..."
        
        summaries.append(summary)
    
    return summaries