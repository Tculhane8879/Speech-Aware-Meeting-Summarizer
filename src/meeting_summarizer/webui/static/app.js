const form = document.getElementById("run-form");
const statusEl = document.getElementById("status");
const summaryEl = document.getElementById("summary-view");
const prosodyMetaEl = document.getElementById("prosody-meta");
const prosodyBodyEl = document.getElementById("prosody-body");
const runButton = document.getElementById("run-btn");

const inputPathEl = document.getElementById("input-path");
const outputDirEl = document.getElementById("output-dir");
const runAsrEl = document.getElementById("run-asr");
const engagementEl = document.getElementById("engagement");

function setStatus(kind, text) {
  statusEl.className = `status ${kind}`;
  statusEl.textContent = text;
}

function setProsodyRows(features) {
  if (!features || features.length === 0) {
    prosodyBodyEl.innerHTML = `
      <tr>
        <td colspan="5" class="empty">No segment-level prosody features were generated for this run.</td>
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

async function runPipeline(event) {
  event.preventDefault();
  runButton.disabled = true;
  setStatus("busy", "Running pipeline... if ASR is enabled, first run can take a while.");

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

    summaryEl.textContent = data.summary_text || "(No summary generated)";

    const prosody = data.prosody;
    const featureCount = prosody?.features?.length ?? 0;
    const sampleRate = prosody?.sample_rate_hz ?? "unknown";
    const audioError = prosody?.audio_read_error;

    prosodyMetaEl.textContent = audioError
      ? `Features: ${featureCount} • sample rate: ${sampleRate} • audio read warning: ${audioError}`
      : `Features: ${featureCount} • sample rate: ${sampleRate} • method: ${prosody?.method ?? "n/a"}`;

    setProsodyRows(prosody?.features || []);
    setStatus("ok", `Done. Outputs written to ${data.output_dir}`);
  } catch (err) {
    setStatus("error", `Error: ${err.message}`);
  } finally {
    runButton.disabled = false;
  }
}

form.addEventListener("submit", runPipeline);
