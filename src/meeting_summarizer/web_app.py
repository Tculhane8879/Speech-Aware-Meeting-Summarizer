from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request

from meeting_summarizer.pipeline import run_pipeline

BASE_DIR = Path(__file__).resolve().parent
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


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


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
    segments_path = output_dir / "segments.json"

    summary_text = summary_path.read_text(encoding="utf-8") if summary_path.exists() else result.summary_text

    prosody: Dict[str, Any] | None = None
    if prosody_path.exists():
        prosody = __import__("json").loads(prosody_path.read_text(encoding="utf-8"))

    response = {
        "ok": True,
        "output_dir": str(output_dir),
        "summary_text": summary_text,
        "run_asr": run_asr,
        "enable_engagement": enable_engagement,
        "files": {
            "summary_md": summary_path.exists(),
            "prosody_json": prosody_path.exists(),
            "segments_json": segments_path.exists(),
        },
        "prosody": prosody,
    }
    return jsonify(response)


def main() -> None:
    app.run(host="127.0.0.1", port=8000, debug=True)


if __name__ == "__main__":
    main()
