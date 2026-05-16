from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    from .runner import (
        ROOT,
        WEBUI_ROOT,
        JobStore,
        RunnerError,
        check_codex,
        list_prompt_packets,
        project_snapshot,
        read_text_if_exists,
        resolve_under_root,
        build_user_guidance,
        cancel_process_job,
        run_juben_operation,
        safe_relative,
        send_process_input,
        start_codex_job,
        start_project_pipeline_job,
    )
except ImportError:  # pragma: no cover - direct script execution
    from runner import (  # type: ignore
        ROOT,
        WEBUI_ROOT,
        JobStore,
        RunnerError,
        check_codex,
        list_prompt_packets,
        project_snapshot,
        read_text_if_exists,
        resolve_under_root,
        build_user_guidance,
        cancel_process_job,
        run_juben_operation,
        safe_relative,
        send_process_input,
        start_codex_job,
        start_project_pipeline_job,
    )


STATIC_ROOT = WEBUI_ROOT / "static"
JOB_STORE = JobStore()


class JsonHandler(BaseHTTPRequestHandler):
    server_version = "JubenV3WebUI/0.1"

    def log_message(self, format: str, *args: object) -> None:
        print("[%s] %s" % (self.log_date_time_string(), format % args))

    def _send_json(self, payload: dict | list, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802 - stdlib hook
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/health":
                self._send_json({
                    "ok": True,
                    "version": "v3_webui/project-start-v1",
                    "features": ["project_start", "file_text_upload", "live_cli_output", "codex_exec"],
                    **project_snapshot(),
                })
                return
            if parsed.path == "/api/codex":
                self._send_json(check_codex())
                return
            if parsed.path == "/api/prompts":
                self._send_json(list_prompt_packets())
                return
            if parsed.path == "/api/guide":
                self._send_json(build_user_guidance())
                return
            if parsed.path == "/api/prompt":
                params = parse_qs(parsed.query)
                prompt = params.get("path", [""])[0]
                path = resolve_under_root(prompt, root=ROOT)
                self._send_json({"path": safe_relative(path, ROOT), "content": read_text_if_exists(path, limit=60000)})
                return
            if parsed.path == "/api/jobs":
                self._send_json(JOB_STORE.list())
                return
            if parsed.path.startswith("/api/jobs/"):
                job_id = parsed.path.rsplit("/", 1)[-1]
                self._send_json(JOB_STORE.read(job_id))
                return
            self._serve_static(parsed.path)
        except RunnerError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=400)
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary
            self._send_json({"ok": False, "error": str(exc)}, status=500)

    def do_POST(self) -> None:  # noqa: N802 - stdlib hook
        parsed = urlparse(self.path)
        try:
            payload = self._read_json()
            if parsed.path == "/api/juben":
                result = run_juben_operation(
                    str(payload.get("operation", "")),
                    batch_id=str(payload.get("batch_id", "")),
                    verdict=str(payload.get("verdict", "PASS")),
                    reviewer=str(payload.get("reviewer", "webui")),
                )
                self._send_json(result)
                return
            if parsed.path == "/api/codex/run":
                job = start_codex_job(
                    JOB_STORE,
                    prompt_path=str(payload.get("prompt_path", "")),
                    model=str(payload.get("model", "")),
                    profile=str(payload.get("profile", "")),
                    sandbox=str(payload.get("sandbox", "workspace-write")),
                    approval=str(payload.get("approval", "never")),
                    dry_run=bool(payload.get("dry_run", False)),
                    timeout_seconds=int(payload.get("timeout_seconds", 1800)),
                )
                self._send_json(job, status=202)
                return
            if parsed.path == "/api/project/start":
                job = start_project_pipeline_job(
                    JOB_STORE,
                    filename=str(payload.get("filename", "novel.md")),
                    novel_text=str(payload.get("novel_text", "")),
                    episodes=int(payload.get("episodes", 25)),
                    target_total_minutes=int(payload.get("target_total_minutes", 50)),
                    auto_codex=bool(payload.get("auto_codex", False)),
                )
                self._send_json(job, status=202)
                return
            if parsed.path == "/api/jobs/input":
                result = send_process_input(str(payload.get("job_id", "")), str(payload.get("text", "")))
                self._send_json(result)
                return
            if parsed.path == "/api/jobs/cancel":
                result = cancel_process_job(JOB_STORE, str(payload.get("job_id", "")))
                self._send_json(result)
                return
            self._send_json({"ok": False, "error": "not found"}, status=404)
        except RunnerError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=400)
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "invalid json"}, status=400)
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary
            self._send_json({"ok": False, "error": str(exc)}, status=500)

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        path = (STATIC_ROOT / relative).resolve()
        try:
            path.relative_to(STATIC_ROOT.resolve())
        except ValueError:
            self._send_text("not found", status=404)
            return
        if not path.exists() or not path.is_file():
            self._send_text("not found", status=404)
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Juben V3 experimental local WebUI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), JsonHandler)
    print(f"Juben V3 WebUI: http://{args.host}:{args.port}")
    print("Local-only control surface. Stop with Ctrl+C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
