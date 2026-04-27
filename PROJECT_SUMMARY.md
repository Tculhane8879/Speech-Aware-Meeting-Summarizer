# Speech-Aware Meeting Summarizer - Project Summary

## What This Project Does

The **Speech-Aware Meeting Summarizer** is an intelligent system that analyzes recorded meetings and creates enhanced summaries that go beyond just transcribing words. It understands **how** people speak—their energy levels, pauses, speaking patterns, and engagement—to provide deeper insights into meeting dynamics.

## The Problem It Solves

Traditional meeting summaries only capture **what** was said, missing valuable context about **how** it was said. This system addresses that gap by:

- **Understanding speaker behavior** - Who spoke most, who seemed most engaged, who was hesitant
- **Detecting conversation flow** - How topics evolved and how speakers interacted
- **Identifying engagement patterns** - Moments of high energy vs. thoughtful pauses
- **Organizing by topics** - Automatically breaking meetings into logical segments

## How It Works (Simple Explanation)

### 1. **Listen & Transcribe**
- Uses AI (Whisper) to convert speech to text
- Identifies different speakers in the conversation

### 2. **Analyze the Sound**
- Measures **energy levels** (how loudly people speak)
- Tracks **pauses** (before and after speaking)
- Calculates **speaking patterns** and rhythms

### 3. **Find Topics**
- Automatically detects when conversation shifts to new subjects
- Groups related segments together
- Identifies key themes and keywords

### 4. **Understand Engagement**
- Scores each speaker's engagement (0-100)
- Detects active participation vs. passive listening
- Identifies moments of high energy or reflection

### 5. **Create Smart Summary**
- Combines all insights into an easy-to-read summary
- Includes speaker profiles and topic breakdown
- Shows engagement levels and conversation dynamics

## What Makes It Special

### **Beyond Words**
While most systems just transcribe, this analyzes the *acoustic features* of speech—energy, pauses, timing—to understand the emotional and engagement context.

### **Speaker Intelligence**
It doesn't just identify speakers, it understands their speaking patterns:
- Who dominates conversations?
- Who speaks thoughtfully with pauses?
- Who seems highly engaged vs. distracted?

### **Topic Awareness**
The system automatically identifies when topics change and organizes the summary accordingly, making it easy to find specific discussions.

### **Visual Timeline**
An interactive timeline shows exactly who spoke when, how topics flowed, and engagement patterns throughout the meeting.

## Real-World Applications

### **Business Meetings**
- Quickly identify who contributed most to decisions
- Understand team dynamics and engagement
- Review key topics without watching full recordings

### **Educational Settings**
- Analyze student participation patterns
- Identify moments of confusion or deep engagement
- Provide feedback on discussion dynamics

### **Research Interviews**
- Understand interviewee engagement levels
- Identify topics that generated more discussion
- Analyze conversational patterns

### **Personal Use**
- Review your own speaking patterns in meetings
- Understand your engagement levels
- Improve communication skills

## Technical Highlights

### **Advanced Speech Analysis**
- Real-time acoustic feature extraction
- HMM-inspired sequence modeling
- Multi-speaker engagement scoring

### **Smart Topic Detection**
- Content-based segmentation
- Keyword extraction and analysis
- Temporal pattern recognition

### **User-Friendly Interface**
- Plain English descriptions (no technical jargon)
- Interactive visualizations
- Audio playback integrated with analysis

### **Modular Design**
- Each component can be improved independently
- Easy to add new analysis features
- Flexible pipeline architecture

## What You Get

### **For Each Meeting**
- **Enhanced Summary** - More than just a transcript
- **Speaker Profiles** - How each person communicated
- **Topic Breakdown** - What was discussed and when
- **Engagement Scores** - Who was most/least engaged
- **Visual Timeline** - See the meeting flow at a glance

### **Technical Outputs**
- `summary.md` - Human-readable meeting summary
- `topics.json` - Structured topic analysis
- `prosody_model.json` - Detailed speech patterns
- `segments.json` - Aligned transcript with speakers

## Why This Matters

In today's remote-work world, we have more recorded meetings than ever before. But most of this valuable information remains locked away in long recordings or basic transcripts. This system unlocks that information by:

1. **Saving Time** - Get insights in minutes instead of hours
2. **Improving Communication** - Understand how teams actually interact
3. **Making Meetings Better** - Identify engagement issues and communication patterns
4. **Preserving Knowledge** - Capture not just what was said, but how it was said

## The Bottom Line

This project transforms ordinary meeting recordings into **intelligent, actionable insights** by understanding the full spectrum of human communication—words, voice, timing, and engagement. It's not just a transcription tool; it's a **meeting intelligence system** that helps teams communicate better and make the most of their time together.

---

**Perfect for:** Teams, researchers, educators, and anyone who wants to understand the deeper dynamics of their conversations.

**Technology:** Python, Whisper ASR, acoustic analysis, machine learning, web visualization

**Output:** Enhanced meeting summaries with speaker insights, topic analysis, and engagement patterns.
