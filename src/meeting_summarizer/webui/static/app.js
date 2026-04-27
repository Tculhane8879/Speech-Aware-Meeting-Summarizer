const form = document.getElementById("run-form");
const statusEl = document.getElementById("status");
const summaryEl = document.getElementById("summary-view");
const prosodyMetaEl = document.getElementById("prosody-meta");
const prosodyBodyEl = document.getElementById("prosody-body");
const sequenceMetaEl = document.getElementById("sequence-meta");
const speakerStatsBodyEl = document.getElementById("speaker-stats-body");
const transitionBodyEl = document.getElementById("transition-body");
const audioMetaEl = document.getElementById("audio-meta");
const audioPlayerEl = document.getElementById("audio-player");
const runButton = document.getElementById("run-btn");
const engagementCardsEl = document.getElementById("engagement-cards");

const inputPathEl = document.getElementById("input-path");
const outputDirEl = document.getElementById("output-dir");
const runAsrEl = document.getElementById("run-asr");
const engagementEl = document.getElementById("engagement");

// ── Helpers ──────────────────────────────────────────────────────────────────

/** "SPEAKER_0" → "Speaker 1", anything else returned as-is */
function friendlySpeaker(raw) {
  if (!raw) return "Unknown";
  const m = raw.match(/^SPEAKER_(\d+)$/i);
  return m ? `Speaker ${parseInt(m[1], 10) + 1}` : raw;
}

/** Raw state label → plain English */
const STATE_LABELS = {
  ACTIVE_SPEECH:    "Active speech",
  REFLECTIVE_PAUSE: "Thoughtful pause",
  STEADY_FLOW:      "Steady flow",
  TRANSITIONAL:     "Transitioning",
  UNKNOWN:          "—",
};
function friendlyState(raw) {
  return STATE_LABELS[raw] || raw;
}

/** Format seconds as "1.2 s" or "—" */
function fmtSec(val) {
  if (val == null) return "—";
  const n = Number(val);
  return n === 0 ? "0 s" : `${n.toFixed(2)} s`;
}

/** Render a loudness bar for an rms_mean value (0–1 scale) */
function loudnessBar(rms) {
  if (rms == null) return '<span class="no-data">—</span>';
  // Typical RMS for speech is 0.01–0.15; scale to a 0–100% bar
  const pct = Math.min(100, Math.round((Number(rms) / 0.15) * 100));
  const label = pct >= 66 ? "Loud" : pct >= 33 ? "Medium" : "Quiet";
  return `<div class="loudness-wrap">
    <div class="loudness-bar" style="width:${pct}%"></div>
    <span class="loudness-label">${label}</span>
  </div>`;
}

/** Engagement level → badge HTML */
function engagementBadge(level) {
  const map = {
    high:     { cls: "badge-high",     icon: "🔥", text: "High engagement" },
    moderate: { cls: "badge-moderate", icon: "💬", text: "Moderate engagement" },
    low:      { cls: "badge-low",      icon: "😐", text: "Low engagement" },
    minimal:  { cls: "badge-minimal",  icon: "💤", text: "Minimal engagement" },
  };
  const b = map[level] || { cls: "badge-moderate", icon: "💬", text: level };
  return `<span class="badge ${b.cls}">${b.icon} ${b.text}</span>`;
}

// ── Status ────────────────────────────────────────────────────────────────────

function setStatus(kind, text) {
  statusEl.className = `status ${kind}`;
  statusEl.textContent = text;
}

// ── Audio preview ─────────────────────────────────────────────────────────────

function setAudioPreview(data) {
  const hasAudio = Boolean(data.audio_file_exists && data.audio_preview_url);
  if (!hasAudio) {
    audioMetaEl.textContent = `Could not find audio file at: ${data.input_path}`;
    audioPlayerEl.removeAttribute("src");
    audioPlayerEl.load();
    return;
  }
  audioMetaEl.textContent = `Now playing: ${data.input_path}`;
  audioPlayerEl.src = data.audio_preview_url;
  audioPlayerEl.load();
}

// ── Prosody rows (turn-by-turn) ───────────────────────────────────────────────

function setProsodyRows(features) {
  if (!features || features.length === 0) {
    prosodyBodyEl.innerHTML = `<tr><td colspan="5" class="empty">No speech data found for this recording.</td></tr>`;
    return;
  }

  const rows = features
    .slice(0, 20)
    .map((f) => `
      <tr>
        <td>${f.segment_id + 1}</td>
        <td>${friendlySpeaker(f.speaker)}</td>
        <td>${fmtSec(f.pause_before_s)}</td>
        <td>${fmtSec(f.pause_after_s)}</td>
        <td>${loudnessBar(f.rms_mean)}</td>
      </tr>
    `)
    .join("");

  prosodyBodyEl.innerHTML = rows;
}

// ── Engagement cards ──────────────────────────────────────────────────────────

function setEngagementCards(prosodyModel) {
  if (!engagementCardsEl) return;
  const speakerEngagement = prosodyModel?.speaker_engagement || [];
  if (speakerEngagement.length === 0) {
    engagementCardsEl.innerHTML = "";
    return;
  }
  engagementCardsEl.innerHTML = speakerEngagement.map(e => `
    <div class="engagement-card">
      <div class="ec-name">${friendlySpeaker(e.speaker)}</div>
      <div class="ec-score">${e.engagement_score}<span class="ec-unit">/100</span></div>
      ${engagementBadge(e.engagement_level)}
      <div class="ec-detail">
        Active turns: ${Math.round((e.factors?.active_ratio || 0) * 100)}% &nbsp;|&nbsp;
        Thoughtful pauses: ${Math.round((e.factors?.reflective_ratio || 0) * 100)}%
      </div>
    </div>
  `).join("");
}

// ── Speaker overview table + transitions ─────────────────────────────────────

function setSequenceRows(prosodyModel) {
  if (!prosodyModel) {
    sequenceMetaEl.textContent = "No speaker data available for this run.";
    speakerStatsBodyEl.innerHTML = `<tr><td colspan="5" class="empty">No speaker data found.</td></tr>`;
    transitionBodyEl.innerHTML = `<tr><td colspan="3" class="empty">No data found.</td></tr>`;
    engagementCardsEl && (engagementCardsEl.innerHTML = "");
    return;
  }

  const speakerStats = prosodyModel.speaker_stats || [];
  const transitions = prosodyModel.sequence?.state_transition_counts || [];
  const sequenceLength = prosodyModel.sequence?.length ?? 0;
  const numSpeakers = speakerStats.length;

  sequenceMetaEl.textContent =
    `${numSpeakers} speaker${numSpeakers !== 1 ? "s" : ""} detected • ${sequenceLength} speaking turns analyzed`;

  setEngagementCards(prosodyModel);

  if (speakerStats.length === 0) {
    speakerStatsBodyEl.innerHTML = `<tr><td colspan="5" class="empty">No speaker data found.</td></tr>`;
  } else {
    speakerStatsBodyEl.innerHTML = speakerStats.map((item) => `
      <tr>
        <td><strong>${friendlySpeaker(item.speaker)}</strong></td>
        <td>${item.segment_count}</td>
        <td>${loudnessBar(item.avg_rms_mean)}</td>
        <td>${fmtSec(item.avg_pause_before_s)}</td>
        <td>${fmtSec(item.avg_pause_after_s)}</td>
      </tr>
    `).join("");
  }

  // Filter out boring UNKNOWN→UNKNOWN transitions
  const meaningful = transitions.filter(t => t.from !== "UNKNOWN" || t.to !== "UNKNOWN");
  const display = meaningful.length > 0 ? meaningful : transitions;

  if (display.length === 0) {
    transitionBodyEl.innerHTML = `<tr><td colspan="3" class="empty">No speaking style shifts detected.</td></tr>`;
  } else {
    transitionBodyEl.innerHTML = display.map((item) => `
      <tr>
        <td>${friendlyState(item.from)}</td>
        <td>→ ${friendlyState(item.to)}</td>
        <td>${item.count} time${item.count !== 1 ? "s" : ""}</td>
      </tr>
    `).join("");
  }
}

// ── Main pipeline call ────────────────────────────────────────────────────────

async function runPipeline(event) {
  event.preventDefault();
  runButton.disabled = true;
  setStatus("busy", "Analyzing your meeting… this may take a minute if transcription is enabled.");

  try {
    const payload = {
      input_path: inputPathEl.value.trim(),
      output_dir: outputDirEl.value.trim(),
      run_asr: runAsrEl.checked,
      enable_engagement: engagementEl.checked,
    };

    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || "Pipeline run failed.");
    }

    summaryEl.textContent = data.summary_text || "(No summary was generated for this run.)";

    const prosody = data.prosody;
    const prosodyModel = data.prosody_model;
    const featureCount = prosody?.features?.length ?? 0;
    const audioError = prosody?.audio_read_error;

    if (audioError) {
      prosodyMetaEl.innerHTML = `<span class="warn">${featureCount} turns found — note: ${audioError}</span>`;
    } else {
      prosodyMetaEl.textContent = `${featureCount} speaking turns analyzed`;
    }

    setProsodyRows(prosody?.features || []);
    setSequenceRows(prosodyModel);
    renderTimeline(data.aligned, data.topics, prosodyModel);
    setAudioPreview(data);
    setStatus("ok", `Analysis complete! Results saved to: ${data.output_dir}`);
  } catch (err) {
    setStatus("error", `Something went wrong: ${err.message}`);
  } finally {
    runButton.disabled = false;
  }
}

function renderTimeline(aligned, topics, prosodyModel) {
  const container = document.getElementById('timeline-container');
  const metaEl = document.getElementById('timeline-meta');
  
  if (!aligned || !aligned.segments || aligned.segments.length === 0) {
    container.innerHTML = '<div class="timeline-placeholder"><p>No timeline data available.</p></div>';
    metaEl.textContent = 'No segment data found.';
    return;
  }
  
  const segments = aligned.segments;
  const maxTime = Math.max(...segments.map(s => s.end || 0));
  
  // Create timeline HTML
  let timelineHTML = '<div class="timeline">';
  
  // Render speaker segments
  segments.forEach((segment, index) => {
    const start = segment.start || 0;
    const end = segment.end || start + 1;
    const duration = end - start;
    const speaker = segment.speaker || 'UNKNOWN';
    
    // Calculate position and width (timeline is 100% wide)
    const left = (start / maxTime) * 100;
    const width = (duration / maxTime) * 100;
    
    // Extract speaker number for styling
    const speakerMatch = speaker.match(/SPEAKER_(\d+)/);
    const speakerNum = speakerMatch ? parseInt(speakerMatch[1]) : 0;
    
    // Create segment
    timelineHTML += `
      <div class="timeline-segment speaker-${speakerNum}" 
           style="left: ${left}%; width: ${width}%; top: ${speakerNum * 35}px;"
           title="${speaker}: ${segment.text ? segment.text.substring(0, 50) + '...' : 'No text'} (${start.toFixed(1)}s - ${end.toFixed(1)}s)">
        ${speaker}
      </div>
    `;
  });
  
  timelineHTML += '</div>';
  
  // Add time labels
  timelineHTML += '<div class="timeline-labels">';
  for (let i = 0; i <= 4; i++) {
    const time = (maxTime * i / 4).toFixed(0);
    timelineHTML += `<span>${time}s</span>`;
  }
  timelineHTML += '</div>';
  
  // Add legend
  const speakers = [...new Set(segments.map(s => s.speaker || 'UNKNOWN'))];
  if (speakers.length > 1) {
    timelineHTML += '<div class="timeline-legend">';
    speakers.forEach((speaker, index) => {
      const speakerMatch = speaker.match(/SPEAKER_(\d+)/);
      const speakerNum = speakerMatch ? parseInt(speakerMatch[1]) : index;
      timelineHTML += `
        <div class="legend-item">
          <div class="legend-color" style="background: linear-gradient(135deg, ${getSpeakerColor(speakerNum)} 0%, ${getSpeakerColor(speakerNum, true)} 100%);"></div>
          <span>${speaker}</span>
        </div>
      `;
    });
    timelineHTML += '</div>';
  }
  
  container.innerHTML = timelineHTML;
  metaEl.textContent = `${segments.length} segments over ${maxTime.toFixed(1)} seconds`;
}

function getSpeakerColor(speakerNum, dark = false) {
  const colors = [
    ['#667eea', '#764ba2'],
    ['#f093fb', '#f5576c'],
    ['#4facfe', '#00f2fe'],
    ['#43e97b', '#38f9d7']
  ];
  return colors[speakerNum % colors.length][dark ? 1 : 0];
}

form.addEventListener("submit", runPipeline);
