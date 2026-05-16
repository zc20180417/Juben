from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WEBUI_ROOT = Path(__file__).resolve().parent
DEFAULT_JUBEN_ROOT = ROOT / "juben"
RUNTIME_ROOT = WEBUI_ROOT / "runtime"
JOB_ROOT = RUNTIME_ROOT / "jobs"
NOVEL_INPUT_ROOT = DEFAULT_JUBEN_ROOT

DEFAULT_CODEX_TIMEOUT_SECONDS = 1800
DEFAULT_COMMAND_TIMEOUT_SECONDS = 120
GUIDE_COMMAND_TIMEOUT_SECONDS = 8


class RunnerError(ValueError):
    """Raised for invalid WebUI runner input."""


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_relative(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path)


def resolve_under_root(raw_path: str, *, root: Path = ROOT) -> Path:
    if not raw_path:
        raise RunnerError("path is required")
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise RunnerError(f"path escapes workspace: {raw_path}") from exc
    return resolved


def read_text_if_exists(path: Path, limit: int = 20000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit] + "\n...[truncated]..."
    return text


def command_to_display(command: list[str]) -> str:
    return " ".join(command)


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "command_display": command_to_display(self.command),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


def run_process(
    command: list[str],
    *,
    cwd: Path = ROOT,
    timeout: int = DEFAULT_COMMAND_TIMEOUT_SECONDS,
    input_text: str | None = None,
) -> CommandResult:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    popen_command = command
    # On Windows, npm-shimmed CLIs often resolve to .cmd files. Python 3.14 may
    # refuse to CreateProcess them directly, so run only those shims through cmd.
    if os.name == "nt" and command and command[0].lower() == "codex":
        popen_command = ["cmd", "/d", "/s", "/c", *command]
    proc = subprocess.run(
        popen_command,
        cwd=str(cwd),
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=env,
    )
    return CommandResult(command=command, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def check_codex() -> dict[str, Any]:
    executable = shutil.which("codex")
    if not executable:
        return {"available": False, "path": "", "version": "", "error": "codex not found in PATH"}
    try:
        result = run_process(["codex", "--version"], timeout=20)
    except Exception as exc:  # pragma: no cover - platform-specific failure
        return {"available": False, "path": executable, "version": "", "error": str(exc)}
    version = (result.stdout or result.stderr).strip()
    return {
        "available": result.returncode == 0,
        "path": executable,
        "version": version,
        "error": "" if result.returncode == 0 else result.stderr.strip(),
    }


def juben_command(args: list[str]) -> list[str]:
    return [sys.executable, "-m", "juben", *args]


JUBEN_OPERATION_ARGS: dict[str, list[str]] = {
    "status": ["status"],
    "next": ["next"],
    "extract": ["extract-book"],
    "map": ["map-book"],
    "export": ["export"],
}


def build_juben_operation(operation: str, batch_id: str = "", verdict: str = "PASS", reviewer: str = "webui") -> list[str]:
    if operation in JUBEN_OPERATION_ARGS:
        return juben_command(JUBEN_OPERATION_ARGS[operation])
    if operation in {"start_prepare", "start_write", "check", "run", "record", "polish", "review_done"}:
        normalized_batch = batch_id.strip()
        if not normalized_batch:
            raise RunnerError("batch_id is required for this operation")
        if operation == "start_prepare":
            return juben_command(["start", normalized_batch, "--prepare-only"])
        if operation == "start_write":
            return juben_command(["start", normalized_batch, "--write"])
        if operation == "check":
            return juben_command(["check", normalized_batch])
        if operation == "run":
            return juben_command(["run", normalized_batch])
        if operation == "record":
            return juben_command(["record", normalized_batch])
        if operation == "polish":
            return juben_command(["polish", normalized_batch])
        if operation == "review_done":
            clean_verdict = verdict.strip().upper()
            if clean_verdict not in {"PASS", "FAIL"}:
                raise RunnerError("verdict must be PASS or FAIL")
            clean_reviewer = reviewer.strip() or "webui"
            return juben_command(["batch-review-done", normalized_batch, clean_verdict, "--reviewer", clean_reviewer])
    raise RunnerError(f"unsupported operation: {operation}")


def run_juben_operation(operation: str, batch_id: str = "", verdict: str = "PASS", reviewer: str = "webui") -> dict[str, Any]:
    command = build_juben_operation(operation, batch_id=batch_id, verdict=verdict, reviewer=reviewer)
    result = run_process(command, cwd=ROOT, timeout=DEFAULT_COMMAND_TIMEOUT_SECONDS)
    return result.to_dict()


def list_prompt_packets() -> list[dict[str, Any]]:
    roots = [
        DEFAULT_JUBEN_ROOT / "harness" / "project" / "prompts",
        DEFAULT_JUBEN_ROOT / "harness" / "project" / "reviews",
        DEFAULT_JUBEN_ROOT / "output" / "_runtime" / "prompts",
        DEFAULT_JUBEN_ROOT / "output" / "_runtime" / "reviews",
    ]
    seen: set[Path] = set()
    packets: list[dict[str, Any]] = []
    for prompt_root in roots:
        if not prompt_root.exists():
            continue
        for path in sorted(prompt_root.rglob("*.md")):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            stat = path.stat()
            packets.append(
                {
                    "path": safe_relative(path, ROOT),
                    "name": path.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                }
            )
    return packets


class JobStore:
    def __init__(self, root: Path = JOB_ROOT) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._active_job_id: str | None = None

    def _job_dir(self, job_id: str) -> Path:
        return self.root / job_id

    def _metadata_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "job.json"

    def create(self, payload: dict[str, Any]) -> str:
        with self._lock:
            if self._active_job_id:
                raise RunnerError(f"job already running: {self._active_job_id}")
            job_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
            job_dir = self._job_dir(job_id)
            job_dir.mkdir(parents=True, exist_ok=False)
            metadata = {
                "id": job_id,
                "status": "queued",
                "created_at": utc_now(),
                "updated_at": utc_now(),
                **payload,
            }
            self._write_metadata(job_id, metadata)
            self._active_job_id = job_id
            return job_id

    def finish(self, job_id: str) -> None:
        with self._lock:
            if self._active_job_id == job_id:
                self._active_job_id = None

    def _write_metadata(self, job_id: str, metadata: dict[str, Any]) -> None:
        metadata["updated_at"] = utc_now()
        self._metadata_path(job_id).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    def update(self, job_id: str, **fields: Any) -> dict[str, Any]:
        metadata = self.read(job_id)
        metadata.update(fields)
        self._write_metadata(job_id, metadata)
        return metadata

    def read(self, job_id: str) -> dict[str, Any]:
        path = self._metadata_path(job_id)
        if not path.exists():
            raise RunnerError(f"job not found: {job_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def list(self) -> list[dict[str, Any]]:
        jobs = []
        if not self.root.exists():
            return jobs
        for path in sorted(self.root.glob("*/job.json"), reverse=True):
            try:
                jobs.append(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
        return jobs

    def output_paths(self, job_id: str) -> tuple[Path, Path]:
        job_dir = self._job_dir(job_id)
        return job_dir / "stdout.log", job_dir / "stderr.log"

    def combined_log_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "combined.log"


PROCESS_REGISTRY: dict[str, subprocess.Popen[str]] = {}
PROCESS_REGISTRY_LOCK = threading.Lock()


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", name).strip(" ._")
    if not cleaned:
        cleaned = "novel"
    if not cleaned.lower().endswith((".md", ".txt")):
        cleaned += ".md"
    return cleaned[:120]


def build_codex_exec_command(
    *,
    model: str = "",
    profile: str = "",
    sandbox: str = "workspace-write",
    approval: str = "never",
    output_last_message: Path | None = None,
) -> list[str]:
    if sandbox not in {"read-only", "workspace-write", "danger-full-access"}:
        raise RunnerError("unsupported sandbox")
    if approval not in {"untrusted", "on-request", "on-failure", "never"}:
        raise RunnerError("unsupported approval policy")
    # `codex exec` does not expose the interactive `-a/--ask-for-approval`
    # flag in current CLI builds. Keep approval in job metadata, but do not
    # pass it to the process.
    command = ["codex", "exec", "-C", str(ROOT), "-s", sandbox]
    if model.strip():
        command.extend(["-m", model.strip()])
    if profile.strip():
        command.extend(["-p", profile.strip()])
    if output_last_message is not None:
        command.extend(["-o", str(output_last_message)])
    command.append("-")
    return command


def start_codex_job(
    store: JobStore,
    *,
    prompt_path: str,
    model: str = "",
    profile: str = "",
    sandbox: str = "workspace-write",
    approval: str = "never",
    dry_run: bool = False,
    timeout_seconds: int = DEFAULT_CODEX_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    resolved_prompt = resolve_under_root(prompt_path, root=ROOT)
    if not resolved_prompt.exists() or not resolved_prompt.is_file():
        raise RunnerError(f"prompt file not found: {prompt_path}")
    prompt_text = resolved_prompt.read_text(encoding="utf-8", errors="replace")
    output_last_message = store.root / "_pending_last_message.txt"
    command = build_codex_exec_command(
        model=model,
        profile=profile,
        sandbox=sandbox,
        approval=approval,
        output_last_message=output_last_message,
    )
    job_id = store.create(
        {
            "type": "codex_exec",
            "status": "dry_run" if dry_run else "queued",
            "prompt_path": safe_relative(resolved_prompt, ROOT),
            "prompt_size": len(prompt_text),
            "command": command,
            "command_display": command_to_display(command),
            "model": model,
            "profile": profile,
            "sandbox": sandbox,
            "approval": approval,
            "dry_run": dry_run,
        }
    )
    final_last_message = store._job_dir(job_id) / "last-message.txt"
    command = build_codex_exec_command(
        model=model,
        profile=profile,
        sandbox=sandbox,
        approval=approval,
        output_last_message=final_last_message,
    )
    store.update(job_id, command=command, command_display=command_to_display(command))
    if dry_run:
        store.finish(job_id)
        return store.read(job_id)

    thread = threading.Thread(
        target=_run_codex_job_thread,
        args=(store, job_id, command, prompt_text, timeout_seconds),
        daemon=True,
    )
    thread.start()
    return store.read(job_id)


def save_novel_input(*, filename: str, novel_text: str) -> Path:
    if not novel_text.strip():
        raise RunnerError("novel_text is required")
    NOVEL_INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    safe_name = "__webui_input_" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + _safe_filename(filename)
    path = NOVEL_INPUT_ROOT / safe_name
    path.write_text(novel_text, encoding="utf-8")
    return path


def start_project_pipeline_job(
    store: JobStore,
    *,
    filename: str,
    novel_text: str,
    episodes: int,
    target_total_minutes: int,
    auto_codex: bool = False,
) -> dict[str, Any]:
    if episodes <= 0 or episodes > 300:
        raise RunnerError("episodes must be between 1 and 300")
    if target_total_minutes <= 0 or target_total_minutes > 1000:
        raise RunnerError("target_total_minutes must be between 1 and 1000")
    novel_path = save_novel_input(filename=filename, novel_text=novel_text)
    novel_rel_to_juben = novel_path.relative_to(DEFAULT_JUBEN_ROOT).as_posix()
    allow_auto_codex = auto_codex and os.environ.get("JUBEN_WEBUI_ALLOW_AUTO_CODEX") == "1"
    command = [
        sys.executable,
        "-m",
        "v3_webui.pipeline_cli",
        "--novel",
        novel_rel_to_juben,
        "--episodes",
        str(episodes),
        "--target-total-minutes",
        str(target_total_minutes),
    ]
    if allow_auto_codex:
        command.append("--auto-codex")

    job_id = store.create(
        {
            "type": "project_pipeline",
            "status": "queued",
            "novel_path": safe_relative(novel_path, ROOT),
            "episodes": episodes,
            "target_total_minutes": target_total_minutes,
            "auto_codex_requested": auto_codex,
            "auto_codex": allow_auto_codex,
            "auto_codex_disabled_reason": ""
            if allow_auto_codex or not auto_codex
            else "disabled by default; set JUBEN_WEBUI_ALLOW_AUTO_CODEX=1 for experimental CLI automation",
            "command": command,
            "command_display": command_to_display(command),
        }
    )
    thread = threading.Thread(
        target=_run_interactive_process_thread,
        args=(store, job_id, command),
        daemon=True,
    )
    thread.start()
    return store.read(job_id)


def _run_interactive_process_thread(store: JobStore, job_id: str, command: list[str]) -> None:
    stdout_path, stderr_path = store.output_paths(job_id)
    combined_path = store.combined_log_path(job_id)
    store.update(
        job_id,
        status="running",
        started_at=utc_now(),
        stdout_path=safe_relative(stdout_path, ROOT),
        stderr_path=safe_relative(stderr_path, ROOT),
        combined_log_path=safe_relative(combined_path, ROOT),
    )
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    proc = subprocess.Popen(
        command,
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )
    with PROCESS_REGISTRY_LOCK:
        PROCESS_REGISTRY[job_id] = proc
    tail = ""
    try:
        assert proc.stdout is not None
        with combined_path.open("w", encoding="utf-8", errors="replace") as combined:
            for line in proc.stdout:
                combined.write(line)
                combined.flush()
                tail = (tail + line)[-8000:]
                store.update(job_id, stdout_tail=tail)
        rc = proc.wait()
        stdout_path.write_text(tail, encoding="utf-8", errors="replace")
        stderr_path.write_text("", encoding="utf-8")
        store.update(
            job_id,
            status="succeeded" if rc == 0 else "failed",
            returncode=rc,
            stdout_tail=tail,
            finished_at=utc_now(),
        )
    except Exception as exc:  # pragma: no cover - defensive background failure handling
        store.update(job_id, status="failed", error=str(exc), stdout_tail=tail, finished_at=utc_now())
    finally:
        with PROCESS_REGISTRY_LOCK:
            PROCESS_REGISTRY.pop(job_id, None)
        store.finish(job_id)


def send_process_input(job_id: str, text: str) -> dict[str, Any]:
    if not text:
        raise RunnerError("input text is required")
    with PROCESS_REGISTRY_LOCK:
        proc = PROCESS_REGISTRY.get(job_id)
    if proc is None or proc.stdin is None or proc.poll() is not None:
        raise RunnerError("job is not running or does not accept input")
    proc.stdin.write(text + "\n")
    proc.stdin.flush()
    return {"ok": True, "job_id": job_id}


def cancel_process_job(store: JobStore, job_id: str) -> dict[str, Any]:
    with PROCESS_REGISTRY_LOCK:
        proc = PROCESS_REGISTRY.get(job_id)
    if proc is None or proc.poll() is not None:
        raise RunnerError("job is not running")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    store.update(job_id, status="cancelled", returncode=proc.returncode, finished_at=utc_now())
    store.finish(job_id)
    with PROCESS_REGISTRY_LOCK:
        PROCESS_REGISTRY.pop(job_id, None)
    return {"ok": True, "job_id": job_id, "status": "cancelled"}


def _run_codex_job_thread(
    store: JobStore,
    job_id: str,
    command: list[str],
    prompt_text: str,
    timeout_seconds: int,
) -> None:
    stdout_path, stderr_path = store.output_paths(job_id)
    store.update(job_id, status="running", started_at=utc_now())
    try:
        result = run_process(command, cwd=ROOT, input_text=prompt_text, timeout=timeout_seconds)
        stdout_path.write_text(result.stdout, encoding="utf-8", errors="replace")
        stderr_path.write_text(result.stderr, encoding="utf-8", errors="replace")
        store.update(
            job_id,
            status="succeeded" if result.returncode == 0 else "failed",
            returncode=result.returncode,
            stdout_path=safe_relative(stdout_path, ROOT),
            stderr_path=safe_relative(stderr_path, ROOT),
            stdout_tail=result.stdout[-4000:],
            stderr_tail=result.stderr[-4000:],
            finished_at=utc_now(),
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stdout_path.write_text(stdout, encoding="utf-8", errors="replace")
        stderr_path.write_text(stderr, encoding="utf-8", errors="replace")
        store.update(
            job_id,
            status="timeout",
            error=f"timeout after {timeout_seconds}s",
            stdout_path=safe_relative(stdout_path, ROOT),
            stderr_path=safe_relative(stderr_path, ROOT),
            stdout_tail=stdout[-4000:],
            stderr_tail=stderr[-4000:],
            finished_at=utc_now(),
        )
    except Exception as exc:  # pragma: no cover - defensive background failure handling
        store.update(job_id, status="failed", error=str(exc), finished_at=utc_now())
    finally:
        store.finish(job_id)


def project_snapshot() -> dict[str, Any]:
    return {
        "workspace": str(ROOT),
        "juben_root": str(DEFAULT_JUBEN_ROOT),
        "codex": check_codex(),
        "prompts": list_prompt_packets(),
    }


def _output_manifest() -> dict[str, Any]:
    path = DEFAULT_JUBEN_ROOT / "output" / "manifest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {}


def _base_guidance_payload(
    *,
    state: str,
    title: str,
    summary: str,
    primary_action: str,
    recommended_buttons: list[str],
    can_run_codex: bool,
    warning: str = "",
    raw: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_dir = DEFAULT_JUBEN_ROOT / "output"
    episodes_dir = output_dir / "episodes"
    manifest = _output_manifest()
    manifest_counts = manifest.get("counts", {}) if isinstance(manifest.get("counts", {}), dict) else {}
    completed_episode_count = int(manifest_counts.get("episodes") or 0)
    if completed_episode_count <= 0 and episodes_dir.exists():
        completed_episode_count = len(list(episodes_dir.glob("EP-*.md")))

    return {
        "state": state,
        "title": title,
        "summary": summary,
        "primary_action": primary_action,
        "recommended_buttons": recommended_buttons,
        "can_run_codex": can_run_codex,
        "warning": warning,
        "paths": {
            "output": safe_relative(output_dir, ROOT),
            "episodes": safe_relative(episodes_dir, ROOT),
            "prompts": safe_relative(DEFAULT_JUBEN_ROOT / "harness" / "project" / "prompts", ROOT),
        },
        "counts": {
            "episodes": completed_episode_count,
            "prompts": len(list_prompt_packets()),
        },
        "raw": raw or {},
    }


def build_user_guidance() -> dict[str, Any]:
    """Return a human-facing workflow summary for the WebUI.

    The existing controller output is intentionally preserved for debugging,
    but the WebUI needs a smaller answer: what state are we in, and what should
    the user do next.
    """
    manifest = _output_manifest()
    if manifest.get("run_status") == "complete":
        return _base_guidance_payload(
            state="complete",
            title="已完成：现在不要启动 Codex",
            summary=f"当前项目已经生成 {manifest.get('counts', {}).get('episodes', 0)} 集成品。",
            primary_action="只需要打开 juben/output/episodes 看剧本；如果要刷新交付目录，点“刷新交付目录”。",
            recommended_buttons=["export"],
            can_run_codex=False,
            raw={"manifest": manifest},
        )

    try:
        status_result = run_process(juben_command(["status"]), cwd=ROOT, timeout=GUIDE_COMMAND_TIMEOUT_SECONDS)
        next_result = run_process(juben_command(["next"]), cwd=ROOT, timeout=GUIDE_COMMAND_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return _base_guidance_payload(
            state="error",
            title="状态判断超时",
            summary="WebUI 没能在 8 秒内读完 Juben 状态。",
            primary_action="这通常不影响已有成品；先看 output/episodes，或重启 WebUI 后再试。",
            recommended_buttons=["status", "next"],
            can_run_codex=False,
            warning="guide command timeout",
        )
    status_text = status_result.stdout
    next_text = next_result.stdout

    state = "unknown"
    title = "还不能判断下一步"
    summary = "WebUI 已连接项目，但没有识别出明确阶段。"
    primary_action = "先点“查看下一步”；如果仍看不懂，把调试输出发给开发者。"
    recommended_buttons = ["status", "next"]
    can_run_codex = False
    warning = ""

    if "Source map not ready" in next_text:
        state = "source_map_pending"
        title = "分集表还没完成：不要开始写剧本"
        summary = "当前项目还没有可用 batch。先完成 book.blueprint.md，再生成 source.map.md。"
        primary_action = "如果已有 extract-book.prompt.md，先执行它；完成后再执行 map-book.prompt.md。"
        recommended_buttons = ["extract", "map", "next"]
        can_run_codex = True
    elif "run_status:   complete" in status_text or "production complete" in next_text:
        state = "complete"
        title = "已完成：现在不要启动 Codex"
        summary = "当前项目已有成品。此时不需要选 prompt，也不需要启动 Codex。"
        primary_action = "只需要打开 juben/output/episodes 看剧本；如果要刷新交付目录，点“刷新交付目录”。"
        recommended_buttons = ["export", "status"]
        can_run_codex = False
    elif "batch review pending verdict" in next_text or "review pending" in next_text:
        state = "review_pending"
        title = "等待人工审稿结论"
        summary = "草稿已经生成，下一步不是继续写，而是按 review prompt 审稿并封板 PASS/FAIL。"
        primary_action = "打开对应 review prompt 审稿；通过后在项目控制区执行 review_done，再 run/record。"
        recommended_buttons = ["check", "run", "record"]
        can_run_codex = False
    elif "Next Batch:" in next_text:
        state = "next_batch"
        title = "可以开始下一批生成"
        summary = "主流程正在等待下一个 batch。先 prepare/write packet，再把 writer prompt 交给 Codex 执行。"
        primary_action = "先点 prepare 或 write packet；生成 prompt 后再使用 Codex Runner。"
        recommended_buttons = ["start_prepare", "start_write"]
        can_run_codex = True
    elif "Prompt packet ready" in status_text or "Prompt:" in next_text:
        state = "prompt_ready"
        title = "已有 prompt packet 等待执行"
        summary = "现在才需要选择 prompt，并用 Codex Runner 执行。"
        primary_action = "先预览 prompt；确认无误后取消 Dry run，启动 Codex job。"
        recommended_buttons = ["next"]
        can_run_codex = True
    elif status_result.returncode != 0 or next_result.returncode != 0:
        state = "error"
        title = "项目状态命令执行失败"
        summary = "WebUI 能启动，但 Juben 状态命令返回错误。"
        primary_action = "查看调试输出，先修复主流程命令。"
        recommended_buttons = ["status", "next"]
        can_run_codex = False
        warning = (status_result.stderr or next_result.stderr).strip()

    return _base_guidance_payload(
        state=state,
        title=title,
        summary=summary,
        primary_action=primary_action,
        recommended_buttons=recommended_buttons,
        can_run_codex=can_run_codex,
        warning=warning,
        raw={
            "status": status_result.to_dict(),
            "next": next_result.to_dict(),
        },
    )
