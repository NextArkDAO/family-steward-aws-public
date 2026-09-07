"""Local product experience for the fictional Family Steward household."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlparse

from family_steward.memory import MemoryKind, MicroMemory
from family_steward.qmd import (
    MemorySearchResult,
    QmdCandidateProvider,
    QmdMemoryRetriever,
    load_verified_manifest,
    qmd_status,
)
from family_steward.steward import FamilySteward

DEMO_NOW = datetime(2026, 8, 24, 12, tzinfo=UTC)
MAX_REQUEST_BYTES = 8_192


def display_label(value: str) -> str:
    return value.removeprefix("fictional_").replace("_", " ").title()


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_dashboard(
    memory: MicroMemory,
    now: datetime = DEMO_NOW,
    retrieval: dict[str, str | bool] | None = None,
) -> dict[str, Any]:
    result = FamilySteward(memory).scan(now)
    active = memory.active(now)
    remembered = [event for event in active if event.kind is not MemoryKind.COMMITMENT]
    return {
        "household": "The Carter Family",
        "steward": "Aster",
        "mode": "Fictional household demo",
        "retrieval": retrieval or qmd_status(None),
        "reviewed_at": now.isoformat(),
        "summary": {
            "decisions": len(result.decisions),
            "prepared": len(result.prepared),
            "remembered": len(remembered),
        },
        "decisions": [
            {
                "decision_id": item.decision_id,
                "subject": item.subject,
                "question": item.question,
                "reason": item.reason,
                "source_event_id": item.source_event_id,
                "source": display_label(item.source),
            }
            for item in result.decisions
        ],
        "prepared": [
            {
                "label": item.detail,
                "status": "Ready",
                "detail": "Prepared quietly from known household information.",
                "subject": display_label(item.subject),
                "source": display_label(item.source),
            }
            for item in result.prepared
        ],
        "memory": [
            {
                "event_id": event.event_id,
                "kind": display_label(event.kind.value),
                "subject": event.subject,
                "value": event.value,
                "source": display_label(event.source),
                "recorded_at": event.recorded_at.isoformat(),
            }
            for event in remembered
        ],
    }


class FamilyStewardApplication:
    def __init__(self, fixture: Path) -> None:
        self.memory = MicroMemory.load_jsonl(fixture)
        self.review_lock = Lock()
        self.review_attempted = False
        self.review_result: dict[str, str] | None = None
        self.changed = False
        self.retriever: QmdMemoryRetriever | None = None
        binary = os.environ.get("FAMILY_STEWARD_QMD_BIN")
        config_dir = os.environ.get("FAMILY_STEWARD_QMD_CONFIG_DIR")
        cache_dir = os.environ.get("FAMILY_STEWARD_QMD_CACHE_DIR")
        self.retrieval_status = qmd_status(binary, config_dir, cache_dir)
        if self.retrieval_status["available"]:
            try:
                root = project_root()
                provider = QmdCandidateProvider(
                    Path(str(binary)),
                    config_dir=Path(str(config_dir)),
                    cache_dir=Path(str(cache_dir)),
                )
                manifest = load_verified_manifest(
                    root / "fixtures" / "qmd-authority-manifest.json",
                    root / "fixtures" / "qmd-corpus",
                )
                self.retriever = QmdMemoryRetriever(provider, manifest)
            except (OSError, TypeError, ValueError):
                self.retrieval_status = qmd_status("unavailable")

    def dashboard(self) -> dict[str, Any]:
        return build_dashboard(self.memory, retrieval=self.retrieval_status)

    def search_memory(self, query: str) -> dict[str, Any]:
        normalized = query.strip()
        if not normalized or len(normalized) > 500:
            raise ValueError("Ask a memory question using 1 to 500 characters.")
        if self.retriever is None:
            return MemorySearchResult(
                "unavailable",
                "Local memory search is unavailable. Aster did not guess or expose raw results.",
                (),
            ).public_dict()
        return self.retriever.search(normalized, self.memory, DEMO_NOW).public_dict()

    def approve(self, decision_id: str) -> dict[str, Any]:
        with self.review_lock:
            return self._approve(decision_id)

    def _approve(self, decision_id: str) -> dict[str, Any]:
        steward = FamilySteward(self.memory)
        decision = next(
            (
                item
                for item in steward.scan(DEMO_NOW).decisions
                if item.decision_id == decision_id
            ),
            None,
        )
        if decision is None:
            raise ValueError("decision is no longer active")
        steward.record_outcome(
            decision=decision,
            outcome_event_id=f"outcome:{decision.source_event_id}",
            outcome="Approved by the fictional household owner.",
            recorded_at=DEMO_NOW,
        )
        self.changed = True
        return self.dashboard()

    def cloud_review(self) -> dict[str, str]:
        """Review only the original fixture, at most once per server process."""
        from family_steward.hosted import review_hosted

        with self.review_lock:
            if self.changed:
                raise ValueError("Restart the demo before reviewing the original cloud snapshot.")
            if self.review_result is not None:
                return dict(self.review_result)
            if self.review_attempted:
                raise ValueError("A review was already attempted. Restart to explicitly retry.")
            self.review_attempted = True
            self.review_result = review_hosted()
            return dict(self.review_result)


def make_handler(
    application: FamilyStewardApplication, web_root: Path
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "FamilySteward/0.1"

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/dashboard":
                self._send_json(application.dashboard())
                return
            asset = "index.html" if path in {"", "/"} else path.lstrip("/")
            requested = (web_root / asset).resolve()
            if web_root.resolve() not in requested.parents and requested != web_root.resolve():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            if not requested.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content_types = {
                ".css": "text/css; charset=utf-8",
                ".html": "text/html; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
            }
            body = requested.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header(
                "Content-Type",
                content_types.get(requested.suffix, "application/octet-stream"),
            )
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/agent/review":
                if self.headers.get("X-Family-Steward-Action") != "cloud-review":
                    self._send_json(
                        {"error": "explicit cloud review confirmation required"},
                        status=HTTPStatus.FORBIDDEN,
                    )
                    return
                try:
                    self._send_json(application.cloud_review())
                except ValueError as error:
                    self._send_json({"error": str(error)}, status=HTTPStatus.CONFLICT)
                except Exception:  # Cloud failures stay private and fail closed at the UI.
                    self._send_json(
                        {"error": "Aster could not complete the cloud review."},
                        status=HTTPStatus.SERVICE_UNAVAILABLE,
                    )
                return
            if path == "/api/memory/search":
                if self.headers.get("X-Family-Steward-Action") != "memory-search":
                    self._send_json(
                        {"error": "explicit memory search confirmation required"},
                        status=HTTPStatus.FORBIDDEN,
                    )
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length <= 0 or length > MAX_REQUEST_BYTES:
                        raise ValueError("invalid request size")
                    payload = json.loads(self.rfile.read(length))
                    self._send_json(application.search_memory(str(payload["query"])))
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                    self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
                return
            if path != "/api/decisions/approve":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_REQUEST_BYTES:
                    raise ValueError("invalid request size")
                payload = json.loads(self.rfile.read(length))
                decision_id = str(payload["decision_id"])
                self._send_json(application.approve(decision_id))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Family Steward experience.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4180)
    args = parser.parse_args()
    root = project_root()
    application = FamilyStewardApplication(root / "fixtures" / "fictional_household.jsonl")
    server = ThreadingHTTPServer((args.host, args.port), make_handler(application, root / "web"))
    print(f"Family Steward is ready at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
