#!/usr/bin/env python3
"""
Harness V2 Controller — programmatic gate enforcement.

Project setup:
  init <novel_file>      Scaffold new project (manifest, source.map, state templates)

Orchestration commands:
  start <batch_id>       Full kickoff: generate brief → freeze → lock → show context
  check <batch_id>       Lint gate + verify-plan + verify instructions
  finish <batch_id>      Lint gate + verify gate + promote + validate + batch-review
  next                   Show pipeline progress and next batch to start

Verify / record gate commands:
  verify-done <EP> <S>   Record verify result (PASS/FAIL) for an episode
  record <batch_id>      Start record phase: acquire state.lock, print instructions
  record-done <batch_id> Seal record phase: validate state files, release state.lock

Low-level commands:
  status                 Show current pipeline state (with batch ownership)
  plan <batch_id>        Freeze batch brief, acquire batch lock
  lint <EP-XX>           Run lint on a draft, gate on result
  gate <batch_id>        Check all drafts in batch passed lint
  promote <batch_id>     Copy drafts → episodes (gates: lint + verify + state.lock)
  validate               Check state files against memory-contract templates
  log <phase> <event>    Append entry to run.log.md
  retry <EP-XX>          Show/increment verify retry count for an episode
  unlock [lock_name]     Release a lock (batch / episode / state / all)
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness"
FRAMEWORK = HARNESS / "framework"
PROJECT = HARNESS / "project"
STATE = PROJECT / "state"
LOCKS = PROJECT / "locks"
DRAFTS = ROOT / "drafts" / "episodes"
EPISODES = ROOT / "episodes"
LINT_SCRIPT = ROOT / "_ops" / "episode-lint.py"
BATCH_BRIEFS = PROJECT / "batch-briefs"
RUN_MANIFEST = PROJECT / "run.manifest.md"
RUN_MANIFEST_JSON = PROJECT / "run.manifest.json"
SOURCE_MAP = PROJECT / "source.map.md"
SOURCE_MAP_JSON = PROJECT / "source.map.json"
RELEASES = PROJECT / "releases"
RELEASE_INDEX = RELEASES / "release.index.json"
GOLD_SET = RELEASES / "gold-set.json"
RUN_LOG = STATE / "run.log.md"
MEMORY_CONTRACT = FRAMEWORK / "memory-contract.md"

RUNTIME_AUTHORITY = "rebuild-2026-04"
RULESET_VERSION = "episode-lint/v2"
LINT_PROFILE = "default"

NOW = datetime.now().strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------
# Lock helpers
# ---------------------------------------------------------------------------

def _read_lock(name: str) -> dict:
    path = LOCKS / name
    data = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip()
    return data


def _write_lock(name: str, status: str, owner: str = "none") -> None:
    path = LOCKS / name
    path.write_text(
        f"status: {status}\nowner: {owner}\nupdated_at: {NOW}\n",
        encoding="utf-8",
    )


def _is_locked(name: str) -> bool:
    return _read_lock(name).get("status") == "locked"


# ---------------------------------------------------------------------------
# Batch brief helpers
# ---------------------------------------------------------------------------

def _find_batch_brief(batch_id: str) -> Path | None:
    # Normalize: "batch01" → regex that matches both "batch01" and "batch1"
    m = re.match(r"batch0*(\d+)", batch_id)
    if not m:
        return None
    num = m.group(1)
    # Match any file whose stem contains "batch" followed by optional zeros + the number
    pattern = re.compile(rf"batch0*{re.escape(num)}")
    for p in BATCH_BRIEFS.glob("*.md"):
        if pattern.search(p.stem):
            return p
    return None


def _read_batch_brief(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    data = {}
    m = re.search(r"batch status:\s*(\S+)", content)
    if m:
        data["status"] = m.group(1)
    episodes = re.search(r"owned episodes:\s*(.+)", content)
    if episodes:
        data["episodes"] = [e.strip() for e in episodes.group(1).split(",")]
    return data


def _set_batch_status(path: Path, new_status: str) -> None:
    content = path.read_text(encoding="utf-8")
    content = re.sub(r"(batch status:\s*)\S+", rf"\g<1>{new_status}", content)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Run manifest helpers
# ---------------------------------------------------------------------------

def _relative_to_root(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json_file(path: Path) -> dict | None:
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v) if not isinstance(v, (dict, list)) else v for k, v in raw.items()}


def _parse_manifest_markdown(content: str) -> dict:
    data = {}
    for line in content.splitlines():
        m = re.match(r"^- ([^:]+):\s*(.+)$", line)
        if m:
            key = m.group(1).strip().replace(" ", "_")
            data[key] = m.group(2).strip()
    return data


def _normalize_manifest(data: dict | None) -> dict:
    base = {
        "framework_entry": "harness/framework/entry.md",
        "source_map": "harness/project/source.map.md",
        "current_batch_brief": "(none)",
        "regression_packs": "optional under harness/project/regressions/",
        "state_directory": "harness/project/state/",
    }
    if data:
        base.update(data)
    return base


def _render_manifest_markdown(data: dict) -> str:
    return f"""# Run Manifest

- source_file: {data.get("source_file", "")}
- total_episodes: {data.get("total_episodes", "")}
- batch_size: {data.get("batch_size", "")}
- key_episodes: {data.get("key_episodes", "")}
- adaptation_mode: {data.get("adaptation_mode", "")}
- adaptation_strategy: {data.get("adaptation_strategy", "")}
- dialogue_adaptation_intensity: {data.get("dialogue_adaptation_intensity", "")}
- generation_execution_mode: {data.get("generation_execution_mode", "")}
- generation_reset_mode: {data.get("generation_reset_mode", "")}
- run_status: {data.get("run_status", "")}
- active_batch: {data.get("active_batch", "")}
- source_authority: {data.get("source_authority", "")}
- draft_lane: {data.get("draft_lane", "")}
- publish_lane: {data.get("publish_lane", "")}
- promotion_policy: {data.get("promotion_policy", "")}

## Current Runtime
- framework entry: {data.get("framework_entry", "harness/framework/entry.md")}
- source map: {data.get("source_map", "harness/project/source.map.md")}
- current batch brief: {data.get("current_batch_brief", "(none)")}
- regression packs: {data.get("regression_packs", "optional under harness/project/regressions/")}
- state directory: {data.get("state_directory", "harness/project/state/")}

## Defaults
- stale legacy v1 files are not runtime authority
- published episodes are read-only outputs for current run
- draft episodes are the only candidate lane for verify
"""


def _write_manifest(data: dict) -> None:
    normalized = _normalize_manifest(data)
    RUN_MANIFEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    RUN_MANIFEST_JSON.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    RUN_MANIFEST.write_text(_render_manifest_markdown(normalized), encoding="utf-8")


def _read_manifest() -> dict:
    json_data = _read_json_file(RUN_MANIFEST_JSON)
    if json_data is not None:
        return _normalize_manifest(json_data)
    return _normalize_manifest(_parse_manifest_markdown(RUN_MANIFEST.read_text(encoding="utf-8")))


def _set_manifest_field(field: str, value: str) -> None:
    data = _read_manifest()
    data[field] = value
    _write_manifest(data)


def _set_manifest_runtime(active_batch: str | None = None, current_batch_brief: Path | None = None) -> None:
    data = _read_manifest()
    if active_batch is not None:
        data["active_batch"] = active_batch
    if current_batch_brief is not None:
        data["current_batch_brief"] = _relative_to_root(current_batch_brief)
    _write_manifest(data)


# ---------------------------------------------------------------------------
# Run log helpers
# ---------------------------------------------------------------------------

def _append_log(batch: str, episode: str, phase: str, event: str, result: str, note: str = "-") -> None:
    content = RUN_LOG.read_text(encoding="utf-8")
    # Update timestamp
    content = re.sub(r"_最后更新：.+_", f"_最后更新：{NOW}_", content)
    entry = f"| {NOW} | {batch} | {episode} | {phase} | {event} | {result} | {note} |"
    content = content.rstrip() + "\n" + entry + "\n"
    RUN_LOG.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Retry tracking (stored in a simple file per episode)
# ---------------------------------------------------------------------------

RETRY_DIR = LOCKS  # reuse locks dir for retry counts

def _retry_path(episode: str) -> Path:
    return RETRY_DIR / f"retry-{episode}.count"


def _get_retry_count(episode: str) -> int:
    p = _retry_path(episode)
    if p.exists():
        return int(p.read_text(encoding="utf-8").strip())
    return 0


def _set_retry_count(episode: str, count: int) -> None:
    _retry_path(episode).write_text(str(count), encoding="utf-8")


def _clear_retry_count(episode: str) -> None:
    p = _retry_path(episode)
    if p.exists():
        p.unlink()


# ---------------------------------------------------------------------------
# Verify result tracking (per-episode JSON in locks dir)
# ---------------------------------------------------------------------------

def _verify_result_path(episode: str) -> Path:
    return LOCKS / f"verify-{episode}.json"


def _read_verify_result(episode: str) -> dict | None:
    p = _verify_result_path(episode)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _write_verify_result(episode: str, tier: str, status: str) -> None:
    data = {"episode": episode, "tier": tier, "status": status, "timestamp": NOW}
    _verify_result_path(episode).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8",
    )


def _clear_verify_result(episode: str) -> None:
    p = _verify_result_path(episode)
    if p.exists():
        p.unlink()


# ---------------------------------------------------------------------------
# State validation helpers
# ---------------------------------------------------------------------------

TEMPLATE_SECTIONS: dict[str, list[str]] = {
    "script.progress.md": ["项目信息", "基础文档", "当前整季状态", "分集记录", "全局记录", "质量统计", "版本记录"],
    "story.state.md": ["当前阶段", "权力格局", "主要角色位置", "最近关键转折", "下一批关键预期"],
    "relationship.board.md": ["核心关系网", "最近关系变动", "待爆关系线"],
    "open_loops.md": ["未回收伏笔", "未爆真相", "待解冲突", "已超期伏笔"],
    "quality.anchor.md": ["场景厚度", "对话节奏", "os 使用方式", "代表性打法"],
    "process.memory.md": ["活跃流程问题", "当前执行准则"],
    "run.log.md": ["Log Entries"],
}


def _validate_state_file(name: str, sections: list[str]) -> list[str]:
    path = STATE / name
    if not path.exists():
        return [f"{name}: file missing"]
    content = path.read_text(encoding="utf-8")
    missing = []
    for s in sections:
        if not re.search(rf"^#+\s.*{re.escape(s)}", content, re.MULTILINE):
            missing.append(f"{name}: section '{s}' missing")
    return missing


# ---------------------------------------------------------------------------
# Source map parsing
# ---------------------------------------------------------------------------

def _parse_source_map_markdown(content: str) -> dict:
    batches = {}

    batch_blocks = re.split(r"(?=^## Batch \d+)", content, flags=re.MULTILINE)

    for block in batch_blocks:
        m = re.match(r"## Batch (\d+)：(EP-\d+)\s*~\s*(EP-\d+)\s*\n原著范围：(.+)", block)
        if not m:
            continue

        batch_num = m.group(1)
        ep_start = m.group(2)
        ep_end = m.group(3)
        source_range = m.group(4).strip()
        batch_id = f"batch{batch_num}"

        episode_data = {}
        ep_blocks = re.split(r"(?=^### EP-\d+)", block, flags=re.MULTILINE)
        episodes = []

        for ep_block in ep_blocks:
            ep_m = re.match(r"### (EP-\d+)", ep_block)
            if not ep_m:
                continue
            ep_id = ep_m.group(1)
            episodes.append(ep_id)

            span_m = re.search(r"source chapter span：(.+)", ep_block)
            beats_m = re.search(r"must-keep beats：(.+)", ep_block)
            not_m = re.search(r"must-not-add / must-not-jump：(.+)", ep_block)
            ending_m = re.search(r"ending type：(.+)", ep_block)

            episode_data[ep_id] = {
                "source_span": span_m.group(1).strip() if span_m else "",
                "must_keep": beats_m.group(1).strip() if beats_m else "",
                "must_not": not_m.group(1).strip() if not_m else "",
                "ending_type": ending_m.group(1).strip() if ending_m else "",
            }

        batches[batch_id] = {
            "batch_num": batch_num,
            "ep_start": ep_start,
            "ep_end": ep_end,
            "episodes": episodes,
            "source_range": source_range,
            "episode_data": episode_data,
        }

    return batches


def _parse_source_map() -> dict:
    """Parse source.map.* into structured batch data."""
    json_data = _read_json_file(SOURCE_MAP_JSON)
    if json_data is not None:
        return json_data
    return _parse_source_map_markdown(SOURCE_MAP.read_text(encoding="utf-8"))


def _generate_batch_brief(batch_id: str, batch_info: dict) -> str:
    """Generate a batch brief markdown from source.map data."""
    episodes = batch_info["episodes"]
    ep_start = batch_info["ep_start"]
    ep_end = batch_info["ep_end"]
    source_range = batch_info["source_range"]
    episode_data = batch_info["episode_data"]

    # Build adjacent continuity from first beats
    continuity_parts = []
    for ep in episodes:
        beats = episode_data.get(ep, {}).get("must_keep", "")
        first_beat = beats.split("；")[0] if beats else ep
        continuity_parts.append(first_beat)
    adjacent = " -> ".join(continuity_parts)

    # Build draft paths
    draft_paths = "\n".join(f"  - drafts/episodes/{ep}.md" for ep in episodes)

    # Build episode mapping
    ep_mapping_lines = []
    for ep in episodes:
        data = episode_data.get(ep, {})
        span = data.get("source_span", "")
        beats = data.get("must_keep", "")
        ending = data.get("ending_type", "前推力")
        beat_arrows = " -> ".join(b.strip() for b in beats.split("；")[:5])
        ep_mapping_lines.append(f"- {ep}：{span}")
        ep_mapping_lines.append(f"  - {beat_arrows}")
        ep_mapping_lines.append(f"  - 集尾类型：{ending}")
    ep_mapping = "\n".join(ep_mapping_lines)

    # Build hard constraints from must-not
    constraints = []
    for ep in episodes:
        must_not = episode_data.get(ep, {}).get("must_not", "")
        if must_not:
            for c in must_not.split("；"):
                c = c.strip()
                if c and c not in constraints:
                    constraints.append(c)
    constraints_text = "\n".join(f"- {c}" for c in constraints)

    # Read manifest for project-specific values
    manifest = _read_manifest()
    source_file = manifest.get("source_file", "原著正文.md")
    strategy = manifest.get("adaptation_strategy", "original_fidelity")
    intensity = manifest.get("dialogue_adaptation_intensity", "light")
    exec_mode = manifest.get("generation_execution_mode", "orchestrated_subagents")
    reset_mode = manifest.get("generation_reset_mode", "clean_rebuild")

    return f"""# Batch Brief: {ep_start} ~ {ep_end}

- batch status: draft
- owned episodes: {", ".join(episodes)}
- source excerpt range: {source_file} {source_range}
- adjacent continuity: {adjacent}
- draft output paths:
{draft_paths}

## Run Context
- adaptation_strategy: {strategy}
- dialogue_adaptation_intensity: {intensity}
- generation_execution_mode: {exec_mode}
- generation_reset_mode: {reset_mode}

## Source Priority
1. `harness/project/run.manifest.md`
2. `harness/project/source.map.md`
3. `harness/framework/write-contract.md`
4. 原著正文 `{source_file}`
5. `voice-anchor.md`
6. `character.md`

## Episode Mapping
{ep_mapping}

## Hard Constraints
{constraints_text}

## verify checklist
- `_ops/episode-lint.py` on each draft: PASS
- `verify-contract.md` high-severity gates: PASS
- `harness/project/regressions/` active pack items: no active hit
- batch ready for promote: yes
"""


def _compute_verify_tiers(episodes: list[str]) -> tuple[list, list, list]:
    """Compute FULL/STANDARD/LIGHT verify tiers for a list of episodes."""
    batches = _parse_source_map()
    episode_map = {}
    for batch in batches.values():
        episode_map.update(batch.get("episode_data", {}))
    manifest = _read_manifest()
    key_episodes_raw = manifest.get("key_episodes", "")
    key_episodes = {e.strip() for e in key_episodes_raw.split(",") if e.strip()}

    full_eps, standard_eps, light_eps = [], [], []
    for i, ep in enumerate(episodes):
        episode_data = episode_map.get(ep, {})
        ending_type = str(episode_data.get("ending_type", ""))
        is_first = (i == 0)
        is_strong_closure = "强闭环" in ending_type
        is_key_episode = ep in key_episodes
        if is_first or is_strong_closure or is_key_episode:
            full_eps.append(ep)
        elif not episode_data:
            light_eps.append(ep)
        else:
            standard_eps.append(ep)
    return full_eps, standard_eps, light_eps


def _normalize_lint_payload(data: dict) -> dict:
    if "contract_failures" in data:
        return {
            "status": data.get("status", "fail"),
            "contract_failures": list(data.get("contract_failures", [])),
            "craft_flags": list(data.get("craft_flags", [])),
            "style_warnings": list(data.get("style_warnings", [])),
            "metrics": data.get("metrics", {}),
        }

    checks = data.get("checks", {})
    contract_failures: list[dict] = []
    for item in checks.get("scene_failures", []):
        for code in item.get("failures", []):
            contract_failures.append(
                {
                    "scope": "scene",
                    "scene": item.get("scene"),
                    "title": item.get("title"),
                    "code": code,
                }
            )
    for code in checks.get("episode_failures", []):
        contract_failures.append({"scope": "episode", "code": code})

    return {
        "status": data.get("status", "fail"),
        "contract_failures": contract_failures,
        "craft_flags": list(checks.get("warnings", [])),
        "style_warnings": [],
        "metrics": {
            "totals": data.get("totals", {}),
            "scenes": data.get("scenes", []),
            "history": data.get("history", {}),
        },
    }


def _run_lint(path: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    try:
        payload = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"lint produced invalid JSON for {path}") from exc
    return _normalize_lint_payload(payload)


def _lint_blocks_promote(payload: dict) -> bool:
    return bool(payload.get("contract_failures", []))


def _release_index_template() -> dict:
    return {
        "runtime_authority": RUNTIME_AUTHORITY,
        "provenance": RUNTIME_AUTHORITY,
        "ruleset_version": RULESET_VERSION,
        "gold_set": _relative_to_root(GOLD_SET),
        "current_batch": "(none)",
        "current_batch_brief": "(none)",
        "episodes": {},
        "updated_at": NOW,
    }


def _gold_set_template() -> dict:
    return {
        "runtime_authority": RUNTIME_AUTHORITY,
        "provenance": RUNTIME_AUTHORITY,
        "episodes": [],
        "updated_at": NOW,
    }


def _load_release_index() -> dict:
    data = _read_json_file(RELEASE_INDEX)
    if data is None:
        data = _release_index_template()
    data.setdefault("episodes", {})
    return data


def _load_gold_set() -> dict:
    data = _read_json_file(GOLD_SET)
    if data is None:
        data = _gold_set_template()
    data.setdefault("episodes", [])
    return data


def _write_release_files(index: dict, gold_set: dict) -> None:
    RELEASES.mkdir(parents=True, exist_ok=True)
    RELEASE_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    GOLD_SET.write_text(json.dumps(gold_set, ensure_ascii=False, indent=2), encoding="utf-8")


def _meta_path(episode: str) -> Path:
    return EPISODES / f"{episode}.meta.json"


def _bootstrap_legacy_entries(index: dict, gold_episodes: set[str]) -> None:
    for episode_file in sorted(EPISODES.glob("EP-*.md")):
        episode = episode_file.stem
        if episode in gold_episodes:
            continue
        index["episodes"].setdefault(
            episode,
            {
                "episode": episode,
                "release_status": "legacy",
                "runtime_authority": "legacy",
                "provenance": "legacy",
                "content_path": _relative_to_root(episode_file),
                "meta_path": None,
            },
        )


def _build_episode_metadata(
    episode: str,
    batch_id: str,
    brief_path: Path,
    lint_payload: dict,
    verify_result: dict,
    release_status: str = "gold",
) -> dict:
    return {
        "episode": episode,
        "provenance": RUNTIME_AUTHORITY,
        "source_batch": batch_id,
        "runtime_authority": RUNTIME_AUTHORITY,
        "gold/provisional": release_status,
        "release_status": release_status,
        "ruleset_version": RULESET_VERSION,
        "lint_profile": LINT_PROFILE,
        "lint_status": lint_payload.get("status", "fail"),
        "verify_tier": verify_result.get("tier", "STANDARD"),
        "verify_status": verify_result.get("status", "MISSING"),
        "contract_failures": lint_payload.get("contract_failures", []),
        "craft_flags": lint_payload.get("craft_flags", []),
        "style_warnings": lint_payload.get("style_warnings", []),
        "batch_brief": _relative_to_root(brief_path),
        "content_path": _relative_to_root(EPISODES / f"{episode}.md"),
        "updated_at": NOW,
    }


def _build_release_entry(metadata: dict) -> dict:
    return {
        "episode": metadata["episode"],
        "release_status": metadata["release_status"],
        "runtime_authority": metadata["runtime_authority"],
        "provenance": metadata["provenance"],
        "source_batch": metadata["source_batch"],
        "verify_tier": metadata["verify_tier"],
        "verify_status": metadata["verify_status"],
        "lint_status": metadata["lint_status"],
        "content_path": metadata["content_path"],
        "meta_path": _relative_to_root(_meta_path(metadata["episode"])),
        "updated_at": metadata["updated_at"],
    }


def _promote_batch(batch_id: str, brief_path: Path, episodes: list[str], lint_results: dict[str, dict]) -> tuple[int, dict]:
    stage_root = RELEASES / "staging" / f"{batch_id}-{NOW.replace(':', '').replace(' ', '-')}"
    stage_root.mkdir(parents=True, exist_ok=True)

    staged_episode_files: dict[str, Path] = {}
    staged_meta_files: dict[str, Path] = {}
    try:
        for episode in episodes:
            src = DRAFTS / f"{episode}.md"
            staged = stage_root / f"{episode}.md"
            shutil.copy2(src, staged)
            staged_episode_files[episode] = staged

        release_index = _load_release_index()
        gold_set = _load_gold_set()
        gold_episodes = set(gold_set.get("episodes", []))
        _bootstrap_legacy_entries(release_index, gold_episodes.union(episodes))

        for episode in episodes:
            verify_result = _read_verify_result(episode) or {"episode": episode, "tier": "STANDARD", "status": "MISSING"}
            metadata = _build_episode_metadata(
                episode=episode,
                batch_id=batch_id,
                brief_path=brief_path,
                lint_payload=lint_results[episode],
                verify_result=verify_result,
            )
            staged_meta = stage_root / f"{episode}.meta.json"
            staged_meta.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            staged_meta_files[episode] = staged_meta
            release_index["episodes"][episode] = _build_release_entry(metadata)
            gold_episodes.add(episode)

        gold_set["episodes"] = sorted(gold_episodes)
        gold_set["updated_at"] = NOW
        release_index["current_batch"] = batch_id
        release_index["current_batch_brief"] = _relative_to_root(brief_path)
        release_index["gold_set"] = _relative_to_root(GOLD_SET)
        release_index["updated_at"] = NOW

        staged_release_index = stage_root / "release.index.json"
        staged_gold_set = stage_root / "gold-set.json"
        staged_release_index.write_text(json.dumps(release_index, ensure_ascii=False, indent=2), encoding="utf-8")
        staged_gold_set.write_text(json.dumps(gold_set, ensure_ascii=False, indent=2), encoding="utf-8")

        EPISODES.mkdir(parents=True, exist_ok=True)
        RELEASES.mkdir(parents=True, exist_ok=True)
        for episode in episodes:
            staged_episode_files[episode].replace(EPISODES / f"{episode}.md")
            staged_meta_files[episode].replace(_meta_path(episode))
        staged_release_index.replace(RELEASE_INDEX)
        staged_gold_set.replace(GOLD_SET)
        return 0, {"release_index": release_index, "gold_set": gold_set}
    finally:
        if stage_root.exists():
            shutil.rmtree(stage_root, ignore_errors=True)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    manifest = _read_manifest()
    print("=== Harness V2 Pipeline Status ===")
    print(f"  run_status:   {manifest.get('run_status', '?')}")
    print(f"  active_batch: {manifest.get('active_batch', '?')}")
    print(f"  current_batch_brief: {manifest.get('current_batch_brief', '?')}")
    print(f"  draft_lane:   {manifest.get('draft_lane', '?')}")
    print(f"  publish_lane: {manifest.get('publish_lane', '?')}")
    print()

    print("=== Locks ===")
    for lock_name in ["batch.lock", "episode-XX.lock", "state.lock"]:
        data = _read_lock(lock_name)
        status = data.get("status", "")
        owner = data.get("owner", "")
        if status == "locked":
            print(f"  {lock_name}: LOCKED (owner: {owner})")
        else:
            print(f"  {lock_name}: free")
    print()

    print("=== Drafts ===")
    if DRAFTS.exists():
        drafts = sorted(DRAFTS.glob("EP-*.md"))
        for d in drafts:
            print(f"  {d.name}")
        if not drafts:
            print("  (none)")
    else:
        print("  (draft lane missing)")
    print()

    print("=== Published (batch ownership) ===")
    # Build map of episode → batch for all promoted batches
    batches = _parse_source_map()
    ep_to_batch: dict[str, str] = {}
    for bid in sorted(batches.keys()):
        bp = _find_batch_brief(bid)
        if bp:
            bd = _read_batch_brief(bp)
            if bd.get("status") == "promoted":
                for ep in bd.get("episodes", []):
                    ep_to_batch[ep] = bid

    if EPISODES.exists():
        eps = sorted(EPISODES.glob("EP-*.md"))
        for e in eps:
            owner = ep_to_batch.get(e.stem)
            if owner:
                print(f"  {e.name}  [{owner}]")
            else:
                print(f"  {e.name}  [UNTRACKED — legacy or orphan]")
        if not eps:
            print("  (none)")
    print()

    # Show verify results if any
    verify_files = sorted(LOCKS.glob("verify-EP-*.json"))
    if verify_files:
        print("=== Verify Results ===")
        for vf in verify_files:
            vr = json.loads(vf.read_text(encoding="utf-8"))
            ep = vr.get("episode", vf.stem)
            print(f"  {ep}: {vr.get('status', '?')} (tier: {vr.get('tier', '?')})")
        print()

    # Show retry counts if any
    retries = sorted(RETRY_DIR.glob("retry-*.count"))
    if retries:
        print("=== Retry Counts ===")
        for r in retries:
            ep = r.stem.replace("retry-", "")
            count = int(r.read_text(encoding="utf-8").strip())
            print(f"  {ep}: {count} failures")
        print()

    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    batch_id = args.batch_id
    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for '{batch_id}'")
        return 1

    brief = _read_batch_brief(brief_path)
    current_status = brief.get("status", "unknown")

    if current_status == "promoted":
        print(f"ERROR: batch '{batch_id}' is already promoted")
        return 1

    if _is_locked("batch.lock"):
        lock_data = _read_lock("batch.lock")
        print(f"ERROR: batch.lock is held by '{lock_data.get('owner', '?')}'")
        return 1

    # Freeze brief
    _set_batch_status(brief_path, "frozen")
    _write_lock("batch.lock", "locked", f"controller:{batch_id}")

    # Clear retry counts for this batch's episodes
    for ep in brief.get("episodes", []):
        _clear_retry_count(ep)

    _append_log(batch_id, "-", "plan_inputs", "batch brief 冻结", "✓", f"controller plan")

    print(f"OK: batch '{batch_id}' frozen, batch.lock acquired")
    print(f"  episodes: {', '.join(brief.get('episodes', []))}")
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    episode = args.episode
    draft = DRAFTS / f"{episode}.md"
    if not draft.exists():
        print(f"ERROR: draft not found: {draft}")
        return 1

    try:
        data = _run_lint(draft)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(json.dumps(data, ensure_ascii=False, indent=2))

    if not _lint_blocks_promote(data):
        print(f"\nLINT OK: {episode} ({data.get('status', 'pass')})")
        return 0

    print(f"\nLINT FAIL: {episode}")
    count = _get_retry_count(episode) + 1
    _set_retry_count(episode, count)
    if count >= 4:
        print(f"WARNING: {episode} has failed {count} times — ESCALATE TO HUMAN")
    elif count >= 3:
        print(f"WARNING: {episode} has failed {count} times — CONTEXT RESET required")
    return 1


def cmd_gate(args: argparse.Namespace) -> int:
    batch_id = args.batch_id
    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for '{batch_id}'")
        return 1

    brief = _read_batch_brief(brief_path)
    episodes = brief.get("episodes", [])
    if not episodes:
        print(f"ERROR: no episodes in batch '{batch_id}'")
        return 1

    all_pass = True
    for ep in episodes:
        draft = DRAFTS / f"{ep}.md"
        if not draft.exists():
            print(f"  MISSING: {ep}")
            all_pass = False
            continue

        try:
            data = _run_lint(draft)
            status = data.get("status", "fail")
            is_blocking = _lint_blocks_promote(data)
        except ValueError:
            status = "error"
            is_blocking = True

        icon = "✓" if not is_blocking else "✗"
        print(f"  {icon} {ep}: {status}")
        if is_blocking:
            all_pass = False

    if all_pass:
        print(f"\nGATE PASS: all {len(episodes)} episodes in {batch_id} passed lint")
        return 0
    else:
        print(f"\nGATE FAIL: not all episodes passed lint")
        return 1


def cmd_promote(args: argparse.Namespace) -> int:
    batch_id = args.batch_id
    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for '{batch_id}'")
        return 1

    brief = _read_batch_brief(brief_path)
    current_status = brief.get("status", "unknown")

    if current_status == "promoted":
        print(f"ERROR: batch '{batch_id}' is already promoted")
        return 1

    if current_status != "frozen":
        print(f"ERROR: batch brief status is '{current_status}', must be 'frozen' to promote")
        return 1

    episodes = brief.get("episodes", [])

    # Gate: all drafts must exist
    missing = [ep for ep in episodes if not (DRAFTS / f"{ep}.md").exists()]
    if missing:
        print(f"ERROR: missing drafts: {', '.join(missing)}")
        return 1

    # Gate: all must pass lint
    print("Running lint gate...")
    lint_results: dict[str, dict] = {}
    for ep in episodes:
        try:
            data = _run_lint(DRAFTS / f"{ep}.md")
        except ValueError:
            print(f"ERROR: {ep} lint error — cannot promote")
            return 1
        lint_results[ep] = data
        if _lint_blocks_promote(data):
            print(f"ERROR: {ep} lint FAIL — cannot promote")
            return 1
        print(f"  ✓ {ep} lint {data.get('status', 'pass')}")

    # Gate: all non-LIGHT episodes must have verify PASS
    print("Running verify gate...")
    full_eps, standard_eps, light_eps = _compute_verify_tiers(episodes)
    for ep in episodes:
        if ep in light_eps:
            print(f"  ✓ {ep} verify: LIGHT (lint-only)")
            continue
        vr = _read_verify_result(ep)
        if vr is None:
            print(f"ERROR: {ep} has no verify result — run aligner + verify-done first")
            return 1
        if vr.get("status") != "PASS":
            print(f"ERROR: {ep} verify {vr.get('status', '?')} — cannot promote")
            return 1
        print(f"  ✓ {ep} verify: PASS (tier: {vr.get('tier', '?')})")

    # Gate: state.lock must be free
    if _is_locked("state.lock"):
        print("ERROR: state.lock is held — cannot promote")
        return 1

    # Execute promote: staging -> atomic replace
    rc, _ = _promote_batch(batch_id, brief_path, episodes, lint_results)
    if rc != 0:
        print("ERROR: staging promote failed")
        return 1
    for ep in episodes:
        print(f"  → {ep}: staging → published")

    # Update batch brief status
    _set_batch_status(brief_path, "promoted")

    # Update run manifest
    _set_manifest_runtime(f"{batch_id}_promoted", brief_path)

    # Release batch lock
    _write_lock("batch.lock", "unlocked")

    # Clear retry counts
    for ep in episodes:
        _clear_retry_count(ep)

    # Log
    ep_range = f"{episodes[0]}~{episodes[-1]}" if len(episodes) > 1 else episodes[0]
    _append_log(batch_id, ep_range, "promote", "controller promote", "✓", f"{len(episodes)} episodes promoted")

    print(f"\nPROMOTE OK: {batch_id} → {len(episodes)} episodes published")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    print("=== State File Validation ===")
    all_ok = True
    for name, sections in TEMPLATE_SECTIONS.items():
        errors = _validate_state_file(name, sections)
        if errors:
            all_ok = False
            for e in errors:
                print(f"  ✗ {e}")
        else:
            print(f"  ✓ {name}")

    if all_ok:
        print("\nVALIDATE OK: all state files comply with memory-contract templates")
        return 0
    else:
        print("\nVALIDATE FAIL: some state files have missing sections")
        return 1


def cmd_log(args: argparse.Namespace) -> int:
    _append_log(
        args.batch or "-",
        args.episode or "-",
        args.phase,
        args.event,
        args.result or "✓",
        args.note or "-",
    )
    print(f"OK: log entry appended")
    return 0


def cmd_retry(args: argparse.Namespace) -> int:
    episode = args.episode
    count = _get_retry_count(episode)

    if args.increment:
        count += 1
        _set_retry_count(episode, count)

    if args.reset:
        _clear_retry_count(episode)
        count = 0

    print(f"{episode}: {count} verify failures")
    if count >= 4:
        print("  → ESCALATE: human intervention required")
    elif count >= 3:
        print("  → ACTION: context reset required before next attempt")
    elif count >= 1:
        print(f"  → writer may retry in current context ({3 - count} attempts before context reset)")
    return 0


def cmd_verify_plan(args: argparse.Namespace) -> int:
    """Compute verify tiers for a batch based on source.map metadata."""
    batch_id = args.batch_id
    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for '{batch_id}'")
        return 1

    brief = _read_batch_brief(brief_path)
    episodes = brief.get("episodes", [])

    full_eps, standard_eps, light_eps = _compute_verify_tiers(episodes)

    print(f"=== Verify Plan: {batch_id} ===")
    print(f"\n  FULL (8-step):    {', '.join(full_eps) or '(none)'}")
    print(f"  STANDARD (5-step): {', '.join(standard_eps) or '(none)'}")
    print(f"  LIGHT (lint only): {', '.join(light_eps) or '(none)'}")
    print(f"\n  Batch-level adversarial sampling: 2 random episodes after all pass")

    # Output as structured data for agent consumption
    plan = {"full": full_eps, "standard": standard_eps, "light": light_eps}
    print(f"\n  JSON: {json.dumps(plan, ensure_ascii=False)}")
    return 0


def cmd_batch_review(args: argparse.Namespace) -> int:
    """Print batch-level review checklist after all episodes in batch pass verify."""
    batch_id = args.batch_id
    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for '{batch_id}'")
        return 1

    brief = _read_batch_brief(brief_path)
    episodes = brief.get("episodes", [])

    # Pick 2 episodes for adversarial sampling
    sample_size = min(2, len(episodes))
    sampled = random.sample(episodes, sample_size)

    print(f"=== Batch Review: {batch_id} ===")
    print(f"\n  Episodes in batch: {', '.join(episodes)}")
    print(f"  Sampled for adversarial deep-check: {', '.join(sampled)}")
    print(f"\n  Checklist for agent (on sampled episodes):")
    print(f"  [ ] 1. 角色替换测试（抽 2 组对话互换）")
    print(f"  [ ] 2. 删除测试（逐场假设删除）")
    print(f"  [ ] 3. 逻辑反推测试（结果反推原因）")
    print(f"  [ ] 4. 钩子有效性测试（集尾最后一段）")
    print(f"  [ ] 5. 画面感测试（抽 2 条 △）")
    print(f"  [ ] 6. 表里不一测试（os 有效性）")
    print(f"\n  Checklist for agent (batch-level):")
    print(f"  [ ] 7. 质量锚对标（本批 vs quality.anchor.md）")
    print(f"  [ ] 8. 批次内角色声纹一致性（跨集比对）")
    print(f"  [ ] 9. 批次内伏笔连续性（open_loops 更新）")
    return 0


def cmd_unlock(args: argparse.Namespace) -> int:
    targets = []
    name = args.lock_name
    if name == "all":
        targets = ["batch.lock", "episode-XX.lock", "state.lock"]
    elif name in ("batch", "episode", "state"):
        mapping = {"batch": "batch.lock", "episode": "episode-XX.lock", "state": "state.lock"}
        targets = [mapping[name]]
    else:
        print(f"ERROR: unknown lock '{name}'. Use: batch, episode, state, or all")
        return 1

    for t in targets:
        _write_lock(t, "unlocked")
        print(f"  unlocked: {t}")

    return 0


# ---------------------------------------------------------------------------
# Verify / Record gate commands
# ---------------------------------------------------------------------------

def cmd_verify_done(args: argparse.Namespace) -> int:
    """Record that an episode has passed (or failed) semantic verify."""
    episode = args.episode
    status = args.status.upper()
    tier = (args.tier or "STANDARD").upper()

    if status not in ("PASS", "FAIL"):
        print(f"ERROR: status must be PASS or FAIL, got '{status}'")
        return 1
    if tier not in ("FULL", "STANDARD", "LIGHT"):
        print(f"ERROR: tier must be FULL, STANDARD, or LIGHT, got '{tier}'")
        return 1

    _write_verify_result(episode, tier, status)
    _append_log(
        args.batch or "-", episode, "verify",
        f"aligner {status}", status,
        f"tier={tier}",
    )
    print(f"  ✓ {episode}: verify {status} (tier: {tier})")

    if status == "FAIL":
        count = _get_retry_count(episode) + 1
        _set_retry_count(episode, count)
        if count >= 4:
            print(f"  ESCALATE: {episode} has failed {count} times — human intervention")
        elif count >= 3:
            print(f"  ACTION: context reset required before next attempt")
        else:
            print(f"  Writer may revise ({3 - count} attempts before context reset)")

    return 0


def cmd_record(args: argparse.Namespace) -> int:
    """Start record phase: gate on promoted, acquire state.lock, print instructions."""
    batch_id = args.batch_id
    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for '{batch_id}'")
        return 1

    brief = _read_batch_brief(brief_path)
    if brief.get("status") != "promoted":
        print(f"ERROR: batch '{batch_id}' must be promoted first (status: {brief.get('status', '?')})")
        return 1

    if _is_locked("state.lock"):
        lock_data = _read_lock("state.lock")
        print(f"ERROR: state.lock held by '{lock_data.get('owner', '?')}'")
        return 1

    episodes = brief.get("episodes", [])
    _write_lock("state.lock", "locked", f"recorder:{batch_id}")
    _append_log(batch_id, "-", "record", "record phase started", "✓", "state.lock acquired")

    print(f"=== Record Phase: {batch_id} ===")
    print(f"  state.lock acquired (owner: recorder:{batch_id})")
    print(f"  Episodes: {', '.join(episodes)}")

    print(f"\n--- Recorder Agent Instructions ---")
    print(f"  Follow script-recorder.md steps 2-9:")
    print(f"  2. Extract per-episode data (weakness labels: 8 types)")
    print(f"  3. Update script.progress.md (分集记录 + 质量统计)")
    print(f"  4. Update story.state.md (权力格局 + 转折 + 预期)")
    print(f"  5. Update relationship.board.md (关系变动 + 待爆线)")
    print(f"  6. Update open_loops.md (新伏笔 + 已回收)")
    print(f"  7. Update quality.anchor.md (代表性打法)")
    print(f"  8. Update process.memory.md (流程问题 + 执行准则)")
    print(f"  9. Append run.log.md entries for this batch")
    print(f"\n  When done: python _ops/controller.py record-done {batch_id}")
    print(f"  Do NOT manually release state.lock — record-done handles it.")

    return 0


def cmd_record_done(args: argparse.Namespace) -> int:
    """Seal record phase: validate state files, release state.lock, log."""
    batch_id = args.batch_id

    lock_data = _read_lock("state.lock")
    if lock_data.get("status") != "locked":
        print(f"ERROR: state.lock is not held — run `record {batch_id}` first")
        return 1

    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for '{batch_id}'")
        return 1

    brief = _read_batch_brief(brief_path)
    episodes = brief.get("episodes", [])

    # Validate all state files
    print(f"=== Validating State Files ===")
    all_valid = True
    for name, sections in TEMPLATE_SECTIONS.items():
        errors = _validate_state_file(name, sections)
        if errors:
            all_valid = False
            for e in errors:
                print(f"  ✗ {e}")
        else:
            print(f"  ✓ {name}")

    if not all_valid:
        print(f"\n  VALIDATION FAIL — fix state files, then re-run record-done {batch_id}")
        return 1

    # Release state.lock
    _write_lock("state.lock", "unlocked")

    ep_range = f"{episodes[0]}~{episodes[-1]}" if len(episodes) > 1 else episodes[0]
    _append_log(batch_id, ep_range, "record", "recorder 完成", "✓", "state 全量写入")

    print(f"\n  ✓ State validation passed")
    print(f"  ✓ state.lock released")
    print(f"  ✓ Record phase complete for {batch_id}")

    # Show next
    batches = _parse_source_map()
    batch_ids = sorted(batches.keys())
    try:
        idx = batch_ids.index(batch_id)
        next_batch = batch_ids[idx + 1] if idx + 1 < len(batch_ids) else None
    except ValueError:
        next_batch = None

    if next_batch:
        next_info = batches[next_batch]
        print(f"\n  Next: python _ops/controller.py start {next_batch}")
        print(f"  ({next_info['ep_start']} ~ {next_info['ep_end']}, {next_info['source_range']})")
    else:
        print(f"\n  All batches complete!")

    return 0


# ---------------------------------------------------------------------------
# High-level orchestration commands
# ---------------------------------------------------------------------------

def _detect_chapters(novel_text: str) -> list[dict]:
    """Detect chapter boundaries in novel text. Returns list of {index, title, start_line, end_line, char_count}."""
    lines = novel_text.split("\n")
    chapter_starts = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^#{1,4}\s*第.+[章回]", stripped):
            title = stripped.lstrip("#").strip()
            chapter_starts.append((i, title))

    chapters = []
    for idx, (start, title) in enumerate(chapter_starts):
        end = chapter_starts[idx + 1][0] if idx + 1 < len(chapter_starts) else len(lines)
        content = "\n".join(lines[start:end])
        chapters.append({
            "index": idx + 1,
            "title": title,
            "start_line": start,
            "end_line": end,
            "char_count": len(content),
        })

    return chapters


def _map_chapters_to_episodes(chapters: list[dict], total_episodes: int) -> list[dict]:
    """Proportionally map chapters to episodes based on chapter length."""
    if not chapters:
        return [{"id": f"EP-{i:02d}", "chapter_span": "（待填写）"} for i in range(1, total_episodes + 1)]

    total_chars = sum(ch["char_count"] for ch in chapters)
    eps_per_char = total_episodes / total_chars if total_chars > 0 else 1

    episodes = []
    current_ep = 1

    for ch in chapters:
        remaining_chapters = len(chapters) - ch["index"] + 1
        remaining_eps = total_episodes - current_ep + 1

        # How many episodes for this chapter?
        raw = ch["char_count"] * eps_per_char
        n = max(1, round(raw))
        # Guarantee at least 1 ep per remaining chapter
        n = min(n, remaining_eps - (remaining_chapters - 1))
        n = max(1, n)

        ch_label = f"第{ch['index']}章"

        if n == 1:
            episodes.append({"id": f"EP-{current_ep:02d}", "chapter_span": ch_label, "chapter_title": ch["title"]})
            current_ep += 1
        elif n == 2:
            episodes.append({"id": f"EP-{current_ep:02d}", "chapter_span": f"{ch_label}前半", "chapter_title": ch["title"]})
            current_ep += 1
            episodes.append({"id": f"EP-{current_ep:02d}", "chapter_span": f"{ch_label}后半", "chapter_title": ch["title"]})
            current_ep += 1
        else:
            for j in range(n):
                episodes.append({"id": f"EP-{current_ep:02d}", "chapter_span": f"{ch_label}第{j+1}段", "chapter_title": ch["title"]})
                current_ep += 1

        if current_ep > total_episodes:
            break

    return episodes[:total_episodes]


def _has_existing_project() -> bool:
    """Check if there is meaningful project data that would be lost by init."""
    # Check for promoted batches
    if BATCH_BRIEFS.exists():
        for p in BATCH_BRIEFS.glob("*.md"):
            bd = _read_batch_brief(p)
            if bd.get("status") == "promoted":
                return True
    # Check for published episodes
    if EPISODES.exists() and list(EPISODES.glob("EP-*.md")):
        return True
    # Check for drafts
    if DRAFTS.exists() and list(DRAFTS.glob("EP-*.md")):
        return True
    # Check for non-empty state files
    if STATE.exists():
        for f in STATE.glob("*.md"):
            if f.stat().st_size > 200:
                return True
    return False


def _backup_project() -> Path | None:
    """Archive current project data to versions/rebuild_snapshots/."""
    snapshot_dir = ROOT / "versions" / "rebuild_snapshots" / NOW.replace(":", "").replace(" ", "-")
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    # Backup episodes
    if EPISODES.exists():
        ep_dst = snapshot_dir / "episodes"
        ep_dst.mkdir(exist_ok=True)
        for f in EPISODES.glob("EP-*.md"):
            shutil.copy2(f, ep_dst / f.name)
            copied += 1
    # Backup drafts
    if DRAFTS.exists():
        dr_dst = snapshot_dir / "drafts"
        dr_dst.mkdir(exist_ok=True)
        for f in DRAFTS.glob("EP-*.md"):
            shutil.copy2(f, dr_dst / f.name)
            copied += 1
    # Backup batch briefs
    if BATCH_BRIEFS.exists():
        bb_dst = snapshot_dir / "batch-briefs"
        bb_dst.mkdir(exist_ok=True)
        for f in BATCH_BRIEFS.glob("*.md"):
            shutil.copy2(f, bb_dst / f.name)
            copied += 1
    # Backup state
    if STATE.exists():
        st_dst = snapshot_dir / "state"
        st_dst.mkdir(exist_ok=True)
        for f in STATE.glob("*.md"):
            shutil.copy2(f, st_dst / f.name)
            copied += 1
    # Backup source.map, manifest, character, voice-anchor
    for name in ["source.map.md", "run.manifest.md"]:
        src = PROJECT / name
        if src.exists():
            shutil.copy2(src, snapshot_dir / name)
            copied += 1
    for name in ["character.md", "voice-anchor.md"]:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, snapshot_dir / name)
            copied += 1

    if copied == 0:
        snapshot_dir.rmdir()
        return None
    return snapshot_dir


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a new project: detect chapters, map episodes, generate all files."""
    novel_path = ROOT / args.novel_file
    if not novel_path.exists():
        print(f"ERROR: novel file not found: {novel_path}")
        return 1

    total_eps = args.episodes
    batch_size = args.batch_size
    strategy = args.strategy
    intensity = args.intensity
    key_eps = args.key_episodes or ""
    novel_name = novel_path.name
    total_batches = (total_eps + batch_size - 1) // batch_size

    # Safety check: detect existing project data
    if _has_existing_project() and not args.force:
        print("ERROR: existing project data detected (promoted batches, episodes, state files)")
        print("  This command will OVERWRITE all project files.")
        print("  To proceed, re-run with --force:")
        print(f"    python _ops/controller.py init {args.novel_file} --force")
        return 1

    # Read novel and detect chapters
    novel_text = novel_path.read_text(encoding="utf-8")
    chapters = _detect_chapters(novel_text)

    print(f"=== Init New Project ===")
    print(f"  Novel:      {novel_name}")
    print(f"  Chapters:   {len(chapters)} detected")
    print(f"  Episodes:   {total_eps} ({total_batches} batches x {batch_size})")
    print(f"  Strategy:   {strategy}")
    print(f"  Intensity:  {intensity}")
    if key_eps:
        print(f"  Key EPs:    {key_eps}")
    print()

    # Map chapters to episodes
    ep_mapping = _map_chapters_to_episodes(chapters, total_eps)

    # Show mapping preview
    print(f"  Chapter → Episode mapping:")
    for ep in ep_mapping[:10]:
        print(f"    {ep['id']}: {ep['chapter_span']}")
    if len(ep_mapping) > 10:
        print(f"    ... ({len(ep_mapping) - 10} more)")
    print()

    # Backup before destructive operations
    snapshot = _backup_project()
    if snapshot:
        print(f"  ↻ Backed up to {snapshot.relative_to(ROOT)}")
    else:
        print(f"  (no existing data to back up)")

    # Clear old project data
    for d in [DRAFTS, EPISODES]:
        if d.exists():
            for f in d.glob("EP-*.md"):
                f.unlink()
    if BATCH_BRIEFS.exists():
        for f in BATCH_BRIEFS.glob("batch*.md"):
            f.unlink()
    if LOCKS.exists():
        for f in LOCKS.iterdir():
            f.unlink()

    # Generate run.manifest.{md,json}
    _write_manifest(
        {
            "source_file": novel_name,
            "total_episodes": str(total_eps),
            "batch_size": str(batch_size),
            "key_episodes": key_eps,
            "adaptation_mode": "novel_to_short_drama",
            "adaptation_strategy": strategy,
            "dialogue_adaptation_intensity": intensity,
            "generation_execution_mode": "orchestrated_subagents",
            "generation_reset_mode": "clean_rebuild",
            "run_status": "active",
            "active_batch": "(none)",
            "source_authority": "original novel manuscript + harness/project/source.map.json",
            "draft_lane": "drafts/episodes",
            "publish_lane": "episodes",
            "promotion_policy": "controller_only_after_full_batch_verify",
            "framework_entry": "harness/framework/entry.md",
            "source_map": "harness/project/source.map.md",
            "current_batch_brief": "(none)",
            "regression_packs": "optional under harness/project/regressions/",
            "state_directory": "harness/project/state/",
        }
    )
    print(f"  + run.manifest.md / run.manifest.json")

    # Generate source.map.md with chapter spans pre-filled
    # Group episodes into batches and find chapter ranges
    source_map_lines = [
        f"# Source Map",
        f"",
        f"日期：{NOW.split()[0]}",
        f"模式：`{strategy}`",
        f"对话改编力度：`{intensity}`",
        f"执行方式：`orchestrated_subagents`",
        f"重建方式：`clean_rebuild`",
        f"",
        f"说明：",
        f"- 本文件是本轮 clean rebuild 的 controller-only 映射权威。",
        f"- 原著章节顺序优先；一章可拆多集，多个相邻章节可合拍。",
        f"- `must-not-add` / `must-not-jump` 为硬边界，writer subagent 不得自行突破。",
        f"",
    ]

    for b in range(total_batches):
        start_idx = b * batch_size
        end_idx = min(start_idx + batch_size, total_eps)
        batch_eps = ep_mapping[start_idx:end_idx]

        ep_start_id = batch_eps[0]["id"]
        ep_end_id = batch_eps[-1]["id"]

        # Determine chapter range for this batch
        spans = [ep["chapter_span"] for ep in batch_eps]
        first_ch = re.search(r"第(\d+)章", spans[0])
        last_ch = re.search(r"第(\d+)章", spans[-1])
        if first_ch and last_ch:
            ch_range = f"第{first_ch.group(1)}章 ~ 第{last_ch.group(1)}章" if first_ch.group(1) != last_ch.group(1) else f"第{first_ch.group(1)}章"
        else:
            ch_range = "（待填写）"

        source_map_lines.append(f"## Batch {b+1:02d}：{ep_start_id} ~ {ep_end_id}")
        source_map_lines.append(f"原著范围：{ch_range}")
        source_map_lines.append("")

        for ep in batch_eps:
            source_map_lines.append(f"### {ep['id']}")
            source_map_lines.append(f"- source chapter span：{ep['chapter_span']}")
            source_map_lines.append(f"- must-keep beats：（AGENT_EXTRACT_REQUIRED）")
            source_map_lines.append(f"- must-not-add / must-not-jump：（AGENT_EXTRACT_REQUIRED）")
            source_map_lines.append(f"- ending type：（AGENT_EXTRACT_REQUIRED）")
            source_map_lines.append("")

    source_map_content = "\n".join(source_map_lines)
    SOURCE_MAP.write_text(source_map_content, encoding="utf-8")
    SOURCE_MAP_JSON.write_text(
        json.dumps(_parse_source_map_markdown(source_map_content), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  + source.map.md / source.map.json ({total_batches} batches, {total_eps} episodes, chapter spans pre-filled)")

    # Generate state file templates
    STATE.mkdir(parents=True, exist_ok=True)
    state_templates = {
        "script.progress.md": "# Script Progress\n\n## 项目信息\n\n## 基础文档\n\n## 当前整季状态\n\n## 分集记录\n\n## 全局记录\n\n## 质量统计\n\n## 版本记录\n",
        "story.state.md": "# Story State\n\n## 当前阶段\n\n## 权力格局\n\n## 主要角色位置\n\n## 最近关键转折\n\n## 下一批关键预期\n",
        "relationship.board.md": "# Relationship Board\n\n## 核心关系网\n\n## 最近关系变动\n\n## 待爆关系线\n",
        "open_loops.md": "# Open Loops\n\n## 未回收伏笔\n\n## 未爆真相\n\n## 待解冲突\n\n## 已超期伏笔\n",
        "quality.anchor.md": "# Quality Anchor\n\n## 场景厚度\n\n## 对话节奏\n\n## os 使用方式\n\n## 代表性打法\n",
        "process.memory.md": "# Process Memory\n\n## 活跃流程问题\n\n## 当前执行准则\n",
        "run.log.md": f"# Run Log\n_最后更新：{NOW}_\n\n## Log Entries\n\n| 时间戳 | batch | episode | phase | event | result | 备注 |\n|---|---|---|---|---|---|---|\n",
    }
    for name, content in state_templates.items():
        (STATE / name).write_text(content, encoding="utf-8")
    print(f"  + state/ (7 template files)")

    # Always generate fresh character.md and voice-anchor.md
    char_path = ROOT / "character.md"
    voice_path = ROOT / "voice-anchor.md"
    char_path.write_text(f"# Character Reference\n\n（AGENT_EXTRACT_REQUIRED — 从 {novel_name} 自动提取）\n", encoding="utf-8")
    # voice-anchor: preserve framework sections (使用原则 + 格式警告), only reset character data
    voice_anchor_header = """\
# Voice Anchor

用于锁定关键角色的说话方式，防止全员同腔。

## 使用原则
- Writer 优先读取本文件；未列出的角色再回退到 `character.md`
- 若本文件只剩模板占位，视为未填写，直接回退到 `character.md`
- 没有原著时，只保留语音指纹；有原著时再补"原著样句 + 抽象特征"
- 这里只存说话方式，不复述人物经历
- 外显台词和 `os` 分开看：外显更克制，`os` 可以更短、更狠，但不能全员金句化

## 格式警告（所有角色通用）
本文件描述的是**角色说话内容的特征**（简洁、压迫、快节奏等），不是剧本排版指令。
- "短句"＝角色说话简洁利落，不等于每句话都要单独占一行
- "连打"/"连下两三句"＝角色一口气连续逼问或施压，通常写在同一行或相邻两行，不是拆成五六行
- 只有语义上有**刻意停顿、转折、施压节拍**时才换行
- 具体格式规则见 `write-contract.md` 的 Dialogue Formatting 章节

## 核心角色

（AGENT_EXTRACT_REQUIRED — 从 """ + novel_name + """ 自动提取）
"""
    voice_path.write_text(voice_anchor_header, encoding="utf-8")
    print(f"  + character.md (pending extraction)")
    print(f"  + voice-anchor.md (pending extraction)")

    # Ensure directories exist
    DRAFTS.mkdir(parents=True, exist_ok=True)
    EPISODES.mkdir(parents=True, exist_ok=True)
    BATCH_BRIEFS.mkdir(parents=True, exist_ok=True)
    LOCKS.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)
    _write_release_files(_release_index_template(), _gold_set_template())

    _append_log("-", "-", "plan_inputs", "project init", "✓", novel_name)

    print(f"\n{'='*50}")
    print(f"  PROJECT INITIALIZED — AGENT EXTRACTION REQUIRED")
    print(f"{'='*50}")
    print(f"\n  AGENT_EXTRACT_REQUIRED markers found in:")
    print(f"  - source.map.md (must-keep beats, must-not, ending type)")
    print(f"  - character.md")
    print(f"  - voice-anchor.md")
    print(f"\n  Agent must now execute the Init Extract Protocol (see AGENTS.md)")
    print(f"  to read {novel_name} and fill in all markers automatically.")

    return 0


def cmd_start(args: argparse.Namespace) -> int:
    """Full pipeline kickoff: generate brief (if missing) → freeze → lock → show context."""
    batch_id = args.batch_id

    batches = _parse_source_map()
    if batch_id not in batches:
        print(f"ERROR: '{batch_id}' not found in source.map")
        print(f"  Available: {', '.join(sorted(batches.keys()))}")
        return 1

    batch_info = batches[batch_id]
    episodes = batch_info["episodes"]

    # Check batch lock
    if _is_locked("batch.lock"):
        lock_data = _read_lock("batch.lock")
        owner = lock_data.get("owner", "?")
        if batch_id not in owner:
            print(f"ERROR: batch.lock held by '{owner}' — finish or unlock first")
            return 1

    # Find or auto-generate batch brief
    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        brief_content = _generate_batch_brief(batch_id, batch_info)
        ep_start_num = batch_info["ep_start"].replace("EP-", "")
        ep_end_num = batch_info["ep_end"].replace("EP-", "")
        batch_num = batch_info["batch_num"]
        fname = f"batch{batch_num}_EP{ep_start_num}-{ep_end_num}.md"
        brief_path = BATCH_BRIEFS / fname
        BATCH_BRIEFS.mkdir(parents=True, exist_ok=True)
        brief_path.write_text(brief_content, encoding="utf-8")
        print(f"  + Generated batch brief: {brief_path.name}")
    else:
        brief = _read_batch_brief(brief_path)
        if brief.get("status") == "promoted":
            print(f"ERROR: batch '{batch_id}' is already promoted")
            return 1
        print(f"  = Found existing brief: {brief_path.name}")

    # Freeze + lock
    _set_batch_status(brief_path, "frozen")
    _write_lock("batch.lock", "locked", f"controller:{batch_id}")
    print(f"  + Brief frozen, batch.lock acquired")

    # Clear retry counts and verify results from prior runs
    for ep in episodes:
        _clear_retry_count(ep)
        _clear_verify_result(ep)

    # Ensure draft lane
    DRAFTS.mkdir(parents=True, exist_ok=True)

    # Warn about existing published files that will be overwritten on promote
    existing = [ep for ep in episodes if (EPISODES / f"{ep}.md").exists()]
    if existing:
        print(f"  ⚠ Existing published files will be overwritten on promote: {', '.join(existing)}")

    # Update manifest
    _set_manifest_runtime(f"{batch_id}_{batch_info['ep_start']}-{batch_info['ep_end']}", brief_path)

    # Log
    _append_log(batch_id, "-", "plan_inputs", "batch brief 冻结", "✓", "controller start")

    # Print writer context
    print(f"\n{'='*50}")
    print(f"  BATCH STARTED: {batch_id}")
    print(f"  Episodes: {', '.join(episodes)}")
    print(f"  Source: {batch_info['source_range']}")
    print(f"{'='*50}")

    print(f"\n--- Writer Context ---")
    for ep in episodes:
        data = batch_info["episode_data"].get(ep, {})
        ending = data.get("ending_type", "")
        mk = data.get("must_keep", "")
        mn = data.get("must_not", "")
        print(f"  {ep} ({data.get('source_span', '')}) [{ending}]")
        print(f"    must-keep: {mk[:80]}{'...' if len(mk) > 80 else ''}")
        print(f"    must-not:  {mn[:80]}{'...' if len(mn) > 80 else ''}")

    # Verify plan
    full_eps, standard_eps, light_eps = _compute_verify_tiers(episodes)
    print(f"\n--- Verify Plan ---")
    print(f"  FULL (8-step):     {', '.join(full_eps) or '(none)'}")
    print(f"  STANDARD (5-step): {', '.join(standard_eps) or '(none)'}")
    print(f"  LIGHT (lint only): {', '.join(light_eps) or '(none)'}")

    print(f"\n--- Next Step ---")
    print(f"  Writer agent: draft {', '.join(episodes)} into drafts/episodes/")
    print(f"  Then run: python _ops/controller.py check {batch_id}")

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Gate (lint all) + verify-plan + semantic verify instructions."""
    batch_id = args.batch_id
    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for '{batch_id}'")
        return 1

    brief = _read_batch_brief(brief_path)
    episodes = brief.get("episodes", [])
    if not episodes:
        print(f"ERROR: no episodes in batch '{batch_id}'")
        return 1

    # Step 1: Lint gate
    print(f"=== Lint Gate: {batch_id} ===")
    all_pass = True
    for ep in episodes:
        draft = DRAFTS / f"{ep}.md"
        if not draft.exists():
            print(f"  ✗ {ep}: draft missing")
            all_pass = False
            continue
        try:
            data = _run_lint(draft)
            status = data.get("status", "fail")
            is_fail = _lint_blocks_promote(data)
        except ValueError:
            status = "error"
            is_fail = True
        icon = "✓" if not is_fail else "✗"
        print(f"  {icon} {ep}: {status}")
        if is_fail:
            all_pass = False

    if not all_pass:
        print(f"\n  GATE FAIL — fix lint errors before proceeding")
        return 1

    print(f"\n  GATE PASS")

    # Step 2: Verify plan
    full_eps, standard_eps, light_eps = _compute_verify_tiers(episodes)
    print(f"\n=== Verify Plan ===")
    print(f"  FULL (8-step):     {', '.join(full_eps) or '(none)'}")
    print(f"  STANDARD (5-step): {', '.join(standard_eps) or '(none)'}")
    print(f"  LIGHT (lint only): {', '.join(light_eps) or '(none)'}")

    # Step 3: Semantic verify instructions
    print(f"\n=== Semantic Verify Instructions (for Aligner agent) ===")
    if full_eps:
        print(f"\n  FULL episodes ({', '.join(full_eps)}):")
        print(f"  Execute all 8 steps per script-aligner.md:")
        print(f"    1. Lint Gate (already passed)")
        print(f"    2. Fail Closed Gate (6 items)")
        print(f"    3. Adversarial Checks (6 tests)")
        print(f"    4. Voice Fingerprint")
        print(f"    5. Expression Density & Dialogue Drift")
        print(f"    6. WARNING Accumulation & Regression Gate")
        print(f"    7. Quality Anchor Benchmark")
        print(f"    8. Judgment & Output")
    if standard_eps:
        print(f"\n  STANDARD episodes ({', '.join(standard_eps)}):")
        print(f"  Execute steps 1-2-3-5-8 per script-aligner.md:")
        print(f"    1. Lint Gate (already passed)")
        print(f"    2. Fail Closed Gate")
        print(f"    3. Adversarial Checks")
        print(f"    5. Expression Density & Dialogue Drift")
        print(f"    8. Judgment & Output")
    if light_eps:
        print(f"\n  LIGHT episodes ({', '.join(light_eps)}):")
        print(f"  Lint only — already passed above")

    # Step 4: Show verify result reporting instructions
    print(f"\n=== Report Verify Results ===")
    print(f"  After aligner completes each episode, report:")
    for ep in episodes:
        if ep in light_eps:
            continue
        tier = "FULL" if ep in full_eps else "STANDARD"
        print(f"    python _ops/controller.py verify-done {ep} PASS --tier {tier} --batch {batch_id}")
    print(f"\n  If an episode fails:")
    print(f"    python _ops/controller.py verify-done <EP-XX> FAIL --tier <tier> --batch {batch_id}")

    print(f"\n--- Next Step ---")
    print(f"  After all verify PASS: python _ops/controller.py finish {batch_id}")

    return 0


def cmd_finish(args: argparse.Namespace) -> int:
    """Promote + validate + batch-review + log + next instructions."""
    batch_id = args.batch_id
    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for '{batch_id}'")
        return 1

    brief = _read_batch_brief(brief_path)
    episodes = brief.get("episodes", [])
    current_status = brief.get("status", "unknown")

    if current_status == "promoted":
        print(f"ERROR: batch '{batch_id}' is already promoted")
        return 1
    if current_status != "frozen":
        print(f"ERROR: batch brief status is '{current_status}', must be 'frozen'")
        return 1

    # Step 1: Final lint gate
    print(f"=== Step 1: Lint Gate ===")
    lint_results: dict[str, dict] = {}
    for ep in episodes:
        draft = DRAFTS / f"{ep}.md"
        if not draft.exists():
            print(f"  ✗ {ep}: draft missing")
            return 1
        try:
            data = _run_lint(draft)
            lint_results[ep] = data
            if _lint_blocks_promote(data):
                print(f"  ✗ {ep} lint FAIL (contract_failures: {data.get('contract_failures', [])}) — cannot finish")
                return 1
        except ValueError:
            print(f"  ✗ {ep} lint error — cannot finish")
            return 1
        print(f"  ✓ {ep} lint {data.get('status', 'pass')}")

    # Step 2: Verify gate — all non-LIGHT episodes must have verify PASS
    print(f"\n=== Step 2: Verify Gate ===")
    full_eps, standard_eps, light_eps = _compute_verify_tiers(episodes)
    for ep in episodes:
        if ep in light_eps:
            print(f"  ✓ {ep}: LIGHT (lint-only)")
            continue
        vr = _read_verify_result(ep)
        if vr is None:
            print(f"  ✗ {ep}: no verify result — run aligner + verify-done first")
            return 1
        if vr.get("status") != "PASS":
            print(f"  ✗ {ep}: verify {vr.get('status', '?')}")
            return 1
        print(f"  ✓ {ep}: verify PASS (tier: {vr.get('tier', '?')})")

    # Step 3: State lock check
    if _is_locked("state.lock"):
        print("ERROR: state.lock is held — cannot finish")
        return 1

    # Step 4: Promote
    print(f"\n=== Step 3: Promote ===")
    rc, _ = _promote_batch(batch_id, brief_path, episodes, lint_results)
    if rc != 0:
        print("  ✗ staging promote failed")
        return 1
    for ep in episodes:
        print(f"  → {ep}: staging → published")

    _set_batch_status(brief_path, "promoted")
    _write_lock("batch.lock", "unlocked")

    for ep in episodes:
        _clear_retry_count(ep)

    ep_range = f"{episodes[0]}~{episodes[-1]}" if len(episodes) > 1 else episodes[0]
    _append_log(batch_id, ep_range, "promote", "controller promote", "✓", f"{batch_id} promoted")
    _set_manifest_runtime(f"{batch_id}_promoted", brief_path)
    print(f"  ✓ {len(episodes)} episodes promoted, batch.lock released")

    # Step 5: Validate state files
    print(f"\n=== Step 4: State Validation ===")
    all_valid = True
    for name, sections in TEMPLATE_SECTIONS.items():
        errors = _validate_state_file(name, sections)
        if errors:
            all_valid = False
            for e in errors:
                print(f"  ⚠ {e}")
        else:
            print(f"  ✓ {name}")
    if not all_valid:
        print(f"  WARNING: state files have gaps — recorder should fix before next batch")

    # Step 6: Batch review sampling
    print(f"\n=== Step 5: Batch Review ===")
    sample_size = min(2, len(episodes))
    sampled = random.sample(episodes, sample_size)
    print(f"  Sampled for adversarial deep-check: {', '.join(sampled)}")
    print(f"  Checklist (on sampled episodes):")
    print(f"  [ ] 1. 角色替换测试")
    print(f"  [ ] 2. 删除测试")
    print(f"  [ ] 3. 逻辑反推测试")
    print(f"  [ ] 4. 钩子有效性测试")
    print(f"  [ ] 5. 画面感测试")
    print(f"  [ ] 6. 表里不一测试")
    print(f"  Checklist (batch-level):")
    print(f"  [ ] 7. 质量锚对标")
    print(f"  [ ] 8. 批次内声纹一致性")
    print(f"  [ ] 9. 批次内伏笔连续性")

    # Step 7: Determine next batch
    batches = _parse_source_map()
    batch_ids = sorted(batches.keys())
    try:
        idx = batch_ids.index(batch_id)
        next_batch = batch_ids[idx + 1] if idx + 1 < len(batch_ids) else None
    except ValueError:
        next_batch = None

    print(f"\n{'='*50}")
    print(f"  BATCH FINISHED: {batch_id}")
    print(f"{'='*50}")
    print(f"\n--- Next Steps ---")
    print(f"  1. Run record phase: python _ops/controller.py record {batch_id}")
    print(f"     (acquires state.lock, prints recorder instructions)")
    print(f"  2. Recorder agent: update all 6 state files per script-recorder.md")
    print(f"  3. Seal record:    python _ops/controller.py record-done {batch_id}")
    print(f"     (validates state files, releases state.lock)")
    if next_batch:
        next_info = batches[next_batch]
        print(f"  4. Start next:     python _ops/controller.py start {next_batch}")
        print(f"     ({next_info['ep_start']} ~ {next_info['ep_end']}, {next_info['source_range']})")
    else:
        print(f"  4. All batches complete!")

    return 0


def cmd_next(args: argparse.Namespace) -> int:
    """Determine and display next batch to work on."""
    manifest = _read_manifest()
    active = manifest.get("active_batch", "")

    batches = _parse_source_map()
    batch_ids = sorted(batches.keys())

    promoted = []
    pending = []
    for bid in batch_ids:
        brief_path = _find_batch_brief(bid)
        if brief_path:
            brief = _read_batch_brief(brief_path)
            if brief.get("status") == "promoted":
                promoted.append(bid)
                continue
        pending.append(bid)

    print(f"=== Pipeline Progress ===")
    print(f"  Promoted: {', '.join(promoted) or '(none)'}")
    print(f"  Pending:  {', '.join(pending) or '(none)'}")
    print(f"  Active:   {active}")
    print(f"  Total:    {len(promoted)}/{len(batch_ids)} batches done")

    if _is_locked("batch.lock"):
        lock_data = _read_lock("batch.lock")
        owner = lock_data.get("owner", "?")
        print(f"\n  batch.lock held by '{owner}'")
        print(f"  Finish or unlock current batch before starting next")
        return 0

    if not pending:
        print(f"\n  All {len(batch_ids)} batches promoted — production complete!")
        return 0

    next_batch = pending[0]
    next_info = batches[next_batch]

    print(f"\n=== Next Batch: {next_batch} ===")
    print(f"  Episodes: {', '.join(next_info['episodes'])}")
    print(f"  Source:   {next_info['source_range']}")
    print(f"\n  To start: python _ops/controller.py start {next_batch}")

    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    """Check manifest, release index, episodes, sidecar metadata, and verify status consistency."""
    errors: list[str] = []

    manifest = _read_manifest()
    active_batch = manifest.get("active_batch", "(none)")
    current_batch_brief = manifest.get("current_batch_brief", "(none)")
    active_batch_match = re.match(r"(batch\d+)", active_batch)
    active_batch_id = active_batch_match.group(1) if active_batch_match else None

    if current_batch_brief != "(none)":
        brief_path = ROOT / current_batch_brief
        if not brief_path.exists():
            errors.append(f"manifest current_batch_brief missing: {current_batch_brief}")
        elif active_batch_id and active_batch_id not in brief_path.stem:
            errors.append(f"manifest mismatch: active_batch={active_batch} current_batch_brief={current_batch_brief}")

    if not RELEASE_INDEX.exists():
        errors.append("release.index.json missing")
    if not GOLD_SET.exists():
        errors.append("gold-set.json missing")

    release_index = _load_release_index()
    gold_set = _load_gold_set()
    release_episodes = release_index.get("episodes", {})
    gold_episodes = set(gold_set.get("episodes", []))

    if active_batch_id and release_index.get("current_batch", "(none)") not in {"(none)", active_batch_id}:
        errors.append(
            f"release.index current_batch mismatch: {release_index.get('current_batch')} vs manifest {active_batch_id}"
        )
    if current_batch_brief != "(none)" and release_index.get("current_batch_brief", "(none)") not in {"(none)", current_batch_brief}:
        errors.append(
            "release.index current_batch_brief mismatch: "
            f"{release_index.get('current_batch_brief')} vs manifest {current_batch_brief}"
        )

    for episode_file in sorted(EPISODES.glob("EP-*.md")):
        episode = episode_file.stem
        entry = release_episodes.get(episode)
        if entry is None:
            errors.append(f"release.index missing episode entry: {episode}")
            continue

        meta_path = _meta_path(episode)
        release_status = entry.get("release_status")
        if release_status == "legacy":
            if meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if meta.get("release_status") != "legacy":
                    errors.append(f"{episode} legacy release entry conflicts with meta status {meta.get('release_status')}")
            continue

        if not meta_path.exists():
            errors.append(f"{episode} missing metadata sidecar")
            continue

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        for field in [
            "episode",
            "provenance",
            "source_batch",
            "runtime_authority",
            "release_status",
            "ruleset_version",
            "lint_profile",
            "lint_status",
            "verify_tier",
            "verify_status",
        ]:
            if field not in meta:
                errors.append(f"{episode} metadata missing field: {field}")

        if meta.get("episode") != episode:
            errors.append(f"{episode} metadata episode mismatch: {meta.get('episode')}")
        if meta.get("release_status") != release_status:
            errors.append(f"{episode} release_status mismatch: meta={meta.get('release_status')} index={release_status}")
        if meta.get("runtime_authority") != entry.get("runtime_authority"):
            errors.append(
                f"{episode} runtime_authority mismatch: meta={meta.get('runtime_authority')} index={entry.get('runtime_authority')}"
            )
        if meta.get("lint_status") != entry.get("lint_status"):
            errors.append(f"{episode} lint_status mismatch: meta={meta.get('lint_status')} index={entry.get('lint_status')}")
        if meta.get("verify_status") != entry.get("verify_status"):
            errors.append(
                f"{episode} verify_status mismatch: meta={meta.get('verify_status')} index={entry.get('verify_status')}"
            )

        verify_result = _read_verify_result(episode)
        if verify_result is None:
            errors.append(f"{episode} missing verify result")
        else:
            if verify_result.get("tier") != meta.get("verify_tier"):
                errors.append(
                    f"{episode} verify_tier mismatch: meta={meta.get('verify_tier')} verify={verify_result.get('tier')}"
                )
            if verify_result.get("status") != meta.get("verify_status"):
                errors.append(
                    f"{episode} verify_status mismatch: meta={meta.get('verify_status')} verify={verify_result.get('status')}"
                )

        if release_status == "gold" and episode not in gold_episodes:
            errors.append(f"{episode} is gold in release.index but missing from gold-set")

    for episode in gold_episodes:
        entry = release_episodes.get(episode)
        if entry is None:
            errors.append(f"gold-set references unknown episode: {episode}")
        elif entry.get("release_status") != "gold":
            errors.append(f"gold-set episode {episode} has non-gold status {entry.get('release_status')}")

    for meta_path in sorted(EPISODES.glob("EP-*.meta.json")):
        episode = meta_path.name.replace(".meta.json", "")
        if episode not in release_episodes:
            errors.append(f"orphan metadata sidecar: {meta_path.name}")

    if errors:
        print("AUDIT FAIL")
        for item in errors:
            print(f"  ✗ {item}")
        return 1

    print("AUDIT OK")
    print(f"  active_batch: {active_batch}")
    print(f"  current_batch_brief: {current_batch_brief}")
    print(f"  release episodes: {len(release_episodes)}")
    print(f"  gold episodes: {len(gold_episodes)}")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Harness V2 Controller")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Show pipeline state")

    p_plan = sub.add_parser("plan", help="Freeze batch brief and acquire lock")
    p_plan.add_argument("batch_id", help="e.g. batch01, batch02")

    p_lint = sub.add_parser("lint", help="Run lint on a draft episode")
    p_lint.add_argument("episode", help="e.g. EP-01")

    p_gate = sub.add_parser("gate", help="Check all drafts in batch passed lint")
    p_gate.add_argument("batch_id")

    p_promote = sub.add_parser("promote", help="Promote batch: copy drafts → episodes")
    p_promote.add_argument("batch_id")

    sub.add_parser("validate", help="Check state files against templates")
    sub.add_parser("audit", help="Check release tracking and verify consistency")

    p_log = sub.add_parser("log", help="Append to run.log.md")
    p_log.add_argument("phase", help="plan_inputs|draft_write|verify|promote|record|recovery")
    p_log.add_argument("event", help="Event description")
    p_log.add_argument("--batch", default=None)
    p_log.add_argument("--episode", default=None)
    p_log.add_argument("--result", default=None)
    p_log.add_argument("--note", default=None)

    p_retry = sub.add_parser("retry", help="Show/manage verify retry count")
    p_retry.add_argument("episode", help="e.g. EP-06")
    p_retry.add_argument("--increment", action="store_true", help="Increment failure count")
    p_retry.add_argument("--reset", action="store_true", help="Reset failure count to 0")

    p_vplan = sub.add_parser("verify-plan", help="Compute verify tiers for a batch")
    p_vplan.add_argument("batch_id")

    p_breview = sub.add_parser("batch-review", help="Generate batch-level review checklist")
    p_breview.add_argument("batch_id")

    p_unlock = sub.add_parser("unlock", help="Release a lock")
    p_unlock.add_argument("lock_name", help="batch|episode|state|all")

    # Project init
    p_init = sub.add_parser("init", help="Scaffold a new project from a novel file")
    p_init.add_argument("novel_file", help="Path to novel manuscript (relative to project root)")
    p_init.add_argument("--episodes", type=int, default=60, help="Total episode count (default: 60)")
    p_init.add_argument("--batch-size", type=int, default=5, help="Episodes per batch (default: 5)")
    p_init.add_argument("--strategy", default="original_fidelity", help="Adaptation strategy")
    p_init.add_argument("--intensity", default="light", help="Dialogue adaptation intensity")
    p_init.add_argument("--key-episodes", default="", help="Comma-separated key episode IDs for FULL verify")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing project data (auto-backup first)")

    # Verify / record gate commands
    p_vdone = sub.add_parser("verify-done", help="Record verify result for an episode")
    p_vdone.add_argument("episode", help="e.g. EP-06")
    p_vdone.add_argument("status", help="PASS or FAIL")
    p_vdone.add_argument("--tier", default=None, help="FULL|STANDARD|LIGHT")
    p_vdone.add_argument("--batch", default=None, help="batch ID for logging")

    p_record = sub.add_parser("record", help="Start record phase (acquire state.lock)")
    p_record.add_argument("batch_id")

    p_rdone = sub.add_parser("record-done", help="Seal record phase (validate + release lock)")
    p_rdone.add_argument("batch_id")

    # High-level orchestration
    p_start = sub.add_parser("start", help="Full batch kickoff (brief → freeze → lock → context)")
    p_start.add_argument("batch_id", help="e.g. batch02")

    p_check = sub.add_parser("check", help="Lint gate + verify-plan + verify instructions")
    p_check.add_argument("batch_id")

    p_finish = sub.add_parser("finish", help="Promote + validate + batch-review + next")
    p_finish.add_argument("batch_id")

    sub.add_parser("next", help="Show pipeline progress and next batch")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "status": cmd_status,
        "plan": cmd_plan,
        "lint": cmd_lint,
        "gate": cmd_gate,
        "promote": cmd_promote,
        "validate": cmd_validate,
        "audit": cmd_audit,
        "log": cmd_log,
        "retry": cmd_retry,
        "verify-plan": cmd_verify_plan,
        "batch-review": cmd_batch_review,
        "unlock": cmd_unlock,
        "verify-done": cmd_verify_done,
        "record": cmd_record,
        "record-done": cmd_record_done,
        "init": cmd_init,
        "start": cmd_start,
        "check": cmd_check,
        "finish": cmd_finish,
        "next": cmd_next,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
