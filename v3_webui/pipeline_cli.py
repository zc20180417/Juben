from __future__ import annotations

import argparse
import os
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT / "juben" / "harness" / "project"
BLUEPRINT_PATH = PROJECT_ROOT / "book.blueprint.md"
SOURCE_MAP_PATH = PROJECT_ROOT / "source.map.md"
DEFAULT_CODEX_PROMPT_TIMEOUT_SECONDS = 1800


def run_stream(command: list[str], *, input_text: str | None = None, timeout_seconds: int | None = None) -> int:
    print("\n$ " + " ".join(command), flush=True)
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    popen_command = command
    if os.name == "nt" and command and command[0].lower() == "codex":
        popen_command = ["cmd", "/d", "/s", "/c", *command]
    proc = subprocess.Popen(
        popen_command,
        cwd=str(ROOT),
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )
    assert proc.stdout is not None
    if input_text is not None:
        try:
            output, _ = proc.communicate(input_text, timeout=timeout_seconds)
        except BrokenPipeError:
            output, _ = proc.communicate()
        except subprocess.TimeoutExpired:
            proc.kill()
            output, _ = proc.communicate()
            if output:
                print(output, end="" if output.endswith("\n") else "\n", flush=True)
            print(f"\nERROR: command timed out after {timeout_seconds}s", flush=True)
            return 124
        if output:
            print(output, end="" if output.endswith("\n") else "\n", flush=True)
        return proc.returncode

    output_queue: queue.Queue[str | None] = queue.Queue()

    def read_stdout() -> None:
        try:
            for line in proc.stdout:
                output_queue.put(line)
        finally:
            output_queue.put(None)

    reader = threading.Thread(target=read_stdout, daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout_seconds if timeout_seconds else None
    stream_done = False
    while not stream_done:
        if deadline is not None and time.monotonic() > deadline:
            proc.kill()
            proc.wait()
            print(f"\nERROR: command timed out after {timeout_seconds}s", flush=True)
            return 124
        try:
            item = output_queue.get(timeout=0.2)
        except queue.Empty:
            if proc.poll() is not None and not reader.is_alive():
                break
            continue
        if item is None:
            stream_done = True
        else:
            print(item, end="", flush=True)
    return proc.wait()


def run_required(command: list[str], *, input_text: str | None = None, timeout_seconds: int | None = None) -> None:
    rc = run_stream(command, input_text=input_text, timeout_seconds=timeout_seconds)
    if rc != 0:
        raise SystemExit(rc)


def read_prompt(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"ERROR: prompt not found: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def run_codex_prompt(prompt_path: Path, *, timeout_seconds: int) -> None:
    print(f"\n=== Codex 执行 prompt: {prompt_path.relative_to(ROOT).as_posix()} ===", flush=True)
    if not prompt_path.exists():
        raise SystemExit(f"ERROR: prompt not found: {prompt_path}")
    prompt_rel = prompt_path.relative_to(ROOT).as_posix()
    instruction = (
        "Read the UTF-8 prompt packet file at "
        f"`{prompt_rel}` and execute it exactly. "
        "Do not summarize the packet. Write only the target files required by that packet, "
        "then stop."
    )
    run_required(
        ["codex", "exec", "-C", str(ROOT), "-s", "workspace-write", instruction],
        timeout_seconds=timeout_seconds,
    )


def read_required_file(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"ERROR: expected file was not created: {display_path(path)}")
    return path.read_text(encoding="utf-8", errors="replace")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def ensure_no_pending_placeholders(path: Path, text: str) -> None:
    pending_markers = (
        "pending_book_extraction",
        "pending_model_recommendation",
        "pending_total_episodes",
        "pending whole-book extraction",
        "pending extraction",
    )
    found = [marker for marker in pending_markers if marker in text]
    if found:
        marker_text = ", ".join(found)
        raise SystemExit(
            "ERROR: model output is still a scaffold, not a completed artifact.\n"
            f"File: {display_path(path)}\n"
            f"Pending markers: {marker_text}\n"
            "Stop here and rerun the corresponding prompt; do not continue the pipeline."
        )


def validate_blueprint() -> None:
    text = read_required_file(BLUEPRINT_PATH)
    ensure_no_pending_placeholders(BLUEPRINT_PATH, text)
    required_markers = ("extraction_status: extracted", "recommended_total_episodes:")
    missing = [marker for marker in required_markers if marker not in text]
    if missing:
        raise SystemExit(
            "ERROR: book.blueprint.md is incomplete after Codex execution.\n"
            f"Missing markers: {', '.join(missing)}\n"
            "Expected Codex to write the full extraction result before map-book runs."
        )
    print("\nOK: book.blueprint.md completed.", flush=True)


def validate_source_map(expected_episodes: int) -> None:
    text = read_required_file(SOURCE_MAP_PATH)
    ensure_no_pending_placeholders(SOURCE_MAP_PATH, text)
    if "mapping_status:" not in text:
        raise SystemExit("ERROR: source.map.md has no mapping_status header.")
    if "mapping_status: complete" not in text and "mapping_status: mapped" not in text:
        raise SystemExit(
            "ERROR: source.map.md was written, but mapping_status is not complete/mapped.\n"
            "The map prompt likely did not finish cleanly."
        )
    episode_ids = {match.replace("-", "") for match in re.findall(r"\bEP-?\d{2,3}\b", text)}
    if len(episode_ids) < expected_episodes:
        raise SystemExit(
            "ERROR: source.map.md does not contain the requested episode coverage.\n"
            f"Requested episodes: {expected_episodes}\n"
            f"Found unique episode ids: {len(episode_ids)}\n"
            "Stop here; rerun map-book prompt before writing batches."
        )
    print(f"\nOK: source.map.md completed with {len(episode_ids)} episodes.", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Juben WebUI new-project pipeline")
    parser.add_argument("--novel", required=True, help="Novel path relative to juben root")
    parser.add_argument("--episodes", type=int, required=True)
    parser.add_argument("--target-total-minutes", type=int, required=True)
    parser.add_argument("--auto-codex", action="store_true", help="Run Codex for extract/map prompts after init")
    parser.add_argument("--codex-timeout-seconds", type=int, default=DEFAULT_CODEX_PROMPT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    print("=== Juben 新项目启动 ===", flush=True)
    print(f"小说文件: juben/{args.novel}", flush=True)
    print(f"目标集数: {args.episodes}", flush=True)
    print(f"目标总时长: {args.target_total_minutes} 分钟", flush=True)
    print(f"自动调用 Codex CLI: {'是（实验）' if args.auto_codex else '否（推荐）'}", flush=True)

    run_required(
        [
            sys.executable,
            "-m",
            "juben",
            "init",
            args.novel,
            "--episodes",
            str(args.episodes),
            "--target-total-minutes",
            str(args.target_total_minutes),
            "--force",
        ]
    )
    run_required([sys.executable, "-m", "juben", "extract-book", "--force"])

    if args.auto_codex:
        run_codex_prompt(
            ROOT / "juben" / "harness" / "project" / "prompts" / "extract-book.prompt.md",
            timeout_seconds=args.codex_timeout_seconds,
        )
        validate_blueprint()
        run_required([sys.executable, "-m", "juben", "map-book", "--force"])
        run_codex_prompt(
            ROOT / "juben" / "harness" / "project" / "prompts" / "map-book.prompt.md",
            timeout_seconds=args.codex_timeout_seconds,
        )
        validate_source_map(args.episodes)
        run_required([sys.executable, "-m", "juben", "next"])
    else:
        print("\n=== 已完成初始化和抽取 prompt 生成 ===", flush=True)
        print("下一步：让 Codex App 或当前 agent 执行这个文件：", flush=True)
        print("juben/harness/project/prompts/extract-book.prompt.md", flush=True)
        print("执行完成后，再回到 WebUI 点 map，生成分集 prompt。", flush=True)
        print("说明：WebUI 默认不自动跑 Codex CLI，因为 codex exec 批处理模式和 Codex App 长会话 agent 不等价。", flush=True)

    print("\n=== 当前状态 ===", flush=True)
    run_required([sys.executable, "-m", "juben", "next"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
