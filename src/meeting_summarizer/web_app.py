from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote

from flask import Flask, jsonify, render_template, request, send_file

from meeting_summarizer.pipeline import run_pipeline

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = BASE_DIR.parent.parent
TEMPLATES_DIR = BASE_DIR / "webui" / "templates"
STATIC_DIR = BASE_DIR / "webui" / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR),
    static_url_path="/static",
)


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def _resolve_audio_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = WORKSPACE_ROOT / path
    return path.resolve()


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/audio")
def audio_file():
    raw_path = (request.args.get("path") or "").strip()
    if not raw_path:
        return jsonify({"ok": False, "error": "Missing 'path' query parameter."}), 400

    audio_path = _resolve_audio_path(raw_path)
    if not audio_path.exists() or not audio_path.is_file():
        return jsonify({"ok": False, "error": f"Audio file not found: {raw_path}"}), 404

    guessed_type = mimetypes.guess_type(str(audio_path))[0] or "application/octet-stream"
    return send_file(str(audio_path), mimetype=guessed_type, conditional=True)


@app.post("/api/run")
def run_pipeline_api():
    payload = request.get_json(silent=True) or {}

    input_path = Path(payload.get("input_path") or "data/raw/sample.wav")
    output_dir = Path(payload.get("output_dir") or "outputs/web_run")
    run_asr = _as_bool(payload.get("run_asr"), default=False)
    enable_engagement = _as_bool(payload.get("enable_engagement"), default=False)

    try:
        result = run_pipeline(
            input_path=input_path,
            output_dir=output_dir,
            run_asr=run_asr,
            enable_engagement=enable_engagement,
        )
    except Exception as exc:  # pragma: no cover - API error formatting
        return jsonify({"ok": False, "error": str(exc)}), 400

    summary_path = output_dir / "summary.md"
    prosody_path = output_dir / "prosody.json"
    prosody_model_path = output_dir / "prosody_model.json"
    segments_path = output_dir / "segments.json"

    summary_text = summary_path.read_text(encoding="utf-8") if summary_path.exists() else result.summary_text

    prosody: Dict[str, Any] | None = None
    if prosody_path.exists():
        prosody = json.loads(prosody_path.read_text(encoding="utf-8"))

    prosody_model: Dict[str, Any] | None = None
    if prosody_model_path.exists():
        prosody_model = json.loads(prosody_model_path.read_text(encoding="utf-8"))

    resolved_input_path = _resolve_audio_path(str(input_path))
    audio_exists = resolved_input_path.exists() and resolved_input_path.is_file()

    response = {
        "ok": True,
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "summary_text": summary_text,
        "run_asr": run_asr,
        "enable_engagement": enable_engagement,
        "audio_file_exists": audio_exists,
        "audio_preview_url": f"/api/audio?path={quote(str(input_path))}" if audio_exists else None,
        "files": {
            "summary_md": summary_path.exists(),
            "prosody_json": prosody_path.exists(),
            "prosody_model_json": prosody_model_path.exists(),
            "segments_json": segments_path.exists(),
        },
        "prosody": prosody,
        "prosody_model": prosody_model,
    }
    return jsonify(response)


def main() -> None:
    app.run(host="127.0.0.1", port=8000, debug=True)


if __name__ == "__main__":
    main()
