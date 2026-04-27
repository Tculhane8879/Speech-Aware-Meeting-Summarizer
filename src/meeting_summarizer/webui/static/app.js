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

const inputPathEl = document.getElementById("input-path");
const outputDirEl = document.getElementById("output-dir");
const runAsrEl = document.getElementById("run-asr");
const engagementEl = document.getElementById("engagement");

function setStatus(kind, text) {
  statusEl.className = `status ${kind}`;
  statusEl.textContent = text;
}

function setAudioPreview(data) {
  const hasAudio = Boolean(data.audio_file_exists && data.audio_preview_url);
  if (!hasAudio) {
    audioMetaEl.textContent = `Could not find audio file at: ${data.input_path}`;
    audioPlayerEl.removeAttribute("src");
    audioPlayerEl.load();
    return;
  }

  audioMetaEl.textContent = `Playing: ${data.input_path}`;
  audioPlayerEl.src = data.audio_preview_url;
  audioPlayerEl.load();
}

function setProsodyRows(features) {
  if (!features || features.length === 0) {
    prosodyBodyEl.innerHTML = `
      <tr>
        <td colspan="5" class="empty">No speech data was found for this recording.</td>
      </tr>
    `;
    return;
  }

  const rows = features
    .slice(0, 12)
    .map((f) => {
      const pauseBefore = Number(f.pause_before_s ?? 0).toFixed(2);
      const pauseAfter = Number(f.pause_after_s ?? 0).toFixed(2);
      const rms =
        f.rms_mean === null || f.rms_mean === undefined
          ? "null"
          : Number(f.rms_mean).toFixed(4);
      return `
        <tr>
          <td>${f.segment_id}</td>
          <td>${f.speaker}</td>
          <td>${pauseBefore}</td>
          <td>${pauseAfter}</td>
          <td>${rms}</td>
        </tr>
      `;
    })
    .join("");

  prosodyBodyEl.innerHTML = rows;
}

function setSequenceRows(prosodyModel) {
  if (!prosodyModel) {
    sequenceMetaEl.textContent = "No speaker pattern data available for this run.";
    speakerStatsBodyEl.innerHTML = `
      <tr><td colspan="5" class="empty">No speaker data found.</td></tr>
    `;
    transitionBodyEl.innerHTML = `
      <tr><td colspan="3" class="empty">No pattern data found.</td></tr>
    `;
    return;
  }

  const speakerStats = prosodyModel.speaker_stats || [];
  const transitions = prosodyModel.sequence?.state_transition_counts || [];
  const sequenceLength = prosodyModel.sequence?.length ?? 0;

  sequenceMetaEl.textContent = `${sequenceLength} speaking turns analyzed`;

  if (speakerStats.length === 0) {
    speakerStatsBodyEl.innerHTML = `
      <tr><td colspan="5" class="empty">No speaker data found.</td></tr>
    `;
  } else {
    speakerStatsBodyEl.innerHTML = speakerStats
      .map((item) => {
        const rms = item.avg_rms_mean == null ? "null" : Number(item.avg_rms_mean).toFixed(4);
        const pb = item.avg_pause_before_s == null ? "null" : Number(item.avg_pause_before_s).toFixed(2);
        const pa = item.avg_pause_after_s == null ? "null" : Number(item.avg_pause_after_s).toFixed(2);
        return `
          <tr>
            <td>${item.speaker}</td>
            <td>${item.segment_count}</td>
            <td>${rms}</td>
            <td>${pb}</td>
            <td>${pa}</td>
          </tr>
        `;
      })
      .join("");
  }

  if (transitions.length === 0) {
    transitionBodyEl.innerHTML = `
      <tr><td colspan="3" class="empty">No speaking style shifts detected.</td></tr>
    `;
  } else {
    transitionBodyEl.innerHTML = transitions
      .map((item) => {
        return `
          <tr>
            <td>${item.from}</td>
            <td>${item.to}</td>
            <td>${item.count}</td>
          </tr>
        `;
      })
      .join("");
  }
}

async function runPipeline(event) {
  event.preventDefault();
  runButton.disabled = true;
  setStatus("busy", "Analyzing your meeting... this may take a minute if transcription is enabled.");

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

    summaryEl.textContent = data.summary_text || "(No summary was generated for this run.)"

    const prosody = data.prosody;
    const prosodyModel = data.prosody_model;
    const featureCount = prosody?.features?.length ?? 0;
    const sampleRate = prosody?.sample_rate_hz ?? "unknown";
    const audioError = prosody?.audio_read_error;

    prosodyMetaEl.textContent = audioError
      ? `${featureCount} speech segments analyzed • sample rate: ${sampleRate} Hz • note: ${audioError}`
      : `${featureCount} speech segments analyzed • sample rate: ${sampleRate} Hz`;

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
