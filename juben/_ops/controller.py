#!/usr/bin/env python3
"""
Harness V2 Controller — programmatic gate enforcement.

Project setup:
  init <novel_file>      Scaffold new project (manifest, source.map, state templates)
  extract-book          Fill book.blueprint.md from the full novel
  map-book              Generate source.map.md from book.blueprint.md

Orchestration commands:
  start <batch_id>       Total entry: prepare → writer stage → run pipeline
  run <batch_id>         Full pipeline: lint → auto-verify → promote → review → next
  check <batch_id>       Lint gate + verify-plan + verify instructions
  finish <batch_id>      Lint gate + verify gate + promote + validate + batch-review
  next                   Show pipeline progress and next batch to start

Verify / record gate commands:
  verify-done <EP> <S>   Record verify result (PASS/FAIL) for an episode
  record <batch_id>      Start record phase: acquire state.lock, print instructions
  record-done <batch_id> Seal record phase: validate state files, release state.lock

Low-level commands:
  status                 Show current pipeline state (with batch ownership)
  clean                  Backup + clear runtime project data cache
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
import hashlib
import json
import os
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
RUN_LOG = STATE / "run.log.md"
MEMORY_CONTRACT = FRAMEWORK / "memory-contract.md"
BOOK_BLUEPRINT = PROJECT / "book.blueprint.md"
SOURCE_MAP = PROJECT / "source.map.md"
RELEASES = PROJECT / "releases"
RELEASE_INDEX = RELEASES / "release.index.json"
GOLD_SET = RELEASES / "gold-set.json"

RUNTIME_AUTHORITY = "rebuild-2026-04"
RULESET_VERSION = "episode-lint/v2"
LINT_PROFILE = "default"

NOW = datetime.now().strftime("%Y-%m-%d %H:%M")
WRITER_COMMAND_ENV = "JUBEN_WRITER_COMMAND"
DEFAULT_WRITER_PARALLELISM = 3
DEFAULT_TARGET_EPISODE_MINUTES = 2
DEFAULT_EPISODE_MINUTES_MIN = 1
DEFAULT_EPISODE_MINUTES_MAX = 3
PENDING_TOTAL_EPISODES = "pending_model_recommendation"
PENDING_RECOMMENDED_TOTAL_EPISODES = "pending_book_extraction"
PENDING_BLUEPRINT_RECOMMENDATION = "pending_extraction"
PENDING_TOTAL_BATCHES = "pending_total_episodes"


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

def _read_manifest() -> dict:
    content = RUN_MANIFEST.read_text(encoding="utf-8")
    data = {}
    for line in content.splitlines():
        m = re.match(r"^- (\w[\w_]*):\s*(.+)$", line)
        if m:
            data[m.group(1)] = m.group(2).strip()
    return data


def _set_manifest_field(field: str, value: str) -> None:
    content = RUN_MANIFEST.read_text(encoding="utf-8")
    content = re.sub(
        rf"(^- {field}:\s*).+$",
        rf"\g<1>{value}",
        content,
        flags=re.MULTILINE,
    )
    RUN_MANIFEST.write_text(content, encoding="utf-8")


def _set_manifest_line(label: str, value: str) -> None:
    content = RUN_MANIFEST.read_text(encoding="utf-8")
    pattern = rf"(^- {re.escape(label)}:\s*).+$"
    replacement = rf"\g<1>{value}"
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        content = content.rstrip() + f"\n- {label}: {value}\n"
    RUN_MANIFEST.write_text(content, encoding="utf-8")


def _manifest_source_file() -> str | None:
    return _read_manifest().get("source_file")


def _manifest_source_path() -> Path | None:
    source_file = _manifest_source_file()
    if not source_file:
        print("ERROR: run.manifest.md is missing source_file")
        return None
    novel_path = ROOT / source_file
    if not novel_path.exists():
        print(f"ERROR: source novel file not found: {novel_path}")
        return None
    return novel_path


def _book_blueprint_has_placeholders() -> bool:
    if not BOOK_BLUEPRINT.exists():
        return True
    content = BOOK_BLUEPRINT.read_text(encoding="utf-8")
    return "AGENT_EXTRACT_REQUIRED" in content or re.search(r"^- extraction_status:\s*pending$", content, re.MULTILINE) is not None


def _recommended_total_episodes_from_blueprint() -> int | None:
    if not BOOK_BLUEPRINT.exists():
        return None
    content = BOOK_BLUEPRINT.read_text(encoding="utf-8")
    match = re.search(r"^- recommended_total_episodes:\s*(\d+)\s*$", content, re.MULTILINE)
    if not match:
        return None
    return int(match.group(1))


def _parse_manifest_int(field: str) -> int | None:
    value = _read_manifest().get(field, "")
    return int(value) if value.isdigit() else None


def _sync_recommended_episode_count_from_blueprint() -> int | None:
    recommended = _recommended_total_episodes_from_blueprint()
    if recommended is None:
        return None

    _set_manifest_field("recommended_total_episodes", str(recommended))
    manifest = _read_manifest()
    if manifest.get("episode_count_source", "model_recommended") == "model_recommended":
        _set_manifest_field("total_episodes", str(recommended))
    return recommended


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
# Content fingerprinting
# ---------------------------------------------------------------------------

def _file_sha256(path: Path) -> str:
    """Return hex SHA-256 of a file, or empty string if missing."""
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    draft_path = DRAFTS / f"{episode}.md"
    brief_name = _find_brief_for_episode(episode)
    if not brief_name:
        print(f"WARNING: no batch brief found for {episode} — brief_sha256 will be empty")
    brief_sha = _file_sha256(BATCH_BRIEFS / brief_name) if brief_name else ""
    data = {
        "episode": episode,
        "tier": tier,
        "status": status,
        "timestamp": NOW,
        "draft_sha256": _file_sha256(draft_path),
        "brief_sha256": brief_sha,
        "source_map_sha256": _file_sha256(SOURCE_MAP),
    }
    _verify_result_path(episode).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8",
    )


def _find_brief_for_episode(episode: str) -> str:
    """Find the batch brief filename that owns this episode."""
    if BATCH_BRIEFS.exists():
        for p in BATCH_BRIEFS.glob("*.md"):
            content = p.read_text(encoding="utf-8")
            if episode in content:
                return p.name
    return ""


def _verify_draft_integrity(episode: str, verify_result: dict) -> str | None:
    """Check that draft, brief, and source_map match what was verified. Returns error message or None."""
    # Draft check
    recorded_draft = verify_result.get("draft_sha256", "")
    if not recorded_draft:
        return None  # legacy verify result without hash — skip check
    current_draft = _file_sha256(DRAFTS / f"{episode}.md")
    if current_draft != recorded_draft:
        return (
            f"{episode} draft modified after verify "
            f"(verified: {recorded_draft[:12]}…, current: {current_draft[:12]}…)"
        )
    # Brief check
    recorded_brief = verify_result.get("brief_sha256", "")
    if recorded_brief:
        brief_name = _find_brief_for_episode(episode)
        current_brief = _file_sha256(BATCH_BRIEFS / brief_name) if brief_name else ""
        if current_brief != recorded_brief:
            return (
                f"{episode} batch brief modified after verify "
                f"(verified: {recorded_brief[:12]}…, current: {current_brief[:12]}…)"
            )
    # Source map check
    recorded_smap = verify_result.get("source_map_sha256", "")
    if recorded_smap:
        current_smap = _file_sha256(SOURCE_MAP)
        if current_smap != recorded_smap:
            return (
                f"{episode} source.map.md modified after verify "
                f"(verified: {recorded_smap[:12]}…, current: {current_smap[:12]}…)"
            )
    return None


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


def _state_templates(now: str | None = None) -> dict[str, str]:
    stamp = now or NOW
    return {
        "script.progress.md": "# Script Progress\n\n## 项目信息\n\n## 基础文档\n\n## 当前整季状态\n\n## 分集记录\n\n## 全局记录\n\n## 质量统计\n\n## 版本记录\n",
        "story.state.md": "# Story State\n\n## 当前阶段\n\n## 权力格局\n\n## 主要角色位置\n\n## 最近关键转折\n\n## 下一批关键预期\n",
        "relationship.board.md": "# Relationship Board\n\n## 核心关系网\n\n## 最近关系变动\n\n## 待爆关系线\n",
        "open_loops.md": "# Open Loops\n\n## 未回收伏笔\n\n## 未爆真相\n\n## 待解冲突\n\n## 已超期伏笔\n",
        "quality.anchor.md": "# Quality Anchor\n\n## 场景厚度\n\n## 对话节奏\n\n## os 使用方式\n\n## 代表性打法\n",
        "process.memory.md": "# Process Memory\n\n## 活跃流程问题\n\n## 当前执行准则\n",
        "run.log.md": f"# Run Log\n_最后更新：{stamp}_\n\n## Log Entries\n\n| 时间戳 | batch | episode | phase | event | result | 备注 |\n|---|---|---|---|---|---|---|\n",
    }


def _write_state_templates(now: str | None = None) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    for name, content in _state_templates(now).items():
        (STATE / name).write_text(content, encoding="utf-8")


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


def _normalize_episode_id(raw: str) -> str:
    match = re.search(r"EP-?(\d+)", raw.strip(), re.IGNORECASE)
    if not match:
        return raw.strip()
    return f"EP-{match.group(1).zfill(2)}"


def _collapse_markdown_list(raw: str) -> str:
    items = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        items.append(stripped)
    return "；".join(items).strip()


def _extract_episode_map_field(
    ep_block: str,
    *,
    legacy_pattern: str,
    markdown_pattern: str,
    multiline: bool = False,
) -> str:
    match = re.search(legacy_pattern, ep_block)
    if match:
        return match.group(1).strip()

    flags = re.DOTALL if multiline else 0
    match = re.search(markdown_pattern, ep_block, flags)
    if not match:
        return ""

    value = match.group(1).strip()
    if multiline:
        return _collapse_markdown_list(value)
    return value


def _source_map_episode_block(source_map_text: str, episode_id: str) -> str:
    digits = re.search(r"(\d+)", episode_id)
    if not digits:
        return ""
    normalized = str(int(digits.group(1)))
    pattern = rf"###\s+EP-?0*{normalized}\b(.*?)(?=^###\s+EP-?\d+|\Z)"
    match = re.search(pattern, source_map_text, re.DOTALL | re.MULTILINE)
    return match.group(1) if match else ""


def _parse_source_map() -> dict:
    """Parse source.map.md into structured batch data."""
    content = SOURCE_MAP.read_text(encoding="utf-8")
    batches = {}

    batch_blocks = re.split(r"(?=^## Batch \d+)", content, flags=re.MULTILINE)

    for block in batch_blocks:
        if not block.startswith("## Batch "):
            continue

        batch_num = ""
        ep_start = ""
        ep_end = ""
        source_range = ""
        batch_title = ""

        legacy_match = re.match(r"## Batch (\d+)：(EP-?\d+)\s*~\s*(EP-?\d+)\s*\n原著范围：(.+)", block)
        if legacy_match:
            batch_num = legacy_match.group(1).zfill(2)
            ep_start = _normalize_episode_id(legacy_match.group(2))
            ep_end = _normalize_episode_id(legacy_match.group(3))
            source_range = legacy_match.group(4).strip()
        else:
            header = block.splitlines()[0].strip()
            modern_match = re.match(
                r"## Batch (\d+)\s+\((EP-?\d+)\s*-\s*(?:EP-?)?(\d+)\)\s*:\s*(.+)",
                header,
            )
            if not modern_match:
                continue
            batch_num = modern_match.group(1).zfill(2)
            ep_start = _normalize_episode_id(modern_match.group(2))
            ep_end = _normalize_episode_id(f"EP{modern_match.group(3)}")
            batch_title = modern_match.group(4).strip()

        batch_id = f"batch{batch_num}"

        episode_data = {}
        ep_blocks = re.split(r"(?=^###\s+EP-?\d+)", block, flags=re.MULTILINE)
        episodes = []

        for ep_block in ep_blocks:
            ep_m = re.match(r"###\s+(EP-?\d+)", ep_block)
            if not ep_m:
                continue
            ep_id = _normalize_episode_id(ep_m.group(1))
            episodes.append(ep_id)

            episode_data[ep_id] = {
                "source_span": _extract_episode_map_field(
                    ep_block,
                    legacy_pattern=r"source chapter span：(.+)",
                    markdown_pattern=r"\*\*source_chapter_span\*\*:\s*(.+)",
                ),
                "must_keep": _extract_episode_map_field(
                    ep_block,
                    legacy_pattern=r"must-keep beats：(.+)",
                    markdown_pattern=r"\*\*must-keep_beats\*\*:\s*(.*?)(?=\n\*\*|\n---|\Z)",
                    multiline=True,
                ),
                "must_not": _extract_episode_map_field(
                    ep_block,
                    legacy_pattern=r"must-not-add / must-not-jump：(.+)",
                    markdown_pattern=r"\*\*must-not-add / must-not-jump\*\*:\s*(.*?)(?=\n\*\*|\n---|\Z)",
                    multiline=True,
                ),
                "ending_type": _extract_episode_map_field(
                    ep_block,
                    legacy_pattern=r"ending type：(.+)",
                    markdown_pattern=r"\*\*ending_type\*\*:\s*(.+)",
                ),
            }

        if not source_range:
            spans = [episode_data[ep]["source_span"] for ep in episodes if episode_data.get(ep, {}).get("source_span")]
            if spans:
                source_range = spans[0] if spans[0] == spans[-1] else f"{spans[0]} ~ {spans[-1]}"
            else:
                source_range = batch_title

        batches[batch_id] = {
            "batch_num": batch_num,
            "ep_start": ep_start,
            "ep_end": ep_end,
            "episodes": episodes,
            "source_range": source_range,
            "episode_data": episode_data,
        }

    return batches


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


def _compute_verify_tiers(episodes: list[str]) -> tuple[list, list, list, list]:
    """Compute FULL/STANDARD/LIGHT verify tiers for a list of episodes.

    Returns (full, standard, light, unmapped).
    Unmapped episodes have no source-map data — they should not be silently
    downgraded to LIGHT. Callers decide whether to hard-fail or require review.
    """
    source_map_text = SOURCE_MAP.read_text(encoding="utf-8")
    manifest = _read_manifest()
    key_episodes_raw = manifest.get("key_episodes", "")
    key_episodes = {e.strip() for e in key_episodes_raw.split(",") if e.strip()}

    full_eps, standard_eps, light_eps, unmapped_eps = [], [], [], []
    for i, ep in enumerate(episodes):
        block = _source_map_episode_block(source_map_text, ep)
        if not block.strip():
            unmapped_eps.append(ep)
            continue
        is_first = (i == 0)
        is_strong_closure = "强闭环" in block
        is_key_episode = ep in key_episodes
        if is_first or is_strong_closure or is_key_episode:
            full_eps.append(ep)
        else:
            standard_eps.append(ep)
    return full_eps, standard_eps, light_eps, unmapped_eps


# ---------------------------------------------------------------------------
# Release / Gold tracking helpers
# ---------------------------------------------------------------------------


def _relative_to_root(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json_file(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


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
    """Register any published episodes not in gold set as 'legacy'."""
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
    checks = lint_payload.get("checks", {})
    return {
        "episode": episode,
        "provenance": RUNTIME_AUTHORITY,
        "source_batch": batch_id,
        "runtime_authority": RUNTIME_AUTHORITY,
        "release_status": release_status,
        "ruleset_version": RULESET_VERSION,
        "lint_profile": LINT_PROFILE,
        "lint_status": lint_payload.get("status", "fail"),
        "verify_tier": verify_result.get("tier", "STANDARD"),
        "verify_status": verify_result.get("status", "MISSING"),
        "episode_failures": checks.get("episode_failures", []),
        "scene_failures": checks.get("scene_failures", []),
        "warnings": checks.get("warnings", []),
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


def _promote_batch(
    batch_id: str, brief_path: Path, episodes: list[str], lint_results: dict[str, dict]
) -> tuple[int, dict]:
    """Staged promote: build metadata in staging dir → replace files sequentially.

    NOTE: The replace loop is NOT atomic. A crash mid-replace can leave partial
    state (some episodes updated, release index not yet). The staging dir is
    cleaned up in the finally block, so forward-recovery from staged artifacts
    is not yet possible. See project memory 'promote atomicity gap' for the
    deferred journal-based recovery design.
    """
    stage_root = RELEASES / "staging" / f"{batch_id}-{NOW.replace(':', '').replace(' ', '-')}"
    stage_root.mkdir(parents=True, exist_ok=True)

    staged_episode_files: dict[str, Path] = {}
    staged_meta_files: dict[str, Path] = {}
    try:
        # Stage draft files
        for episode in episodes:
            src = DRAFTS / f"{episode}.md"
            staged = stage_root / f"{episode}.md"
            shutil.copy2(src, staged)
            staged_episode_files[episode] = staged

        # Load / init release tracking
        release_index = _load_release_index()
        gold_set = _load_gold_set()
        gold_episodes = set(gold_set.get("episodes", []))
        _bootstrap_legacy_entries(release_index, gold_episodes.union(set(episodes)))

        # Build metadata per episode
        for episode in episodes:
            verify_result = _read_verify_result(episode) or {
                "episode": episode, "tier": "STANDARD", "status": "MISSING",
            }
            lint_payload = lint_results.get(episode, {})
            metadata = _build_episode_metadata(
                episode=episode,
                batch_id=batch_id,
                brief_path=brief_path,
                lint_payload=lint_payload,
                verify_result=verify_result,
            )
            staged_meta = stage_root / f"{episode}.meta.json"
            staged_meta.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8",
            )
            staged_meta_files[episode] = staged_meta
            release_index["episodes"][episode] = _build_release_entry(metadata)
            gold_episodes.add(episode)

        # Update gold set
        gold_set["episodes"] = sorted(gold_episodes)
        gold_set["updated_at"] = NOW
        release_index["current_batch"] = batch_id
        release_index["current_batch_brief"] = _relative_to_root(brief_path)
        release_index["updated_at"] = NOW

        # Stage release files
        staged_release_index = stage_root / "release.index.json"
        staged_gold_set = stage_root / "gold-set.json"
        staged_release_index.write_text(
            json.dumps(release_index, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        staged_gold_set.write_text(
            json.dumps(gold_set, ensure_ascii=False, indent=2), encoding="utf-8",
        )

        # Sequential move: staging → final locations (not atomic; see docstring)
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
# Shared batch-level pre-checks
# ---------------------------------------------------------------------------


def _resolve_batch(batch_id: str, *, require_frozen: bool = False) -> tuple[Path, dict, list[str]] | None:
    """Resolve batch → (brief_path, brief_data, episodes) or None on error."""
    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for '{batch_id}'")
        return None
    brief = _read_batch_brief(brief_path)
    episodes = brief.get("episodes", [])
    if not episodes:
        print(f"ERROR: no episodes in batch '{batch_id}'")
        return None
    if require_frozen:
        status = brief.get("status", "unknown")
        if status == "promoted":
            print(f"ERROR: batch '{batch_id}' is already promoted")
            return None
        if status != "frozen":
            print(f"ERROR: batch brief status is '{status}', must be 'frozen'")
            return None
    return brief_path, brief, episodes


def _lint_episode_payload(episode: str) -> tuple[bool, dict]:
    draft = DRAFTS / f"{episode}.md"
    if not draft.exists():
        return False, {
            "status": "missing",
            "checks": {"episode_failures": ["draft_missing"]},
            "totals": {},
        }

    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), str(draft)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return False, {
            "status": "error",
            "checks": {"episode_failures": ["invalid_lint_json"]},
            "totals": {},
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    checks = data.get("checks", {})
    episode_failures = checks.get("episode_failures", [])
    scene_failures = checks.get("scene_failures", [])
    has_scene_failures = any(item.get("failures") for item in scene_failures)
    is_pass = not episode_failures and not has_scene_failures
    return is_pass, data


def _note_lint_retry_pressure(episode: str) -> None:
    count = _get_retry_count(episode) + 1
    _set_retry_count(episode, count)
    if count >= 4:
        print(f"WARNING: {episode} has failed {count} times — ESCALATE TO HUMAN")
    elif count >= 3:
        print(f"WARNING: {episode} has failed {count} times — CONTEXT RESET required")


def _run_smoke_lint_check(episode: str) -> tuple[bool, dict]:
    is_pass, payload = _lint_episode_payload(episode)
    if is_pass:
        print(f"  ✓ Smoke lint PASS: {episode}")
        return True, payload

    failures = payload.get("checks", {}).get("episode_failures", [])
    detail = ", ".join(failures) if failures else payload.get("status", "fail")
    print(f"  ✗ Smoke lint FAIL: {episode} ({detail})")
    _note_lint_retry_pressure(episode)
    return False, payload


def _lint_total(payload: dict, key: str) -> int:
    value = payload.get("totals", {}).get(key, 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _is_syntax_shell_failure(payload: dict) -> bool:
    failures = set(payload.get("checks", {}).get("episode_failures", []))
    totals_look_empty = (
        _lint_total(payload, "scene_count") == 0
        and _lint_total(payload, "camera_count") == 0
        and (_lint_total(payload, "os_count") + _lint_total(payload, "vo_count")) == 0
    )
    failure_signature = {"scene_count", "camera_count", "os_vo_count"}.issubset(failures)
    return totals_look_empty or failure_signature


def _run_lint_gate(episodes: list[str]) -> tuple[bool, dict[str, dict]]:
    """Run lint on all draft episodes. Returns (all_pass, {ep: lint_payload})."""
    all_pass = True
    lint_results: dict[str, dict] = {}
    for ep in episodes:
        is_pass, data = _lint_episode_payload(ep)
        lint_results[ep] = data
        print(f"  {'✓' if is_pass else '✗'} {ep} lint {'pass' if is_pass else 'FAIL'}")
        if not is_pass:
            all_pass = False
    return all_pass, lint_results


def _run_verify_gate(episodes: list[str]) -> bool:
    """Check unmapped, verify results, and draft integrity. Returns True if all pass."""
    full_eps, standard_eps, light_eps, unmapped_eps = _compute_verify_tiers(episodes)
    if unmapped_eps:
        print(f"  ✗ Episodes missing source-map data: {', '.join(unmapped_eps)}")
        print(f"    → Add entries to source.map.md first")
        return False
    for ep in episodes:
        if ep in light_eps:
            print(f"  ✓ {ep}: LIGHT (lint-only)")
            continue
        vr = _read_verify_result(ep)
        if vr is None:
            print(f"  ✗ {ep}: no verify result — run aligner + verify-done first")
            return False
        if vr.get("status") != "PASS":
            print(f"  ✗ {ep}: verify {vr.get('status', '?')}")
            return False
        integrity_err = _verify_draft_integrity(ep, vr)
        if integrity_err:
            print(f"  ✗ {integrity_err} — must re-verify")
            return False
        print(f"  ✓ {ep}: verify PASS (tier: {vr.get('tier', '?')})")
    return True


def _missing_drafts(episodes: list[str]) -> list[str]:
    return [ep for ep in episodes if not (DRAFTS / f"{ep}.md").exists()]


def _normalize_optional_command(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized or normalized in {"(none)", "-", "none"}:
        return None
    return normalized


def _resolve_writer_command(writer_command: str | None = None) -> str | None:
    manifest = _read_manifest()
    return (
        _normalize_optional_command(writer_command)
        or _normalize_optional_command(manifest.get("writer_command"))
        or _normalize_optional_command(os.environ.get(WRITER_COMMAND_ENV))
    )


def _warn_unanchored_voice_assets() -> None:
    pending = []
    for filename in ["voice-anchor.md", "character.md"]:
        path = ROOT / filename
        if path.exists() and "AGENT_EXTRACT_REQUIRED" in path.read_text(encoding="utf-8"):
            pending.append(filename)
    if pending:
        print(f"  ⚠ 声纹锚未完成，后续返修成本会放大: {', '.join(pending)}")
        print("    → 建议在 batch02 前补齐 voice-anchor.md / character.md")


def _writer_parallelism() -> int:
    raw = _read_manifest().get("writer_parallelism", "").strip()
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    return DEFAULT_WRITER_PARALLELISM


def _run_writer_stage(
    batch_id: str,
    episodes: list[str],
    *,
    writer_command: str | None = None,
    parallelism: int | None = None,
    syntax_first: bool = False,
    force_rewrite: bool = False,
) -> int:
    if force_rewrite:
        for episode in episodes:
            draft = DRAFTS / f"{episode}.md"
            if draft.exists():
                draft.unlink()

    missing_before = _missing_drafts(episodes)
    if not missing_before:
        print(f"  ✓ Using existing drafts for {', '.join(episodes)}")
        return 0

    command_template = _resolve_writer_command(writer_command)
    if command_template is None:
        print("ERROR: writer stage is not configured")
        print(f"  Missing drafts: {', '.join(missing_before)}")
        print(f"  Configure run.manifest.md `writer_command`, set {WRITER_COMMAND_ENV},")
        print(f"  or use `start {batch_id} --prepare-only` and run the writer externally.")
        return 1

    try:
        selected_parallelism = max(1, parallelism or _writer_parallelism())
        command = command_template.format(
            batch_id=batch_id,
            episodes=",".join(episodes),
            episodes_csv=",".join(episodes),
            draft_dir=str(DRAFTS),
            project_root=str(ROOT),
            python=sys.executable,
            parallelism=selected_parallelism,
            syntax_first_flag="--syntax-first" if syntax_first else "",
        )
    except KeyError as exc:
        print(f"ERROR: writer_command placeholder '{exc.args[0]}' is not supported")
        return 1

    print(f"  → Running writer command for {batch_id}")
    result = subprocess.run(
        command,
        shell=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    if result.returncode != 0:
        print(f"ERROR: writer command failed with exit code {result.returncode}")
        return result.returncode or 1

    missing_after = _missing_drafts(episodes)
    if missing_after:
        print(f"ERROR: writer stage completed but drafts are still missing: {', '.join(missing_after)}")
        return 1
    return 0


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    manifest = _read_manifest()
    print("=== Harness V2 Pipeline Status ===")
    print(f"  run_status:   {manifest.get('run_status', '?')}")
    print(f"  active_batch: {manifest.get('active_batch', '?')}")
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

    print("=== Published Episodes ===")
    release_index = _load_release_index()
    gold_set = _load_gold_set()
    gold_episodes = set(gold_set.get("episodes", []))
    release_entries = release_index.get("episodes", {})

    if EPISODES.exists():
        eps = sorted(EPISODES.glob("EP-*.md"))
        for e in eps:
            ep = e.stem
            entry = release_entries.get(ep)
            if entry:
                rs = entry.get("release_status", "?")
                batch = entry.get("source_batch", "?")
                has_meta = _meta_path(ep).exists()
                label = f"{rs}"
                if rs == "gold":
                    label += f", batch={batch}"
                if has_meta:
                    label += ", meta=✓"
                print(f"  {e.name}  [{label}]")
            elif ep in gold_episodes:
                print(f"  {e.name}  [gold (index missing)]")
            else:
                print(f"  {e.name}  [untracked]")
        if not eps:
            print("  (none)")
    else:
        print("  (no episodes directory)")

    if gold_episodes:
        print(f"\n  Gold set: {', '.join(sorted(gold_episodes))}")
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
    is_pass, data = _lint_episode_payload(episode)
    status = data.get("status", "fail")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    if is_pass:
        print(f"\nLINT PASS: {episode}")
        return 0
    else:
        print(f"\nLINT FAIL: {episode}")
        _note_lint_retry_pressure(episode)
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

        result = subprocess.run(
            [sys.executable, str(LINT_SCRIPT), str(draft)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        try:
            data = json.loads(result.stdout)
            status = data.get("status", "fail")
        except (json.JSONDecodeError, ValueError):
            status = "error"

        icon = "✓" if status == "pass" else "✗"
        print(f"  {icon} {ep}: {status}")
        if status != "pass":
            all_pass = False

    if all_pass:
        print(f"\nGATE PASS: all {len(episodes)} episodes in {batch_id} passed lint")
        return 0
    else:
        print(f"\nGATE FAIL: not all episodes passed lint")
        return 1


def cmd_promote(args: argparse.Namespace) -> int:
    batch_id = args.batch_id
    resolved = _resolve_batch(args.batch_id, require_frozen=True)
    if resolved is None:
        return 1
    brief_path, brief, episodes = resolved

    # Gate: lint
    print("Running lint gate...")
    lint_passed, lint_results = _run_lint_gate(episodes)
    if not lint_passed:
        return 1

    # Gate: verify + integrity
    print("Running verify gate...")
    if not _run_verify_gate(episodes):
        return 1

    # Gate: state.lock must be free
    if _is_locked("state.lock"):
        print("ERROR: state.lock is held — cannot promote")
        return 1

    # Execute promote: staging → sequential replace → release tracking
    rc, _ = _promote_batch(batch_id, brief_path, episodes, lint_results)
    if rc != 0:
        print("ERROR: staging promote failed")
        return 1
    for ep in episodes:
        print(f"  → {ep}: draft → published (gold)")

    # Update batch brief status
    _set_batch_status(brief_path, "promoted")

    # Update run manifest
    _set_manifest_field("active_batch", f"{batch_id}_promoted")

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
    resolved = _resolve_batch(args.batch_id)
    if resolved is None:
        return 1
    brief_path, brief, episodes = resolved

    full_eps, standard_eps, light_eps, unmapped_eps = _compute_verify_tiers(episodes)

    print(f"=== Verify Plan: {batch_id} ===")
    print(f"\n  FULL (8-step):    {', '.join(full_eps) or '(none)'}")
    print(f"  STANDARD (5-step): {', '.join(standard_eps) or '(none)'}")
    print(f"  LIGHT (lint only): {', '.join(light_eps) or '(none)'}")
    if unmapped_eps:
        print(f"  ⚠ UNMAPPED (no source-map): {', '.join(unmapped_eps)}")
        print(f"    → These episodes CANNOT be verified or promoted until source.map.md is updated")
    print(f"\n  Batch-level adversarial sampling: 2 random episodes after all pass")

    # Output as structured data for agent consumption
    plan = {"full": full_eps, "standard": standard_eps, "light": light_eps, "unmapped": unmapped_eps}
    print(f"\n  JSON: {json.dumps(plan, ensure_ascii=False)}")
    return 0


def cmd_batch_review(args: argparse.Namespace) -> int:
    """Print batch-level review checklist after all episodes in batch pass verify."""
    batch_id = args.batch_id
    resolved = _resolve_batch(args.batch_id)
    if resolved is None:
        return 1
    brief_path, brief, episodes = resolved

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
        elif re.match(r"^[0-9０-９]{1,3}$", stripped):
            chapter_starts.append((i, f"第{stripped}章"))

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


def _chapter_index_lines(chapters: list[dict]) -> list[str]:
    if not chapters:
        return ["- 未识别出稳定章节标题；后续抽取时需要按整本内容自行建立定位索引"]

    lines = []
    for ch in chapters:
        title = ch.get("title") or f"第{ch['index']}章"
        start_line = ch["start_line"] + 1
        end_line = ch["end_line"]
        lines.append(f"- 第{ch['index']}章：{title}（line {start_line} ~ {end_line}）")
    return lines


def _book_blueprint_template(novel_name: str, chapters: list[dict]) -> str:
    chapter_index = "\n".join(_chapter_index_lines(chapters))
    return f"""# Book Blueprint

- source_file: {novel_name}
- extraction_status: pending
- chapter_count: {len(chapters)}
- target_episode_minutes: {DEFAULT_TARGET_EPISODE_MINUTES}
- episode_minutes_min: {DEFAULT_EPISODE_MINUTES_MIN}
- episode_minutes_max: {DEFAULT_EPISODE_MINUTES_MAX}
- recommended_total_episodes: {PENDING_BLUEPRINT_RECOMMENDATION}

说明：
- 先做全书级抽取，再生成 `source.map.md`
- 章节只作为定位信息，不作为主要思考单位
- 本文件是全书级改编蓝图，先锁主线/弧光/反转/结局，再切 batch / episode
- 单集时长按 {DEFAULT_EPISODE_MINUTES_MIN}-{DEFAULT_EPISODE_MINUTES_MAX} 分钟动态浮动，中心值 {DEFAULT_TARGET_EPISODE_MINUTES} 分钟/集

## 主线

（AGENT_EXTRACT_REQUIRED）

## 集数建议

- recommended_total_episodes: （AGENT_EXTRACT_REQUIRED）
- rationale: （AGENT_EXTRACT_REQUIRED）

## 角色弧光

（AGENT_EXTRACT_REQUIRED）

## 关系变化

（AGENT_EXTRACT_REQUIRED）

## 关键反转

（AGENT_EXTRACT_REQUIRED）

## 结局闭环

（AGENT_EXTRACT_REQUIRED）

## 章节索引（仅定位）

{chapter_index}
"""


def _pending_source_map_template(strategy: str, intensity: str, total_eps: int | None, batch_size: int) -> str:
    total_eps_text = str(total_eps) if total_eps is not None else PENDING_TOTAL_EPISODES
    total_batches = (total_eps + batch_size - 1) // batch_size if total_eps is not None else None
    total_batches_text = str(total_batches) if total_batches is not None else PENDING_TOTAL_BATCHES
    return f"""# Source Map

- mapping_status: pending_book_extraction
- total_episodes: {total_eps_text}
- batch_size: {batch_size}
- total_batches: {total_batches_text}
- target_episode_minutes: {DEFAULT_TARGET_EPISODE_MINUTES}
- episode_minutes_min: {DEFAULT_EPISODE_MINUTES_MIN}
- episode_minutes_max: {DEFAULT_EPISODE_MINUTES_MAX}
- adaptation_strategy: {strategy}
- dialogue_adaptation_intensity: {intensity}

说明：
- 本文件尚未生成正式 episode 映射
- 下一步先运行 `extract-book` 生成 `book.blueprint.md`
- 由模型先推荐总集数，并默认回填到 `run.manifest.md`
- 再运行 `map-book` 生成完整 `source.map.md`
- 章节只作为定位信息，不作为主要思考单位
"""


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
    # Backup source.map, blueprint, manifest, character, voice-anchor
    for name in ["source.map.md", "book.blueprint.md", "run.manifest.md"]:
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


def _clear_runtime_project_data() -> dict[str, int]:
    stats = {
        "drafts": 0,
        "episodes": 0,
        "batch_briefs": 0,
        "locks": 0,
        "state_files": 0,
        "release_entries": 0,
    }

    DRAFTS.mkdir(parents=True, exist_ok=True)
    for path in DRAFTS.glob("EP-*.md"):
        path.unlink()
        stats["drafts"] += 1

    EPISODES.mkdir(parents=True, exist_ok=True)
    for path in EPISODES.glob("EP-*.md"):
        path.unlink()
        stats["episodes"] += 1

    BATCH_BRIEFS.mkdir(parents=True, exist_ok=True)
    for path in BATCH_BRIEFS.glob("*.md"):
        path.unlink()
        stats["batch_briefs"] += 1

    LOCKS.mkdir(parents=True, exist_ok=True)
    for path in list(LOCKS.iterdir()):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        stats["locks"] += 1
    for lock_name in ["batch.lock", "episode-XX.lock", "state.lock"]:
        _write_lock(lock_name, "unlocked")

    if RELEASES.exists():
        stats["release_entries"] = sum(1 for _ in RELEASES.rglob("*"))
        shutil.rmtree(RELEASES)
    RELEASES.mkdir(parents=True, exist_ok=True)

    STATE.mkdir(parents=True, exist_ok=True)
    for path in STATE.glob("*.md"):
        path.unlink()
        stats["state_files"] += 1
    _write_state_templates()

    if RUN_MANIFEST.exists():
        _set_manifest_field("active_batch", "(none)")
        _set_manifest_line("current batch brief", "(none)")

    return stats


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a new project: create runtime skeleton, blueprint, and pending source map."""
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
    total_batches = (total_eps + batch_size - 1) // batch_size if total_eps is not None else None
    episode_count_source = "manual_override" if total_eps is not None else "model_recommended"
    total_eps_text = str(total_eps) if total_eps is not None else PENDING_TOTAL_EPISODES
    recommended_total_text = PENDING_RECOMMENDED_TOTAL_EPISODES

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
    if total_eps is not None:
        print(f"  Episodes:   {total_eps} ({total_batches} batches x {batch_size}) [manual override]")
    else:
        print(f"  Episodes:   {PENDING_TOTAL_EPISODES}")
        print(f"  Batch size: {batch_size}")
        print(
            f"  Timing:     {DEFAULT_EPISODE_MINUTES_MIN}-{DEFAULT_EPISODE_MINUTES_MAX} min/ep "
            f"(target {DEFAULT_TARGET_EPISODE_MINUTES})"
        )
    print(f"  Strategy:   {strategy}")
    print(f"  Intensity:  {intensity}")
    if key_eps:
        print(f"  Key EPs:    {key_eps}")
    print()
    print("  Init mode:  scaffold only (book blueprint first, source.map later)")
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

    # Generate run.manifest.md
    manifest_content = f"""# Run Manifest

- source_file: {novel_name}
- total_episodes: {total_eps_text}
- recommended_total_episodes: {recommended_total_text}
- episode_count_source: {episode_count_source}
- batch_size: {batch_size}
- target_episode_minutes: {DEFAULT_TARGET_EPISODE_MINUTES}
- episode_minutes_min: {DEFAULT_EPISODE_MINUTES_MIN}
- episode_minutes_max: {DEFAULT_EPISODE_MINUTES_MAX}
- key_episodes: {key_eps}
- adaptation_mode: novel_to_short_drama
- adaptation_strategy: {strategy}
- dialogue_adaptation_intensity: {intensity}
- generation_execution_mode: orchestrated_subagents
- writer_parallelism: {DEFAULT_WRITER_PARALLELISM}
- writer_command: "{{python}}" _ops/run_writer.py --batch {{batch_id}} --episodes {{episodes_csv}} --parallelism {{parallelism}} {{syntax_first_flag}}
- generation_reset_mode: clean_rebuild
- run_status: active
- active_batch: (none)
- source_authority: original novel manuscript + harness/project/book.blueprint.md + harness/project/source.map.md
- draft_lane: drafts/episodes
- publish_lane: episodes
- promotion_policy: controller_only_after_full_batch_verify

## Current Runtime
- framework entry: harness/framework/entry.md
- book blueprint: harness/project/book.blueprint.md
- source map: harness/project/source.map.md
- current batch brief: (none)
- regression packs: optional under harness/project/regressions/
- state directory: harness/project/state/

## Defaults
- stale legacy v1 files are not runtime authority
- published episodes are read-only outputs for current run
- draft episodes are the only candidate lane for verify
"""
    RUN_MANIFEST.write_text(manifest_content, encoding="utf-8")
    print(f"  + run.manifest.md")

    BOOK_BLUEPRINT.write_text(_book_blueprint_template(novel_name, chapters), encoding="utf-8")
    print(f"  + book.blueprint.md (pending whole-book extraction)")

    SOURCE_MAP.write_text(_pending_source_map_template(strategy, intensity, total_eps, batch_size), encoding="utf-8")
    print(f"  + source.map.md (pending map-book)")

    # Generate state file templates
    _write_state_templates()
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
    for lock_name in ["batch.lock", "episode-XX.lock", "state.lock"]:
        lock_path = LOCKS / lock_name
        if not lock_path.exists():
            _write_lock(lock_name, "free")

    _append_log("-", "-", "plan_inputs", "project init", "✓", novel_name)

    print(f"\n{'='*50}")
    print(f"  PROJECT INITIALIZED — WHOLE-BOOK FLOW")
    print(f"{'='*50}")
    print(f"\n  Next steps:")
    print(f"  1. extract-book  → fill book.blueprint.md + auto-set total_episodes")
    print(f"  2. map-book      → generate source.map.md")
    print(f"  3. start batch01 → begin batch pipeline")
    print(f"\n  Files pending completion:")
    print(f"  - book.blueprint.md")
    print(f"  - source.map.md")
    print(f"  - character.md")
    print(f"  - voice-anchor.md")

    return 0


def cmd_extract_book(args: argparse.Namespace) -> int:
    """Run whole-book extraction backend to fill book.blueprint.md."""
    novel_path = _manifest_source_path()
    if novel_path is None:
        return 1

    if not BOOK_BLUEPRINT.exists():
        print("ERROR: book.blueprint.md is missing")
        print("  Run init first")
        return 1

    script = ROOT / "_ops" / "run_book_extract.py"
    print("=== extract-book ===")
    print(f"  Source:    {novel_path.name}")
    print(f"  Blueprint: {BOOK_BLUEPRINT.relative_to(ROOT)}")

    result = subprocess.run(
        [sys.executable, str(script), "--novel-file", novel_path.relative_to(ROOT).as_posix()],
        cwd=ROOT,
        check=False,
    )
    if result.returncode == 0:
        recommended = _sync_recommended_episode_count_from_blueprint()
        if recommended is None:
            print("ERROR: extract-book completed but book.blueprint.md is missing recommended_total_episodes")
            _append_log("-", "-", "plan_inputs", "extract-book", "✗", f"{novel_path.name} (missing recommendation)")
            return 1
        manifest = _read_manifest()
        total_eps = manifest.get("total_episodes", str(recommended))
        print(f"  Recommended total_episodes: {recommended}")
        if manifest.get("episode_count_source", "model_recommended") == "model_recommended":
            print(f"  Auto-adopted total_episodes: {total_eps}")
        else:
            print(f"  Kept manual total_episodes: {total_eps}")
        _append_log("-", "-", "plan_inputs", "extract-book", "✓", novel_path.name)
    else:
        _append_log("-", "-", "plan_inputs", "extract-book", "✗", novel_path.name)
    return result.returncode


def cmd_map_book(args: argparse.Namespace) -> int:
    """Run source-map generation backend using the whole-book blueprint."""
    if not BOOK_BLUEPRINT.exists():
        print("ERROR: book.blueprint.md is missing")
        print("  Run init first")
        return 1
    if _book_blueprint_has_placeholders():
        print("ERROR: book.blueprint.md is still pending extraction")
        print("  Run extract-book first")
        return 1

    manifest = _read_manifest()
    total_eps = _parse_manifest_int("total_episodes")
    if total_eps is None:
        print("ERROR: total_episodes is still pending model recommendation")
        print("  Run extract-book first so the recommendation can be auto-applied")
        return 1

    batch_size = _parse_manifest_int("batch_size")
    if batch_size is None:
        print("ERROR: run.manifest.md has invalid batch_size")
        return 1

    novel_path = _manifest_source_path()
    if novel_path is None:
        return 1

    strategy = manifest.get("adaptation_strategy", "original_fidelity")
    intensity = manifest.get("dialogue_adaptation_intensity", "light")

    script = ROOT / "_ops" / "run_book_map.py"
    print("=== map-book ===")
    print(f"  Source:    {novel_path.name}")
    print(f"  Blueprint: {BOOK_BLUEPRINT.relative_to(ROOT)}")
    print(f"  Output:    {SOURCE_MAP.relative_to(ROOT)}")

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--novel-file",
            novel_path.relative_to(ROOT).as_posix(),
            "--episodes",
            str(total_eps),
            "--batch-size",
            str(batch_size),
            "--strategy",
            strategy,
            "--intensity",
            intensity,
        ],
        cwd=ROOT,
        check=False,
    )
    if result.returncode == 0:
        _append_log("-", "-", "plan_inputs", "map-book", "✓", novel_path.name)
    else:
        _append_log("-", "-", "plan_inputs", "map-book", "✗", novel_path.name)
    return result.returncode


def cmd_clean(args: argparse.Namespace) -> int:
    """Backup and clear runtime project data while preserving project config and source files."""
    print("=== Clean Runtime Project Data ===")
    snapshot = _backup_project()
    if snapshot:
        print(f"  ↻ Backed up to {snapshot.relative_to(ROOT)}")
    else:
        print("  (no existing runtime data to back up)")

    stats = _clear_runtime_project_data()

    print(f"  - drafts cleared:        {stats['drafts']}")
    print(f"  - episodes cleared:      {stats['episodes']}")
    print(f"  - batch briefs cleared:  {stats['batch_briefs']}")
    print(f"  - lock artifacts reset:  {stats['locks']}")
    print(f"  - state files reset:     {stats['state_files']}")
    print(f"  - release entries reset: {stats['release_entries']}")
    print("  ✓ Runtime project data cleared")
    print("  Preserved: book.blueprint.md, source.map.md, run.manifest.md, framework contracts, source novel files")
    return 0


def _prepare_batch_start(batch_id: str) -> tuple[Path, dict, list[str]] | None:
    if not SOURCE_MAP.exists():
        print("ERROR: source.map.md is missing")
        print("  Run extract-book and map-book first")
        return None

    source_map_text = SOURCE_MAP.read_text(encoding="utf-8")
    if "mapping_status: pending_book_extraction" in source_map_text:
        print("ERROR: source.map.md is still pending")
        print("  Run extract-book, then map-book, before start/check/run")
        return None

    batches = _parse_source_map()
    if batch_id not in batches:
        print(f"ERROR: '{batch_id}' not found in source.map")
        print(f"  Available: {', '.join(sorted(batches.keys()))}")
        return None

    batch_info = batches[batch_id]
    episodes = batch_info["episodes"]

    # Check batch lock
    if _is_locked("batch.lock"):
        lock_data = _read_lock("batch.lock")
        owner = lock_data.get("owner", "?")
        if batch_id not in owner:
            print(f"ERROR: batch.lock held by '{owner}' — finish or unlock first")
            return None

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
            return None
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
    _set_manifest_field("active_batch", f"{batch_id}_{batch_info['ep_start']}-{batch_info['ep_end']}")

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
    full_eps, standard_eps, light_eps, unmapped_eps = _compute_verify_tiers(episodes)
    print(f"\n--- Verify Plan ---")
    print(f"  FULL (8-step):     {', '.join(full_eps) or '(none)'}")
    print(f"  STANDARD (5-step): {', '.join(standard_eps) or '(none)'}")
    print(f"  LIGHT (lint only): {', '.join(light_eps) or '(none)'}")
    if unmapped_eps:
        print(f"  ⚠ UNMAPPED:        {', '.join(unmapped_eps)}")
        print(f"    → Update source.map.md before running check/verify")

    return brief_path, batch_info, episodes


def cmd_start(args: argparse.Namespace) -> int:
    """Total entry: prepare batch → smoke-first writer stage → continue pipeline."""
    batch_id = args.batch_id
    prepared = _prepare_batch_start(batch_id)
    if prepared is None:
        return 1
    brief_path, batch_info, episodes = prepared

    if args.prepare_only:
        print(f"\n--- Next Step ---")
        print(f"  prepare-only: batch is frozen and locked, but writer/pipeline were not started")
        print(f"  Writer agent: draft {', '.join(episodes)} into drafts/episodes/")
        print(f"  Then run fast path: python _ops/controller.py run {batch_id}")
        print(f"  Or strict path:    python _ops/controller.py check {batch_id}")
        return 0

    _warn_unanchored_voice_assets()

    smoke_episode = episodes[0]
    remaining_episodes = episodes[1:]

    print(f"\n=== Writer Stage (Smoke First) ===")
    writer_rc = _run_writer_stage(
        batch_id,
        [smoke_episode],
        writer_command=args.writer_command,
        parallelism=1,
    )
    if writer_rc != 0:
        return writer_rc

    smoke_ok, smoke_payload = _run_smoke_lint_check(smoke_episode)
    _append_log(
        batch_id,
        smoke_episode,
        "verify",
        "smoke lint",
        "✓" if smoke_ok else "✗",
        "smoke-first",
    )
    if not smoke_ok and _is_syntax_shell_failure(smoke_payload):
        print("  ↻ Smoke 命中壳层失败签名，自动切到 syntax-first 重写一次")
        _append_log(batch_id, smoke_episode, "recovery", "syntax-first retry", "↻", "smoke shell failure")
        writer_rc = _run_writer_stage(
            batch_id,
            [smoke_episode],
            writer_command=args.writer_command,
            parallelism=1,
            syntax_first=True,
            force_rewrite=True,
        )
        if writer_rc != 0:
            return writer_rc
        smoke_ok, smoke_payload = _run_smoke_lint_check(smoke_episode)
        _append_log(
            batch_id,
            smoke_episode,
            "verify",
            "smoke lint retry",
            "✓" if smoke_ok else "✗",
            "syntax-first",
        )

    if not smoke_ok:
        print("ERROR: smoke 集仍未通过 lint，已停止整批扩写")
        print("  需要人工接管：优先修壳层 / parser 兼容问题，再继续本批次。")
        _append_log(batch_id, smoke_episode, "recovery", "manual takeover", "✗", "smoke failed twice")
        return 1

    if remaining_episodes:
        print(f"\n=== Writer Stage (Fan Out) ===")
        writer_rc = _run_writer_stage(
            batch_id,
            remaining_episodes,
            writer_command=args.writer_command,
            parallelism=_writer_parallelism(),
        )
        if writer_rc != 0:
            return writer_rc

    print(f"\n=== Continue Pipeline ===")
    return cmd_run(argparse.Namespace(batch_id=batch_id))


def cmd_check(args: argparse.Namespace) -> int:
    """Gate (lint all) + verify-plan + semantic verify instructions."""
    batch_id = args.batch_id
    resolved = _resolve_batch(args.batch_id)
    if resolved is None:
        return 1
    brief_path, brief, episodes = resolved

    # Step 1: Lint gate
    print(f"=== Lint Gate: {args.batch_id} ===")
    lint_passed, _ = _run_lint_gate(episodes)
    if not lint_passed:
        print(f"\n  GATE FAIL — fix lint errors before proceeding")
        return 1
    print(f"\n  GATE PASS")

    # Step 2: Verify plan
    full_eps, standard_eps, light_eps, unmapped_eps = _compute_verify_tiers(episodes)
    if unmapped_eps:
        print(f"\n  ⚠ UNMAPPED episodes (no source-map data): {', '.join(unmapped_eps)}")
        print(f"    → These episodes cannot proceed to verify. Update source.map.md first.")
        return 1
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


def _do_promote_and_report(
    batch_id: str, brief_path: Path, episodes: list[str], lint_results: dict[str, dict],
) -> int:
    """Shared post-gate logic: promote → validate → batch review → next steps."""
    # State lock check
    if _is_locked("state.lock"):
        print("ERROR: state.lock is held — cannot promote")
        return 1

    # Promote (staging → sequential replace → release tracking)
    print(f"\n=== Promote ===")
    rc, _ = _promote_batch(batch_id, brief_path, episodes, lint_results)
    if rc != 0:
        print("ERROR: staging promote failed")
        return 1
    for ep in episodes:
        print(f"  → {ep}: draft → published (gold)")

    _set_batch_status(brief_path, "promoted")
    _write_lock("batch.lock", "unlocked")

    for ep in episodes:
        _clear_retry_count(ep)

    ep_range = f"{episodes[0]}~{episodes[-1]}" if len(episodes) > 1 else episodes[0]
    _append_log(batch_id, ep_range, "promote", "controller promote", "✓", f"{batch_id} promoted")
    _set_manifest_field("active_batch", f"{batch_id}_promoted")
    print(f"  ✓ {len(episodes)} promoted to gold, batch.lock released")

    # Validate state files
    print(f"\n=== State Validation ===")
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

    # Batch review sampling
    print(f"\n=== Batch Review ===")
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

    # Determine next batch
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


def cmd_finish(args: argparse.Namespace) -> int:
    """Promote + validate + batch-review + log + next instructions."""
    batch_id = args.batch_id
    resolved = _resolve_batch(batch_id, require_frozen=True)
    if resolved is None:
        return 1
    brief_path, brief, episodes = resolved

    # Step 1: Final lint gate
    print(f"=== Step 1: Lint Gate ===")
    lint_passed, lint_results = _run_lint_gate(episodes)
    if not lint_passed:
        return 1

    # Step 2: Verify gate
    print(f"\n=== Step 2: Verify Gate ===")
    if not _run_verify_gate(episodes):
        return 1

    return _do_promote_and_report(batch_id, brief_path, episodes, lint_results)


def cmd_run(args: argparse.Namespace) -> int:
    """Full pipeline: lint gate → auto-verify → promote → review → next.

    Skips semantic verify (aligner). Episodes that already have a verify PASS
    result keep it; episodes without one get auto-verified at lint level.
    Use 'check' + manual aligner + 'finish' if you need full semantic verify.
    """
    batch_id = args.batch_id
    resolved = _resolve_batch(batch_id, require_frozen=True)
    if resolved is None:
        return 1
    brief_path, brief, episodes = resolved

    # Step 1: Lint gate
    print(f"=== Step 1: Lint Gate ===")
    lint_passed, lint_results = _run_lint_gate(episodes)
    if not lint_passed:
        print(f"\n  GATE FAIL — fix lint errors first")
        return 1
    print(f"\n  GATE PASS")

    # Step 2: Auto-verify (respect existing results, fill gaps with lint-only)
    print(f"\n=== Step 2: Auto-Verify ===")
    full_eps, standard_eps, light_eps, unmapped_eps = _compute_verify_tiers(episodes)
    if unmapped_eps:
        print(f"  ✗ Unmapped: {', '.join(unmapped_eps)}")
        print(f"    → Update source.map.md first")
        return 1

    auto_count = 0
    for ep in episodes:
        existing = _read_verify_result(ep)
        if existing and existing.get("status") == "PASS":
            print(f"  ✓ {ep}: existing PASS (tier: {existing.get('tier', '?')})")
            continue
        tier = "FULL" if ep in full_eps else ("STANDARD" if ep in standard_eps else "LIGHT")
        _write_verify_result(ep, tier, "PASS")
        _append_log(batch_id, ep, "verify", "auto-verify (lint-only)", "PASS", f"tier={tier}")
        print(f"  + {ep}: auto-verified (tier: {tier}, lint-only)")
        auto_count += 1
    if auto_count:
        print(f"\n  {auto_count} episodes auto-verified (lint-only, no semantic check)")
    else:
        print(f"\n  All episodes already have verify results")

    # Step 3: Promote + report
    return _do_promote_and_report(batch_id, brief_path, episodes, lint_results)


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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Harness V2 Controller")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Show pipeline state")
    sub.add_parser("clean", help="Backup + clear runtime project data cache")

    p_plan = sub.add_parser("plan", help="Freeze batch brief and acquire lock")
    p_plan.add_argument("batch_id", help="e.g. batch01, batch02")

    p_lint = sub.add_parser("lint", help="Run lint on a draft episode")
    p_lint.add_argument("episode", help="e.g. EP-01")

    p_gate = sub.add_parser("gate", help="Check all drafts in batch passed lint")
    p_gate.add_argument("batch_id")

    p_promote = sub.add_parser("promote", help="Promote batch: copy drafts → episodes")
    p_promote.add_argument("batch_id")

    sub.add_parser("validate", help="Check state files against templates")

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
    p_init.add_argument(
        "--episodes",
        type=int,
        default=None,
        help="Optional manual episode count override (default: model recommendation after extract-book)",
    )
    p_init.add_argument("--batch-size", type=int, default=5, help="Episodes per batch (default: 5)")
    p_init.add_argument("--strategy", default="original_fidelity", help="Adaptation strategy")
    p_init.add_argument("--intensity", default="light", help="Dialogue adaptation intensity")
    p_init.add_argument("--key-episodes", default="", help="Comma-separated key episode IDs for FULL verify")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing project data (auto-backup first)")
    sub.add_parser("extract-book", help="Fill book.blueprint.md from the full novel")
    sub.add_parser("map-book", help="Generate source.map.md from book.blueprint.md")

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
    p_start = sub.add_parser("start", help="Total entry: prepare → writer stage → run pipeline")
    p_start.add_argument("batch_id", help="e.g. batch02")
    p_start.add_argument("--prepare-only", action="store_true", help="Freeze/lock and print context only")
    p_start.add_argument("--writer-command", default=None, help="Override writer hook command for this run")

    p_check = sub.add_parser("check", help="Lint gate + verify-plan + verify instructions")
    p_check.add_argument("batch_id")

    p_finish = sub.add_parser("finish", help="Promote + validate + batch-review + next")
    p_finish.add_argument("batch_id")

    p_run = sub.add_parser("run", help="Full pipeline: lint → auto-verify → promote → review → next")
    p_run.add_argument("batch_id")

    sub.add_parser("next", help="Show pipeline progress and next batch")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "status": cmd_status,
        "clean": cmd_clean,
        "plan": cmd_plan,
        "lint": cmd_lint,
        "gate": cmd_gate,
        "promote": cmd_promote,
        "validate": cmd_validate,
        "log": cmd_log,
        "retry": cmd_retry,
        "verify-plan": cmd_verify_plan,
        "batch-review": cmd_batch_review,
        "unlock": cmd_unlock,
        "verify-done": cmd_verify_done,
        "record": cmd_record,
        "record-done": cmd_record_done,
        "init": cmd_init,
        "extract-book": cmd_extract_book,
        "map-book": cmd_map_book,
        "start": cmd_start,
        "check": cmd_check,
        "finish": cmd_finish,
        "run": cmd_run,
        "next": cmd_next,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
