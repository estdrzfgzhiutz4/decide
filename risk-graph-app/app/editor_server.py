"""Local-only editor server for scenario authoring."""

from __future__ import annotations

import json
import tempfile
import webbrowser
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from .evaluator import evaluate_scenario
from .loader import load_scenario, load_scenario_data, save_scenario, scenario_to_dict
from .renderer import render_scenario
from .validator import validate_scenario


@dataclass
class EditorService:
    """Stateful service backing editor APIs."""

    scenario_path: Path
    preview_path: Path

    def get_scenario(self) -> Dict[str, Any]:
        scenario = load_scenario(self.scenario_path)
        return scenario_to_dict(scenario)

    def load(self, path: str) -> Dict[str, Any]:
        self.scenario_path = Path(path)
        scenario = load_scenario(self.scenario_path)
        return scenario_to_dict(scenario)

    def save(self, scenario_data: Dict[str, Any], mode: str = "strict", path: Optional[str] = None) -> Dict[str, Any]:
        scenario = load_scenario_data(scenario_data)
        if mode == "draft":
            scenario.mode = "draft"
        validation = validate_scenario(scenario, mode=mode)
        if mode == "strict" and validation.errors:
            return {
                "ok": False,
                "errors": validation.errors,
                "warnings": validation.warnings,
                "draft_warnings": validation.draft_warnings,
            }
        target = Path(path) if path else self.scenario_path
        save_scenario(target, scenario)
        self.scenario_path = target
        return {
            "ok": True,
            "path": str(target),
            "errors": validation.errors,
            "warnings": validation.warnings,
            "draft_warnings": validation.draft_warnings,
        }

    def validate(self, scenario_data: Dict[str, Any], mode: str | None = None) -> Dict[str, Any]:
        scenario = load_scenario_data(scenario_data)
        result = validate_scenario(scenario, mode=mode)
        return {
            "ok": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "draft_warnings": result.draft_warnings,
            "incomplete_items": result.incomplete_items,
        }

    def evaluate(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        scenario = load_scenario_data(scenario_data)
        summary = evaluate_scenario(scenario)
        return {
            "scenario_name": summary.scenario_name,
            "skipped_incomplete_edges": summary.skipped_incomplete_edges,
            "skipped_decisions": summary.skipped_decisions,
            "assumptions": summary.assumptions,
            "decisions": [
                {
                    "id": d.decision_node_id,
                    "label": d.decision_label,
                    "catastrophic_probability": d.catastrophic_probability,
                    "positive_end_probability": d.positive_end_probability,
                    "expected_harm": d.expected_harm,
                    "score": d.composite_score,
                    "interpretation": d.interpretation,
                }
                for d in summary.decision_results
            ],
        }

    def render(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        scenario = load_scenario_data(scenario_data)
        out = render_scenario(scenario, self.preview_path.parent, fmt="svg")
        self.preview_path = out
        return {"ok": True, "preview": "/api/preview.svg", "path": str(out)}


SERVICE: Optional[EditorService] = None
ROOT_DIR = Path(__file__).resolve().parent
STATIC_DIR = ROOT_DIR / "static"


class EditorRequestHandler(BaseHTTPRequestHandler):
    """HTTP handlers for local editor operations."""

    def _json_response(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        assert SERVICE is not None
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self._serve_file(STATIC_DIR / "editor.html", "text/html; charset=utf-8")
        if parsed.path == "/static/editor.css":
            return self._serve_file(STATIC_DIR / "editor.css", "text/css; charset=utf-8")
        if parsed.path == "/static/editor.js":
            return self._serve_file(STATIC_DIR / "editor.js", "application/javascript; charset=utf-8")
        if parsed.path == "/api/scenario":
            return self._json_response({"scenario": SERVICE.get_scenario(), "path": str(SERVICE.scenario_path)})
        if parsed.path == "/api/preview.svg":
            return self._serve_file(SERVICE.preview_path, "image/svg+xml")
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        assert SERVICE is not None
        parsed = urlparse(self.path)
        payload = self._read_json()

        if parsed.path == "/api/scenario/load":
            scenario = SERVICE.load(payload["path"])
            return self._json_response({"scenario": scenario, "path": str(SERVICE.scenario_path)})
        if parsed.path == "/api/scenario/save":
            result = SERVICE.save(payload["scenario"], mode="strict", path=payload.get("path"))
            status = 200 if result.get("ok") else 400
            return self._json_response(result, status=status)
        if parsed.path == "/api/scenario/save-draft":
            result = SERVICE.save(payload["scenario"], mode="draft", path=payload.get("path"))
            return self._json_response(result)
        if parsed.path == "/api/validate":
            return self._json_response(SERVICE.validate(payload["scenario"], mode=payload.get("mode")))
        if parsed.path == "/api/evaluate":
            return self._json_response(SERVICE.evaluate(payload["scenario"]))
        if parsed.path == "/api/render":
            return self._json_response(SERVICE.render(payload["scenario"]))

        self.send_error(HTTPStatus.NOT_FOUND)


def run_editor_server(scenario_path: str, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run local editor server bound to localhost."""
    global SERVICE
    preview = Path(tempfile.gettempdir()) / "risk_graph_preview.svg"
    SERVICE = EditorService(scenario_path=Path(scenario_path), preview_path=preview)

    server = ThreadingHTTPServer((host, port), EditorRequestHandler)
    url = f"http://{host}:{port}/"
    print(f"Editor running at {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Editor stopped.")
    finally:
        server.server_close()
