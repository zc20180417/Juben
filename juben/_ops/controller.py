#!/usr/bin/env python3
"""
Harness V2 Controller — reviewer-gated orchestration.

Project setup:
  init <novel_file>      Scaffold new project (manifest, source.map, state templates)
  extract-book           Generate extraction prompt packet for book.blueprint.md
  map-book               Generate mapping prompt packet for source.map.md

Orchestration commands:
  start <batch_id>       Prepare batch → writer stage → stop for review
  check <batch_id>       Rebuild review packet only (fallback/debug)
  polish <batch_id>      Create optional premium polish prompt packet
  run <batch_id>         Review gate → promote → next
  finish <batch_id>      Deprecated alias for run
  next                   Show pipeline progress and next batch to start

Review / record commands:
  batch-review <batch>        Create durable batch review artifacts
  batch-review-done <batch>   Seal batch review verdict (PASS/FAIL)
  record <batch_id>           Auto-update state files for a promoted batch
  record-done <batch_id>      Compatibility alias: validate recorded state

Low-level commands:
  status                 Show current pipeline state (with batch ownership)
  clean                  Backup + clear runtime project data cache
  plan <batch_id>        Freeze batch brief, acquire batch lock
  promote <batch_id>     Copy drafts → episodes (requires batch review PASS)
  validate               Check state files against memory-contract templates
  export                 Refresh human-facing output/ index and mirrors
  log <phase> <event>    Append entry to run.log.md
  unlock [lock_name]     Release a lock (batch / episode / state / all)
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import random
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness"
FRAMEWORK = HARNESS / "framework"
PROJECT = HARNESS / "project"
STATE = PROJECT / "state"
BATCH_STATUS_DIR = STATE / "batch-status"
LOCKS = PROJECT / "locks"
DRAFTS = ROOT / "drafts" / "episodes"
EPISODES = ROOT / "episodes"
OUTPUT = ROOT / "output"
BATCH_BRIEFS = PROJECT / "batch-briefs"
RUN_MANIFEST = PROJECT / "run.manifest.md"
RUN_LOG = STATE / "run.log.md"
MEMORY_CONTRACT = FRAMEWORK / "memory-contract.md"
REVIEW_STANDARD = FRAMEWORK / "review-standard.md"
REVIEW_PROMPT_TEMPLATE = FRAMEWORK / "reviewer-prompt.template.md"
POLISH_PROMPT_TEMPLATE = FRAMEWORK / "polish-prompt.template.md"
BOOK_BLUEPRINT = PROJECT / "book.blueprint.md"
SOURCE_MAP = PROJECT / "source.map.md"
RELEASES = PROJECT / "releases"
REVIEWS = PROJECT / "reviews"
PROMPTS = PROJECT / "prompts"
RELEASE_JOURNALS = RELEASES / "journals"
RELEASE_INDEX = RELEASES / "release.index.json"
GOLD_SET = RELEASES / "gold-set.json"

RUNTIME_AUTHORITY = "rebuild-2026-04"
RULESET_VERSION = "reviewer-gate/v1"

NOW = datetime.now().strftime("%Y-%m-%d %H:%M")
DEFAULT_WRITER_PARALLELISM = 1
WRITER_STAGE_PROMPTS_READY = 2
DEFAULT_TARGET_TOTAL_MINUTES = 50
DEFAULT_TARGET_EPISODE_MINUTES = 2
DEFAULT_EPISODE_MINUTES_MIN = 1
DEFAULT_EPISODE_MINUTES_MAX = 3
PENDING_TOTAL_EPISODES = "pending_model_recommendation"
PENDING_RECOMMENDED_TOTAL_EPISODES = "pending_book_extraction"
PENDING_BLUEPRINT_RECOMMENDATION = "pending_extraction"
PENDING_TOTAL_BATCHES = "pending_total_episodes"


def _configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except ValueError:
                pass


_configure_stdio()


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


def _batch_runtime_phase(batch_id: str) -> str | None:
    runtime = _read_batch_status(batch_id)
    if not runtime:
        return None
    return runtime.get("phase")


def _is_runtime_promoted(batch_id: str) -> bool:
    return _batch_runtime_phase(batch_id) in {"promoted", "recorded"}


# ---------------------------------------------------------------------------
# Batch runtime status + review helpers
# ---------------------------------------------------------------------------

def _batch_status_path(batch_id: str) -> Path:
    return BATCH_STATUS_DIR / f"{batch_id}.status.json"


def _batch_review_json_path(batch_id: str) -> Path:
    return REVIEWS / f"{batch_id}.review.json"


def _batch_review_md_path(batch_id: str) -> Path:
    return REVIEWS / f"{batch_id}.review.md"


def _batch_review_prompt_path(batch_id: str) -> Path:
    return REVIEWS / f"{batch_id}.review.prompt.md"


def _batch_polish_report_path(batch_id: str) -> Path:
    return REVIEWS / f"{batch_id}.polish.md"


def _empty_batch_status(
    batch_id: str,
    *,
    phase: str = "planned",
    status: str = "ACTIVE",
    episodes: list[str] | None = None,
    completed_episodes: list[str] | None = None,
    brief_path: Path | None = None,
    batch_review_status: str = "MISSING",
) -> dict:
    return {
        "batch_id": batch_id,
        "phase": phase,
        "status": status,
        "episodes": episodes or [],
        "completed_episodes": completed_episodes or [],
        "brief_path": _relative_to_root(brief_path) if brief_path else "",
        "batch_review_status": batch_review_status,
        "updated_at": NOW,
    }


def _read_batch_status(batch_id: str) -> dict | None:
    path = _batch_status_path(batch_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_batch_status(batch_id: str, data: dict) -> None:
    BATCH_STATUS_DIR.mkdir(parents=True, exist_ok=True)
    data["batch_id"] = batch_id
    data["updated_at"] = NOW
    _batch_status_path(batch_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _upsert_batch_status(
    batch_id: str,
    *,
    phase: str | None = None,
    status: str | None = None,
    episodes: list[str] | None = None,
    completed_episodes: list[str] | None = None,
    brief_path: Path | None = None,
    batch_review_status: str | None = None,
) -> dict:
    data = _read_batch_status(batch_id) or _empty_batch_status(batch_id)
    if phase is not None:
        data["phase"] = phase
    if status is not None:
        data["status"] = status
    if episodes is not None:
        data["episodes"] = episodes
    if completed_episodes is not None:
        data["completed_episodes"] = completed_episodes
    if brief_path is not None:
        data["brief_path"] = _relative_to_root(brief_path)
    if batch_review_status is not None:
        data["batch_review_status"] = batch_review_status
    _write_batch_status(batch_id, data)
    return data


def _sampled_batch_review_episodes(episodes: list[str]) -> list[str]:
    return episodes[: min(2, len(episodes))]


def _empty_batch_review(batch_id: str, episodes: list[str], sampled_episodes: list[str]) -> dict:
    return {
        "batch_id": batch_id,
        "status": "PENDING",
        "reviewer": "",
        "timestamp": NOW,
        "episodes": episodes,
        "sampled_episodes": sampled_episodes,
        "blocking_reasons": [],
        "warning_families": [],
        "arc_regressions": [],
        "function_theft_findings": [],
        "quality_anchor_findings": [],
        "evidence_refs": [],
        "reason": "",
    }


def _read_batch_review(batch_id: str) -> dict | None:
    path = _batch_review_json_path(batch_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _render_batch_review_markdown(review: dict) -> str:
    def _bullet_block(items: list[str], empty: str = "(none)") -> str:
        if not items:
            return f"- {empty}"
        return "\n".join(f"- {item}" for item in items)

    return (
        f"# Batch Review: {review['batch_id']}\n\n"
        f"- status: {review.get('status', 'PENDING')}\n"
        f"- reviewer: {review.get('reviewer', '') or '(pending)'}\n"
        f"- timestamp: {review.get('timestamp', NOW)}\n"
        f"- episodes: {', '.join(review.get('episodes', []))}\n"
        f"- sampled episodes: {', '.join(review.get('sampled_episodes', [])) or '(none)'}\n\n"
        f"## Checklist\n\n"
        f"- [ ] sampled-episode adversarial checks complete\n"
        f"- [ ] cross-episode arc continuity reviewed\n"
        f"- [ ] future-payoff theft checked\n"
        f"- [ ] unsupported additions assessed\n"
        f"- [ ] quality anchor regression assessed\n\n"
        f"## Evidence\n\n"
        f"{_bullet_block(review.get('evidence_refs', []))}\n\n"
        f"## Blocking Reasons\n\n"
        f"{_bullet_block(review.get('blocking_reasons', []))}\n\n"
        f"## Warning Families\n\n"
        f"{_bullet_block(review.get('warning_families', []))}\n\n"
        f"## Arc Regressions\n\n"
        f"{_bullet_block(review.get('arc_regressions', []))}\n\n"
        f"## Function Theft Findings\n\n"
        f"{_bullet_block(review.get('function_theft_findings', []))}\n\n"
        f"## Quality Anchor Findings\n\n"
        f"{_bullet_block(review.get('quality_anchor_findings', []))}\n\n"
        f"## Final Verdict\n\n"
        f"- verdict: {review.get('status', 'PENDING')}\n"
        f"- reviewer: {review.get('reviewer', '') or '(pending)'}\n"
        f"- reason: {review.get('reason', '') or '(none)'}\n"
    )


def _render_template_text(template_path: Path, replacements: dict[str, str]) -> str:
    text = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def _render_batch_review_prompt(review: dict, brief_path: Path | None = None) -> str:
    sampled = review.get("sampled_episodes", []) or []
    episodes = review.get("episodes", []) or []
    draft_paths = "\n".join(f"- drafts/episodes/{episode}.md" for episode in episodes) or "- (none)"
    sampled_block = "\n".join(f"- {episode}" for episode in sampled) or "- (none)"
    review_json_rel = _relative_to_root(_batch_review_json_path(review["batch_id"]))
    review_md_rel = _relative_to_root(_batch_review_md_path(review["batch_id"]))
    brief_rel = _relative_to_root(brief_path) if brief_path is not None else "(unknown)"
    replacements = {
        "batch_id": review["batch_id"],
        "episodes": ", ".join(episodes) or "(none)",
        "sampled_episodes": sampled_block,
        "batch_brief_path": brief_rel,
        "source_map_path": _relative_to_root(SOURCE_MAP),
        "quality_anchor_path": _relative_to_root(STATE / "quality.anchor.md"),
        "open_loops_path": _relative_to_root(STATE / "open_loops.md"),
        "review_json_path": review_json_rel,
        "review_md_path": review_md_rel,
        "review_standard_path": _relative_to_root(REVIEW_STANDARD),
        "draft_paths": draft_paths,
    }
    return _render_template_text(REVIEW_PROMPT_TEMPLATE, replacements)


def _write_batch_review_artifacts(batch_id: str, review: dict, brief_path: Path | None = None) -> None:
    REVIEWS.mkdir(parents=True, exist_ok=True)
    review["timestamp"] = NOW
    _batch_review_json_path(batch_id).write_text(
        json.dumps(review, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _batch_review_md_path(batch_id).write_text(
        _render_batch_review_markdown(review),
        encoding="utf-8",
    )
    _batch_review_prompt_path(batch_id).write_text(
        _render_batch_review_prompt(review, brief_path=brief_path),
        encoding="utf-8",
    )


def _ensure_batch_review_artifacts(batch_id: str, episodes: list[str], brief_path: Path | None = None) -> dict:
    sampled = _sampled_batch_review_episodes(episodes)
    review = _read_batch_review(batch_id) or _empty_batch_review(batch_id, episodes, sampled)
    review.setdefault("episodes", episodes)
    review.setdefault("sampled_episodes", sampled)
    review.setdefault("blocking_reasons", [])
    review.setdefault("warning_families", [])
    review.setdefault("arc_regressions", [])
    review.setdefault("function_theft_findings", [])
    review.setdefault("quality_anchor_findings", [])
    review.setdefault("evidence_refs", [])
    review.setdefault("reason", "")
    _write_batch_review_artifacts(batch_id, review, brief_path=brief_path)
    return review


def _require_batch_review_pass(batch_id: str) -> tuple[bool, str]:
    review = _read_batch_review(batch_id)
    if review is None:
        return False, (
            f"ERROR: batch review artifact missing for '{batch_id}' "
            f"(run `start {batch_id} --write` first; use `check {batch_id}` only to rebuild review packet)"
        )
    status = review.get("status", "MISSING")
    if status != "PASS":
        return False, f"ERROR: batch review verdict is {status} for '{batch_id}'"
    return True, ""


def _known_batch_ids() -> list[str]:
    batch_ids: set[str] = set()
    try:
        batch_ids.update(_parse_source_map().keys())
    except Exception:
        pass

    if BATCH_BRIEFS.exists():
        for path in BATCH_BRIEFS.glob("*.md"):
            stem = path.stem
            match = re.search(r"batch0*\d+", stem)
            if match:
                batch_ids.add(match.group(0).lower())

    if BATCH_STATUS_DIR.exists():
        for path in BATCH_STATUS_DIR.glob("*.status.json"):
            batch_ids.add(path.stem.replace(".status", ""))

    if REVIEWS.exists():
        for path in REVIEWS.glob("*.review.json"):
            batch_ids.add(path.stem.replace(".review", ""))

    if RELEASE_JOURNALS.exists():
        for path in RELEASE_JOURNALS.glob("*.promote.json"):
            batch_ids.add(path.stem.replace(".promote", ""))

    return sorted(batch_ids)


def _batch_status_summary(batch_id: str) -> dict:
    runtime = _read_batch_status(batch_id)
    review = _read_batch_review(batch_id)
    promote_journal = _read_release_journal(batch_id)
    brief_path = _find_batch_brief(batch_id)
    brief = _read_batch_brief(brief_path) if brief_path else {}

    if runtime:
        phase = runtime.get("phase", "?")
        status = runtime.get("status", "?")
        batch_review_status = runtime.get("batch_review_status", "MISSING")
        authority = "runtime"
        brief_ref = runtime.get("brief_path") or (_relative_to_root(brief_path) if brief_path else "")
        episodes = runtime.get("episodes", []) or brief.get("episodes", [])
    else:
        phase = brief.get("status", "unknown")
        status = "ACTIVE" if phase in {"draft", "frozen"} else ("DONE" if phase == "promoted" else "?")
        batch_review_status = review.get("status", "MISSING") if review else "MISSING"
        authority = "brief-fallback"
        brief_ref = _relative_to_root(brief_path) if brief_path else ""
        episodes = brief.get("episodes", [])

    review_artifact = "present" if review else "missing"
    review_reason = ""
    if review:
        review_reason = (review.get("reason", "") or "").strip()
    if promote_journal:
        journal_phase = promote_journal.get("phase", "?")
        if promote_journal.get("completed", False):
            promote_journal_status = f"completed:{journal_phase}"
        else:
            promote_journal_status = f"incomplete:{journal_phase}"
    else:
        promote_journal_status = "missing"
    return {
        "batch_id": batch_id,
        "phase": phase,
        "status": status,
        "batch_review_status": batch_review_status,
        "review_artifact": review_artifact,
        "review_reason": review_reason,
        "promote_journal": promote_journal_status,
        "authority": authority,
        "brief_path": brief_ref or "(none)",
        "episodes": episodes,
    }


def _first_incomplete_promote_batch(batch_ids: list[str]) -> tuple[str, dict] | None:
    for batch_id in batch_ids:
        journal = _read_release_journal(batch_id)
        if journal and not journal.get("completed", False):
            return batch_id, journal
    return None


def _next_batch_review_action(batch_id: str, runtime: dict | None, review: dict | None) -> tuple[str, str] | None:
    batch_review_status = (runtime or {}).get("batch_review_status", "MISSING")
    phase = (runtime or {}).get("phase", "")
    if phase != "review_pending":
        return None
    if review is None or batch_review_status == "MISSING":
        return (
            "batch review artifact missing",
            f"python _ops/controller.py check {batch_id}  # rebuild review packet only",
        )
    review_status = review.get("status", batch_review_status)
    if review_status == "PENDING":
        return (
            "batch review pending verdict",
            f"python _ops/controller.py batch-review-done {batch_id} PASS --reviewer <name>",
        )
    if review_status == "FAIL":
        return (
            f"batch review failed: {(review.get('reason', '') or '(no reason recorded)')}",
            f"python _ops/controller.py batch-review-done {batch_id} PASS --reviewer <name>",
        )
    return None


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


def _extract_first_int(text: str) -> int | None:
    match = re.search(r"(?<!\d)(\d{1,4})(?!\d)", text or "")
    if not match:
        return None
    return int(match.group(1))


def _blueprint_episode_conclusion_count(content: str | None = None) -> int | None:
    if content is None:
        if not BOOK_BLUEPRINT.exists():
            return None
        content = BOOK_BLUEPRINT.read_text(encoding="utf-8")

    match = re.search(r"^- recommended_total_episodes:\s*(\d+)\s*$", content, re.MULTILINE)
    if match:
        return int(match.group(1))

    section = _blueprint_section(content, "集数建议")
    if not section:
        return None

    final_value = _extract_structured_bullet(section, "最终采用")
    parsed = _extract_first_int(final_value)
    if parsed is not None:
        return parsed

    for line in section.splitlines():
        stripped = line.strip()
        if "最终采用" in stripped or "recommended_total_episodes" in stripped:
            parsed = _extract_first_int(stripped)
            if parsed is not None:
                return parsed
    return None


def _recommended_total_episodes_from_blueprint() -> int | None:
    return _blueprint_episode_conclusion_count()


def _blueprint_section(content: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    return match.group("body").strip() if match else ""


def _extract_structured_bullet(section: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}[:：]\s*(.+)\s*$", section, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _book_blueprint_quality_issues() -> list[str]:
    if not BOOK_BLUEPRINT.exists():
        return ["book.blueprint.md missing"]

    content = BOOK_BLUEPRINT.read_text(encoding="utf-8")
    section = _blueprint_section(content, "集数建议")
    if not section:
        return ["missing '## 集数建议' section"]

    issues = []
    if _blueprint_episode_conclusion_count(content) is None:
        issues.append("集数建议缺少可解析的集数结论（recommended_total_episodes 或 最终采用）")
    return issues


def _book_blueprint_is_complete() -> bool:
    return (
        not _book_blueprint_has_placeholders()
        and _blueprint_episode_conclusion_count() is not None
        and not _book_blueprint_quality_issues()
    )


def _voice_anchor_quality_issues() -> list[str]:
    path = ROOT / "voice-anchor.md"
    if not path.exists():
        return ["voice-anchor.md missing"]
    content = path.read_text(encoding="utf-8")
    issues = []
    if "常用表达" in content:
        issues.append("voice-anchor.md 仍包含“常用表达”模板区，容易把 writer 推向复用句式")
    if "口头禅" in content:
        issues.append("voice-anchor.md 不应为角色预设口头禅式模板")
    return issues


def _replace_markdown_section(content: str, heading: str, body: str) -> str:
    pattern = rf"(^##\s+{re.escape(heading)}\s*$\n)(.*?)(?=^##\s+|\Z)"
    if re.search(pattern, content, re.MULTILINE | re.DOTALL):
        return re.sub(
            pattern,
            lambda match: f"{match.group(1)}{body.rstrip()}\n\n",
            content,
            count=1,
            flags=re.MULTILINE | re.DOTALL,
        )
    return content.rstrip() + f"\n\n## {heading}\n{body.rstrip()}\n"


def _section_is_blank_template(content: str, heading: str) -> bool:
    body = _blueprint_section(content, heading) if heading.startswith("蓝图::") else ""
    if heading.startswith("蓝图::"):
        body = _blueprint_section(content, heading.split("::", 1)[1])
    else:
        match = re.search(
            rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )
        body = match.group("body").strip() if match else ""
    return not body


def _sync_state_from_blueprint() -> list[str]:
    if not BOOK_BLUEPRINT.exists():
        return ["book.blueprint.md missing"]

    STATE.mkdir(parents=True, exist_ok=True)
    blueprint = BOOK_BLUEPRINT.read_text(encoding="utf-8")
    mainline = _blueprint_section(blueprint, "主线") or "（待补）"
    arcs = _blueprint_section(blueprint, "角色弧光") or "（待补）"
    relations = _blueprint_section(blueprint, "关系变化") or "（待补）"
    twists = _blueprint_section(blueprint, "关键反转") or "（待补）"
    recommendation = _blueprint_section(blueprint, "集数建议") or "（待补）"

    updated = []

    story_path = STATE / "story.state.md"
    story_content = story_path.read_text(encoding="utf-8") if story_path.exists() else _state_templates().get("story.state.md", "")
    if _section_is_blank_template(story_content, "当前阶段"):
        story_content = _replace_markdown_section(story_content, "当前阶段", mainline)
    if _section_is_blank_template(story_content, "权力格局"):
        story_content = _replace_markdown_section(story_content, "权力格局", relations)
    if _section_is_blank_template(story_content, "主要角色位置"):
        story_content = _replace_markdown_section(story_content, "主要角色位置", arcs)
    if _section_is_blank_template(story_content, "最近关键转折"):
        story_content = _replace_markdown_section(story_content, "最近关键转折", twists)
    if _section_is_blank_template(story_content, "下一批关键预期"):
        story_content = _replace_markdown_section(story_content, "下一批关键预期", recommendation)
    story_path.write_text(story_content, encoding="utf-8")
    updated.append("story.state.md")

    relation_path = STATE / "relationship.board.md"
    relation_content = relation_path.read_text(encoding="utf-8") if relation_path.exists() else _state_templates().get("relationship.board.md", "")
    if _section_is_blank_template(relation_content, "核心关系网"):
        relation_content = _replace_markdown_section(relation_content, "核心关系网", relations)
    if _section_is_blank_template(relation_content, "最近关系变动"):
        relation_content = _replace_markdown_section(relation_content, "最近关系变动", "初始化同步：以上游蓝图为准；进入 batch 后由 record 阶段按已生成集更新。")
    if _section_is_blank_template(relation_content, "待爆关系线"):
        relation_content = _replace_markdown_section(relation_content, "待爆关系线", twists)
    relation_path.write_text(relation_content, encoding="utf-8")
    updated.append("relationship.board.md")

    quality_path = STATE / "quality.anchor.md"
    quality_content = quality_path.read_text(encoding="utf-8") if quality_path.exists() else _state_templates().get("quality.anchor.md", "")
    if _section_is_blank_template(quality_content, "场景厚度"):
        quality_content = _replace_markdown_section(
            quality_content,
            "场景厚度",
            "初始化同步：每集优先承担独立戏剧动作，不靠重复羞辱、重复试探、重复态度词填充时长。",
        )
    if _section_is_blank_template(quality_content, "对话节奏"):
        quality_content = _replace_markdown_section(
            quality_content,
            "对话节奏",
            "初始化同步：对白优先承接原著关系温度与信息顺序；短句服务情境，不服务模板化网感。",
        )
    if _section_is_blank_template(quality_content, "os 使用方式"):
        quality_content = _replace_markdown_section(
            quality_content,
            "os 使用方式",
            "初始化同步：os 只补瞬时判断或代价感，不替代剧情说明，不重复画面已给信息。",
        )
    if _section_is_blank_template(quality_content, "代表性打法"):
        quality_content = _replace_markdown_section(quality_content, "代表性打法", recommendation)
    quality_path.write_text(quality_content, encoding="utf-8")
    updated.append("quality.anchor.md")

    return updated


def _source_map_is_complete() -> bool:
    if not SOURCE_MAP.exists():
        return False
    content = SOURCE_MAP.read_text(encoding="utf-8")
    if "mapping_status: pending_book_extraction" in content:
        return False
    if re.search(r"^- mapping_status:\s*complete\s*$", content, re.MULTILINE):
        return not _source_map_quality_issues()
    return bool(re.search(r"^## Batch\s+\d+", content, re.MULTILINE))


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

def _ensure_run_log(now: str | None = None) -> None:
    """Guarantee run.log.md exists before any append operation.

    `clean` and interrupted runs can leave runtime state partially rebuilt.
    Logging should be fail-safe rather than crashing `start` before writer runs.
    """
    if RUN_LOG.exists():
        return
    STATE.mkdir(parents=True, exist_ok=True)
    RUN_LOG.write_text(_state_templates(now).get("run.log.md", ""), encoding="utf-8")


def _append_log(batch: str, episode: str, phase: str, event: str, result: str, note: str = "-") -> None:
    _ensure_run_log()
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


def _empty_verify_result(episode: str, tier: str, status: str) -> dict:
    draft_path = DRAFTS / f"{episode}.md"
    brief_name = _find_brief_for_episode(episode)
    if not brief_name:
        print(f"WARNING: no batch brief found for {episode} — brief_sha256 will be empty")
    brief_sha = _file_sha256(BATCH_BRIEFS / brief_name) if brief_name else ""
    return {
        "episode": episode,
        "tier": tier,
        "status": status,
        "timestamp": NOW,
        "draft_sha256": _file_sha256(draft_path),
        "brief_sha256": brief_sha,
        "source_map_sha256": _file_sha256(SOURCE_MAP),
        "reviewers": {},
    }


def _recompute_verify_status(data: dict) -> None:
    reviewers = data.get("reviewers", {})
    aligner_status = reviewers.get("aligner", {}).get("status", "MISSING")
    source_compare_status = reviewers.get("source_compare", {}).get("status", "MISSING")

    if "FAIL" in {aligner_status, source_compare_status}:
        overall = "FAIL"
    elif aligner_status == "PASS" and source_compare_status == "PASS":
        overall = "PASS"
    else:
        overall = "PENDING"

    data["aligner_status"] = aligner_status
    data["source_compare_status"] = source_compare_status
    data["status"] = overall
    data["timestamp"] = NOW


def _find_brief_for_episode(episode: str) -> str:
    """Find the batch brief filename that owns this episode."""
    if BATCH_BRIEFS.exists():
        for p in BATCH_BRIEFS.glob("*.md"):
            content = p.read_text(encoding="utf-8")
            if episode in content:
                return p.name
    return ""


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


def _ensure_state_files_initialized() -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    templates = _state_templates()
    for name, content in templates.items():
        path = STATE / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    _sync_state_from_blueprint()


def _shorten_text(text: str, limit: int = 48) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _episode_contract_rows(batch_id: str, episodes: list[str]) -> list[dict[str, object]]:
    batches = _parse_source_map()
    batch = batches.get(batch_id, {})
    episode_data = batch.get("episode_data", {})
    rows: list[dict[str, object]] = []
    for episode in episodes:
        data = _normalize_episode_function_metadata(episode, episode_data.get(episode, {}))
        beats = _beats_from_raw(data.get("must_keep", ""))
        relation_beats = [beat for beat in beats if "【关系】" in beat]
        rows.append(
            {
                "episode": episode,
                "source_span": str(data.get("source_span", "")).strip() or "(missing source span)",
                "beats": beats,
                "relation_beats": relation_beats,
                "ending_function": str(data.get("ending_function", "")).strip(),
            }
        )
    return rows


def _replace_state_section(path: Path, heading: str, body: str) -> None:
    content = path.read_text(encoding="utf-8") if path.exists() else _state_templates().get(path.name, "")
    path.write_text(_replace_markdown_section(content, heading, body), encoding="utf-8")


def _next_batch_expectation_block(batch_id: str) -> str:
    batches = _parse_source_map()
    batch_ids = sorted(batches.keys())
    try:
        idx = batch_ids.index(batch_id)
        next_batch = batch_ids[idx + 1] if idx + 1 < len(batch_ids) else None
    except ValueError:
        next_batch = None
    if next_batch is None:
        return "- 当前已是最后一批，下一批关键预期为空。"
    next_rows = _episode_contract_rows(next_batch, batches[next_batch].get("episodes", []))
    if not next_rows:
        return f"- 下一批 {next_batch} 已排定，但尚未读取到 episode contract。"
    preview = []
    for row in next_rows[:2]:
        first_beat = _shorten_text((row["beats"] or ["（待补）"])[0])
        preview.append(f"- {row['episode']}: {first_beat}")
    return "\n".join([f"- 下一批：{next_batch}"] + preview)


def _apply_batch_record(batch_id: str, brief_path: Path, brief: dict, review: dict | None) -> list[str]:
    _ensure_state_files_initialized()
    manifest = _read_manifest()
    episodes = brief.get("episodes", [])
    rows = _episode_contract_rows(batch_id, episodes)
    review = review or _read_batch_review(batch_id) or {}
    review_status = review.get("status", "MISSING")
    warnings = review.get("warning_families", []) or []
    quality_findings = review.get("quality_anchor_findings", []) or []
    published_count = len(list(EPISODES.glob("EP-*.md")))
    ep_range = f"{episodes[0]} ~ {episodes[-1]}" if len(episodes) > 1 else (episodes[0] if episodes else batch_id)

    script_progress = STATE / "script.progress.md"
    _replace_state_section(
        script_progress,
        "项目信息",
        "\n".join(
            [
                f"- source_file: {manifest.get('source_file', '(unknown)')}",
                f"- total_episodes: {manifest.get('total_episodes', '(pending)')}",
                f"- batch_size: {manifest.get('batch_size', '(unknown)')}",
            ]
        ),
    )
    _replace_state_section(
        script_progress,
        "基础文档",
        "\n".join(
            [
                f"- book.blueprint: {_relative_to_root(BOOK_BLUEPRINT)}",
                f"- source.map: {_relative_to_root(SOURCE_MAP)}",
                f"- batch brief: {_relative_to_root(brief_path)}",
            ]
        ),
    )
    _replace_state_section(
        script_progress,
        "当前整季状态",
        "\n".join(
            [
                f"- latest_recorded_batch: {batch_id}",
                f"- published_episode_count: {published_count}",
                f"- batch_review_status: {review_status}",
            ]
        ),
    )
    record_lines = [f"### {batch_id} ({ep_range})"]
    for row in rows:
        beat_preview = " / ".join(_shorten_text(beat, 28) for beat in row["beats"][:2]) or "（待补）"
        record_lines.append(f"- {row['episode']}: {beat_preview}")
    _replace_state_section(script_progress, "分集记录", "\n".join(record_lines))
    _replace_state_section(
        script_progress,
        "全局记录",
        "\n".join(
            [
                f"- {NOW}: {batch_id} 已发布并完成自动 record。",
                f"- review verdict: {review_status}",
            ]
        ),
    )
    _replace_state_section(
        script_progress,
        "质量统计",
        "\n".join(
            [
                f"- warning_families: {', '.join(warnings) if warnings else '(none)'}",
                f"- quality_anchor_findings: {', '.join(quality_findings) if quality_findings else '(none)'}",
            ]
        ),
    )
    _replace_state_section(
        script_progress,
        "版本记录",
        f"- {NOW}: {batch_id} record auto-applied",
    )

    story_state = STATE / "story.state.md"
    _replace_state_section(story_state, "当前阶段", f"- 已完成 {batch_id} 记录，覆盖 {ep_range}。")
    _replace_state_section(
        story_state,
        "权力格局",
        "\n".join(f"- {row['episode']}: {_shorten_text((row['beats'] or ['（待补）'])[0])}" for row in rows) or "- （待补）",
    )
    _replace_state_section(
        story_state,
        "主要角色位置",
        "\n".join(
            f"- {row['episode']}: source={row['source_span']}; ending={row['ending_function'] or '(none)'}"
            for row in rows
        ) or "- （待补）",
    )
    _replace_state_section(
        story_state,
        "最近关键转折",
        "\n".join(
            f"- {row['episode']}: {_shorten_text((row['beats'] or ['（待补）'])[-1])}" for row in rows
        ) or "- （待补）",
    )
    _replace_state_section(story_state, "下一批关键预期", _next_batch_expectation_block(batch_id))

    relationship_board = STATE / "relationship.board.md"
    relation_lines = [
        f"- {row['episode']}: {_shorten_text(beat)}"
        for row in rows
        for beat in row["relation_beats"][:2]
    ]
    relation_block = "\n".join(relation_lines) or "- 本批合同未显式标注关系 beat。"
    _replace_state_section(relationship_board, "核心关系网", relation_block)
    _replace_state_section(relationship_board, "最近关系变动", relation_block)
    _replace_state_section(relationship_board, "待爆关系线", _next_batch_expectation_block(batch_id))

    open_loops = STATE / "open_loops.md"
    unresolved = [
        f"- {row['episode']}: ending_function={row['ending_function']}"
        for row in rows
        if row["ending_function"] and row["ending_function"] not in {"closure", "emotional_payoff"}
    ]
    unresolved_block = "\n".join(unresolved) or "- 无明显未闭合结尾。"
    _replace_state_section(open_loops, "未回收伏笔", unresolved_block)
    _replace_state_section(open_loops, "未爆真相", unresolved_block)
    _replace_state_section(open_loops, "待解冲突", unresolved_block)
    _replace_state_section(open_loops, "已超期伏笔", "- 无")

    quality_anchor = STATE / "quality.anchor.md"
    _replace_state_section(
        quality_anchor,
        "场景厚度",
        f"- 当前批次 {batch_id} 以 reviewer verdict 为主，warning={', '.join(warnings) if warnings else '(none)'}。",
    )
    _replace_state_section(
        quality_anchor,
        "对话节奏",
        "- 继续沿用 write-contract.md / writer-style.md 作为主约束，不再依赖后验 lint 配额。",
    )
    _replace_state_section(
        quality_anchor,
        "os 使用方式",
        "- reviewer 只对明显直给或偷解释的 os 记 warning；无 warning 时默认可接受。",
    )
    _replace_state_section(
        quality_anchor,
        "代表性打法",
        "\n".join(f"- {item}" for item in quality_findings) if quality_findings else f"- {batch_id}: reviewer-only gate / contract-first writing",
    )

    process_memory = STATE / "process.memory.md"
    _replace_state_section(
        process_memory,
        "活跃流程问题",
        "\n".join(
            [
                "- check 已降级为 review packet 重建入口，不再是主流程必经步骤。",
                "- record 已收编为 controller 自动写入 state，不再依赖 script-recorder.md 手工执行。",
                "- writer 外调命令已改为参数列表执行，避免 shell=True 带来的 Windows 不稳定。",
            ]
        ),
    )
    _replace_state_section(
        process_memory,
        "当前执行准则",
        "\n".join(
            [
                "- start batchXX",
                "- start batchXX --write",
                "- batch-review-done batchXX PASS|FAIL --reviewer <name>",
                "- run batchXX",
                "- record batchXX",
            ]
        ),
    )

    _append_log(batch_id, ep_range, "record", "controller record", "✓", "state auto-updated")
    return [name for name in TEMPLATE_SECTIONS]


# ---------------------------------------------------------------------------
# Source map parsing
# ---------------------------------------------------------------------------


def _normalize_episode_id(raw: str) -> str:
    match = re.search(r"EP-?(\d+)", raw.strip(), re.IGNORECASE)
    if not match:
        return raw.strip()
    return f"EP-{match.group(1).zfill(2)}"


ALLOWED_ENDING_FUNCTIONS = {
    "arrival",
    "confrontation_pending",
    "reveal_pending",
    "locked_in",
    "reversal_triggered",
    "emotional_payoff",
    "closure",
}

ALLOWED_IRREVERSIBILITY_LEVELS = {"soft", "medium", "hard"}

def _split_fact_list(raw: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;,，；]+", raw) if item.strip()]


def _beats_from_raw(must_keep_raw: str | list[str]) -> list[str]:
    if isinstance(must_keep_raw, list):
        return [str(item).strip() for item in must_keep_raw if str(item).strip()]
    text = str(must_keep_raw)
    if "\n" in text:
        return [
            beat.strip(" -")
            for beat in text.splitlines()
            if beat.strip(" -")
        ]
    return [
        beat.strip(" -")
        for beat in re.split(r"[\uff1b;]+", text)
        if beat.strip(" -")
    ]


def _beat_looks_executable(beat: str) -> bool:
    text = beat.strip()
    if not text:
        return False
    if "【" in text:
        return True
    if any(token in text for token in ("，", "。", "；", "：", ":", "->", "→")):
        return True
    return len(text) >= 8


def _parse_function_signal_field(raw: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for line in raw.splitlines():
        stripped = line.strip().lstrip("-").strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        normalized_key = key.strip().lower()
        values = _split_fact_list(value.strip())
        if normalized_key == "opening_function" and values:
            result["opening_function"] = values[0]
        elif normalized_key == "middle_functions":
            result["middle_functions"] = values
        elif normalized_key in {"strong_signals", "strong_function_tags"}:
            result["strong_function_tags"] = values
    return result


def _collapse_markdown_list(raw: str) -> str:
    items = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        items.append(stripped)
    return "\n".join(items).strip()


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
                "knowledge_boundary": _extract_episode_map_field(
                    ep_block,
                    legacy_pattern=r"knowledge boundary：(.+)",
                    markdown_pattern=r"\*\*knowledge_boundary\*\*:\s*(.*?)(?=\n\*\*|\n---|\Z)",
                    multiline=True,
                ),
                "must_not": _extract_episode_map_field(
                    ep_block,
                    legacy_pattern=r"must-not-add / must-not-jump：(.+)",
                    markdown_pattern=r"\*\*must-not-add / must-not-jump\*\*:\s*(.*?)(?=\n\*\*|\n---|\Z)",
                    multiline=True,
                ),
                "ending_function": _extract_episode_map_field(
                    ep_block,
                    legacy_pattern=r"ending function：(.+)",
                    markdown_pattern=r"\*\*ending_function\*\*:\s*(.+)",
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
        parsed_beats = _beats_from_raw(beats)
        first_beat = parsed_beats[0] if parsed_beats else ep
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
        beat_arrows = " -> ".join(_beats_from_raw(beats)[:5])
        knowledge_lines = _beats_from_raw(data.get("knowledge_boundary", ""))
        ep_mapping_lines.append(f"- {ep}：{span}")
        ep_mapping_lines.append(f"  - {beat_arrows}")
        if knowledge_lines:
            ep_mapping_lines.append("  - knowledge_boundary:")
            ep_mapping_lines.extend(f"    - {item}" for item in knowledge_lines)
    ep_mapping = "\n".join(ep_mapping_lines)

    # Build hard constraints from must-not
    constraints = []
    for ep in episodes:
        must_not = episode_data.get(ep, {}).get("must_not", "")
        if must_not:
            for c in _beats_from_raw(must_not):
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

## Writer Authority
- 当前 batch brief：决定本批每集的任务、beats 与收尾上下文
- `harness/project/source.map.md`：决定 source 顺序、knowledge_boundary、must-not-add、must-not-jump 边界
- `harness/project/run.manifest.md`：只提供运行参数，不裁决内容冲突
- `voice-anchor.md` / `character.md`：仅作气质、禁区与称谓参考，不覆盖当前集任务

## Episode Mapping
{ep_mapping}

## Hard Constraints
{constraints_text}
"""


def _normalize_episode_function_metadata(episode: str, data: dict[str, object]) -> dict[str, object]:
    ending_function = str(data.get("ending_function", "")).strip()
    normalized = dict(data)
    normalized["ending_function"] = ending_function if ending_function in ALLOWED_ENDING_FUNCTIONS else ""
    return normalized


def _source_map_quality_issues() -> list[str]:
    if not SOURCE_MAP.exists():
        return ["source.map.md missing"]

    issues = []
    try:
        batches = _parse_source_map()
    except Exception as exc:  # pragma: no cover - defensive guard for malformed map files
        return [f"source.map parse failed: {exc}"]

    for batch_id, batch in batches.items():
        for episode in batch.get("episodes", []):
            episode_data = _normalize_episode_function_metadata(
                episode,
                batch["episode_data"].get(episode, {}),
            )
            source_span = str(episode_data.get("source_span", "")).strip()
            must_keep = _beats_from_raw(episode_data.get("must_keep", ""))
            knowledge_boundary = _beats_from_raw(episode_data.get("knowledge_boundary", ""))
            if not source_span:
                issues.append(f"{batch_id}/{episode}: source_chapter_span is missing")
            if not must_keep:
                issues.append(f"{batch_id}/{episode}: must-keep beats are missing")
            elif not any(_beat_looks_executable(beat) for beat in must_keep):
                issues.append(
                    f"{batch_id}/{episode}: must-keep beats are too abstract; add at least one actionable beat"
                )
            if not knowledge_boundary:
                issues.append(f"{batch_id}/{episode}: knowledge_boundary is missing")
    return issues


def _compute_review_focus(episodes: list[str]) -> dict[str, list[str]]:
    deep: list[str] = []
    standard: list[str] = []
    light: list[str] = []
    unmapped: list[str] = []

    manifest = _read_manifest()
    key_episodes = {
        item.strip()
        for item in str(manifest.get("key_episodes", "")).split(",")
        if item.strip()
    }

    source_map_text = SOURCE_MAP.read_text(encoding="utf-8") if SOURCE_MAP.exists() else ""
    for index, episode in enumerate(episodes):
        block = _source_map_episode_block(source_map_text, episode)
        if not block.strip():
            unmapped.append(episode)
            continue
        if episode in key_episodes or index == 0:
            deep.append(episode)
        else:
            standard.append(episode)

    return {"deep": deep, "standard": standard, "light": light, "unmapped": unmapped}

def _print_start_next_steps(
    batch_id: str,
    episodes: list[str],
    focus: dict[str, list[str]],
    *,
    include_writer_instruction: bool,
) -> None:
    step_no = 1
    if include_writer_instruction:
        print(f"  {step_no}. Writer stage:    draft {', '.join(episodes)} into drafts/episodes/")
        step_no += 1

    print(f"  {step_no}. Review verdict:  python _ops/controller.py batch-review-done {batch_id} PASS --reviewer <name>")
    step_no += 1

    unmapped_eps = focus.get("unmapped", [])
    if unmapped_eps:
        print(f"  ? Unmapped episodes: {', '.join(unmapped_eps)}")
        print("    ? Update source.map.md before trusting the review packet.")

    deep_eps = focus.get("deep", [])
    standard_eps = focus.get("standard", [])
    light_eps = focus.get("light", [])
    if deep_eps or standard_eps or light_eps:
        print(f"  {step_no}. Reviewer focus:")
        if deep_eps:
            print(f"     DEEP:     {', '.join(deep_eps)}")
        if standard_eps:
            print(f"     STANDARD: {', '.join(standard_eps)}")
        if light_eps:
            print(f"     LIGHT:    {', '.join(light_eps)}")
        step_no += 1

    print(f"  {step_no}. Formal release:  python _ops/controller.py run {batch_id}")

def _relative_to_root(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json_file(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def _release_journal_path(batch_id: str) -> Path:
    return RELEASE_JOURNALS / f"{batch_id}.promote.json"


def _resolve_root_relative_path(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path
    return ROOT / path


def _write_release_journal(batch_id: str, payload: dict) -> Path:
    RELEASE_JOURNALS.mkdir(parents=True, exist_ok=True)
    payload["updated_at"] = NOW
    path = _release_journal_path(batch_id)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _read_release_journal(batch_id: str) -> dict | None:
    return _read_json_file(_release_journal_path(batch_id))


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
    release_status: str = "gold",
) -> dict:
    review = _read_batch_review(batch_id) or {}
    return {
        "episode": episode,
        "provenance": RUNTIME_AUTHORITY,
        "source_batch": batch_id,
        "runtime_authority": RUNTIME_AUTHORITY,
        "release_status": release_status,
        "ruleset_version": RULESET_VERSION,
        "review_status": review.get("status", "MISSING"),
        "reviewer": review.get("reviewer", ""),
        "warnings": review.get("warning_families", []),
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
        "review_status": metadata["review_status"],
        "content_path": metadata["content_path"],
        "meta_path": _relative_to_root(_meta_path(metadata["episode"])),
        "updated_at": metadata["updated_at"],
    }


def _promote_batch(batch_id: str, brief_path: Path, episodes: list[str]) -> tuple[int, dict]:
    """Staged promote with a minimal journal for deterministic resume."""
    RELEASES.mkdir(parents=True, exist_ok=True)
    RELEASE_JOURNALS.mkdir(parents=True, exist_ok=True)
    RELEASE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    GOLD_SET.parent.mkdir(parents=True, exist_ok=True)
    journal = _read_json_file(_release_journal_path(batch_id))

    release_index: dict
    gold_set: dict
    if journal and not journal.get("completed", False):
        if journal.get("batch_id") != batch_id:
            return 1, {"error": "promote journal batch mismatch"}
        if journal.get("episodes") and journal.get("episodes") != episodes:
            return 1, {"error": "promote journal episode set mismatch"}

        stage_root = _resolve_root_relative_path(journal.get("stage_root"))
        staged_release_index = _resolve_root_relative_path(journal.get("staged_release_index"))
        staged_gold_set = _resolve_root_relative_path(journal.get("staged_gold_set"))
        if stage_root is None or staged_release_index is None or staged_gold_set is None:
            return 1, {"error": "promote journal is missing staged paths"}
        if not stage_root.exists():
            return 1, {"error": "promote journal exists but staged directory is missing"}

        staged_episode_files = {
            episode: _resolve_root_relative_path(path_value)
            for episode, path_value in journal.get("staged_episode_files", {}).items()
        }
        staged_meta_files = {
            episode: _resolve_root_relative_path(path_value)
            for episode, path_value in journal.get("staged_meta_files", {}).items()
        }
        published_episodes = set(journal.get("published_episodes", []))
        release_files_written = bool(journal.get("release_files_written", False))
        release_index = _read_json_file(staged_release_index) or _load_release_index()
        gold_set = _read_json_file(staged_gold_set) or _load_gold_set()
    else:
        stage_root = RELEASES / "staging" / f"{batch_id}-{NOW.replace(':', '').replace(' ', '-')}"
        stage_root.mkdir(parents=True, exist_ok=True)

        staged_episode_files: dict[str, Path] = {}
        staged_meta_files: dict[str, Path] = {}
        for episode in episodes:
            src = DRAFTS / f"{episode}.md"
            staged = stage_root / f"{episode}.md"
            shutil.copy2(src, staged)
            staged_episode_files[episode] = staged

        release_index = _load_release_index()
        gold_set = _load_gold_set()
        gold_episodes = set(gold_set.get("episodes", []))
        _bootstrap_legacy_entries(release_index, gold_episodes.union(set(episodes)))

        for episode in episodes:
            metadata = _build_episode_metadata(
                episode=episode,
                batch_id=batch_id,
                brief_path=brief_path,
            )
            staged_meta = stage_root / f"{episode}.meta.json"
            staged_meta.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            staged_meta_files[episode] = staged_meta
            release_index["episodes"][episode] = _build_release_entry(metadata)
            gold_episodes.add(episode)

        gold_set["episodes"] = sorted(gold_episodes)
        gold_set["updated_at"] = NOW

        staged_release_index = stage_root / "release.index.json"
        staged_gold_set = stage_root / "gold-set.json"
        staged_release_index.write_text(json.dumps(release_index, ensure_ascii=False, indent=2), encoding="utf-8")
        staged_gold_set.write_text(json.dumps(gold_set, ensure_ascii=False, indent=2), encoding="utf-8")

        published_episodes = set()
        release_files_written = False
        journal = {
            "batch_id": batch_id,
            "episodes": episodes,
            "phase": "publishing",
            "completed": False,
            "stage_root": _relative_to_root(stage_root),
            "staged_episode_files": {episode: _relative_to_root(path) for episode, path in staged_episode_files.items()},
            "staged_meta_files": {episode: _relative_to_root(path) for episode, path in staged_meta_files.items()},
            "staged_release_index": _relative_to_root(staged_release_index),
            "staged_gold_set": _relative_to_root(staged_gold_set),
            "published_episodes": sorted(published_episodes),
            "release_files_written": release_files_written,
        }
        _release_journal_path(batch_id).write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")

    EPISODES.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)

    for episode in episodes:
        if episode in published_episodes:
            continue
        staged_episode = staged_episode_files.get(episode)
        staged_meta = staged_meta_files.get(episode)
        if staged_episode is None or staged_meta is None or not staged_episode.exists() or not staged_meta.exists():
            return 1, {"error": f"staged artifacts missing for {episode}"}
        staged_episode.replace(EPISODES / f"{episode}.md")
        staged_meta.replace(_meta_path(episode))
        published_episodes.add(episode)
        journal["published_episodes"] = sorted(published_episodes)
        _release_journal_path(batch_id).write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")

    if not release_files_written:
        staged_release_index.replace(RELEASE_INDEX)
        staged_gold_set.replace(GOLD_SET)
        journal["release_files_written"] = True
        _release_journal_path(batch_id).write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")

    journal["completed"] = True
    journal["phase"] = "completed"
    _release_journal_path(batch_id).write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")

    if stage_root.exists():
        shutil.rmtree(stage_root, ignore_errors=True)

    return 0, {"release_index": _load_release_index(), "gold_set": _load_gold_set()}

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
    runtime_phase = _batch_runtime_phase(batch_id)
    if require_frozen:
        if runtime_phase in {"promoted", "recorded"}:
            print(f"ERROR: batch '{batch_id}' is already promoted")
            return None
        status = brief.get("status", "unknown")
        if runtime_phase is None and status == "promoted":
            print(f"ERROR: batch '{batch_id}' is already promoted")
            return None
        if runtime_phase is None and status != "frozen":
            print(f"ERROR: batch brief status is '{status}', must be 'frozen'")
            return None
    return brief_path, brief, episodes


def _missing_drafts(episodes: list[str]) -> list[str]:
    return [ep for ep in episodes if not (DRAFTS / f"{ep}.md").exists()]


def _write_prompt_packet(filename: str, prompt: str) -> Path:
    PROMPTS.mkdir(parents=True, exist_ok=True)
    path = PROMPTS / filename
    path.write_text(prompt, encoding="utf-8")
    return path


def _render_polish_prompt(batch_id: str, episodes: list[str], brief_path: Path) -> str:
    manifest = _read_manifest()
    draft_paths = "\n".join(f"- drafts/episodes/{episode}.md" for episode in episodes) or "- (none)"
    return _render_template_text(
        POLISH_PROMPT_TEMPLATE,
        {
            "batch_id": batch_id,
            "quality_mode": manifest.get("quality_mode", "standard"),
            "episodes": ", ".join(episodes),
            "batch_brief_path": _relative_to_root(brief_path),
            "source_map_path": _relative_to_root(SOURCE_MAP),
            "character_path": _relative_to_root(ROOT / "character.md"),
            "voice_anchor_path": _relative_to_root(ROOT / "voice-anchor.md"),
            "writer_style_path": _relative_to_root(FRAMEWORK / "writer-style.md"),
            "write_contract_path": _relative_to_root(FRAMEWORK / "write-contract.md"),
            "draft_paths": draft_paths,
            "polish_report_path": _relative_to_root(_batch_polish_report_path(batch_id)),
        },
    )


def _print_prompt_ready(prompt_path: Path, target_paths: list[Path], *, next_command: str | None = None) -> None:
    print("  -> Prompt packet ready; no Python-managed model process was started.")
    print(f"  Prompt: {_relative_to_root(prompt_path)}")
    print("  Expected output:")
    for target in target_paths:
        print(f"  - {_relative_to_root(target)}")
    if next_command:
        print("  After the agent writes the expected output, run:")
        print(f"    {next_command}")


def _sync_run_writer_paths(run_writer_module) -> None:
    """Keep imported prompt builder paths aligned with controller-level test/runtime patches."""
    run_writer_module.ROOT = ROOT
    run_writer_module.PASSING_SAMPLE = FRAMEWORK / "passing-episode.sample.md"
    run_writer_module.WRITE_CONTRACT_PATH = FRAMEWORK / "write-contract.md"
    run_writer_module.WRITER_STYLE_PATH = FRAMEWORK / "writer-style.md"
    run_writer_module.WRITER_PROMPT_TEMPLATE = FRAMEWORK / "writer-prompt.template.md"
    run_writer_module.WRITER_BATCH_PROMPT_TEMPLATE = FRAMEWORK / "writer-batch-prompt.template.md"
    run_writer_module.PROMPTS_DIR = PROMPTS


def _load_run_writer_prompt_builder():
    script_path = Path(__file__).resolve().with_name("run_writer.py")
    spec = importlib.util.spec_from_file_location("juben_run_writer_prompt_builder", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _warn_unanchored_voice_assets() -> None:
    pending = _pending_voice_assets()
    if pending:
        print(f"  ⚠ 声纹锚未完成，后续返修成本会放大: {', '.join(pending)}")
        print("    → 建议在 batch02 前补齐 voice-anchor.md / character.md")


def _pending_voice_assets() -> list[str]:
    pending = []
    for filename in ["voice-anchor.md", "character.md"]:
        path = ROOT / filename
        if not path.exists():
            pending.append(filename)
            continue
        if "AGENT_EXTRACT_REQUIRED" in path.read_text(encoding="utf-8"):
            pending.append(filename)
    return pending


def _guard_quality_anchors() -> bool:
    pending = _pending_voice_assets()
    if pending:
        print(f"WARNING: quality anchors are still pending extraction: {', '.join(pending)}")
        print("  Writer will continue without them;补齐后可提升角色稳定性")
        return True
    voice_issues = _voice_anchor_quality_issues()
    if voice_issues:
        print("ERROR: voice-anchor.md did not pass the quality gate")
        for issue in voice_issues:
            print(f"  - {issue}")
        print("  Rewrite voice-anchor.md as气质/节奏/边界约束，而不是常用表达模板")
        return False
    return True


def _writer_parallelism() -> int:
    raw = _read_manifest().get("writer_parallelism", "").strip()
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    return DEFAULT_WRITER_PARALLELISM


def _run_writer_stage(
    batch_id: str,
    episodes: list[str],
    *,
    parallelism: int | None = None,
    syntax_first: bool = False,
    force_rewrite: bool = False,
) -> int:
    if force_rewrite:
        for episode in episodes:
            draft = DRAFTS / f"{episode}.md"
            if draft.exists():
                draft.unlink()

    requested_parallelism = max(1, parallelism or _writer_parallelism())
    completed_episodes = [ep for ep in episodes if (DRAFTS / f"{ep}.md").exists()]
    if len(completed_episodes) == len(episodes):
        print(f"  ✓ Using existing drafts for {', '.join(episodes)}")
        _upsert_batch_status(batch_id, completed_episodes=completed_episodes)
        return 0

    remaining = [ep for ep in episodes if ep not in completed_episodes]
    print(f"  -> Writer drafts missing: {', '.join(remaining)}")
    print("  -> Building writer prompt packet only; controller will not call model CLIs.")

    try:
        run_writer = _load_run_writer_prompt_builder()
    except ImportError as exc:
        print(f"ERROR: failed to load writer prompt builder: {exc}")
        return 1
    _sync_run_writer_paths(run_writer)

    brief_path = run_writer._find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for {batch_id}")
        return 1

    batch_context_path = run_writer._build_batch_context_bundle(batch_id, brief_path)
    source_excerpt_paths = {
        episode: run_writer._build_episode_source_excerpt(batch_id, episode)
        for episode in remaining
    }

    prompt_targets = [DRAFTS / f"{episode}.md" for episode in remaining]
    if len(remaining) > 1 and requested_parallelism == 1:
        prompt = run_writer._build_sequential_batch_writer_prompt(
            batch_id,
            remaining,
            brief_path,
            batch_context_path=batch_context_path,
            source_excerpt_paths=source_excerpt_paths,
            syntax_first=syntax_first,
        )
        prompt_path = _write_prompt_packet(f"{batch_id}.writer.batch.prompt.md", prompt)
        prompt_paths = [prompt_path]
    else:
        prompt_paths = []
        for episode in remaining:
            prompt = run_writer._build_writer_prompt(
                batch_id,
                episode,
                brief_path,
                batch_context_path=batch_context_path,
                source_excerpt_path=source_excerpt_paths[episode],
                syntax_first=syntax_first,
            )
            prompt_paths.append(_write_prompt_packet(f"{batch_id}.{episode}.writer.prompt.md", prompt))

    _upsert_batch_status(
        batch_id,
        phase="writing_pending",
        status="BLOCKED",
        episodes=episodes,
        completed_episodes=completed_episodes,
    )
    for prompt_path in prompt_paths:
        _print_prompt_ready(
            prompt_path,
            prompt_targets,
            next_command=f"python _ops/controller.py start {batch_id} --write",
        )
    return WRITER_STAGE_PROMPTS_READY


def _run_polish_stage(batch_id: str, episodes: list[str], brief_path: Path) -> int:
    missing = _missing_drafts(episodes)
    if missing:
        print(f"ERROR: cannot polish; missing drafts: {', '.join(missing)}")
        print(f"  Run first: python _ops/controller.py start {batch_id} --write")
        return 1
    if not POLISH_PROMPT_TEMPLATE.exists():
        print(f"ERROR: polish prompt template missing: {_relative_to_root(POLISH_PROMPT_TEMPLATE)}")
        return 1

    REVIEWS.mkdir(parents=True, exist_ok=True)
    prompt = _render_polish_prompt(batch_id, episodes, brief_path)
    prompt_path = _write_prompt_packet(f"{batch_id}.polish.prompt.md", prompt)
    target_paths = [DRAFTS / f"{episode}.md" for episode in episodes]
    target_paths.append(_batch_polish_report_path(batch_id))
    _upsert_batch_status(
        batch_id,
        phase="polish_pending",
        status="BLOCKED",
        episodes=episodes,
        brief_path=brief_path,
    )
    _print_prompt_ready(
        prompt_path,
        target_paths,
        next_command=f"python _ops/controller.py start {batch_id} --write",
    )
    print("  Polish mode: external agent only; this command does not call model CLIs.")
    print("  After polish edits drafts, re-run start --write to refresh the review packet.")
    return WRITER_STAGE_PROMPTS_READY


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

    print("=== Batch Overview ===")
    batch_ids = _known_batch_ids()
    if batch_ids:
        for batch_id in batch_ids:
            summary = _batch_status_summary(batch_id)
            episode_suffix = ""
            if summary["episodes"]:
                episode_suffix = f", episodes={', '.join(summary['episodes'])}"
            review_reason_suffix = ""
            if summary["review_reason"]:
                review_reason_suffix = f", review_reason={summary['review_reason']}"
            print(
                "  "
                f"{summary['batch_id']}: "
                f"phase={summary['phase']}, "
                f"status={summary['status']}, "
                f"batch_review={summary['batch_review_status']}, "
                f"review_artifact={summary['review_artifact']}, "
                f"promote_journal={summary['promote_journal']}, "
                f"authority={summary['authority']}, "
                f"brief={summary['brief_path']}"
                f"{review_reason_suffix}"
                f"{episode_suffix}"
            )
    else:
        print("  (none)")
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
    runtime_phase = _batch_runtime_phase(batch_id)

    if runtime_phase in {"promoted", "recorded"} or current_status == "promoted":
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


def cmd_promote(args: argparse.Namespace) -> int:
    batch_id = args.batch_id
    resolved = _resolve_batch(args.batch_id, require_frozen=True)
    if resolved is None:
        return 1
    brief_path, _brief, episodes = resolved

    ok, message = _require_batch_review_pass(batch_id)
    if not ok:
        print(message)
        return 1

    if _is_locked("state.lock"):
        print("ERROR: state.lock is held — cannot promote")
        return 1

    rc, _ = _promote_batch(batch_id, brief_path, episodes)
    if rc != 0:
        print("ERROR: staging promote failed")
        return 1
    for ep in episodes:
        print(f"  → {ep}: draft → published (gold)")

    _set_batch_status(brief_path, "promoted")
    _upsert_batch_status(batch_id, phase="promoted", status="ACTIVE", batch_review_status="PASS")
    _set_manifest_field("active_batch", f"{batch_id}_promoted")
    _write_lock("batch.lock", "unlocked")

    for ep in episodes:
        _clear_retry_count(ep)

    ep_range = f"{episodes[0]}~{episodes[-1]}" if len(episodes) > 1 else episodes[0]
    _append_log(batch_id, ep_range, "promote", "controller promote", "✓", f"{len(episodes)} episodes promoted")

    stats = _export_outputs()
    print(f"\nPROMOTE OK: {batch_id} → {len(episodes)} episodes published")
    print(f"  Output refreshed: output/ ({stats.get('episodes', 0)} episodes)")
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


def cmd_export(args: argparse.Namespace) -> int:
    _sync_manifest_completion_state()
    stats = _export_outputs()
    print("=== Output Export Complete ===")
    print(f"  Root: {OUTPUT.relative_to(ROOT)}")
    print(f"  Summary: {(OUTPUT / 'SUMMARY.md').relative_to(ROOT)}")
    print(f"  Manifest: {(OUTPUT / 'manifest.json').relative_to(ROOT)}")
    for key in ("episodes", "drafts", "reviews", "prompts", "briefs", "maps", "anchors", "state"):
        print(f"  {key}: {stats.get(key, 0)}")
    return 0


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


def cmd_polish(args: argparse.Namespace) -> int:
    batch_id = args.batch_id
    resolved = _resolve_batch(batch_id)
    if resolved is None:
        return 1
    brief_path, _brief, episodes = resolved
    print(f"=== Polish Prompt Packet: {batch_id} ===")
    return _run_polish_stage(batch_id, episodes, brief_path)


def cmd_batch_review(args: argparse.Namespace) -> int:
    """Create durable batch review artifacts and print review instructions."""
    batch_id = args.batch_id
    resolved = _resolve_batch(args.batch_id)
    if resolved is None:
        return 1
    brief_path, brief, episodes = resolved

    review = _ensure_batch_review_artifacts(batch_id, episodes, brief_path=brief_path)
    review_status = review.get("status", "PENDING")
    phase = "review_passed" if review_status == "PASS" else "review_pending"
    runtime_status = "ACTIVE" if review_status == "PASS" else "BLOCKED"
    _upsert_batch_status(batch_id, phase=phase, status=runtime_status, batch_review_status=review_status)

    print(f"=== Batch Review: {batch_id} ===")
    print(f"\n  Episodes in batch: {', '.join(review.get('episodes', episodes))}")
    print(f"  Sampled for adversarial deep-check: {', '.join(review.get('sampled_episodes', [])) or '(none)'}")
    print(f"  Review JSON: {_batch_review_json_path(batch_id).relative_to(ROOT)}")
    print(f"  Review MD:   {_batch_review_md_path(batch_id).relative_to(ROOT)}")
    print(f"  Review Prompt: {_batch_review_prompt_path(batch_id).relative_to(ROOT)}")
    print(f"  Review Standard: {REVIEW_STANDARD.relative_to(ROOT)}")
    print(f"  Verdict:     {review.get('status', 'PENDING')}")
    print(f"\n  Use the prompt file above as the reviewer instruction.")
    print(f"  Use the standard file above as the grading rubric.")
    print(f"\n  When review is complete:")
    print(f"    python _ops/controller.py batch-review-done {batch_id} PASS --reviewer <name>")
    print(f"    python _ops/controller.py batch-review-done {batch_id} FAIL --reviewer <name> --reason \"...\"")
    return 0


def cmd_batch_review_done(args: argparse.Namespace) -> int:
    batch_id = args.batch_id
    verdict = args.status.upper()
    reviewer = (args.reviewer or "").strip()
    reason = (args.reason or "").strip()
    blocking_reasons = [item.strip() for item in getattr(args, "blocking_reasons", []) if item and item.strip()]
    warning_families = [item.strip() for item in getattr(args, "warning_families", []) if item and item.strip()]
    arc_regressions = [item.strip() for item in getattr(args, "arc_regressions", []) if item and item.strip()]
    function_theft_findings = [
        item.strip() for item in getattr(args, "function_theft_findings", []) if item and item.strip()
    ]
    quality_anchor_findings = [
        item.strip() for item in getattr(args, "quality_anchor_findings", []) if item and item.strip()
    ]
    evidence_refs = [item.strip() for item in getattr(args, "evidence_refs", []) if item and item.strip()]

    if verdict not in {"PASS", "FAIL"}:
        print(f"ERROR: status must be PASS or FAIL, got '{args.status}'")
        return 1
    if not reviewer:
        print("ERROR: --reviewer is required")
        return 1
    if verdict == "FAIL" and not reason:
        print("ERROR: --reason is required when verdict is FAIL")
        return 1

    review = _read_batch_review(batch_id)
    if review is None:
        print(f"ERROR: batch review artifact missing for '{batch_id}'")
        print(f"  Run: python _ops/controller.py start {batch_id} --write")
        print(f"  Fallback: python _ops/controller.py check {batch_id}")
        return 1

    if verdict == "FAIL" and reason and reason not in blocking_reasons:
        blocking_reasons.insert(0, reason)

    review["status"] = verdict
    review["reviewer"] = reviewer
    review["reason"] = reason
    review["blocking_reasons"] = blocking_reasons
    review["warning_families"] = warning_families
    review["arc_regressions"] = arc_regressions
    review["function_theft_findings"] = function_theft_findings
    review["quality_anchor_findings"] = quality_anchor_findings
    review["evidence_refs"] = evidence_refs
    _write_batch_review_artifacts(batch_id, review, brief_path=_find_batch_brief(batch_id))

    if verdict == "PASS":
        _upsert_batch_status(batch_id, phase="review_passed", status="ACTIVE", batch_review_status="PASS")
    else:
        _upsert_batch_status(batch_id, phase="review_pending", status="BLOCKED", batch_review_status="FAIL")

    print(f"OK: batch review {verdict} recorded for {batch_id}")
    print(f"  reviewer: {reviewer}")
    if reason:
        print(f"  reason: {reason}")
    if blocking_reasons:
        print(f"  blocking_reasons: {len(blocking_reasons)}")
    if evidence_refs:
        print(f"  evidence_refs: {len(evidence_refs)}")
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

def cmd_record(args: argparse.Namespace) -> int:
    """Automatically update state files for a promoted batch and release state.lock."""
    batch_id = args.batch_id
    brief_path = _find_batch_brief(batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for '{batch_id}'")
        return 1

    brief = _read_batch_brief(brief_path)
    runtime = _read_batch_status(batch_id)
    if runtime:
        if runtime.get("phase") != "promoted":
            print(
                f"ERROR: batch '{batch_id}' must be promoted first "
                f"(runtime phase: {runtime.get('phase', '?')})"
            )
            return 1
    elif brief.get("status") != "promoted":
        print(f"ERROR: batch '{batch_id}' must be promoted first (status: {brief.get('status', '?')})")
        return 1

    if _is_locked("state.lock"):
        lock_data = _read_lock("state.lock")
        print(f"ERROR: state.lock held by '{lock_data.get('owner', '?')}'")
        return 1

    episodes = brief.get("episodes", [])
    _write_lock("state.lock", "locked", f"recorder:{batch_id}")
    try:
        review = _read_batch_review(batch_id)
        updated_files = _apply_batch_record(batch_id, brief_path, brief, review)
        validation_errors: list[str] = []
        for name, sections in TEMPLATE_SECTIONS.items():
            validation_errors.extend(_validate_state_file(name, sections))
        if validation_errors:
            print("ERROR: automatic record wrote incomplete state files")
            for error in validation_errors:
                print(f"  - {error}")
            return 1
        _write_lock("state.lock", "unlocked")
        _upsert_batch_status(batch_id, phase="recorded", status="DONE", batch_review_status="PASS")
        _sync_manifest_completion_state()
        stats = _export_outputs()
        print(f"=== Record Complete: {batch_id} ===")
        print(f"  Episodes: {', '.join(episodes)}")
        print(f"  Updated state files: {', '.join(updated_files)}")
        print(f"  Output refreshed: output/ ({stats.get('episodes', 0)} episodes)")
        print("  state.lock released")
        return 0
    finally:
        if _read_lock("state.lock").get("status") == "locked":
            _write_lock("state.lock", "unlocked")


def cmd_record_done(args: argparse.Namespace) -> int:
    """Compatibility alias: validate state files after auto-record."""
    batch_id = args.batch_id

    lock_data = _read_lock("state.lock")
    if lock_data.get("status") != "locked":
        runtime = _read_batch_status(batch_id) or {}
        if runtime.get("phase") == "recorded":
            print(f"=== Record Validation: {batch_id} ===")
            all_valid = True
            for name, sections in TEMPLATE_SECTIONS.items():
                errors = _validate_state_file(name, sections)
                if errors:
                    all_valid = False
                    for e in errors:
                        print(f"  ✗ {e}")
                else:
                    print(f"  ✓ {name}")
            if all_valid:
                print("\n  ✓ Record already complete; state files remain valid")
                return 0
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

    # Release state.lock (legacy path only)
    _write_lock("state.lock", "unlocked")
    _upsert_batch_status(batch_id, phase="recorded", status="DONE", batch_review_status="PASS")

    ep_range = f"{episodes[0]}~{episodes[-1]}" if len(episodes) > 1 else episodes[0]
    _append_log(batch_id, ep_range, "record", "recorder 完成", "✓", "state 全量写入")
    stats = _export_outputs()

    print(f"\n  ✓ State validation passed")
    print(f"  ✓ state.lock released")
    print(f"  ✓ Record phase complete for {batch_id}")
    print(f"  ✓ Output refreshed: output/ ({stats.get('episodes', 0)} episodes)")

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
    plain_chapter_pattern = (
        r"^第[0-9０-９一二三四五六七八九十百千万两〇零○]+[章节回卷]"
        r"(?:$|[\s\u3000]+.+)$"
    )

    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^#{1,4}\s*第.+[章回]", stripped):
            title = stripped.lstrip("#").strip()
            chapter_starts.append((i, title))
        elif re.match(plain_chapter_pattern, stripped):
            chapter_starts.append((i, stripped))
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


def _book_blueprint_template(
    novel_name: str,
    chapters: list[dict],
    *,
    target_total_minutes: int = DEFAULT_TARGET_TOTAL_MINUTES,
) -> str:
    chapter_index = "\n".join(_chapter_index_lines(chapters))
    return f"""# Book Blueprint

- source_file: {novel_name}
- extraction_status: pending
- chapter_count: {len(chapters)}
- target_total_minutes: {target_total_minutes}
- target_episode_minutes: {DEFAULT_TARGET_EPISODE_MINUTES}
- episode_minutes_min: {DEFAULT_EPISODE_MINUTES_MIN}
- episode_minutes_max: {DEFAULT_EPISODE_MINUTES_MAX}
- recommended_total_episodes: {PENDING_BLUEPRINT_RECOMMENDATION}

说明：
- 先做全书级抽取，再生成 `source.map.md`
- 章节只作为定位信息，不作为主要思考单位
- 本文件是全书级改编蓝图，先锁主线/弧光/反转/结局，再切 batch / episode
- 全剧目标总时长约 {target_total_minutes} 分钟；集数建议围绕总时长、单集时长和有效戏剧单元共同估算
- 单集时长按 {DEFAULT_EPISODE_MINUTES_MIN}-{DEFAULT_EPISODE_MINUTES_MAX} 分钟动态浮动，中心值 {DEFAULT_TARGET_EPISODE_MINUTES} 分钟/集

## 主线

（AGENT_EXTRACT_REQUIRED）

## 集数建议

- 推荐区间： （AGENT_EXTRACT_REQUIRED）
- 最终采用： （AGENT_EXTRACT_REQUIRED）
- 可独立成集戏剧节点： （AGENT_EXTRACT_REQUIRED）
- 应合并压缩的内容： （AGENT_EXTRACT_REQUIRED）
- 为什么不是更短/更长： （AGENT_EXTRACT_REQUIRED）

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


def _rewrite_book_blueprint_template_from_novel(
    novel_path: Path,
    *,
    target_total_minutes: int = DEFAULT_TARGET_TOTAL_MINUTES,
) -> None:
    novel_text = novel_path.read_text(encoding="utf-8")
    chapters = _detect_chapters(novel_text)
    BOOK_BLUEPRINT.write_text(
        _book_blueprint_template(
            novel_path.name,
            chapters,
            target_total_minutes=target_total_minutes,
        ),
        encoding="utf-8",
    )


def _pending_source_map_template(
    strategy: str,
    intensity: str,
    total_eps: int | None,
    batch_size: int,
    *,
    target_total_minutes: int = DEFAULT_TARGET_TOTAL_MINUTES,
) -> str:
    total_eps_text = str(total_eps) if total_eps is not None else PENDING_TOTAL_EPISODES
    total_batches = (total_eps + batch_size - 1) // batch_size if total_eps is not None else None
    total_batches_text = str(total_batches) if total_batches is not None else PENDING_TOTAL_BATCHES
    return f"""# Source Map

- mapping_status: pending_book_extraction
- total_episodes: {total_eps_text}
- batch_size: {batch_size}
- total_batches: {total_batches_text}
- target_total_minutes: {target_total_minutes}
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
        shutil.rmtree(snapshot_dir)
        return None
    return snapshot_dir


# ---------------------------------------------------------------------------
# Human-facing output export
# ---------------------------------------------------------------------------

def _reset_output_dir(path: Path) -> None:
    """Clear one generated output subdirectory without touching runtime state."""
    output_root = OUTPUT.resolve()
    target = path.resolve()
    if output_root != target and output_root not in target.parents:
        raise ValueError(f"refusing to clear path outside output/: {target}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _copy_files_to_output(source_dir: Path, dest_dir: Path, patterns: list[str]) -> int:
    if not source_dir.exists():
        return 0
    count = 0
    for pattern in patterns:
        for source in sorted(source_dir.glob(pattern)):
            if source.is_file():
                shutil.copy2(source, dest_dir / source.name)
                count += 1
    return count


def _episode_sort_key(episode_id: str) -> tuple[int, str]:
    match = re.search(r"EP-(\d+)", episode_id)
    if not match:
        return (99999, episode_id)
    return (int(match.group(1)), episode_id)


def _episode_ids_in_dir(path: Path) -> list[str]:
    if not path.exists():
        return []
    episode_ids = [_normalize_episode_id(item.stem) for item in path.glob("EP-*.md") if item.is_file()]
    return sorted(set(episode_ids), key=_episode_sort_key)


def _safe_read_manifest() -> dict:
    if not RUN_MANIFEST.exists():
        return {}
    try:
        return _read_manifest()
    except Exception:
        return {}


def _safe_parse_source_map() -> dict:
    if not SOURCE_MAP.exists():
        return {}
    try:
        return _parse_source_map()
    except Exception:
        return {}


def _collect_output_batch_summaries() -> list[dict]:
    batches = _safe_parse_source_map()
    known_ids = set(batches)
    if BATCH_STATUS_DIR.exists():
        for path in BATCH_STATUS_DIR.glob("batch*.status.json"):
            known_ids.add(path.stem.replace(".status", ""))

    summaries = []
    for batch_id in sorted(known_ids):
        info = batches.get(batch_id, {})
        runtime = _read_batch_status(batch_id)
        review = _read_batch_review(batch_id)
        episodes = (
            runtime.get("episodes")
            if runtime and runtime.get("episodes")
            else info.get("episodes", [])
        )
        summaries.append(
            {
                "batch_id": batch_id,
                "episodes": episodes,
                "source_range": info.get("source_range", ""),
                "phase": runtime.get("phase", "planned") if runtime else "planned",
                "status": runtime.get("status", "ACTIVE") if runtime else "ACTIVE",
                "review_status": (review or {}).get(
                    "status",
                    runtime.get("batch_review_status", "MISSING") if runtime else "MISSING",
                ),
                "reviewer": (review or {}).get("reviewer", ""),
                "review_reason": (review or {}).get("reason", ""),
                "updated_at": runtime.get("updated_at", "") if runtime else "",
            }
        )
    return summaries


def _output_next_action(batch_summaries: list[dict]) -> str:
    if _is_locked("batch.lock"):
        lock_data = _read_lock("batch.lock")
        owner = lock_data.get("owner", "?")
        return f"batch.lock 当前由 {owner} 持有；先完成当前批次或运行 `python _ops/controller.py unlock batch.lock`。"

    for item in batch_summaries:
        batch_id = item["batch_id"]
        phase = item.get("phase", "")
        review_status = item.get("review_status", "MISSING")
        if phase in {"promoted", "recorded"}:
            continue
        if review_status == "PENDING":
            return f"评审 {batch_id}：`~review {batch_id} PASS --reviewer <name>` 或记录 FAIL 原因。"
        if review_status == "FAIL":
            return f"修正 {batch_id} 后重新评审：`~start {batch_id} --write`，再 `~review {batch_id} PASS --reviewer <name>`。"
        if phase in {"writer_ready", "review_pending"}:
            return f"生成或重建 {batch_id} 评审包：`python _ops/controller.py check {batch_id}`。"
        return f"启动下一批 {batch_id}：`~start {batch_id} --write`。"

    if batch_summaries:
        return "所有已映射批次都已发布；可直接交付 `output/`，或继续人工精修成稿。"
    return "尚未生成 source.map；先运行 `~init <书名.md> --episodes N --target-total-minutes M`，再让 agent 执行抽取和分集。"


def _all_mapped_batches_recorded(batch_summaries: list[dict] | None = None) -> bool:
    summaries = batch_summaries if batch_summaries is not None else _collect_output_batch_summaries()
    if not summaries:
        return False
    return all(
        item.get("phase") == "recorded"
        and item.get("status") == "DONE"
        and item.get("review_status") == "PASS"
        for item in summaries
    )


def _sync_manifest_completion_state() -> None:
    if not RUN_MANIFEST.exists():
        return
    if _all_mapped_batches_recorded():
        _set_manifest_field("run_status", "complete")
        _set_manifest_field("active_batch", "(none)")


def _write_output_summary(stats: dict[str, int]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = _safe_read_manifest()
    batch_summaries = _collect_output_batch_summaries()
    published = _episode_ids_in_dir(EPISODES)
    source_file = manifest.get("source_file", "(unknown)")
    total_episodes = manifest.get("total_episodes", "")
    target_total_minutes = manifest.get("target_total_minutes", "")
    target_episode_minutes = manifest.get("target_episode_minutes", "")
    active_batch = manifest.get("active_batch", "")
    run_status = manifest.get("run_status", "")
    next_action = _output_next_action(batch_summaries)

    episode_lines = "\n".join(f"- [{ep}](episodes/{ep}.md)" for ep in published) or "- 暂无已发布成稿"
    batch_lines = []
    for item in batch_summaries:
        episodes = ", ".join(item.get("episodes", [])) or "-"
        review = item.get("review_status", "MISSING")
        phase = item.get("phase", "planned")
        reviewer = item.get("reviewer", "")
        reviewer_text = f" / {reviewer}" if reviewer else ""
        batch_lines.append(f"- {item['batch_id']}：{phase} / review={review}{reviewer_text} / {episodes}")
    batch_text = "\n".join(batch_lines) or "- 暂无批次状态"

    summary = (
        "# Juben V1 Output Summary\n\n"
        "这是当前项目给外部使用者看的固定入口。公开交付内容在根目录，运行态诊断材料统一收进 `_runtime/`。\n\n"
        "## 项目概况\n\n"
        f"- 原著文件：{source_file}\n"
        f"- 目标集数：{total_episodes or '(unknown)'}\n"
        f"- 目标总时长：{target_total_minutes or '(unknown)'} 分钟\n"
        f"- 单集中心时长：{target_episode_minutes or '(unknown)'} 分钟\n"
        f"- 当前状态：{run_status or '(unknown)'}\n"
        f"- 当前批次：{active_batch or '(none)'}\n"
        f"- 已发布成稿：{len(published)} 集\n"
        f"- 内部草稿镜像：{stats.get('drafts', 0)} 集\n\n"
        "## 下一步\n\n"
        f"{next_action}\n\n"
        "## 交付入口\n\n"
        "- `episodes/`：正式成稿，每集一个 `EP-xx.md`\n"
        "- `anchors/`：角色与声纹参考，可给人工精修或审稿 agent 使用\n"
        "- `manifest.json`：机器可读索引\n"
        "- `_runtime/`：内部诊断包，包含草稿、prompt、review、brief、map、state；普通交付可忽略\n\n"
        "## 已发布剧集\n\n"
        f"{episode_lines}\n\n"
        "## 批次状态\n\n"
        f"{batch_text}\n\n"
        "## 导出统计\n\n"
        f"- episodes: {stats.get('episodes', 0)}\n"
        f"- drafts: {stats.get('drafts', 0)}\n"
        f"- reviews: {stats.get('reviews', 0)}\n"
        f"- prompts: {stats.get('prompts', 0)}\n"
        f"- briefs: {stats.get('briefs', 0)}\n"
        f"- maps: {stats.get('maps', 0)}\n"
        f"- anchors: {stats.get('anchors', 0)}\n"
        f"- state: {stats.get('state', 0)}\n"
    )
    (OUTPUT / "SUMMARY.md").write_text(summary, encoding="utf-8")


def _write_output_manifest(stats: dict[str, int]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = _safe_read_manifest()
    batch_summaries = _collect_output_batch_summaries()
    published = _episode_ids_in_dir(EPISODES)
    drafts = _episode_ids_in_dir(DRAFTS)

    payload = {
        "schema_version": "juben-output/v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_file": manifest.get("source_file", ""),
        "total_episodes": manifest.get("total_episodes", ""),
        "target_total_minutes": manifest.get("target_total_minutes", ""),
        "target_episode_minutes": manifest.get("target_episode_minutes", ""),
        "batch_size": manifest.get("batch_size", ""),
        "run_status": manifest.get("run_status", ""),
        "active_batch": manifest.get("active_batch", ""),
        "counts": stats,
        "paths": {
            "summary": "SUMMARY.md",
            "episodes": "episodes/",
            "anchors": "anchors/",
            "runtime": "_runtime/",
            "drafts": "_runtime/drafts/",
            "reviews": "_runtime/reviews/",
            "prompts": "_runtime/prompts/",
            "briefs": "_runtime/briefs/",
            "maps": "_runtime/maps/",
            "state": "_runtime/state/",
        },
        "published_episodes": [
            {"episode": ep, "path": f"episodes/{ep}.md"} for ep in published
        ],
        "draft_episodes": [
            {"episode": ep, "path": f"_runtime/drafts/{ep}.md"} for ep in drafts
        ],
        "batches": batch_summaries,
        "next_action": _output_next_action(batch_summaries),
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _write_output_readme(stats: dict[str, int]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    readme = OUTPUT / "README.md"
    readme.write_text(
        "# Juben Output\n\n"
        "这里是给外部使用者看的交付入口。每次运行 `export` 都会完整重建本目录。\n\n"
        "## 常用入口\n\n"
        "- `SUMMARY.md`：项目摘要、状态和成稿入口\n"
        "- `episodes/`：正式成稿，只放 `EP-xx.md`\n"
        "- `anchors/`：角色与声纹锚点，可用于人工精修\n"
        "- `manifest.json`：给工具或平台读取的机器可读索引\n"
        "- `_runtime/`：内部诊断包，普通交付可忽略\n\n"
        "## `_runtime/` 内容\n\n"
        "- `_runtime/drafts/`：当前草稿镜像\n"
        "- `_runtime/reviews/`：批次评审结论，包含 Markdown 与 JSON\n"
        "- `_runtime/prompts/`：可交给 agent 执行的提示词包\n"
        "- `_runtime/briefs/`：批次 brief\n"
        "- `_runtime/maps/`：全书蓝图、source map、run manifest\n"
        "- `_runtime/state/`：连续性、关系、open loop 等状态摘要\n\n"
        "## 刷新方式\n\n"
        "```powershell\n"
        "python _ops/controller.py export\n"
        "```\n\n"
        "## 当前导出统计\n\n"
        f"- episodes: {stats.get('episodes', 0)}\n"
        f"- drafts: {stats.get('drafts', 0)}\n"
        f"- reviews: {stats.get('reviews', 0)}\n"
        f"- prompts: {stats.get('prompts', 0)}\n"
        f"- briefs: {stats.get('briefs', 0)}\n"
        f"- maps: {stats.get('maps', 0)}\n"
        f"- anchors: {stats.get('anchors', 0)}\n"
        f"- state: {stats.get('state', 0)}\n",
        encoding="utf-8",
    )


def _export_outputs() -> dict[str, int]:
    """Build a human-facing output/ mirror from runtime project files."""
    _reset_output_dir(OUTPUT)
    runtime = OUTPUT / "_runtime"
    sections = {
        "episodes": OUTPUT / "episodes",
        "anchors": OUTPUT / "anchors",
        "drafts": runtime / "drafts",
        "reviews": runtime / "reviews",
        "prompts": runtime / "prompts",
        "briefs": runtime / "briefs",
        "maps": runtime / "maps",
        "state": runtime / "state",
    }
    for dest in sections.values():
        dest.mkdir(parents=True, exist_ok=True)

    stats: dict[str, int] = {}
    stats["episodes"] = _copy_files_to_output(EPISODES, sections["episodes"], ["EP-*.md"])
    stats["drafts"] = _copy_files_to_output(DRAFTS, sections["drafts"], ["EP-*.md"])
    stats["reviews"] = _copy_files_to_output(REVIEWS, sections["reviews"], ["*.review.md", "*.review.json", "*.polish.md"])
    stats["prompts"] = _copy_files_to_output(PROMPTS, sections["prompts"], ["*.md"])
    stats["prompts"] += _copy_files_to_output(REVIEWS, sections["prompts"], ["*.review.prompt.md"])
    stats["briefs"] = _copy_files_to_output(BATCH_BRIEFS, sections["briefs"], ["*.md"])

    stats["maps"] = 0
    for source in (BOOK_BLUEPRINT, SOURCE_MAP, RUN_MANIFEST):
        if source.exists():
            shutil.copy2(source, sections["maps"] / source.name)
            stats["maps"] += 1

    stats["anchors"] = 0
    for source in (ROOT / "character.md", ROOT / "voice-anchor.md"):
        if source.exists():
            shutil.copy2(source, sections["anchors"] / source.name)
            stats["anchors"] += 1

    stats["state"] = _copy_files_to_output(STATE, sections["state"], ["*.md"])
    _write_output_readme(stats)
    _write_output_summary(stats)
    _write_output_manifest(stats)
    return stats


def _clear_runtime_project_data() -> dict[str, int]:
    stats = {
        "drafts": 0,
        "episodes": 0,
        "batch_briefs": 0,
        "locks": 0,
        "state_files": 0,
        "batch_statuses": 0,
        "review_files": 0,
        "prompt_files": 0,
        "output_entries": 0,
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
    if REVIEWS.exists():
        stats["review_files"] = sum(1 for _ in REVIEWS.rglob("*"))
        shutil.rmtree(REVIEWS)
    REVIEWS.mkdir(parents=True, exist_ok=True)
    if PROMPTS.exists():
        stats["prompt_files"] = sum(1 for _ in PROMPTS.rglob("*"))
        shutil.rmtree(PROMPTS)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        stats["output_entries"] = sum(1 for _ in OUTPUT.rglob("*"))
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    STATE.mkdir(parents=True, exist_ok=True)
    for path in list(STATE.iterdir()):
        if path.is_dir():
            if path.name == "batch-status":
                stats["batch_statuses"] += sum(1 for _ in path.rglob("*"))
            shutil.rmtree(path)
        elif path.suffix == ".md":
            path.unlink()
            stats["state_files"] += 1
    _write_state_templates()

    if RUN_MANIFEST.exists():
        _set_manifest_field("active_batch", "(none)")
        _set_manifest_line("current batch brief", "(none)")

    return stats


def _ensure_runtime_directories() -> None:
    for path in (
        PROJECT,
        STATE,
        BATCH_STATUS_DIR,
        LOCKS,
        DRAFTS,
        EPISODES,
        BATCH_BRIEFS,
        REVIEWS,
        PROMPTS,
        RELEASES,
        RELEASE_JOURNALS,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _suggested_episode_count(target_total_minutes: int) -> int:
    return max(1, round(target_total_minutes / max(1, DEFAULT_TARGET_EPISODE_MINUTES)))


def _prompt_init_episode_count(target_total_minutes: int) -> int | None:
    """Prompt only for human terminals; scripts/tests keep model-recommendation mode."""
    stdin = getattr(sys, "stdin", None)
    if not stdin or not hasattr(stdin, "isatty") or not stdin.isatty():
        return None

    suggested = _suggested_episode_count(target_total_minutes)
    prompt = (
        f"请输入计划生成总集数（建议约 {suggested} 集；"
        "直接回车则让模型根据原著推荐）："
    )
    for _ in range(3):
        raw = input(prompt).strip()
        if not raw:
            return None
        match = re.search(r"\d+", raw)
        if match and int(match.group(0)) > 0:
            return int(match.group(0))
        print("ERROR: 请输入大于 0 的整数，例如 25；或直接回车让模型推荐。")
    print("ERROR: 集数输入无效，已改为让模型推荐。")
    return None


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a new project: create runtime skeleton, blueprint, and pending source map."""
    novel_file = args.novel_file
    if not novel_file and RUN_MANIFEST.exists():
        novel_file = _read_manifest().get("source_file")
    if not novel_file:
        print("ERROR: novel file is required for first init")
        print("  Usage: python _ops/controller.py init <novel_file>")
        return 1

    novel_path = ROOT / novel_file
    if not novel_path.exists():
        print(f"ERROR: novel file not found: {novel_path}")
        return 1

    total_eps = args.episodes
    batch_size = args.batch_size
    target_total_minutes = args.target_total_minutes
    strategy = args.strategy
    intensity = args.intensity
    quality_mode = "premium" if getattr(args, "premium", False) else getattr(args, "quality_mode", "standard")
    key_eps = args.key_episodes or ""
    novel_name = novel_path.name

    # Safety check: detect existing project data
    if _has_existing_project() and not args.force:
        print("ERROR: existing project data detected (promoted batches, episodes, state files)")
        print("  This command will OVERWRITE all project files.")
        print("  To proceed, re-run with --force:")
        print(f"    python _ops/controller.py init {novel_file} --force")
        return 1

    if total_eps is None:
        total_eps = _prompt_init_episode_count(target_total_minutes)

    _ensure_runtime_directories()

    total_batches = (total_eps + batch_size - 1) // batch_size if total_eps is not None else None
    episode_count_source = "manual_override" if total_eps is not None else "model_recommended"
    total_eps_text = str(total_eps) if total_eps is not None else PENDING_TOTAL_EPISODES
    recommended_total_text = PENDING_RECOMMENDED_TOTAL_EPISODES

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
        print(f"  Runtime:    ~{target_total_minutes} min total")
        print(
            f"  Timing:     {DEFAULT_EPISODE_MINUTES_MIN}-{DEFAULT_EPISODE_MINUTES_MAX} min/ep "
            f"(target {DEFAULT_TARGET_EPISODE_MINUTES})"
        )
    print(f"  Strategy:   {strategy}")
    print(f"  Intensity:  {intensity}")
    print(f"  Quality:    {quality_mode}")
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
- target_total_minutes: {target_total_minutes}
- target_episode_minutes: {DEFAULT_TARGET_EPISODE_MINUTES}
- episode_minutes_min: {DEFAULT_EPISODE_MINUTES_MIN}
- episode_minutes_max: {DEFAULT_EPISODE_MINUTES_MAX}
- key_episodes: {key_eps}
- adaptation_mode: novel_to_short_drama
- adaptation_strategy: {strategy}
- dialogue_adaptation_intensity: {intensity}
- quality_mode: {quality_mode}
- generation_execution_mode: prompt_packet_external_agent
- writer_parallelism: {DEFAULT_WRITER_PARALLELISM}
- generation_reset_mode: clean_rebuild
- run_status: active
- active_batch: (none)
- source_authority: original novel manuscript + harness/project/book.blueprint.md + harness/project/source.map.md
- draft_lane: drafts/episodes
- publish_lane: episodes
- promotion_policy: controller_only_after_batch_verify_gate

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

    BOOK_BLUEPRINT.write_text(
        _book_blueprint_template(
            novel_name,
            chapters,
            target_total_minutes=target_total_minutes,
        ),
        encoding="utf-8",
    )
    print(f"  + book.blueprint.md (pending whole-book extraction)")

    SOURCE_MAP.write_text(
        _pending_source_map_template(
            strategy,
            intensity,
            total_eps,
            batch_size,
            target_total_minutes=target_total_minutes,
        ),
        encoding="utf-8",
    )
    print(f"  + source.map.md (pending map-book)")

    # Generate state file templates
    _write_state_templates()
    print(f"  + state/ (7 template files)")

    # Always generate fresh character.md and voice-anchor.md
    char_path = ROOT / "character.md"
    voice_path = ROOT / "voice-anchor.md"
    char_path.write_text(
        f"# Character Reference\n\n"
        "用于记录人物关系、立场、经历与镜头抓手，不负责规定固定台词。\n\n"
        "## 填写原则\n"
        "- 优先写人物处境、关系压力、欲望、软肋、外在抓手\n"
        "- 不要把人物小传写成剧情复述，也不要直接替角色发明口号式台词\n\n"
        f"（AGENT_EXTRACT_REQUIRED — 从 {novel_name} 自动提取）\n",
        encoding="utf-8",
    )
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
  - 优先写“温度、节奏、回避/施压方式、面对不同对象时的变化”，不要写成口号库
  - 除非原著反复出现固定说法，否则不要填写“常用表达”清单

  ## 格式警告（所有角色通用）
  本文件描述的是**角色说话内容的特征**（简洁、压迫、快节奏等），不是剧本排版指令。
  - "短句"＝角色说话简洁利落，不等于每句话都要单独占一行
  - "连打"/"连下两三句"＝角色一口气连续逼问或施压，通常写在同一行或相邻两行，不是拆成五六行
  - 只有语义上有**刻意停顿、转折、施压节拍**时才换行
  - 具体格式规则见 `write-contract.md` 的 Dialogue Formatting 章节

  ## 核心角色

建议按以下骨架填写，而不是自由堆砌形容词：

### 角色名
- 说话温度：
- 句法与节奏：
- 对不同对象的变化：
- 外显台词边界：
- `os` 边界：
- 禁止滑坡：

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
    if quality_mode == "premium":
        print(f"  4. polish batchXX → optional精品稿二修 before review")
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

    force = getattr(args, "force", False)
    if _book_blueprint_is_complete() and not force:
        recommended = _sync_recommended_episode_count_from_blueprint()
        print("=== extract-book ===")
        print(f"  Source:    {novel_path.name}")
        print(f"  Blueprint: {BOOK_BLUEPRINT.relative_to(ROOT)}")
        print("  ↷ Skip: existing book.blueprint.md is already complete")
        if recommended is not None:
            print(f"  Reused recommended total_episodes: {recommended}")
        _append_log("-", "-", "plan_inputs", "extract-book", "↷", f"{novel_path.name} (cache-hit)")
        return 0

    print("=== extract-book ===")
    print(f"  Source:    {novel_path.name}")
    print(f"  Blueprint: {BOOK_BLUEPRINT.relative_to(ROOT)}")
    target_total_minutes = _parse_manifest_int("target_total_minutes") or DEFAULT_TARGET_TOTAL_MINUTES
    _rewrite_book_blueprint_template_from_novel(
        novel_path,
        target_total_minutes=target_total_minutes,
    )
    print("  -> Reset blueprint scaffold to the structured extraction template")
    try:
        import run_book_extract
    except ImportError as exc:
        print(f"ERROR: failed to load prompt builder: {exc}")
        return 1

    prompt = run_book_extract._build_extract_prompt(novel_path)
    prompt_path = _write_prompt_packet("extract-book.prompt.md", prompt)
    _print_prompt_ready(
        prompt_path,
        [BOOK_BLUEPRINT, ROOT / "character.md", ROOT / "voice-anchor.md"],
        next_command="python _ops/controller.py map-book --force",
    )
    print("  Note: fill book.blueprint.md first; map-book will reject pending placeholders.")
    _append_log("-", "-", "plan_inputs", "extract-book", "prompt", novel_path.name)
    return 0


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
    blueprint_issues = _book_blueprint_quality_issues()
    if blueprint_issues:
        print("ERROR: book.blueprint.md is present but not actionable enough for mapping")
        for issue in blueprint_issues:
            print(f"  - {issue}")
        print("  Re-run extract-book until the blueprint passes the quality gate")
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
    force = getattr(args, "force", False)

    if _source_map_is_complete() and not force:
        print("=== map-book ===")
        print(f"  Source:    {novel_path.name}")
        print(f"  Blueprint: {BOOK_BLUEPRINT.relative_to(ROOT)}")
        print(f"  Output:    {SOURCE_MAP.relative_to(ROOT)}")
        print("  ↷ Skip: existing source.map.md is already complete")
        _append_log("-", "-", "plan_inputs", "map-book", "↷", f"{novel_path.name} (cache-hit)")
        return 0

    print("=== map-book ===")
    print(f"  Source:    {novel_path.name}")
    print(f"  Blueprint: {BOOK_BLUEPRINT.relative_to(ROOT)}")
    print(f"  Output:    {SOURCE_MAP.relative_to(ROOT)}")
    try:
        import run_book_map
    except ImportError as exc:
        print(f"ERROR: failed to load prompt builder: {exc}")
        return 1

    prompt = run_book_map._build_map_prompt(
        novel_path,
        episodes=total_eps,
        batch_size=batch_size,
        strategy=strategy,
        intensity=intensity,
    )
    prompt_path = _write_prompt_packet("map-book.prompt.md", prompt)
    _print_prompt_ready(
        prompt_path,
        [SOURCE_MAP],
        next_command="python _ops/controller.py start batch01",
    )
    print("  Note: fill source.map.md first; start will reject pending placeholders.")
    _append_log("-", "-", "plan_inputs", "map-book", "prompt", novel_path.name)
    return 0


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
    print(f"  - batch status reset:    {stats['batch_statuses']}")
    print(f"  - review files reset:    {stats['review_files']}")
    print(f"  - prompt files reset:    {stats['prompt_files']}")
    print(f"  - output entries reset:  {stats['output_entries']}")
    print(f"  - release entries reset: {stats['release_entries']}")
    print("  ✓ Runtime project data cleared")
    print("  Preserved: book.blueprint.md, source.map.md, run.manifest.md, framework contracts, source novel files")
    return 0


def _prepare_batch_start(batch_id: str) -> tuple[Path, dict, list[str]] | None:
    blueprint_issues = _book_blueprint_quality_issues()
    if blueprint_issues:
        print("ERROR: book.blueprint.md did not pass the extraction quality gate")
        for issue in blueprint_issues:
            print(f"  - {issue}")
        print("  Re-run extract-book before start/check/run")
        return None

    if not SOURCE_MAP.exists():
        print("ERROR: source.map.md is missing")
        print("  Run extract-book and map-book first")
        return None

    source_map_text = SOURCE_MAP.read_text(encoding="utf-8")
    if "mapping_status: pending_book_extraction" in source_map_text:
        print("ERROR: source.map.md is still pending")
        print("  Run extract-book, then map-book, before start/check/run")
        return None
    source_map_issues = _source_map_quality_issues()
    if source_map_issues:
        print("ERROR: source.map.md did not pass the mapping quality gate")
        for issue in source_map_issues[:10]:
            print(f"  - {issue}")
        if len(source_map_issues) > 10:
            print(f"  - ... and {len(source_map_issues) - 10} more")
        print("  Re-run map-book before start/check/run")
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
            print(f"ERROR: batch.lock held by '{owner}' — run or unlock first")
            return None

    # Find or auto-generate batch brief
    brief_path = _find_batch_brief(batch_id)
    needs_brief_refresh = False
    if brief_path is None:
        ep_start_num = batch_info["ep_start"].replace("EP-", "")
        ep_end_num = batch_info["ep_end"].replace("EP-", "")
        batch_num = batch_info["batch_num"]
        fname = f"batch{batch_num}_EP{ep_start_num}-{ep_end_num}.md"
        brief_path = BATCH_BRIEFS / fname
        BATCH_BRIEFS.mkdir(parents=True, exist_ok=True)
        needs_brief_refresh = True
    else:
        brief = _read_batch_brief(brief_path)
        if brief.get("status") == "promoted":
            print(f"ERROR: batch '{batch_id}' is already promoted")
            return None
        brief_text = brief_path.read_text(encoding="utf-8")
        needs_brief_refresh = (
            "## Writer Authority" not in brief_text
            or "knowledge_boundary" not in brief_text
        )

    if needs_brief_refresh:
        brief_content = _generate_batch_brief(batch_id, batch_info)
        brief_path.write_text(brief_content, encoding="utf-8")
        brief = _read_batch_brief(brief_path)
        print(f"  + Refreshed batch brief: {brief_path.name}")
    else:
        brief = _read_batch_brief(brief_path)
        print(f"  = Found existing brief: {brief_path.name}")

    # Freeze + lock
    _set_batch_status(brief_path, "frozen")
    _write_lock("batch.lock", "locked", f"controller:{batch_id}")
    _upsert_batch_status(
        batch_id,
        phase="planned",
        status="ACTIVE",
        episodes=brief.get("episodes", []),
        brief_path=brief_path,
        batch_review_status="MISSING",
    )
    _upsert_batch_status(
        batch_id,
        phase="writing",
        status="ACTIVE",
        episodes=episodes,
        brief_path=brief_path,
        batch_review_status="MISSING",
    )
    print(f"  + Brief frozen, batch.lock acquired")

    # Clear retry counts from prior runs
    for ep in episodes:
        _clear_retry_count(ep)

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
        ending = data.get("ending_function", "")
        mk = data.get("must_keep", "")
        mn = data.get("must_not", "")
        print(f"  {ep} ({data.get('source_span', '')}) [{ending}]")
        print(f"    must-keep: {mk[:80]}{'...' if len(mk) > 80 else ''}")
        print(f"    must-not:  {mn[:80]}{'...' if len(mn) > 80 else ''}")

    # Review focus
    focus = _compute_review_focus(episodes)
    print(f"\n--- Review Focus ---")
    print(f"  DEEP:     {', '.join(focus['deep']) or '(none)'}")
    print(f"  STANDARD: {', '.join(focus['standard']) or '(none)'}")
    print(f"  LIGHT:    {', '.join(focus['light']) or '(none)'}")
    if focus["unmapped"]:
        print(f"  ⚠ UNMAPPED: {', '.join(focus['unmapped'])}")
        print("    → Update source.map.md before trusting the review packet")

    return brief_path, batch_info, episodes


def cmd_start(args: argparse.Namespace) -> int:
    """Prepare batch; writer stage only runs when explicitly requested."""
    batch_id = args.batch_id
    prepared = _prepare_batch_start(batch_id)
    if prepared is None:
        return 1
    brief_path, _batch_info, episodes = prepared

    synced = _sync_state_from_blueprint()
    if synced:
        print(f"  + Synced state from blueprint: {', '.join(synced)}")

    focus = _compute_review_focus(episodes)

    if args.prepare_only or not getattr(args, "write", False):
        print("\n--- Next Step ---")
        if args.prepare_only:
            print("  prepare-only: batch is frozen and locked, but writer stage was not started")
        else:
            print("  default prepare mode: batch is frozen and locked; add --write to start per-episode writing")
        _print_start_next_steps(batch_id, episodes, focus, include_writer_instruction=True)
        return 0

    if not _guard_quality_anchors():
        return 1

    print("\n=== Writer Stage ===")
    writer_rc = _run_writer_stage(
        batch_id,
        episodes,
        parallelism=1,
    )
    if writer_rc == WRITER_STAGE_PROMPTS_READY:
        print("\n=== Writer Prompt Packet Ready ===")
        print("  Drafts are still pending; have an agent execute the prompt packet above.")
        print(f"  Re-run after drafts exist: python _ops/controller.py start {batch_id} --write")
        return 0
    if writer_rc != 0:
        return writer_rc

    quality_mode = _read_manifest().get("quality_mode", "standard")
    _upsert_batch_status(
        batch_id,
        phase="review_pending",
        status="BLOCKED",
        episodes=episodes,
        brief_path=brief_path,
        batch_review_status="PENDING",
    )
    review = _ensure_batch_review_artifacts(batch_id, episodes, brief_path=brief_path)

    print("\n=== Writer Stage Complete ===")
    print(f"  Drafts ready: {', '.join(episodes)}")
    print("\n=== Review Packet Ready ===")
    print(f"  Review JSON: {_relative_to_root(_batch_review_json_path(batch_id))}")
    print(f"  Review MD:   {_relative_to_root(_batch_review_md_path(batch_id))}")
    print(f"  Review Prompt: {_relative_to_root(_batch_review_prompt_path(batch_id))}")
    print(f"  Verdict: {review.get('status', 'PENDING')}")
    if quality_mode == "premium":
        print("\n=== Optional Polish ===")
        print(f"  Premium mode is enabled. Recommended before review: python _ops/controller.py polish {batch_id}")
    print("\n--- Next Steps ---")
    _print_start_next_steps(batch_id, episodes, focus, include_writer_instruction=False)
    return 0

def cmd_check(args: argparse.Namespace) -> int:
    """Rebuild batch review artifact manually (fallback/debug only)."""
    batch_id = args.batch_id
    resolved = _resolve_batch(args.batch_id)
    if resolved is None:
        return 1
    brief_path, _brief, episodes = resolved

    print(f"=== Rebuild Review Packet: {batch_id} ===")
    print("  note: `check` is now a fallback/debug command.")
    print("  main flow should use `start <batch> --write`, which already generates the review packet.")

    _upsert_batch_status(
        batch_id,
        phase="review_pending",
        status="BLOCKED",
        episodes=episodes,
        brief_path=brief_path,
        batch_review_status="PENDING",
    )
    return cmd_batch_review(args)

def _do_promote_and_report(batch_id: str, brief_path: Path, episodes: list[str]) -> int:
    """Shared post-review logic: promote → validate → next steps."""
    if _is_locked("state.lock"):
        print("ERROR: state.lock is held — cannot promote")
        return 1

    print("\n=== Promote ===")
    rc, _ = _promote_batch(batch_id, brief_path, episodes)
    if rc != 0:
        print("ERROR: staging promote failed")
        return 1
    for ep in episodes:
        print(f"  → {ep}: draft → published (gold)")

    _set_batch_status(brief_path, "promoted")
    _upsert_batch_status(batch_id, phase="promoted", status="ACTIVE", batch_review_status="PASS")
    _write_lock("batch.lock", "unlocked")

    for ep in episodes:
        _clear_retry_count(ep)

    ep_range = f"{episodes[0]}~{episodes[-1]}" if len(episodes) > 1 else episodes[0]
    _append_log(batch_id, ep_range, "promote", "controller promote", "✓", f"{batch_id} promoted")
    _set_manifest_field("active_batch", f"{batch_id}_promoted")
    stats = _export_outputs()
    print(f"  ✓ {len(episodes)} promoted to gold, batch.lock released")
    print(f"  ✓ Output refreshed: output/ ({stats.get('episodes', 0)} episodes)")

    print("\n=== State Validation ===")
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
        print("  WARNING: state files have gaps — recorder should fix before next batch")

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
    print("\n--- Next Steps ---")
    print(f"  1. Update state:   python _ops/controller.py record {batch_id}")
    print("     (controller auto-writes state files and validates them)")
    if next_batch:
        next_info = batches[next_batch]
        print(f"  2. Start next:     python _ops/controller.py start {next_batch}")
        print(f"     ({next_info['ep_start']} ~ {next_info['ep_end']}, {next_info['source_range']})")
    else:
        print("  2. All batches complete!")

    return 0

def cmd_finish(args: argparse.Namespace) -> int:
    """Deprecated alias for cmd_run()."""
    print("WARNING: 'finish' is deprecated; use 'run' as the only formal release entry.")
    print(f"  Re-run with: python _ops/controller.py run {args.batch_id}")
    return cmd_run(args)


def cmd_run(args: argparse.Namespace) -> int:
    """Formal release entry: batch review gate → promote → next."""
    batch_id = args.batch_id
    resolved = _resolve_batch(batch_id, require_frozen=True)
    if resolved is None:
        return 1
    brief_path, _brief, episodes = resolved

    print("=== Step 1: Batch Review Gate ===")
    ok, message = _require_batch_review_pass(batch_id)
    if not ok:
        print(message)
        print("\n  GATE FAIL — complete batch review before formal release")
        return 1
    print("\n  GATE PASS")

    return _do_promote_and_report(batch_id, brief_path, episodes)

def cmd_next(args: argparse.Namespace) -> int:
    """Determine and display next batch to work on."""
    manifest = _read_manifest()
    active = manifest.get("active_batch", "")

    batches = _parse_source_map()
    batch_ids = sorted(batches.keys())

    promoted = []
    pending = []
    runtime_by_batch: dict[str, dict | None] = {}
    review_by_batch: dict[str, dict | None] = {}
    for bid in batch_ids:
        runtime = _read_batch_status(bid)
        review = _read_batch_review(bid)
        runtime_by_batch[bid] = runtime
        review_by_batch[bid] = review
        if runtime:
            if runtime.get("phase") in {"promoted", "recorded"}:
                promoted.append(bid)
                continue
            pending.append(bid)
            continue
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

    promote_recovery = _first_incomplete_promote_batch(batch_ids)
    if promote_recovery:
        batch_id, journal = promote_recovery
        published = ", ".join(journal.get("published_episodes", [])) or "(none)"
        print(f"\n=== Promote Recovery Required: {batch_id} ===")
        print(f"  Journal phase: {journal.get('phase', '?')}")
        print(f"  Published in prior attempt: {published}")
        print(f"  To resume: python _ops/controller.py promote {batch_id}")
        return 0

    for bid in batch_ids:
        action = _next_batch_review_action(bid, runtime_by_batch.get(bid), review_by_batch.get(bid))
        if action:
            reason, command = action
            print(f"\n=== Current Blocker: {bid} ===")
            print(f"  {reason}")
            print(f"  Next action: {command}")
            return 0

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

    p_promote = sub.add_parser("promote", help="Promote batch: copy drafts ? episodes")
    p_promote.add_argument("batch_id")

    sub.add_parser("validate", help="Check state files against templates")
    sub.add_parser("export", help="Refresh human-facing output/ mirrors")

    p_log = sub.add_parser("log", help="Append to run.log.md")
    p_log.add_argument("phase", help="plan_inputs|draft_write|review|promote|record|recovery")
    p_log.add_argument("event", help="Event description")
    p_log.add_argument("--batch", default=None)
    p_log.add_argument("--episode", default=None)
    p_log.add_argument("--result", default=None)
    p_log.add_argument("--note", default=None)

    p_breview = sub.add_parser("batch-review", help="Create durable batch review artifacts")
    p_breview.add_argument("batch_id")

    p_polish = sub.add_parser("polish", help="Create optional premium polish prompt packet for a batch")
    p_polish.add_argument("batch_id")

    p_breview_done = sub.add_parser("batch-review-done", help="Seal batch review verdict")
    p_breview_done.add_argument("batch_id")
    p_breview_done.add_argument("status", help="PASS or FAIL")
    p_breview_done.add_argument("--reviewer", required=True, help="Reviewer name")
    p_breview_done.add_argument("--reason", default="", help="Reason for FAIL or optional PASS note")
    p_breview_done.add_argument("--blocking-reason", dest="blocking_reasons", action="append", default=[], help="Blocking finding summary (repeatable)")
    p_breview_done.add_argument("--warning-family", dest="warning_families", action="append", default=[], help="Repeated warning family (repeatable)")
    p_breview_done.add_argument("--arc-regression", dest="arc_regressions", action="append", default=[], help="Cross-episode arc regression (repeatable)")
    p_breview_done.add_argument("--function-theft", dest="function_theft_findings", action="append", default=[], help="Future-function theft finding (repeatable)")
    p_breview_done.add_argument("--quality-anchor-finding", dest="quality_anchor_findings", action="append", default=[], help="Quality anchor regression finding (repeatable)")
    p_breview_done.add_argument("--evidence-ref", dest="evidence_refs", action="append", default=[], help="Evidence reference (repeatable)")

    p_unlock = sub.add_parser("unlock", help="Release a lock")
    p_unlock.add_argument("lock_name", help="batch|episode|state|all")

    p_init = sub.add_parser("init", help="Scaffold a new project from a novel file")
    p_init.add_argument("novel_file", nargs="?", help="Path to novel manuscript (relative to project root; defaults to run.manifest.md source_file)")
    p_init.add_argument("--episodes", type=int, default=None, help="Optional manual episode count override (default: model recommendation after extract-book)")
    p_init.add_argument("--batch-size", type=int, default=5, help="Episodes per batch (default: 5)")
    p_init.add_argument("--target-total-minutes", type=int, default=DEFAULT_TARGET_TOTAL_MINUTES, help="Approximate full-series runtime target in minutes (default: 50)")
    p_init.add_argument("--strategy", default="original_fidelity", help="Adaptation strategy")
    p_init.add_argument("--intensity", default="light", help="Dialogue adaptation intensity")
    p_init.add_argument("--quality-mode", choices=["standard", "premium"], default="standard", help="Draft quality mode (default: standard; premium suggests polish before review)")
    p_init.add_argument("--premium", action="store_true", help="Shortcut for --quality-mode premium")
    p_init.add_argument("--key-episodes", default="", help="Comma-separated key episode IDs for deep review focus")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing project data (auto-backup first)")

    p_extract = sub.add_parser("extract-book", help="Fill book.blueprint.md from the full novel")
    p_extract.add_argument("--force", action="store_true", help="Re-run extraction even if blueprint already looks complete")
    p_map = sub.add_parser("map-book", help="Generate source.map.md from book.blueprint.md")
    p_map.add_argument("--force", action="store_true", help="Re-run mapping even if source.map.md already looks complete")

    p_record = sub.add_parser("record", help="Auto-write state files for a promoted batch")
    p_record.add_argument("batch_id")

    p_rdone = sub.add_parser("record-done", help="Compatibility check: validate recorded state")
    p_rdone.add_argument("batch_id")

    p_start = sub.add_parser("start", help="Prepare batch by default; add --write to run writer stage")
    p_start.add_argument("batch_id", help="e.g. batch02")
    p_start.add_argument("--prepare-only", action="store_true", help="Freeze/lock and print context only")
    p_start.add_argument("--write", action="store_true", help="Create writer prompt packet; review packet is created after drafts exist")

    p_check = sub.add_parser("check", help="Rebuild review packet only (fallback/debug)")
    p_check.add_argument("batch_id")

    p_finish = sub.add_parser("finish", help="Deprecated alias for run")
    p_finish.add_argument("batch_id")

    p_run = sub.add_parser("run", help="Review gate ? promote ? next")
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
        "promote": cmd_promote,
        "validate": cmd_validate,
        "export": cmd_export,
        "log": cmd_log,
        "polish": cmd_polish,
        "batch-review": cmd_batch_review,
        "batch-review-done": cmd_batch_review_done,
        "unlock": cmd_unlock,
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
