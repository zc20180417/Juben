from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PASSING_SAMPLE = ROOT / "harness" / "framework" / "passing-episode.sample.md"
WRITE_CONTRACT_PATH = ROOT / "harness" / "framework" / "write-contract.md"
WRITER_STYLE_PATH = ROOT / "harness" / "framework" / "writer-style.md"
WRITE_CONTRACT_PROMPT_SECTIONS = (
    "MARKER_FORMAT",
    "OS_RULES",
    "SCENE_RULES",
    "CHARACTER_KNOWLEDGE",
    "PRE_SUBMIT_CHECK",
)
WRITER_STYLE_PROMPT_SECTIONS = (
    "NARRATIVE_POSTURE",
    "SCENE_CRAFT",
    "DIALOGUE_CRAFT",
    "STYLE_RED_LINES",
)
DEFAULT_WRITER_PARALLELISM = 1
LLM_CLI_ENV = "JUBEN_LLM_CLI"
LINT_FEEDBACK_ENV = "JUBEN_WRITER_LINT_FEEDBACK"
PROMPT_DUMP_DIR_ENV = "JUBEN_LLM_PROMPT_DUMP_DIR"
SUPPORTED_LLM_CLIS = ("codex", "qwen", "claude")
CHAPTER_HEADING_RE = re.compile(r"^第\s*([0-9一二三四五六七八九十百千零两]+)\s*章[^\n\r]*$", re.MULTILINE)
SOURCE_QUOTE_RE = re.compile(r"[“\"]([^”\"\n]{2,80})[”\"]")
DECORATIVE_PARAGRAPH_RE = re.compile(r"^[-=*_~·•]{6,}$")
HEADING_LEVEL3_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
JSON_FENCE_RE = re.compile(r"```json\s*(.*?)```", re.DOTALL | re.IGNORECASE)
TRANSIENT_LLM_FAILURE_MARKERS = (
    "stream disconnected",
    "retrying sampling request",
    "reconnecting",
)
TRANSIENT_LLM_RETRY_ATTEMPTS = 3
LLM_TIMEOUT_RETURNCODE = 124
SEQUENTIAL_BATCH_WRITE_TIMEOUT_SECONDS = int(os.environ.get("JUBEN_BATCH_WRITE_TIMEOUT_SECONDS", "240"))
SEQUENTIAL_BATCH_REWRITE_TIMEOUT_SECONDS = int(os.environ.get("JUBEN_BATCH_REWRITE_TIMEOUT_SECONDS", "180"))
SINGLE_EPISODE_REWRITE_TIMEOUT_SECONDS = int(os.environ.get("JUBEN_SINGLE_EPISODE_REWRITE_TIMEOUT_SECONDS", "60"))
WHOLE_DRAFT_PATCH_SKIP_MIN_LINES = 20
PATCH_FIDELITY_MAX_BLOCKS = int(os.environ.get("JUBEN_PATCH_MAX_BLOCKS", "2"))
PATCH_FIDELITY_MAX_TOTAL_SPAN_LINES = int(os.environ.get("JUBEN_PATCH_MAX_TOTAL_SPAN_LINES", "10"))
PATCH_FIDELITY_MAX_PROMPT_BYTES = int(os.environ.get("JUBEN_PATCH_MAX_PROMPT_BYTES", "6000"))
REVEAL_SCENE_KEYWORDS = (
    "结果出来",
    "主持人",
    "欢迎",
    "全场",
    "哗然",
    "掌声",
    "惊呼",
    "你就是鸢",
    "我就是时鸢",
    "很意外吗",
)
RESULT_CONFIRMATION_SCENE_KEYWORDS = (
    "亲子鉴定报告",
    "亲子鉴定结果",
    "鉴定结果",
    "结果出来了",
    "结果出来",
    "确认了",
    "确实是我们苏家",
    "确实是我们",
    "失散多年的女儿",
)
PRESSURE_SCENE_KEYWORDS = (
    "站住",
    "什么态度",
    "不感恩",
    "不懂事",
    "嫌弃",
    "你看看",
    "比你",
    "礼仪",
    "规矩",
    "丢人",
    "亲生父母",
    "你这孩子怎么说话呢",
)
EARLY_SIBLING_RELATION_LABEL_RE = re.compile(
    r"(姐姐|妹妹|哥哥|弟弟|亲姐|亲妹|亲哥|亲弟|亲姐姐|亲妹妹|亲哥哥|亲弟弟)"
)
RELATION_CONFIRMATION_RE = re.compile(
    r"(亲子鉴定|鉴定结果|结果出来|确认.*(女儿|儿子|姐妹|兄妹|兄弟)|血缘|亲生|真千金|真少爷|认亲|就是当年走失的那个孩子)"
)
ABSTRACT_NARRATION_KEYWORDS = (
    "最风光",
    "像刀子一样",
    "彻底打醒了所有人",
    "恢复平静",
    "只剩",
    "敬畏",
    "崇拜",
    "光芒万丈",
    "失而复得",
    "盛满",
    "满是",
    "激动",
    "心疼",
    "尘埃落定",
    "再无立足之地",
    "终被抚平",
)
GENERIC_ROLE_TOKENS = (
    "养女",
    "Guest A",
    "Guest B",
    "Guest",
    "宾客甲",
    "宾客乙",
    "宾客",
    "男人",
    "女人",
    "女孩",
    "男声",
    "女声",
    "Assistant",
    "助理",
    "负责人",
    "工作人员",
    "保安",
    "主持人",
    "会所老板",
    "老板",
    "经理",
    "前台",
    "路人",
)
FILL_BLOCK_KEYWORDS = (
    "助理",
    "流程卡",
    "工作室流程",
    "后台",
    "候场",
    "耳麦",
    "对讲",
    "主秀图",
    "版房",
    "送审",
    "抬杯",
    "寒暄",
    "介绍",
    "先进去，把话说清",
    "到了地方再说",
    "今晚没有这个环节",
)
_PROMPT_DUMP_COUNTER = 0
ABSTRACT_LINE_PATTERNS = (
    re.compile(r"眼[里底].{0,8}(是|满是|盛满)"),
    re.compile(r"恢复平静"),
    re.compile(r"只剩"),
    re.compile(r"像刀子一样"),
)
REVEAL_FILL_TOKENS = (
    "寒暄",
    "抬杯",
    "举杯",
    "碰杯",
    "附和",
    "后台",
    "候场",
    "耳麦",
    "对讲",
    "流程卡",
    "介绍",
)
PATCH_FAMILY_ALLOWED_ACTIONS: dict[str, tuple[str, ...]] = {
    "restore_names": ("replace",),
    "restore_long_lines": ("replace",),
    "delete_fill_blocks": ("delete",),
    "externalize_lines": ("replace",),
}
PATCH_FAMILY_PRIORITY: dict[str, int] = {
    "restore_names": 3,
    "restore_long_lines": 3,
    "delete_fill_blocks": 2,
    "externalize_lines": 1,
}


def _configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except ValueError:
                pass


def _llm_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("NO_COLOR", "1")
    env.setdefault("FORCE_COLOR", "0")
    env.setdefault("CLICOLOR", "0")
    env.setdefault("CLICOLOR_FORCE", "0")
    return env


_configure_stdio()


def _batch_briefs_dir() -> Path:
    return ROOT / "harness" / "project" / "batch-briefs"


def _drafts_dir() -> Path:
    return ROOT / "drafts" / "episodes"


def _quality_anchor_path() -> Path:
    return ROOT / "harness" / "project" / "state" / "quality.anchor.md"


def _batch_context_dir() -> Path:
    return ROOT / "harness" / "project" / "state" / "batch-context"


def _source_excerpt_dir(batch_id: str) -> Path:
    return ROOT / "harness" / "project" / "state" / "source-excerpts" / batch_id


def _source_excerpt_markdown_path(batch_id: str, episode: str) -> Path:
    return _source_excerpt_dir(batch_id) / f"{episode}.source.md"


def _source_excerpt_json_path(batch_id: str, episode: str) -> Path:
    return _source_excerpt_dir(batch_id) / f"{episode}.source.json"


def _batch_context_markdown_path(batch_id: str) -> Path:
    return _batch_context_dir() / f"{batch_id}.writer-context.md"


def _batch_context_json_path(batch_id: str) -> Path:
    return _batch_context_dir() / f"{batch_id}.writer-context.json"


def _source_excerpt_runtime_path(path: Path) -> Path:
    if path.suffix == ".json":
        return path
    if path.name.endswith(".source.md"):
        return path.with_suffix(".json")
    return path


def _batch_context_runtime_path(path: Path) -> Path:
    if path.suffix == ".json":
        return path
    if path.name.endswith(".writer-context.md"):
        return path.with_suffix(".json")
    return path


def _parse_episodes(raw: str) -> list[str]:
    return [episode.strip() for episode in raw.split(",") if episode.strip()]


def _episode_sort_key(episode: str) -> int:
    return int(episode.split("-")[1])


def _find_batch_brief(batch_id: str) -> Path | None:
    match = re.match(r"batch0*(\d+)", batch_id)
    if not match:
        return None
    num = match.group(1)
    pattern = re.compile(rf"batch0*{re.escape(num)}")
    for path in _batch_briefs_dir().glob("*.md"):
        if pattern.search(path.stem):
            return path
    return None


def _missing_drafts(episodes: list[str]) -> list[str]:
    drafts = _drafts_dir()
    return [episode for episode in episodes if not (drafts / f"{episode}.md").exists()]


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _format_section_refs(section_ids: tuple[str, ...]) -> str:
    return " ".join(f"[SECTION:{section_id}]" for section_id in section_ids)


def _build_contract_style_reference_block() -> str:
    contract_rel = _rel(WRITE_CONTRACT_PATH)
    style_rel = _rel(WRITER_STYLE_PATH)
    contract_sections = _format_section_refs(WRITE_CONTRACT_PROMPT_SECTIONS)
    style_sections = _format_section_refs(WRITER_STYLE_PROMPT_SECTIONS)
    return (
        "契约引用：\n"
        f"- 遵循 `{contract_rel}` {contract_sections}\n"
        f"- 遵循 `{style_rel}` {style_sections}"
    )


def _build_required_reads_block(*paths: str, extra_paths: list[str] | None = None) -> str:
    lines = ["必读输入："]
    lines.extend(f"- {path}" for path in paths)
    lines.extend(f"- {path}" for path in (extra_paths or []))
    return "\n".join(lines)


def _safe_read_text(path: Path) -> str:
    if not path.exists():
        return "（文件不存在，跳过）"
    return path.read_text(encoding="utf-8")


def _adjacent_context_paths(episode: str) -> list[tuple[str, Path]]:
    episode_num = _episode_sort_key(episode)
    context: list[tuple[str, Path]] = []

    if episode_num <= 1:
        return context

    previous_episode = f"EP-{episode_num - 1:02d}.md"
    previous_draft = _drafts_dir() / previous_episode
    previous_published = ROOT / "episodes" / previous_episode

    if previous_draft.exists():
        context.append(("上一集草稿，优先用于切集边界防重演", previous_draft))
    elif previous_published.exists():
        context.append(("上一集已发布稿，用于切集边界防重演", previous_published))

    return context


def _source_map_path() -> Path:
    return ROOT / "harness" / "project" / "source.map.md"


def _run_manifest_path() -> Path:
    return ROOT / "harness" / "project" / "run.manifest.md"


def _manifest_source_file() -> Path | None:
    manifest = _run_manifest_path()
    if not manifest.exists():
        return None
    text = manifest.read_text(encoding="utf-8")
    match = re.search(r"^- source_file:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return None
    raw = match.group(1).strip()
    if not raw or raw == "(none)":
        return None
    return ROOT / raw


def _batch_number(batch_id: str) -> str | None:
    match = re.match(r"batch0*(\d+)", batch_id)
    if not match:
        return None
    return match.group(1)


def _batch_source_map_slice(batch_id: str) -> str:
    source_map = _source_map_path()
    if not source_map.exists():
        return "（source.map 不存在）"

    batch_num = _batch_number(batch_id)
    if batch_num is None:
        return source_map.read_text(encoding="utf-8")

    lines = source_map.read_text(encoding="utf-8").splitlines()
    start = None
    end = len(lines)
    heading_pattern = re.compile(rf"^##\s+Batch\s+0*{re.escape(batch_num)}\b", re.IGNORECASE)

    for idx, line in enumerate(lines):
        if heading_pattern.match(line):
            start = idx
            continue
        if start is not None and line.startswith("## Batch "):
            end = idx
            break

    if start is None:
        return source_map.read_text(encoding="utf-8")
    return "\n".join(lines[start:end]).strip() + "\n"


def _episode_source_span(episode: str) -> str | None:
    source_map = _source_map_path()
    if not source_map.exists():
        return None

    episode_num = int(episode.split("-")[1])
    text = source_map.read_text(encoding="utf-8")
    block_pattern = re.compile(
        rf"^###\s+EP0*{episode_num}\b.*?(?=^###\s+EP0*\d+\b|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = block_pattern.search(text)
    if not match:
        return None

    block = match.group(0)
    span_match = re.search(r"^\*\*source_chapter_span\*\*:\s*(.+?)\s*$", block, re.MULTILINE)
    if not span_match:
        return None
    return span_match.group(1).strip()


def _chapter_sections(text: str) -> list[tuple[str, str]]:
    matches = list(CHAPTER_HEADING_RE.finditer(text))
    if not matches:
        stripped = text.strip()
        return [("全文", stripped)] if stripped else []

    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        heading = match.group(0).strip()
        body = text[start:end].strip()
        sections.append((heading, body))
    return sections


def _chapter_number_from_label(label: str) -> int | None:
    match = re.search(r"第\s*([0-9]+)\s*章", label)
    if match:
        return int(match.group(1))
    return None


def _split_text_half(text: str) -> tuple[str, str]:
    stripped = text.strip()
    if not stripped:
        return "", ""

    paragraphs = [
        chunk.strip()
        for chunk in re.split(r"\n\s*\n", stripped)
        if chunk.strip() and not DECORATIVE_PARAGRAPH_RE.fullmatch(chunk.strip())
    ]
    if len(paragraphs) >= 2:
        pivot = max(1, len(paragraphs) // 2)
        left = "\n\n".join(paragraphs[:pivot]).strip()
        right = "\n\n".join(paragraphs[pivot:]).strip()
        if left and right:
            return left, right

    midpoint = len(stripped) // 2
    sentence_break = re.search(r"[。！？!?]", stripped[midpoint:])
    if sentence_break:
        pivot = midpoint + sentence_break.end()
    else:
        pivot = midpoint
    left = stripped[:pivot].strip()
    right = stripped[pivot:].strip()
    return left, right


def _has_substantive_excerpt(text: str) -> bool:
    candidate = text.strip()
    if not candidate:
        return False
    lines = [line.strip() for line in candidate.splitlines() if line.strip()]
    if not lines:
        return False
    meaningful = [
        line
        for line in lines
        if not CHAPTER_HEADING_RE.fullmatch(line)
        and not DECORATIVE_PARAGRAPH_RE.fullmatch(line)
        and line not in {"（原文为空，无法抽取对应片段）"}
    ]
    return bool(meaningful)


def _excerpt_paragraphs(text: str) -> list[str]:
    return [
        chunk.strip()
        for chunk in re.split(r"\n\s*\n", text.strip())
        if chunk.strip()
    ]


def _paragraph_mentions_any(paragraph: str, anchors: list[str]) -> bool:
    return any(anchor and anchor in paragraph for anchor in anchors)


def _selected_excerpt_paragraph_indexes(
    paragraphs: list[str],
    *,
    excerpt_tier: str,
    must_keep_names: list[str],
    reusable_lines: list[str],
) -> list[int]:
    if len(paragraphs) <= 3:
        return list(range(len(paragraphs)))

    selected_indexes = {0, len(paragraphs) - 1}
    reusable_anchors = [
        line.strip("“”\" \t\r\n")
        for line in reusable_lines
        if line.strip("“”\" \t\r\n")
    ]

    for index, paragraph in enumerate(paragraphs):
        if _paragraph_mentions_any(paragraph, must_keep_names):
            selected_indexes.add(index)
            continue
        if excerpt_tier == "low_risk" and (
            _paragraph_mentions_any(paragraph, reusable_anchors)
            or SOURCE_QUOTE_RE.search(paragraph)
        ):
            selected_indexes.add(index)

    if len(selected_indexes) >= len(paragraphs) - 1:
        return list(range(len(paragraphs)))
    return sorted(selected_indexes)


def _event_anchor_paragraphs(
    excerpt_text: str,
    *,
    excerpt_tier: str,
    must_keep_names: list[str],
    reusable_lines: list[str],
) -> list[str]:
    paragraphs = _excerpt_paragraphs(excerpt_text)
    selected_indexes = _selected_excerpt_paragraph_indexes(
        paragraphs,
        excerpt_tier=excerpt_tier,
        must_keep_names=must_keep_names,
        reusable_lines=reusable_lines,
    )
    return [paragraphs[index] for index in selected_indexes]


def _compact_original_excerpt(
    excerpt_text: str,
    *,
    excerpt_tier: str,
    must_keep_names: list[str],
    reusable_lines: list[str],
) -> str:
    if excerpt_tier == "strong_scene":
        return excerpt_text.strip()

    paragraphs = _excerpt_paragraphs(excerpt_text)
    selected_indexes = _selected_excerpt_paragraph_indexes(
        paragraphs,
        excerpt_tier=excerpt_tier,
        must_keep_names=must_keep_names,
        reusable_lines=reusable_lines,
    )
    if len(selected_indexes) == len(paragraphs):
        return excerpt_text.strip()

    compacted: list[str] = []
    last_index = -1
    for index in selected_indexes:
        if compacted and index - last_index > 1:
            compacted.append("（中间细节已压缩，仍按原文顺序推进）")
        compacted.append(paragraphs[index])
        last_index = index
    return "\n\n".join(compacted).strip()


def _span_to_excerpt_text(span_label: str, novel_text: str) -> str:
    sections = _chapter_sections(novel_text)
    if not sections:
        return "（原文为空，无法抽取对应片段）"

    chapter_num = _chapter_number_from_label(span_label)
    if chapter_num is None:
        return sections[0][1]

    section_index = chapter_num - 1
    if section_index < 0 or section_index >= len(sections):
        return sections[0][1]

    heading, body = sections[section_index]
    front, back = _split_text_half(body)

    if "前半" in span_label:
        excerpt = front if _has_substantive_excerpt(front) else back if _has_substantive_excerpt(back) else body
    elif "后半" in span_label or "後半" in span_label:
        excerpt = back if _has_substantive_excerpt(back) else front if _has_substantive_excerpt(front) else body
    else:
        excerpt = body

    return f"{heading}\n\n{excerpt}".strip()


def _extract_all_source_quote_lines(excerpt_text: str) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    for match in SOURCE_QUOTE_RE.finditer(excerpt_text):
        line = match.group(1).strip()
        if len(line) < 2:
            continue
        if line in seen:
            continue
        seen.add(line)
        candidates.append(line)
    return candidates


def _line_has_unconfirmed_sibling_relation_label(line: str, excerpt_text: str) -> bool:
    if not EARLY_SIBLING_RELATION_LABEL_RE.search(line):
        return False
    line_index = excerpt_text.find(line)
    context = excerpt_text[:line_index] if line_index >= 0 else excerpt_text
    return not RELATION_CONFIRMATION_RE.search(context)


def _filter_relation_unsafe_lines(lines: list[str], excerpt_text: str) -> list[str]:
    return [
        line
        for line in lines
        if not _line_has_unconfirmed_sibling_relation_label(line, excerpt_text)
    ]


def _extract_reusable_source_lines(excerpt_text: str) -> list[str]:
    all_lines = _filter_relation_unsafe_lines(_extract_all_source_quote_lines(excerpt_text), excerpt_text)
    if len(all_lines) <= 10:
        return all_lines
    head = all_lines[:6]
    tail = all_lines[-4:]
    ordered: list[str] = []
    seen: set[str] = set()
    for line in head + tail:
        if line in seen:
            continue
        seen.add(line)
        ordered.append(line)
    return ordered


def _excerpt_should_include_reusable_lines(
    reusable_lines: list[str],
    *,
    excerpt_tier: str,
) -> bool:
    if not reusable_lines:
        return False
    return excerpt_tier in {"low_risk", "strong_scene"}


def _classify_excerpt_tier(
    *,
    scene_modes: list[str],
    must_keep_long_lines: list[str],
    abstract_narration: list[str],
    reusable_lines_present: bool,
) -> str:
    if (
        must_keep_long_lines
        or abstract_narration
        or any(mode in {"reveal_scene", "result_confirmation_scene", "pressure_scene"} for mode in scene_modes)
    ):
        return "strong_scene"
    if reusable_lines_present:
        return "low_risk"
    return "baseline"


def _extract_excerpt_tier(text: str) -> str | None:
    match = re.search(r"^- excerpt_tier:\s*(baseline|low_risk|strong_scene)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def _excerpt_tier_from_profile_sections(text: str) -> str:
    scene_modes = _extract_bullet_section(text, "Scene Modes")
    must_keep_long_lines = _extract_bullet_section(text, "Must-Keep Long Lines")
    abstract_narration = _extract_bullet_section(text, "Abstract Narration To Externalize")
    reusable_lines_present = "## Reusable Source Lines" in text
    return _classify_excerpt_tier(
        scene_modes=scene_modes,
        must_keep_long_lines=must_keep_long_lines,
        abstract_narration=abstract_narration,
        reusable_lines_present=reusable_lines_present,
    )


def _known_character_names() -> list[str]:
    names: set[str] = set()
    for path in (ROOT / "voice-anchor.md", ROOT / "character.md"):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for match in HEADING_LEVEL3_RE.finditer(text):
            heading = match.group(1).strip()
            if any(token in heading for token in ("×", "/", " ")):
                continue
            if 1 < len(heading) <= 4:
                names.add(heading)
    return sorted(names)


def _extract_must_keep_names(excerpt_text: str) -> list[str]:
    names = [name for name in _known_character_names() if name in excerpt_text]
    names.sort(key=excerpt_text.find)
    return names[:8]


def _extract_must_keep_long_lines(excerpt_text: str, reusable_lines: list[str]) -> list[str]:
    all_quote_lines = _extract_all_source_quote_lines(excerpt_text)
    indexed: list[tuple[int, str]] = []
    for index, line in enumerate(all_quote_lines):
        cleaned = line.strip()
        if len(cleaned) < 18:
            continue
        if _line_has_unconfirmed_sibling_relation_label(cleaned, excerpt_text):
            continue
        indexed.append((index, cleaned))

    if indexed:
        ranked = sorted(indexed, key=lambda item: len(item[1]), reverse=True)[:4]
        keep_indexes = {index for index, _ in ranked}
        return [line for index, line in indexed if index in keep_indexes]

    must_keep_names = _extract_must_keep_names(excerpt_text)
    seen: set[str] = set()
    candidates: list[str] = []

    for line in reusable_lines:
        cleaned = line.strip("“”\" \t\r\n")
        if len(cleaned) < 18 or cleaned in seen:
            continue
        if _line_has_unconfirmed_sibling_relation_label(cleaned, excerpt_text):
            continue
        seen.add(cleaned)
        candidates.append(cleaned)

    for sentence in re.split(r"[。！？!?]", excerpt_text):
        cleaned = sentence.strip("“”\" \t\r\n")
        if len(cleaned) < 24 or cleaned in seen:
            continue
        if _line_has_unconfirmed_sibling_relation_label(cleaned, excerpt_text):
            continue
        if must_keep_names and not any(name in cleaned for name in must_keep_names):
            continue
        seen.add(cleaned)
        candidates.append(cleaned)
    return candidates[:3]


def _extract_abstract_narration_to_externalize(excerpt_text: str) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    for sentence in re.split(r"[。！？!?]\s*|\n+", excerpt_text):
        cleaned = sentence.strip("“”\" \t\r\n")
        if len(cleaned) < 8:
            continue
        if not any(keyword in cleaned for keyword in ABSTRACT_NARRATION_KEYWORDS):
            continue
        if cleaned in seen:
            continue
        seen.add(cleaned)
        candidates.append(cleaned)
    return candidates[:10]


def _detect_scene_modes(excerpt_text: str) -> list[str]:
    modes: list[str] = []
    if any(keyword in excerpt_text for keyword in REVEAL_SCENE_KEYWORDS):
        modes.append("reveal_scene")
    if any(keyword in excerpt_text for keyword in RESULT_CONFIRMATION_SCENE_KEYWORDS):
        modes.append("result_confirmation_scene")
    if any(keyword in excerpt_text for keyword in PRESSURE_SCENE_KEYWORDS):
        modes.append("pressure_scene")
    if not modes:
        modes.append("default_scene")
    return modes


def _forbidden_fill_hints(scene_modes: list[str]) -> list[str]:
    hints = [
        "新承接对白",
        "额外宾客台词",
        "额外角色OS",
        "后台流程扩写",
        "动作尾句扩写",
    ]
    if "reveal_scene" in scene_modes:
        hints.extend(
            [
                "揭露前寒暄",
                "揭露前附和反应",
            ]
        )
    if "pressure_scene" in scene_modes:
        hints.extend(
            [
                "模板短句嘴仗",
                "削弱施压解释句",
            ]
        )
    return hints


def _compact_json_text(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def _clean_inline_fact_text(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    for marker in (
        "source chapter span",
        "must-keep beats",
        "must-not-add / must-not-jump",
        "function signals",
        "ending function",
        "irreversibility level",
        "ending type",
    ):
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0].strip()
    return cleaned.strip("：: \t\r\n")


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


def _beat_lines_from_raw(beats: str | list[str]) -> list[str]:
    if isinstance(beats, list):
        return [str(item).strip() for item in beats if str(item).strip()]
    return [part.strip(" -") for part in re.split(r"[\n；;]+", str(beats)) if part.strip(" -")]


def _infer_function_name_from_text(text: str, *, fallback: str) -> str:
    if not text:
        return fallback
    hints = (
        ("intrusion", ("误认", "错认", "闯", "拦", "带走", "带回", "撞见", "突然出现", "找上门")),
        ("reveal", ("揭露", "公开", "掉马", "鉴定", "真相", "认出", "确认", "身份", "点出", "暗示")),
        ("confrontation", ("对峙", "拒认", "质问", "撕破", "断亲", "切割", "反击", "回击", "摊牌")),
        ("reversal", ("翻车", "反转", "打脸", "反杀", "站队", "制裁")),
        ("escalation", ("施压", "升级", "逼", "强行", "带上车", "困住", "推进", "压下", "围堵", "追求")),
        ("emotional_payoff", ("和解", "释怀", "求婚", "婚礼", "团圆", "落泪")),
        ("arrival", ("到达", "抵达", "驶进", "走进", "入场")),
    )
    for function_name, keywords in hints:
        if any(keyword in text for keyword in keywords):
            return function_name
    return fallback


def _normalize_ending_function(raw: str, beats: list[str]) -> str:
    text = raw.strip()
    if text in ALLOWED_ENDING_FUNCTIONS:
        return text
    inferred = _infer_function_name_from_text(text or (beats[-1] if beats else ""), fallback="")
    joined_beats = " ".join(beats)
    if "身份钩子" in text and any(keyword in joined_beats for keyword in ("卷进", "卷入", "带上车", "带走", "锁", "困", "无法抽身")):
        return "locked_in"
    keyword_map = (
        ("locked_in", ("锁", "困", "带走", "卷入", "无法抽身", "进门", "上车")),
        ("reversal_triggered", ("反转", "打脸", "掉马", "反杀", "翻车", "公开身份", "站队")),
        ("reveal_pending", ("身份钩子", "即将揭露", "揭晓", "揭穿", "真相")),
        ("confrontation_pending", ("前推", "对抗", "施压", "逼问", "试探", "对峙")),
        ("emotional_payoff", ("情绪回收", "释怀", "和解", "甜", "求婚")),
        ("closure", ("闭环", "终局", "成型", "收束")),
        ("arrival", ("到达", "抵达", "入场", "开场")),
    )
    for ending_function, keywords in keyword_map:
        if any(keyword in text for keyword in keywords):
            return ending_function
    if inferred == "reveal":
        return "reveal_pending"
    if inferred in {"confrontation", "escalation"}:
        return "confrontation_pending"
    if inferred == "reversal":
        return "reversal_triggered"
    if inferred == "emotional_payoff":
        return "emotional_payoff"
    if inferred == "arrival":
        return "arrival"
    return "confrontation_pending"


def _infer_irreversibility_level(ending_function: str, beats: list[str]) -> str:
    if ending_function in {"locked_in", "reversal_triggered", "reveal_pending"}:
        return "hard"
    if ending_function in {"confrontation_pending", "arrival"}:
        return "medium"
    if ending_function in {"emotional_payoff", "closure"}:
        return "soft"
    if any(any(keyword in beat for keyword in ("公开", "确认", "断绝", "锁", "带走")) for beat in beats):
        return "hard"
    return "medium"


def _infer_function_signals(episode_id: str, beats: list[str], ending_function: str) -> dict[str, object]:
    opening_function = _infer_function_name_from_text(beats[0] if beats else "", fallback="setup")
    middle_candidates = beats[1:-1] if len(beats) > 2 else beats[1:]
    middle_functions = [
        _infer_function_name_from_text(beat, fallback="escalation")
        for beat in middle_candidates
    ]
    middle_functions = [name for name in middle_functions if name != opening_function] or ["escalation"]
    strong_tags: list[str] = []
    episode_num = int(episode_id.split("-")[1])
    if episode_num == 1 or ending_function in {"locked_in", "reveal_pending", "reversal_triggered", "confrontation_pending"}:
        if opening_function in {"intrusion", "reveal", "arrival"}:
            strong_tags.append("intrusion")
        if any(name in {"escalation", "reveal"} for name in middle_functions):
            strong_tags.append("escalation")
        if any(name in {"confrontation", "reversal"} for name in middle_functions) or ending_function in {"confrontation_pending", "reversal_triggered"}:
            strong_tags.append("confrontation_or_reversal")
        if ending_function in {"locked_in", "reveal_pending", "reversal_triggered", "confrontation_pending", "arrival"}:
            strong_tags.append("hook")
    return {
        "opening_function": opening_function,
        "middle_functions": middle_functions,
        "strong_function_tags": strong_tags,
    }


def _parse_function_signal_block(items: list[str]) -> dict[str, object]:
    result: dict[str, object] = {}
    for item in items:
        if ":" not in item:
            continue
        key, raw_value = item.split(":", 1)
        normalized_key = key.strip().lower()
        values = _split_fact_list(raw_value.strip())
        if normalized_key == "opening_function" and values:
            result["opening_function"] = values[0]
        elif normalized_key == "middle_functions":
            result["middle_functions"] = values
        elif normalized_key in {"strong_signals", "strong_function_tags"}:
            result["strong_function_tags"] = values
    return result


def _extract_block_bullets(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        value = _clean_inline_fact_text(stripped[2:])
        if value:
            items.append(value)
    return items


def _extract_marked_block(text: str, start_marker: str, end_markers: tuple[str, ...]) -> str:
    start = text.find(start_marker)
    if start == -1:
        return ""
    start += len(start_marker)
    end = len(text)
    for marker in end_markers:
        marker_index = text.find(marker, start)
        if marker_index != -1:
            end = min(end, marker_index)
    return text[start:end].strip()


def _extract_source_map_header_value(text: str, key: str) -> str | None:
    match = re.search(rf"^- {re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip()


def _extract_batch_facts_from_source_map(batch_id: str) -> dict[str, object]:
    batch_slice = _batch_source_map_slice(batch_id)
    lines = batch_slice.splitlines()
    batch_heading = next((line.strip() for line in lines if line.startswith("## Batch ")), "")
    episode_blocks = list(
        re.finditer(
            r"^###\s+EP0*(\d+)\b.*?(?=^###\s+EP0*\d+\b|\Z)",
            batch_slice,
            re.MULTILINE | re.DOTALL,
        )
    )
    episodes: list[dict[str, object]] = []
    for block_match in episode_blocks:
        block = block_match.group(0)
        episode_num = int(block_match.group(1))
        episode_id = f"EP-{episode_num:02d}"
        source_span = _clean_inline_fact_text(
            _extract_marked_block(
                block,
                "**source_chapter_span**:",
                (
                    "**must-keep_beats**:",
                    "**must-not-add / must-not-jump**:",
                    "**function_signals**:",
                    "**ending_function**:",
                    "**irreversibility_level**:",
                    "**ending_type**:",
                ),
            )
        )
        must_keep_beats = _extract_block_bullets(
            _extract_marked_block(
                block,
                "**must-keep_beats**:",
                (
                    "**must-not-add / must-not-jump**:",
                    "**function_signals**:",
                    "**ending_function**:",
                    "**irreversibility_level**:",
                    "**ending_type**:",
                ),
            )
        )
        must_not_add = _extract_block_bullets(
            _extract_marked_block(
                block,
                "**must-not-add / must-not-jump**:",
                ("**function_signals**:", "**ending_function**:", "**irreversibility_level**:", "**ending_type**:"),
            )
        )
        function_signals = _parse_function_signal_block(
            _extract_block_bullets(
                _extract_marked_block(
                    block,
                    "**function_signals**:",
                    ("**ending_function**:", "**irreversibility_level**:", "**ending_type**:"),
                )
            )
        )
        ending_function = _clean_inline_fact_text(
            _extract_marked_block(block, "**ending_function**:", ("**irreversibility_level**:", "**ending_type**:"))
        )
        if not ending_function:
            ending_function = _normalize_ending_function(
                _clean_inline_fact_text(_extract_marked_block(block, "**ending_type**:", ())),
                must_keep_beats,
            )
        irreversibility_level = _clean_inline_fact_text(
            _extract_marked_block(block, "**irreversibility_level**:", ("**ending_type**:",))
        )
        if irreversibility_level not in ALLOWED_IRREVERSIBILITY_LEVELS:
            irreversibility_level = _infer_irreversibility_level(ending_function, must_keep_beats)
        inferred_function_signals = _infer_function_signals(episode_id, must_keep_beats, ending_function)
        function_signals = {
            "opening_function": function_signals.get("opening_function") or inferred_function_signals["opening_function"],
            "middle_functions": function_signals.get("middle_functions") or inferred_function_signals["middle_functions"],
            "strong_function_tags": function_signals.get("strong_function_tags") or inferred_function_signals["strong_function_tags"],
        }
        episodes.append(
            {
                "episode": episode_id,
                "source_span": source_span,
                "must_keep_beats": must_keep_beats,
                "must_not_add": must_not_add,
                "function_signals": function_signals,
                "ending_function": ending_function,
                "irreversibility_level": irreversibility_level,
            }
        )
    return {
        "batch_heading": batch_heading,
        "episodes": episodes,
    }


def _extract_brief_metadata(brief_path: Path) -> dict[str, object]:
    text = _safe_read_text(brief_path)
    owned_match = re.search(r"^- owned episodes:\s*(.+?)\s*$", text, re.MULTILINE)
    source_range_match = re.search(r"^- source excerpt range:\s*(.+?)\s*$", text, re.MULTILINE)
    adjacency_match = re.search(r"^- adjacent continuity:\s*(.+?)\s*$", text, re.MULTILINE)
    return {
        "owned_episodes": [item.strip() for item in (owned_match.group(1).split(",") if owned_match else []) if item.strip()],
        "source_excerpt_range": source_range_match.group(1).strip() if source_range_match else "",
        "adjacent_continuity": adjacency_match.group(1).strip() if adjacency_match else "",
    }


def _contract_digest() -> dict[str, object]:
    return {
        "adaptation_strategy": "original_fidelity",
        "dialogue_adaptation_intensity": "light",
        "shell_format": [
            "场EP-N：",
            "日/夜",
            "外/内",
            "场景：",
            "♪：",
            "△：",
            "【镜头】：",
            "角色（os）：",
        ],
        "hard_constraints": [
            "batch brief 定当前集任务与 beats",
            "source.map + event_anchors 定顺序与边界",
            "禁新事件/流程/职业说明/承接对白",
            "只能写 drafts/episodes/EP-XX.md",
            "禁改 episodes/、state/、source.map、run.manifest",
            "整集 >= 2 场，场次数按 beats 决定",
        ],
    }


def _style_digest() -> dict[str, object]:
    return {
        "format_rules": [
            "壳层独行",
            "优先可拍动作/画面",
            "light 改编，不复用示例句",
        ],
        "line_prefixes": {
            "action": "△：",
            "music": "♪：",
            "camera": "【镜头】：",
            "os": "角色（os）：",
        },
    }


def _quality_digest() -> dict[str, object]:
    return {
        "checks": [
            "本集 beats 一项不漏",
            "硬事件不后拖",
            "可删的新增桥接句就删",
            "场尾留新增推进",
            "总结句改可拍反应",
        ]
    }


def _reference_names_digest() -> dict[str, object]:
    return {"primary_names": _known_character_names()}


def _build_episode_source_excerpt(batch_id: str, episode: str) -> Path:
    excerpt_dir = _source_excerpt_dir(batch_id)
    excerpt_dir.mkdir(parents=True, exist_ok=True)
    excerpt_path = _source_excerpt_markdown_path(batch_id, episode)
    excerpt_json_path = _source_excerpt_json_path(batch_id, episode)

    source_path = _manifest_source_file()
    source_span = _episode_source_span(episode) or "（未在 source.map 中找到 source_chapter_span）"

    if source_path is None or not source_path.exists():
        excerpt_body = "（source_file 不存在，无法抽取当前集原文片段）"
    else:
        novel_text = source_path.read_text(encoding="utf-8")
        excerpt_body = _span_to_excerpt_text(source_span, novel_text)
    reusable_lines = _extract_reusable_source_lines(excerpt_body)
    scene_modes = _detect_scene_modes(excerpt_body)
    must_keep_names = _extract_must_keep_names(excerpt_body)
    must_keep_long_lines = _extract_must_keep_long_lines(excerpt_body, reusable_lines)
    abstract_narration = _extract_abstract_narration_to_externalize(excerpt_body)
    forbidden_fill = _forbidden_fill_hints(scene_modes)
    excerpt_tier = _classify_excerpt_tier(
        scene_modes=scene_modes,
        must_keep_long_lines=must_keep_long_lines,
        abstract_narration=abstract_narration,
        reusable_lines_present=bool(reusable_lines),
    )
    include_reusable_lines = _excerpt_should_include_reusable_lines(
        reusable_lines,
        excerpt_tier=excerpt_tier,
    )
    event_anchors = _event_anchor_paragraphs(
        excerpt_body,
        excerpt_tier=excerpt_tier,
        must_keep_names=must_keep_names,
        reusable_lines=reusable_lines,
    )
    rendered_excerpt_body = _compact_original_excerpt(
        excerpt_body,
        excerpt_tier=excerpt_tier,
        must_keep_names=must_keep_names,
        reusable_lines=reusable_lines,
    )
    reusable_block = (
        "\n".join(f"- {line}" for line in reusable_lines)
        if reusable_lines
        else "（当前片段未提取到可直接复用的引号台词；仍需贴着原文语义和信息顺序改写）"
    )
    scene_modes_block = "\n".join(f"- {mode}" for mode in scene_modes)
    must_keep_names_block = (
        "\n".join(f"- {name}" for name in must_keep_names)
        if must_keep_names
        else "（当前片段未抽到可直接锁定的人名；仍以原文显式出现的称谓为准）"
    )
    must_keep_long_lines_block = (
        "\n".join(f"- {line}" for line in must_keep_long_lines)
        if must_keep_long_lines
        else "（当前片段未抽到必须保长句的台词；仍应优先保留原文递进）"
    )
    abstract_narration_block = (
        "\n".join(f"- {line}" for line in abstract_narration)
        if abstract_narration
        else "（当前片段未抽到必须外化的抽象叙述；仍要避免把小说总结句原样落进 `△`）"
    )
    forbidden_fill_block = "\n".join(f"- {item}" for item in forbidden_fill)

    sections = [
        f"# Source Excerpt: {episode}",
        "",
        f"- source_span: {source_span}",
        f"- excerpt_tier: {excerpt_tier}",
        "",
        "## Original Excerpt",
        rendered_excerpt_body,
        "",
        "## Must-Keep Names",
        must_keep_names_block,
        "",
    ]
    if include_reusable_lines:
        sections.extend(
            [
                "## Reusable Source Lines",
                reusable_block,
                "",
            ]
        )
    if excerpt_tier == "strong_scene":
        sections.extend(
            [
                "## Scene Modes",
                scene_modes_block,
                "",
                "## Must-Keep Long Lines",
                must_keep_long_lines_block,
                "",
                "## Abstract Narration To Externalize",
                abstract_narration_block,
                "",
            ]
        )
    sections.extend(
        [
            "## Forbidden Fill",
            forbidden_fill_block,
            "",
        ]
    )

    payload: dict[str, object] = {
        "episode": episode,
        "source_span": source_span,
        "excerpt_tier": excerpt_tier,
        "event_anchors": event_anchors,
        "must_keep_names": must_keep_names,
        "forbidden_fill": forbidden_fill,
    }
    if excerpt_tier in {"low_risk", "strong_scene"}:
        payload["reusable_source_lines"] = reusable_lines
    if excerpt_tier == "strong_scene":
        payload["scene_modes"] = scene_modes
        payload["must_keep_long_lines"] = must_keep_long_lines
        payload["abstract_narration"] = abstract_narration

    excerpt_path.write_text("\n".join(sections), encoding="utf-8")
    excerpt_json_path.write_text(_compact_json_text(payload), encoding="utf-8")
    return excerpt_path


def _build_batch_context_bundle(batch_id: str, brief_path: Path) -> Path:
    bundle_dir = _batch_context_dir()
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = _batch_context_markdown_path(batch_id)
    bundle_json_path = _batch_context_json_path(batch_id)
    sections = [
        "# Batch Writer Context Bundle",
        "",
        f"- batch_id: {batch_id}",
        f"- generated_from: {_rel(brief_path)}",
        "- purpose: batch 级静态上下文预打包，减少每个 episode 重复读同一组规则文件",
        "",
        "说明：",
        "- 这个 bundle 只聚合 batch 内共享且相对静态的上下文。",
        "- writer prompt 只消费 batch brief / source.map / batch-context / source excerpt，不再读取全局 state 文件。",
        "",
    ]
    sections.extend(
        [
            "## 运行清单",
            f"- source: {_rel(ROOT / 'harness' / 'project' / 'run.manifest.md')}",
            "",
            _safe_read_text(ROOT / "harness" / "project" / "run.manifest.md"),
            "",
            "---",
            "",
            "## 当前 batch source map 切片",
            f"- source: {_rel(_source_map_path())} (batch slice)",
            "",
            _batch_source_map_slice(batch_id),
            "",
            "---",
            "",
            "## 当前 batch brief",
            f"- source: {_rel(brief_path)}",
            "",
            _safe_read_text(brief_path),
            "",
            "---",
            "",
            "## 写作合同",
            f"- source: {_rel(ROOT / 'harness' / 'framework' / 'write-contract.md')}",
            "",
            _safe_read_text(ROOT / "harness" / "framework" / "write-contract.md"),
            "",
            "---",
            "",
            "## 成稿风格",
            f"- source: {_rel(ROOT / 'harness' / 'framework' / 'writer-style.md')}",
            "",
            _safe_read_text(ROOT / "harness" / "framework" / "writer-style.md"),
            "",
            "---",
            "",
        ]
    )

    quality_anchor = _quality_anchor_path()
    if quality_anchor.exists():
        sections.extend(
            [
                "## 质量锚",
                f"- source: {_rel(quality_anchor)}",
                "",
                _safe_read_text(quality_anchor),
                "",
                "---",
                "",
            ]
        )

    voice_anchor = ROOT / "voice-anchor.md"
    if voice_anchor.exists():
        sections.extend(
            [
                "## 声纹锚",
                f"- source: {_rel(voice_anchor)}",
                "",
                _safe_read_text(voice_anchor),
                "",
                "---",
                "",
            ]
        )

    character = ROOT / "character.md"
    if character.exists():
        sections.extend(
            [
                "## 角色参考",
                f"- source: {_rel(character)}",
                "",
                _safe_read_text(character),
                "",
                "---",
                "",
            ]
        )

    if PASSING_SAMPLE.exists():
        sections.extend(
            [
                "## 通过 lint 的样例壳",
                f"- source: {_rel(PASSING_SAMPLE)}",
                "",
                _safe_read_text(PASSING_SAMPLE),
                "",
                "---",
                "",
            ]
        )
    bundle_path.write_text("\n".join(sections).rstrip() + "\n", encoding="utf-8")
    source_map_text = _safe_read_text(_source_map_path())
    brief_metadata = _extract_brief_metadata(brief_path)
    source_map_batch_facts = _extract_batch_facts_from_source_map(batch_id)
    bundle_payload = {
        "batch_id": batch_id,
        "authority": {
            "brief_path": _rel(brief_path),
            "source_map_path": _rel(_source_map_path()),
            "manifest_path": _rel(_run_manifest_path()),
        },
        "batch_facts": {
            "owned_episodes": brief_metadata["owned_episodes"],
            "source_excerpt_range": brief_metadata["source_excerpt_range"],
            "adjacent_continuity": brief_metadata["adjacent_continuity"],
            "batch_heading": source_map_batch_facts["batch_heading"],
            "episodes": source_map_batch_facts["episodes"],
        },
        "contract_digest": _contract_digest()
        | {
            "adaptation_strategy": _extract_source_map_header_value(source_map_text, "adaptation_strategy") or "original_fidelity",
            "dialogue_adaptation_intensity": _extract_source_map_header_value(source_map_text, "dialogue_adaptation_intensity") or "light",
        },
        "style_digest": _style_digest(),
        "quality_digest": _quality_digest(),
        "reference_names": _reference_names_digest(),
    }
    bundle_json_path.write_text(_compact_json_text(bundle_payload), encoding="utf-8")
    return bundle_path


def _extract_bullet_section(text: str, heading: str) -> list[str]:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return []
    body = match.group(1)
    items: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        value = line[2:].strip()
        if not value or value.startswith("（") or value.startswith("("):
            continue
        items.append(value)
    return items


def _read_json_object(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _batch_context_episode_facts(batch_context_path: Path, episode: str) -> dict[str, object]:
    payload = _read_json_object(_batch_context_runtime_path(batch_context_path)) or {}
    batch_facts = payload.get("batch_facts")
    if not isinstance(batch_facts, dict):
        return {}
    episodes = batch_facts.get("episodes")
    if not isinstance(episodes, list):
        return {}
    for item in episodes:
        if isinstance(item, dict) and str(item.get("episode", "")).strip() == episode:
            return item
    return {}


def _render_episode_beats(episode_facts: dict[str, object]) -> str:
    beats = episode_facts.get("must_keep_beats")
    if not isinstance(beats, list) or not beats:
        return "- （未抽到 must_keep_beats；仍必须以 batch brief 当前集任务为准，不得擅自补设定）"
    return "\n".join(f"- {str(item).strip()}" for item in beats if str(item).strip())


def _render_episode_function_goals(episode_facts: dict[str, object]) -> str:
    function_signals = episode_facts.get("function_signals")
    if not isinstance(function_signals, dict):
        return "- opening: （未配置）\n- middle: （未配置）\n- ending: （未配置）\n- irreversibility: medium"
    opening_function = str(function_signals.get("opening_function", "")).strip() or "setup"
    middle_functions = [
        str(item).strip()
        for item in function_signals.get("middle_functions", [])
        if str(item).strip()
    ]
    strong_function_tags = [
        str(item).strip()
        for item in function_signals.get("strong_function_tags", [])
        if str(item).strip()
    ]
    ending_function = str(episode_facts.get("ending_function", "")).strip() or "confrontation_pending"
    irreversibility_level = str(episode_facts.get("irreversibility_level", "")).strip() or "medium"
    lines = [
        f"- opening: {opening_function}",
        f"- middle: {', '.join(middle_functions) or 'escalation'}",
        f"- ending: {ending_function}",
        f"- irreversibility: {irreversibility_level}",
    ]
    if strong_function_tags:
        lines.append(f"- 强功能补齐: {', '.join(strong_function_tags)}")
    return "\n".join(lines)


def _scene_function_plan_slots(episode_facts: dict[str, object]) -> list[str]:
    function_signals = episode_facts.get("function_signals")
    if not isinstance(function_signals, dict):
        return ["setup", str(episode_facts.get("ending_function", "confrontation_pending")).strip() or "confrontation_pending"]
    opening_function = str(function_signals.get("opening_function", "")).strip() or "setup"
    middle_functions = [
        str(item).strip()
        for item in function_signals.get("middle_functions", [])
        if str(item).strip()
    ]
    ending_function = str(episode_facts.get("ending_function", "")).strip() or "confrontation_pending"
    strong_function_tags = {
        str(item).strip()
        for item in function_signals.get("strong_function_tags", [])
        if str(item).strip()
    }

    slots: list[str] = [opening_function, *middle_functions]
    if "escalation" in strong_function_tags and "escalation" not in slots and len(middle_functions) < 2:
        insert_at = 1 if slots else 0
        slots.insert(insert_at, "escalation")
    if "confrontation_or_reversal" in strong_function_tags and not any(
        item in {"confrontation", "reversal"} for item in slots
    ):
        insert_at = len(slots) if slots else 0
        slots.insert(insert_at, "confrontation")
    slots.append(ending_function)
    if len(slots) < 2:
        slots.insert(0, "setup" if slots[0] != "setup" else "intrusion")
    return slots


def _scene_function_ending_requirement(primary_function: str, *, is_final: bool, ending_function: str) -> str:
    if is_final:
        ending_requirements = {
            "arrival": "到达已发生，下一空间或关系压力立刻顶上来",
            "confrontation_pending": "对抗已起，下一拍逼问、逼选或压迫立刻接上",
            "reveal_pending": "关键信息已亮出，下一拍揭晓或反应必须启动",
            "locked_in": "物理约束或空间封闭落地，角色已无法轻易离开",
            "reversal_triggered": "反转已被触发，旧局面不能立刻恢复",
            "emotional_payoff": "情绪兑现落地，后续关系变化已被触发",
            "closure": "当前阶段闭环成立，不再回撤到前状态",
        }
        return ending_requirements.get(ending_function, "终场必须把当前集最后推进落地，不能停在总结态")

    requirements = {
        "intrusion": "异常闯入成立，开场前两三个拍点就要撞上或截停，下一步必须被迫应对",
        "escalation": "压力升级完成，下一步代价或控制继续加码",
        "confrontation": "对抗立住，至少落一个硬反抗/阻挡动作，下一步逼选或反制必须接上",
        "reveal": "关键信息已亮相，下一步识别或反应必须启动",
        "reversal": "局面开始翻转，旧优势不能立刻恢复",
        "arrival": "到场只是起点，下一步冲突或揭晓立刻接上",
        "emotional_payoff": "情绪兑现后，下一步关系变化立刻显形",
        "setup": "局势一旦建立，必须立刻推进到下一功能",
    }
    return requirements.get(primary_function, "当前功能一旦成立，下一步推进必须立刻接上")


def _scene_function_irreversibility_hint(
    primary_function: str,
    *,
    is_final: bool,
    irreversibility_level: str,
) -> str:
    if is_final:
        final_hints = {
            "hard": "物理约束、空间封闭或方向不可逆至少落一项；优先门锁/封门/导航/驶离主路，不靠 OS 总结",
            "medium": "结果已触发，角色已被推入下一步，不能轻易撤回",
            "soft": "情绪或关系变化已经发生，不能完全回到前状态",
        }
        return final_hints.get(irreversibility_level, "结果已触发，不能轻易撤回")

    progression_hints = {
        "intrusion": "已经被盯上或卷入，不能当作什么都没发生；别先写环境、穿着或气质总述",
        "escalation": "控制或施压已升级，下一步只能更近不能后退",
        "confrontation": "拒绝或反击已说出口，关系不再回到试探前；优先手上、脚下、门边、座位边的硬反抗动作",
        "reveal": "信息已暴露给观众或对手，不能当作未出现",
        "reversal": "局面已经偏转，旧优势不再稳定",
        "arrival": "位置已经变化，下一空间压力已经启动",
        "setup": "当前状态一旦成立，下一步必须立即接上",
    }
    return progression_hints.get(primary_function, "当前推进已成立，不能轻易回到上一步")


def _build_scene_function_plan(episode: str, episode_facts: dict[str, object]) -> list[dict[str, object]]:
    slots = _scene_function_plan_slots(episode_facts)
    beats = [str(item).strip() for item in episode_facts.get("must_keep_beats", []) if str(item).strip()]
    middle_beats = beats[1:-1] if len(beats) > 2 else beats[1:]
    episode_num = int(episode.split("-")[1])
    ending_function = str(episode_facts.get("ending_function", "")).strip() or "confrontation_pending"
    irreversibility_level = str(episode_facts.get("irreversibility_level", "")).strip() or "medium"
    plan: list[dict[str, object]] = []
    for idx, slot in enumerate(slots):
        if idx == 0:
            beat_text = beats[0] if beats else "先完成当前集第一拍异常/入局"
        elif idx == len(slots) - 1:
            beat_text = beats[-1] if beats else "终段必须完成 ending_function 对应的最后推进"
        else:
            middle_idx = idx - 1
            if middle_beats:
                beat_text = middle_beats[min(middle_idx, len(middle_beats) - 1)]
            elif len(beats) > 1:
                beat_text = beats[min(idx, len(beats) - 1)]
            else:
                beat_text = "承接当前集中的升级/对抗/反打推进"
        is_final = idx == len(slots) - 1
        plan.append(
            {
                "scene_num": idx + 1,
                "scene_id": f"场{episode_num}-{idx + 1}",
                "primary_function": slot,
                "beat_coverage": [beat_text],
                "ending_requirement": _scene_function_ending_requirement(
                    slot,
                    is_final=is_final,
                    ending_function=ending_function,
                ),
                "irreversibility_hint": _scene_function_irreversibility_hint(
                    slot,
                    is_final=is_final,
                    irreversibility_level=irreversibility_level,
                ),
                "ending_function": ending_function if is_final else "",
                "irreversibility_level": irreversibility_level if is_final else "",
            }
        )
    return plan


def _scene_function_plan_lines(episode: str, episode_facts: dict[str, object]) -> list[str]:
    lines: list[str] = []
    for item in _build_scene_function_plan(episode, episode_facts):
        beat_coverage = [str(beat).strip() for beat in item.get("beat_coverage", []) if str(beat).strip()]
        beat_text = " / ".join(beat_coverage) if beat_coverage else "承接当前功能推进"
        line = (
            f"- {item['scene_id']}：主功能 `{item['primary_function']}`；"
            f"覆盖：{beat_text}；"
            f"场尾要求：{item['ending_requirement']}；"
            f"不可逆提示：{item['irreversibility_hint']}"
        )
        ending_function = str(item.get("ending_function", "")).strip()
        irreversibility_level = str(item.get("irreversibility_level", "")).strip()
        if ending_function and irreversibility_level:
            line += f"；终场必须落 `{ending_function}`，并满足 `irreversibility={irreversibility_level}`"
        lines.append(line)
    return lines


def _render_scene_function_plan(episode: str, episode_facts: dict[str, object], *, indent: str = "") -> str:
    return "\n".join(f"{indent}{line}" for line in _scene_function_plan_lines(episode, episode_facts))


def _episode_function_signal_tokens(episode_facts: dict[str, object]) -> list[str]:
    function_signals = episode_facts.get("function_signals")
    if not isinstance(function_signals, dict):
        return []
    tokens: list[str] = []
    opening_function = str(function_signals.get("opening_function", "")).strip()
    if opening_function:
        tokens.append(f"opening:{opening_function}")
    middle_functions = [
        str(item).strip()
        for item in function_signals.get("middle_functions", [])
        if str(item).strip()
    ]
    for item in middle_functions:
        tokens.append(f"middle:{item}")
    ending_function = str(episode_facts.get("ending_function", "")).strip()
    if ending_function:
        tokens.append(f"ending:{ending_function}")
    irreversibility_level = str(episode_facts.get("irreversibility_level", "")).strip()
    if irreversibility_level:
        tokens.append(f"irreversibility:{irreversibility_level}")
    strong_function_tags = [
        str(item).strip()
        for item in function_signals.get("strong_function_tags", [])
        if str(item).strip()
    ]
    tokens.extend(f"strong:{item}" for item in strong_function_tags)
    return tokens


def _build_rule_priority_block() -> str:
    lines = [
        "冲突优先级：",
        "1. 完成当前集全部 beats > 其他一切；`【信息】/【关系】/【动作】/【钩子】` 任何一类都不能缺失。",
        "2. source 顺序与边界 > 节奏性后拖或压场数；已发生硬事件不能后拖。",
        "3. batch brief 当前集任务 > voice/style 借用；`voice-anchor` 只看气质与禁区，不抢任务优先级。",
        "4. `角色（os）：` 只是壳；不得新增第一人称“我……”式旁白。",
        "5. `must_keep_long_lines` 只有在不违反 `forbidden_fill`、must-not-add、must-not-jump 时才保。",
    ]
    return "\n".join(lines)


def _source_excerpt_companion_paths(path: Path) -> tuple[Path, Path]:
    if path.suffix == ".json":
        return path, path.with_suffix(".md")
    if path.suffix == ".md":
        return path.with_suffix(".json"), path
    return path.with_suffix(".json"), path.with_suffix(".md")


def _source_excerpt_requires_fidelity_rewrite(source_excerpt_path: Path) -> bool:
    return bool(_fidelity_rewrite_reasons(_episode_rule_profile(source_excerpt_path)))


def _episode_rule_profile(source_excerpt_path: Path) -> dict[str, object]:
    empty_profile = {
        "excerpt_tier": "baseline",
        "scene_modes": [],
        "must_keep_names": [],
        "must_keep_long_lines": [],
        "abstract_narration": [],
        "forbidden_fill": [],
        "reusable_lines_present": False,
    }

    json_path, markdown_path = _source_excerpt_companion_paths(source_excerpt_path)
    payload = _read_json_object(json_path)
    if payload is not None:
        reusable_source_lines = payload.get("reusable_source_lines", [])
        return {
            "excerpt_tier": str(payload.get("excerpt_tier", "baseline")),
            "scene_modes": [item for item in payload.get("scene_modes", []) if isinstance(item, str)],
            "must_keep_names": [item for item in payload.get("must_keep_names", []) if isinstance(item, str)],
            "must_keep_long_lines": [item for item in payload.get("must_keep_long_lines", []) if isinstance(item, str)],
            "abstract_narration": [item for item in payload.get("abstract_narration", []) if isinstance(item, str)],
            "forbidden_fill": [item for item in payload.get("forbidden_fill", []) if isinstance(item, str)],
            "reusable_lines_present": isinstance(reusable_source_lines, list) and bool(reusable_source_lines),
        }

    if not markdown_path.exists():
        return empty_profile

    text = markdown_path.read_text(encoding="utf-8")
    excerpt_tier = _extract_excerpt_tier(text) or _excerpt_tier_from_profile_sections(text)
    return {
        "excerpt_tier": excerpt_tier,
        "scene_modes": _extract_bullet_section(text, "Scene Modes"),
        "must_keep_names": _extract_bullet_section(text, "Must-Keep Names"),
        "must_keep_long_lines": _extract_bullet_section(text, "Must-Keep Long Lines"),
        "abstract_narration": _extract_bullet_section(text, "Abstract Narration To Externalize"),
        "forbidden_fill": _extract_bullet_section(text, "Forbidden Fill"),
        "reusable_lines_present": "## Reusable Source Lines" in text,
    }


def _rule_profile_signals(profile: dict[str, object]) -> list[str]:
    signals: list[str] = []
    excerpt_tier = str(profile.get("excerpt_tier", "baseline"))
    signals.append(f"tier:{excerpt_tier}")
    scene_modes = set(profile.get("scene_modes", []))
    if "reveal_scene" in scene_modes:
        signals.append("reveal_scene")
    if "result_confirmation_scene" in scene_modes:
        signals.append("result_confirmation_scene")
    if "pressure_scene" in scene_modes:
        signals.append("pressure_scene")
    if profile.get("must_keep_names"):
        signals.append("must_keep_names")
    if profile.get("must_keep_long_lines"):
        signals.append("must_keep_long_lines")
    if profile.get("abstract_narration"):
        signals.append("abstract_externalization")
    if profile.get("forbidden_fill"):
        signals.append("forbidden_fill")
    return signals


def _summarize_candidate_families(candidate_blocks: list[dict[str, object]]) -> list[str]:
    families: set[str] = set()
    for block in candidate_blocks:
        families.update(str(family) for family in block.get("problem_families", []))
    return sorted(families)


def _fidelity_rewrite_reasons(profile: dict[str, object]) -> list[str]:
    reasons: list[str] = []
    scene_modes = set(profile.get("scene_modes", []))
    if "reveal_scene" in scene_modes:
        reasons.append("reveal_scene")
    if "result_confirmation_scene" in scene_modes:
        reasons.append("result_confirmation_scene")
    if "pressure_scene" in scene_modes:
        reasons.append("pressure_scene")
    if profile.get("must_keep_long_lines"):
        reasons.append("must_keep_long_lines")
    if profile.get("abstract_narration"):
        reasons.append("abstract_externalization")
    return reasons


def _patch_family_contracts_from_profile(profile: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "problem_family": "restore_names",
            "items": list(profile.get("must_keep_names", [])),
            "allowed_actions": list(PATCH_FAMILY_ALLOWED_ACTIONS["restore_names"]),
        },
        {
            "problem_family": "restore_long_lines",
            "items": list(profile.get("must_keep_long_lines", []))[:4],
            "allowed_actions": list(PATCH_FAMILY_ALLOWED_ACTIONS["restore_long_lines"]),
        },
        {
            "problem_family": "delete_fill_blocks",
            "items": list(profile.get("forbidden_fill", [])),
            "allowed_actions": list(PATCH_FAMILY_ALLOWED_ACTIONS["delete_fill_blocks"]),
        },
        {
            "problem_family": "externalize_lines",
            "items": list(profile.get("abstract_narration", []))[:8],
            "allowed_actions": list(PATCH_FAMILY_ALLOWED_ACTIONS["externalize_lines"]),
        },
    ]


def _build_rewrite_patch_spec(profile: dict[str, object]) -> dict[str, object]:
    return {
        "scene_modes": list(profile.get("scene_modes", [])),
        "families": _patch_family_contracts_from_profile(profile),
        "reuse_original_lines": bool(profile.get("reusable_lines_present")),
    }


def _render_rewrite_patch_spec(patch_spec: dict[str, object]) -> str:
    return "```json\n" + json.dumps(patch_spec, ensure_ascii=False, indent=2) + "\n```"


def _patch_spec_family_contracts(patch_spec: dict[str, object]) -> dict[str, dict[str, object]]:
    contracts: dict[str, dict[str, object]] = {}
    for raw_family in patch_spec.get("families", []):
        if not isinstance(raw_family, dict):
            continue
        family = raw_family.get("problem_family")
        if not isinstance(family, str) or not family:
            continue
        items = raw_family.get("items", [])
        allowed_actions = raw_family.get("allowed_actions", [])
        contracts[family] = {
            "items": [item for item in items if isinstance(item, str)],
            "allowed_actions": [action for action in allowed_actions if isinstance(action, str)],
        }
    return contracts


def _render_numbered_draft(draft_text: str) -> str:
    lines = draft_text.splitlines()
    if not lines:
        return "1: "
    width = max(2, len(str(len(lines))))
    return "\n".join(f"{index:0{width}d}: {line}" for index, line in enumerate(lines, start=1))


def _split_dialogue_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped:
        return None
    separator = "：" if "：" in stripped else ":" if ":" in stripped else None
    if separator is None:
        return None
    label, body = stripped.split(separator, 1)
    label = label.strip()
    body = body.strip()
    normalized_label = label.lower()
    if not label or label in {"△", "♪", "【镜头】"} or normalized_label in {"action", "music", "camera"}:
        return None
    if re.fullmatch(r"(场\d+-\d+|scene-\d+(?:-\d+)?)", normalized_label):
        return None
    return label, body


def _extract_dialogue_label(line: str) -> str | None:
    parts = _split_dialogue_line(line)
    if parts is None:
        return None
    return parts[0]


def _line_is_dialogue_like(line: str) -> bool:
    return _extract_dialogue_label(line) is not None


def _line_has_abstract_summary(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if any(keyword in stripped for keyword in ABSTRACT_NARRATION_KEYWORDS):
        return True
    return any(pattern.search(stripped) for pattern in ABSTRACT_LINE_PATTERNS)


def _line_has_fill_signal(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    dialogue = _split_dialogue_line(stripped)
    body = dialogue[1] if dialogue else stripped
    if any(keyword in body for keyword in FILL_BLOCK_KEYWORDS):
        return True
    if dialogue is None and any(keyword in stripped for keyword in FILL_BLOCK_KEYWORDS):
        return True
    return False


def _label_is_obvious_name_weakening(label: str, known_names: list[str]) -> bool:
    normalized = label.strip()
    if len(normalized) < 2:
        return False
    if any(token in normalized for token in GENERIC_ROLE_TOKENS):
        return False
    for name in known_names:
        if normalized == name:
            continue
        if normalized in name and len(normalized) < len(name):
            return True
    return False


def _line_matches_long_line_contract(line_body: str, long_lines: list[str]) -> bool:
    stripped = line_body.strip()
    if not stripped:
        return False
    return any(stripped in long_line or long_line in stripped for long_line in long_lines)


def _line_matches_delete_fill_contract(line: str, *, reveal_scene: bool) -> bool:
    if _line_has_fill_signal(line):
        return True
    if reveal_scene and any(token in line for token in REVEAL_FILL_TOKENS):
        return True
    return False


def _find_patch_candidate_blocks(draft_text: str, patch_spec: dict[str, object]) -> list[dict[str, object]]:
    lines = draft_text.splitlines()
    if not lines:
        return []

    family_contracts = _patch_spec_family_contracts(patch_spec)
    restore_names = list(family_contracts.get("restore_names", {}).get("items", []))
    restore_long_lines = list(family_contracts.get("restore_long_lines", {}).get("items", []))
    delete_fill_blocks = list(family_contracts.get("delete_fill_blocks", {}).get("items", []))
    externalize_lines = list(family_contracts.get("externalize_lines", {}).get("items", []))
    scene_modes = set(patch_spec.get("scene_modes", []))
    active_families = {family for family, contract in family_contracts.items() if contract.get("items")}

    candidate_families_by_index: dict[int, set[str]] = {}
    for index, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        label = _extract_dialogue_label(line)
        if restore_names and label:
            if any(token in label for token in GENERIC_ROLE_TOKENS) and not any(name in label for name in restore_names):
                candidate_families_by_index.setdefault(index, set()).add("restore_names")
            elif _label_is_obvious_name_weakening(label, restore_names):
                candidate_families_by_index.setdefault(index, set()).add("restore_names")

        if delete_fill_blocks and _line_matches_delete_fill_contract(
            line,
            reveal_scene="reveal_scene" in scene_modes,
        ):
            candidate_families_by_index.setdefault(index, set()).add("delete_fill_blocks")

        if externalize_lines and _line_has_abstract_summary(line):
            candidate_families_by_index.setdefault(index, set()).add("externalize_lines")

        if restore_long_lines and _line_is_dialogue_like(line):
            _, line_body = _split_dialogue_line(line) or ("", "")
            if _line_matches_long_line_contract(line_body, restore_long_lines):
                candidate_families_by_index.setdefault(index, set()).add("restore_long_lines")
            elif "pressure_scene" in scene_modes and len(line_body.strip()) <= 26:
                candidate_families_by_index.setdefault(index, set()).add("restore_long_lines")

    if not candidate_families_by_index:
        if not active_families:
            return []
        return [
            {
                "block_id": "B01",
                "start_line": 1,
                "end_line": len(lines),
                "problem_families": sorted(active_families),
            }
        ]

    expanded_families_by_index: dict[int, set[str]] = {}
    max_index = len(lines)
    for index, families in candidate_families_by_index.items():
        start = max(1, index - 1)
        end = min(max_index, index + 1)
        for expanded_index in range(start, end + 1):
            expanded_families_by_index.setdefault(expanded_index, set()).update(families)

    sorted_indexes = sorted(expanded_families_by_index)
    blocks: list[dict[str, object]] = []
    start = sorted_indexes[0]
    end = sorted_indexes[0]
    block_families = set(expanded_families_by_index[start])
    for index in sorted_indexes[1:]:
        if index <= end + 1:
            end = index
            block_families.update(expanded_families_by_index[index])
            continue
        blocks.append(
            {
                "block_id": f"B{len(blocks) + 1:02d}",
                "start_line": start,
                "end_line": end,
                "problem_families": sorted(block_families),
            }
        )
        start = end = index
        block_families = set(expanded_families_by_index[index])
    blocks.append(
        {
            "block_id": f"B{len(blocks) + 1:02d}",
            "start_line": start,
            "end_line": end,
            "problem_families": sorted(block_families),
        }
    )
    return blocks


def _candidate_scope_is_whole_draft(
    draft_text: str,
    candidate_blocks: list[dict[str, object]],
) -> bool:
    lines = draft_text.splitlines()
    if len(candidate_blocks) != 1 or len(lines) < WHOLE_DRAFT_PATCH_SKIP_MIN_LINES:
        return False
    block = candidate_blocks[0]
    return int(block.get("start_line", 0)) == 1 and int(block.get("end_line", 0)) == len(lines)


def _candidate_blocks_total_span(candidate_blocks: list[dict[str, object]]) -> int:
    total = 0
    for block in candidate_blocks:
        start = int(block.get("start_line", 0))
        end = int(block.get("end_line", 0))
        if start > 0 and end >= start:
            total += end - start + 1
    return total


def _candidate_family_priority(candidate_families: list[str]) -> tuple[int, str]:
    highest = max((PATCH_FAMILY_PRIORITY.get(family, 0) for family in candidate_families), default=0)
    if highest >= 3:
        return highest, "high"
    if highest == 2:
        return highest, "medium"
    if highest == 1:
        return highest, "low"
    return highest, "none"


def _should_run_fidelity_patch(
    profile: dict[str, object],
    draft_text: str,
    candidate_blocks: list[dict[str, object]],
    candidate_families: list[str],
) -> tuple[bool, str]:
    if not candidate_blocks:
        return False, "no_candidate_blocks"
    if _candidate_scope_is_whole_draft(draft_text, candidate_blocks):
        return False, "whole_draft_fallback"

    family_rank, family_priority = _candidate_family_priority(candidate_families)
    if family_rank <= 1:
        return False, f"family_priority={family_priority}"

    block_count = len(candidate_blocks)
    if block_count > PATCH_FIDELITY_MAX_BLOCKS:
        return False, f"candidate_blocks={block_count}>max_blocks={PATCH_FIDELITY_MAX_BLOCKS}"

    total_span = _candidate_blocks_total_span(candidate_blocks)
    if total_span > PATCH_FIDELITY_MAX_TOTAL_SPAN_LINES:
        return False, f"candidate_span={total_span}>max_span={PATCH_FIDELITY_MAX_TOTAL_SPAN_LINES}"

    excerpt_tier = str(profile.get("excerpt_tier", "baseline"))
    if excerpt_tier != "strong_scene" and family_rank < 3:
        return False, f"excerpt_tier={excerpt_tier},family_priority={family_priority}"

    return True, "run"


def _render_numbered_candidate_blocks(draft_text: str, candidate_blocks: list[dict[str, object]]) -> str:
    if not candidate_blocks:
        return _render_numbered_draft(draft_text)

    lines = draft_text.splitlines()
    width = max(2, len(str(len(lines))))
    blocks: list[str] = []
    for candidate_block in candidate_blocks:
        block_id = str(candidate_block["block_id"])
        start = int(candidate_block["start_line"])
        end = int(candidate_block["end_line"])
        families = list(candidate_block.get("problem_families", []))
        family_text = f" | families: {', '.join(families)}" if families else ""
        block_lines = [f"{line_no:0{width}d}: {lines[line_no - 1]}" for line_no in range(start, end + 1)]
        blocks.extend(
            [
                f"[Block {block_id} | lines {start}-{end}{family_text}]",
                *block_lines,
                "",
            ]
        )
    return "\n".join(blocks).rstrip()


def _extract_json_payload(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty JSON payload")
    match = JSON_FENCE_RE.search(stripped)
    payload = match.group(1).strip() if match else stripped
    return json.loads(payload)


def _normalize_patch_operations(payload: Any, candidate_blocks: list[dict[str, object]]) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        operations = payload.get("operations", [])
    elif isinstance(payload, list):
        operations = payload
    else:
        raise ValueError("patch payload must be a JSON object or list")

    if not isinstance(operations, list):
        raise ValueError("patch operations must be a list")

    block_lookup = {
        str(block["block_id"]): {
            "start_line": int(block["start_line"]),
            "end_line": int(block["end_line"]),
            "problem_families": set(block.get("problem_families", [])),
        }
        for block in candidate_blocks
    }
    normalized: list[dict[str, Any]] = []
    for raw_op in operations:
        if not isinstance(raw_op, dict):
            raise ValueError("each patch operation must be an object")
        block_id = raw_op.get("block_id")
        if not isinstance(block_id, str) or block_id not in block_lookup:
            raise ValueError(f"unknown patch block_id: {block_id!r}")
        problem_family = raw_op.get("problem_family")
        if not isinstance(problem_family, str) or problem_family not in PATCH_FAMILY_ALLOWED_ACTIONS:
            raise ValueError(f"unsupported patch problem_family: {problem_family!r}")
        action = raw_op.get("action")
        start_line = raw_op.get("start_line")
        end_line = raw_op.get("end_line", start_line)
        if action not in PATCH_FAMILY_ALLOWED_ACTIONS[problem_family]:
            raise ValueError(f"action {action!r} is not allowed for family {problem_family!r}")
        if not isinstance(start_line, int) or not isinstance(end_line, int):
            raise ValueError("patch line numbers must be integers")
        if start_line < 1 or end_line < start_line:
            raise ValueError("patch line range is invalid")
        block = block_lookup[block_id]
        if problem_family not in block["problem_families"]:
            raise ValueError(f"family {problem_family!r} is not allowed for block {block_id!r}")
        if start_line < block["start_line"] or end_line > block["end_line"]:
            raise ValueError(f"patch line range exceeds block {block_id!r}")
        content = raw_op.get("content", "")
        if action == "replace" and not isinstance(content, str):
            raise ValueError("replace patch content must be a string")
        reason = raw_op.get("reason", "")
        if reason is not None and not isinstance(reason, str):
            raise ValueError("patch reason must be a string")
        normalized.append(
            {
                "block_id": block_id,
                "problem_family": problem_family,
                "action": action,
                "start_line": start_line,
                "end_line": end_line,
                "content": content,
                "reason": reason,
            }
        )
    return normalized


def _apply_patch_operations_to_text(draft_text: str, operations: list[dict[str, Any]]) -> str:
    lines = draft_text.splitlines()
    trailing_newline = draft_text.endswith("\n")

    sorted_ops = sorted(operations, key=lambda item: (item["start_line"], item["end_line"]))
    previous_end = 0
    for op in sorted_ops:
        if op["start_line"] <= previous_end:
            raise ValueError("patch operations overlap")
        if op["end_line"] > max(len(lines), 1 if not lines else len(lines)):
            raise ValueError("patch operation exceeds draft length")
        previous_end = op["end_line"]

    for op in reversed(sorted_ops):
        start_index = op["start_line"] - 1
        end_index = op["end_line"]
        replacement_lines = [] if op["action"] == "delete" else op["content"].splitlines()
        lines[start_index:end_index] = replacement_lines

    rewritten = "\n".join(lines)
    if rewritten or trailing_newline:
        rewritten += "\n"
    return rewritten


def _build_minimal_rule_pack(
    profile: dict[str, object],
    episode_facts: dict[str, object],
    *,
    include_adjacent_boundary: bool,
) -> str:
    excerpt_tier = str(profile.get("excerpt_tier", "baseline"))
    function_signals = episode_facts.get("function_signals")
    if not isinstance(function_signals, dict):
        function_signals = {}
    opening_function = str(function_signals.get("opening_function", "")).strip() or "setup"
    middle_functions = [
        str(item).strip()
        for item in function_signals.get("middle_functions", [])
        if str(item).strip()
    ]
    ending_function = str(episode_facts.get("ending_function", "")).strip() or "confrontation_pending"
    irreversibility_level = str(episode_facts.get("irreversibility_level", "")).strip() or "medium"
    strong_function_tags = [
        str(item).strip()
        for item in function_signals.get("strong_function_tags", [])
        if str(item).strip()
    ]
    bullets = [
        "- `function_signals` 决定场次功能；必须完成 opening / middle / ending / irreversibility，不得只顾场数。",
        "- 一场只主打一项功能；若一场同时承担两个强功能，就继续拆场，不要糊成总结场。",
        f"- 当前集功能：opening={opening_function}；middle={', '.join(middle_functions) or 'escalation'}；ending={ending_function}；irreversibility={irreversibility_level}。",
        "- `event_anchors` 定顺序；已发生事件不得后拖。",
        "- 默认禁新事件、禁新流程、禁新职业说明、禁新后台调度、禁新承接对白。",
        "- 角色只按当场已公开信息行动；模型知道不等于角色知道。",
        "- `voice-anchor.md` 只看气质和禁区，不复用例句。",
        "- 每场至少保住 3 个 `△`；别把同一轮入场、相认或施压过早切场。",
        "- 非终场最后一个 `△` 必须带新压力、未完动作或下一拍将发生的变化，别停在静态结果或环境余波。",
        "- 禁新增第一人称叙述；`角色（os）：` 也不能写成“我……”式内心旁白。",
        "- `OS` 只在非写不可时用来补最后半步心理落点；能用动作、对白、停顿顶出来，就别补解释性 `OS`。",
    ]
    if excerpt_tier == "strong_scene":
        bullets.insert(
            1,
            "- `strong_scene`：先读 `scene_modes` / `must_keep_names` / `must_keep_long_lines` / `abstract_narration` / `forbidden_fill`；有 `reusable_source_lines` 先保原句。",
        )
    elif excerpt_tier == "low_risk":
        bullets.insert(
            1,
            "- `low_risk`：先读 `reusable_source_lines` / `must_keep_names` / `forbidden_fill`；贴原句和句意写，别补桥接句。",
        )
    else:
        bullets.insert(
            1,
            "- `baseline`：先读 `event_anchors` / `must_keep_names` / `forbidden_fill`；贴锚点和句意写，别补桥接句。",
        )
    if include_adjacent_boundary:
        bullets.append("- 承接上一集最多 1-2 镜头，随后立刻进入新增推进。")
    if strong_function_tags:
        bullets.append("- 首集/强冲突集必须补齐适用强功能：" + "、".join(strong_function_tags) + "；缺哪项就补哪项，不要把多个强功能并成一个总结场。")
    if opening_function == "intrusion":
        bullets.append("- `opening=intrusion`：首场前两三个 `△` 直接入拦截、误认、撞上或被迫停下；别先写城市夜色、穿着、人设或职业背景总述。")
    if "confrontation" in middle_functions:
        bullets.append("- `middle=confrontation`：别只靠“冷冷看着”“平静开口”撑场；至少给一个硬反抗动作、阻挡动作或被迫顶回去的动作。")
    if ending_function == "locked_in":
        bullets.append("- `ending_function=locked_in`：终段必须让角色已被卷入或锁进局面，不得只写“即将到达”。")
        bullets.append("- `ending_function=locked_in`：优先落车锁、门锁、封门、导航、驶离主路这类物理约束；默认别用 `OS` 总结局面。")
    elif ending_function == "reveal_pending":
        bullets.append("- `ending_function=reveal_pending`：终段要把揭露逼到眼前，不得回退成漫长等待。")
    elif ending_function == "reversal_triggered":
        bullets.append("- `ending_function=reversal_triggered`：终段必须让翻盘已启动，而不是只停在预感。")
    elif ending_function == "confrontation_pending":
        bullets.append("- `ending_function=confrontation_pending`：终段要把对抗顶到下一拍，别停在结果已落地。")
    if irreversibility_level == "hard":
        bullets.append("- `irreversibility=hard`：结尾要落不可逆结果，不能只写去向暗示。")

    scene_modes = set(profile.get("scene_modes", []))
    if profile.get("must_keep_names"):
        bullets.append("- `must_keep_names` 非空时，人名别退化成泛称。")
    if profile.get("must_keep_long_lines"):
        bullets.append("- `must_keep_long_lines` 非空时，至少保住 1 句长句递进。")
    if excerpt_tier == "strong_scene":
        bullets.append("- `△` 优先落手、眼、肩背、站位、道具或声场变化，别只写“冷静”“漠然”“惊艳”“死寂”这类抽象判断。")
        bullets.append("- 未公开的关系词、身份词、真名别抢跑；没到那一步时别替角色先叫“姐姐”“亲生女儿”。")
        bullets.append("- `event_anchors` 里的关系称谓若还没确认，只保句意和施压方向，别逐字照抄成抢跑称呼。")
    if "result_confirmation_scene" in scene_modes:
        bullets.append("- `result_confirmation_scene`：结果确认拍别压成单场总结；整集至少 2 场、至少 2 个 `【镜头】`。")
        bullets.append("- `result_confirmation_scene`：第一场先落结果与第一反应，后续场再写压迫升级、去留决定或关系断裂。")
    if "pressure_scene" in scene_modes:
        bullets.append("- `pressure_scene`：别把整轮施压拆成模板短句。")
        bullets.append("- `pressure_scene`：非终场结尾要让压迫继续往下一拍顶上来，优先写拦门、逼近、压话、夺物或下一句更重的话已经顶到嘴边。")
        bullets.append("- `pressure_scene`：`空气更静了`、`众人僵住`、`她看着他` 这类结果态不算 hook。")
    if "reveal_scene" in scene_modes:
        bullets.append("- `reveal_scene`：一进揭露拍点就写揭露本体，别补寒暄/附和/后台铺垫。")
        bullets.append("- 若 `event_anchors` 没给出幕后入场、幕布切换、后台脚步，就别自己补“从后台走出”“黑幕一分”这类过门。")
    if profile.get("abstract_narration"):
        bullets.append("- `abstract_narration` 非空时，把对应句意外化成可拍反应。")
        bullets.append("- 别保留“眼里是……情绪”“眼底满是……”“盛满了……”这类总结句。")
    if profile.get("forbidden_fill"):
        bullets.append("- `forbidden_fill` 命中后，删掉仍成立的内容必须删。")

    return "运行时最小规则包：\n" + "\n".join(bullets)


def _build_minimal_self_check(profile: dict[str, object], episode_facts: dict[str, object]) -> str:
    excerpt_tier = str(profile.get("excerpt_tier", "baseline"))
    scene_modes = set(profile.get("scene_modes", []))
    function_signals = episode_facts.get("function_signals")
    if not isinstance(function_signals, dict):
        function_signals = {}
    opening_function = str(function_signals.get("opening_function", "")).strip() or "setup"
    middle_functions = [
        str(item).strip()
        for item in function_signals.get("middle_functions", [])
        if str(item).strip()
    ]
    ending_function = str(episode_facts.get("ending_function", "")).strip() or "confrontation_pending"
    irreversibility_level = str(episode_facts.get("irreversibility_level", "")).strip() or "medium"
    strong_function_tags = [
        str(item).strip()
        for item in function_signals.get("strong_function_tags", [])
        if str(item).strip()
    ]
    bullets = [
        "- beats：`【信息】/【关系】/【动作】/【钩子】` 一项不缺。",
        f"- 功能：opening={opening_function}、middle={', '.join(middle_functions) or 'escalation'}、ending={ending_function}、irreversibility={irreversibility_level} 都已完成。",
        "- 顺序：`event_anchors` 不后拖；不越过 `must-not-add / must-not-jump`。",
        "- 壳层：`△ / ♪ / 【镜头】： / 角色： / 角色（os）：` 各自独行。",
        "- 场次：整集至少 2 场；一场只主打一项功能；每场 >= 3 个 `△`；非终场最后一个 `△` 留新增推进。",
        "- 叙述：禁新增第一人称 `OS` / “我……”旁白；能不用 `OS` 就不用。",
        "- 节奏：别把整场 `△` 都压成一种短句模板；场内至少留一处 2-3 句递进，其余按动作需要变化。",
    ]
    if strong_function_tags:
        bullets.append("- 强功能：" + "、".join(strong_function_tags) + " 已按需补齐，没有把多个强功能糊成总结场。")
    if opening_function == "intrusion":
        bullets.append("- 开场：首场没先写环境/穿着/气质总述；前两三个 `△` 已直接撞上异常或拦截。")
    if "confrontation" in middle_functions:
        bullets.append("- 对抗：至少有一个手上、脚下、门边、座位边的硬反抗/阻挡动作，不只剩态度词。")
    if ending_function == "locked_in":
        bullets.append("- 锁局：终场已落物理约束或方向不可逆；默认 `OS=0`，除非 source 非写不可。")

    if excerpt_tier in {"low_risk", "strong_scene"} and profile.get("reusable_lines_present"):
        bullets.append("- 原句：有 `reusable_source_lines` 就优先保；否则贴着 `event_anchors` 句意写。")
    else:
        bullets.append("- 原句：贴着 `event_anchors` 句意写。")

    if profile.get("must_keep_long_lines"):
        bullets.append("- 长句：`must_keep_long_lines` 至少保住 1 句长句递进。")

    if excerpt_tier == "strong_scene":
        strong_checks = ["`△` 多落手、眼、站位、道具、声场，少写抽象判断词", "别先叫“姐姐”“亲生女儿”"]
        if "result_confirmation_scene" in scene_modes:
            strong_checks.append("结果确认拍别压成单场总结；整集 >= 2 场、>= 2 个 `【镜头】`")
        if "pressure_scene" in scene_modes:
            strong_checks.append("施压：非终场结尾要落到拦门、逼近、压话、夺物；这类结果态不算 hook")
        if "reveal_scene" in scene_modes:
            strong_checks.append("揭露：幕后入场或幕布过门别自己补")
        bullets.append("- 强场：" + "；".join(strong_checks) + "。")

    if profile.get("abstract_narration") or profile.get("forbidden_fill"):
        ending_checks: list[str] = []
        if profile.get("abstract_narration"):
            ending_checks.append("`abstract_narration` 要外化")
        if profile.get("forbidden_fill"):
            ending_checks.append("新增承接/流程/后台删后仍成立就删")
        bullets.append("- 外化：" + "；".join(ending_checks) + "。")

    return "交稿前最小自检：\n" + "\n".join(bullets)


def _build_writer_prompt(
    batch_id: str,
    episode: str,
    brief_path: Path,
    *,
    batch_context_path: Path,
    source_excerpt_path: Path,
    syntax_first: bool = False,
) -> str:
    draft_target = f"drafts/episodes/{episode}.md"
    brief_rel = _rel(brief_path)
    sample_rel = _rel(PASSING_SAMPLE)
    batch_context_rel = _rel(_batch_context_runtime_path(batch_context_path))
    source_excerpt_rel = _rel(_source_excerpt_runtime_path(source_excerpt_path))
    episode_num = str(int(episode.split("-")[1]))
    context_paths = _adjacent_context_paths(episode)
    episode_facts = _batch_context_episode_facts(batch_context_path, episode)
    must_keep_beats_block = _render_episode_beats(episode_facts)
    function_goals_block = _render_episode_function_goals(episode_facts)
    scene_function_plan_block = _render_scene_function_plan(episode, episode_facts)
    rule_profile = _episode_rule_profile(source_excerpt_path)
    rule_pack = _build_minimal_rule_pack(
        rule_profile,
        episode_facts,
        include_adjacent_boundary=bool(context_paths),
    )
    minimal_self_check = _build_minimal_self_check(rule_profile, episode_facts)
    contract_style_reference_block = _build_contract_style_reference_block()
    rule_priority = _build_rule_priority_block()
    reads_block = _build_required_reads_block(
        batch_context_rel,
        source_excerpt_rel,
        extra_paths=[_rel(path) for _note, path in context_paths],
    )
    syntax_guidance = (
        "语法壳优先：先把语法壳和排版写对，先对齐壳层和排版，再考虑剧情润色。\n"
        "- 不确定剧情细节时，宁可保守，不要写成 Markdown 场记。\n"
    ) if syntax_first else ""
    lint_feedback = os.environ.get(LINT_FEEDBACK_ENV, "").strip()
    lint_feedback_block = (
        "本次是 smoke lint 回修重写。上一版未过的原因如下：\n"
        f"{lint_feedback}\n"
        "回修要求：\n"
        "- 只修本次 lint 命中的问题，不改 source.map 事实，不重排整集结构。\n"
        "- 若命中 `too_many_hookless_scenes`：把非终场的最后一个 `△` 改成“立即会发生的新压力 / 未完成动作”，不要停在环境余波。\n"
        "- 回修优先顺序：先修场尾推进，再修壳层和多余台词。\n"
    ) if lint_feedback else ""

    return f"""任务目标：
- 立即创建并写完 `{draft_target}`。
- 你只扮演 Writer，不做 verify、promote、record。
- 完成标准：`{draft_target}` 已存在，且当前集全部 beats 已完成。

{reads_block}

权威输入：
- `{brief_rel}` 决定当前集任务与 beats。
- `harness/project/source.map.md` 决定 source 顺序、must-not-add、must-not-jump 边界。
- `run.manifest.md` 里的 `current batch brief` 只用于运行时定位；若它滞后或冲突，忽略它。
当前 batch：{batch_id}
当前 episode：{episode}

{contract_style_reference_block}

{rule_priority}

输出壳与场次规则：
- 只写 `{draft_target}`；不改 `episodes/`、`harness/project/state/`、`harness/project/source.map.md`、`harness/project/run.manifest.md`；不 promote、不写 state、不越 `must-not-add / must-not-jump`。
- 信息不足时保守贴合 batch brief 与 source.map，不擅自补设定。
- 先把 Harness V2 语法壳写正确；写完即停，并确认 `{draft_target}` 已存在。
- 直接生成 `{episode}` 完整草稿，保持 original_fidelity + light 对话改编力度。
- 语法壳：`场{episode_num}-1：` / `场{episode_num}-N：`、`日/夜`、`外/内`、`场景：`、`♪：`、`△：`、`【镜头】：`、`角色（os）：`。
- 首场编号固定为 `{episode_num}`；整集至少 2 场；必须完成当前集全部功能信号；一场只主打一项功能，若同时承担两个强功能就继续拆场。
- 排版参考 `style_digest` 与 `{sample_rel}`。

当前集 beats 清单：
{must_keep_beats_block}
- 上面这些 beats 必须全部完成；`【信息】/【关系】/【动作】/【钩子】` 任何一类都不能缺。

当前集功能目标：
{function_goals_block}
- 场次数由功能完成决定；不要为了压场数省略功能槽位。

场次功能拆解：
{scene_function_plan_block}
- 先按上面的 `scene_function_plan` 执行；若某场还承担第二个强功能，就继续拆场，不要反向合并。

{rule_pack}
{minimal_self_check}
{lint_feedback_block}
{syntax_guidance}
"""


def _build_sequential_batch_writer_prompt(
    batch_id: str,
    episodes: list[str],
    brief_path: Path,
    *,
    batch_context_path: Path,
    source_excerpt_paths: dict[str, Path],
    syntax_first: bool = False,
) -> str:
    brief_rel = _rel(brief_path)
    sample_rel = _rel(PASSING_SAMPLE)
    batch_context_rel = _rel(_batch_context_runtime_path(batch_context_path))
    first_episode = episodes[0]
    first_context_paths = _adjacent_context_paths(first_episode)
    profiles = {
        episode: _episode_rule_profile(source_excerpt_paths[episode])
        for episode in episodes
    }
    reads_block = _build_required_reads_block(
        batch_context_rel,
        extra_paths=[_rel(path) for _note, path in first_context_paths],
    )
    contract_style_reference_block = _build_contract_style_reference_block()
    rule_priority = _build_rule_priority_block()
    targets_block = "\n".join(
        (
            f"- {episode} -> drafts/episodes/{episode}.md\n"
            f"  - excerpt: {_rel(_source_excerpt_runtime_path(source_excerpt_paths[episode]))}\n"
            f"  - signals: {', '.join(_rule_profile_signals(profiles[episode]) + _episode_function_signal_tokens(_batch_context_episode_facts(batch_context_path, episode))) or 'baseline_only'}\n"
            f"  - 场次：首场 `场{int(episode.split('-')[1])}-1`；整集至少 2 场；一场一功能\n"
            f"  - beats：{'; '.join(_batch_context_episode_facts(batch_context_path, episode).get('must_keep_beats', [])) or '以 batch brief 当前集任务为准'}；`【信息】/【关系】/【动作】/【钩子】` 不能缺\n"
            f"  - 功能：opening={str((_batch_context_episode_facts(batch_context_path, episode).get('function_signals') or {}).get('opening_function', 'setup'))}; "
            f"middle={', '.join(((_batch_context_episode_facts(batch_context_path, episode).get('function_signals') or {}).get('middle_functions') or ['escalation']))}; "
            f"ending={_batch_context_episode_facts(batch_context_path, episode).get('ending_function', 'confrontation_pending')}; "
            f"irreversibility={_batch_context_episode_facts(batch_context_path, episode).get('irreversibility_level', 'medium')}\n"
            f"  - scene_function_plan:\n{_render_scene_function_plan(episode, _batch_context_episode_facts(batch_context_path, episode), indent='    ')}"
        )
        for episode in episodes
    )
    syntax_guidance = (
        "语法壳优先：先把语法壳和排版写对，先对齐壳层和排版，再考虑剧情润色。\n"
        "- 不确定剧情细节时，宁可保守，不要写成 Markdown 场记。\n"
    ) if syntax_first else ""
    sequence_runtime_lines = [
        "批次顺序写作最小规则：",
        "- 每集只读自己的 excerpt 与 function_signals，并完成自己在 batch brief / batch_facts 里的全部 beats；压场数不能成为缺 beat 的理由。",
        "- 一场只主打一项功能；opening / middle / ending / irreversibility 缺任何一项都不算完成。",
        "- `event_anchors` 定顺序；`must_keep_names`、`forbidden_fill` 守边界；有 `reusable_source_lines` 就先保原句。",
        "- 每场至少 3 个 `△`；别把同一轮入场、相认或施压过早切成两场。",
        "- 整集至少 2 场；若一场已经承担两个强功能，就继续拆场。",
        "- 非终场最后一个 `△` 必须带服务 beats 的新增推进，别停在静态结果。",
        "- 禁新增第一人称叙述；`角色（os）：` 也不能写成“我……”式内心旁白。",
        "- 上一集只给边界；承接最多 1-2 个镜头。模型知道不等于角色知道；身份、关系、真名只按当场已公开信息写。",
        "- `voice-anchor` 只看气质与禁区，优先级低于当前集 beats 和 source 边界。",
    ]
    if any("result_confirmation_scene" in set(profiles[episode].get("scene_modes", [])) for episode in episodes):
        sequence_runtime_lines.append("- 命中 `result_confirmation_scene` 的集数：整集至少 2 场、至少 2 个 `【镜头】`；结果确认与后续压迫/去留要分场承载。")
    if any(
        "hook" in ((_batch_context_episode_facts(batch_context_path, episode).get("function_signals") or {}).get("strong_function_tags") or [])
        for episode in episodes
    ):
        sequence_runtime_lines.append("- 命中强钩子集数：终段必须把下一拍要炸的压力顶出来，不得停在总结态。")
    sequence_runtime_pack = "\n".join(sequence_runtime_lines)
    return f"""任务：立即在当前工作区按顺序创建并写完以下草稿文件。完成条件：下面列出的每个目标文件都存在，且每集的全部 beats 已完成。不要输出角色确认，不要索要更多输入，不要只总结规则；在所有目标文件真正写出来之前，不得停止。
你现在只扮演 Harness V2 的 Writer 角色，不扮演 Controller、Verifier 或 Recorder。

{reads_block}

权威输入：
- `{brief_rel}` 决定每集任务与 beats。
- `harness/project/source.map.md` 决定 source 顺序、must-not-add、must-not-jump 边界。
- `harness/project/run.manifest.md` 的 `current batch brief` 只用于运行时定位；若冲突则忽略。
本次只处理 batch：{batch_id}

{contract_style_reference_block}

{rule_priority}

目标文件：
{targets_block}

顺序写作要求：
1. 严格按上面列出的 episode 顺序逐个完成，禁止跳集、并集或提前写后面的 episode。
2. 每完成一集后，先确认对应草稿文件已写入磁盘，再开始下一集。
3. 写每一集前，先重新读取该集对应的 `source excerpt`，并从中建立当前集的内部 `must_keep` 清单。
4. 写下一集之前，只重新读取刚写完的上一集草稿和必要的相邻集上下文，再决定承接边界。
5. 整个批次里优先保护相邻集之间的信息增量和关系渐进，不要为了提速把多集写成同一种试探节奏。

{sequence_runtime_pack}

硬约束：
- 只能写 `drafts/episodes/EP-XX.md`
- 不得 promote
- 不得写 state
- 不得修改 `episodes/`
- 不得修改 `harness/project/run.manifest.md`
- 不得修改 `harness/project/source.map.md`
- 不得修改 `harness/project/state/`
- 不得修改 locks、tests、docs 或其他无关文件
- 不得跨越 source.map 里的 must-not-add / must-not-jump
- 全部目标草稿都写完后立刻停止，不要继续做 verify、promote、record

批次级最小自检：
- 每一集单独成稿，不得把两集合并到同一个文件。
- 每一集的 `【信息】/【关系】/【动作】/【钩子】` beats 都要完成，不能为了压场数缺项。
- 若 source excerpt 已发生硬事件，而正文还停在“等待 / 前夜 / 即将揭晓”，说明你把事件往后拖了。
- 每集至少 2 场，非终场结尾必须留下服务 beats 的新增推进。
- `角色（os）：` 不得写成新增第一人称“我……”旁白。

{syntax_guidance}
"""


def _build_fidelity_rewrite_prompt(
    batch_id: str,
    episode: str,
    brief_path: Path,
    *,
    source_excerpt_path: Path,
    draft_text: str,
    patch_spec: dict[str, object] | None = None,
    candidate_blocks: list[dict[str, object]] | None = None,
) -> str:
    source_excerpt_rel = _rel(_source_excerpt_runtime_path(source_excerpt_path))
    profile = _episode_rule_profile(source_excerpt_path)
    patch_spec = patch_spec or _build_rewrite_patch_spec(profile)
    patch_spec_block = _render_rewrite_patch_spec(patch_spec)
    candidate_blocks = candidate_blocks or _find_patch_candidate_blocks(draft_text, patch_spec)
    numbered_candidates = _render_numbered_candidate_blocks(draft_text, candidate_blocks)
    candidate_scope_note = (
        "下面只给出本地命中的候选句段；未出现的行默认保持原样，不允许顺手改动。"
        if candidate_blocks and not (len(candidate_blocks) == 1 and int(candidate_blocks[0]["start_line"]) == 1 and int(candidate_blocks[0]["end_line"]) == max(1, len(draft_text.splitlines())))
        else "当前未能可靠缩窄候选句段，暂时回退为整份已编号 draft；仍然只允许围绕 patch spec 命中的问题修改。"
    )
    return f"""任务：为 {episode} 输出一份局部 source-fidelity patch JSON。

你不是整集重写，也不是直接返回整份剧本。你只做“命中问题的局部修句计划”：
- 删除命中的无依据新增
- 恢复命中的原句、人名、称谓和长句递进
- 把命中的抽象叙述外化成可拍反应
- 未命中的段落保持原样，不要顺手整集重写

先读取：
- {source_excerpt_rel}

你当前可修改的对象只有下面这些带全局行号的“候选句段”（也就是已编号 draft 中命中的局部块）：
```text
{numbered_candidates}
```
{candidate_scope_note}

本轮 patch spec（只允许围绕这些命中项修改）：
{patch_spec_block}

输出要求：
- 只输出 JSON，不要解释，不要 markdown，不要额外文本
- JSON 结构固定为：
{{
  "operations": [
    {{
      "block_id": "B01",
      "problem_family": "restore_names",
      "start_line": 12,
      "end_line": 12,
      "action": "replace",
      "content": "替换后的新行，可包含\\n多行",
      "reason": "restore_names"
    }},
    {{
      "block_id": "B01",
      "problem_family": "delete_fill_blocks",
      "start_line": 18,
      "end_line": 19,
      "action": "delete",
      "reason": "delete_fill_blocks"
    }}
  ]
}}
- `block_id` 必须引用上面候选块里真实存在的 block id
- `problem_family` 只能使用 patch spec 里已有的 family，不得自创
- `start_line` / `end_line` 必须引用上面编号 draft 中真实存在的行号
- `action` 只能使用该 family 允许的动作：
  - `restore_names` -> `replace`
  - `restore_long_lines` -> `replace`
  - `delete_fill_blocks` -> `delete`
  - `externalize_lines` -> `replace`
- `replace` 只能改命中的行块；`delete` 只能删命中的填充/多余块
- 不允许新增新事件、新场面、新桥接句、新后台流程
- 若无必要修改，返回 `{{"operations":[]}}`

局部 patch 规则：
1. `reuse_original_lines=true` 时，优先恢复 source 已给出的原句，不要把它压成更短更硬的模板短句。
2. `problem_family=restore_names` 时，只处理人名/称谓恢复，不要顺手改剧情。
3. `problem_family=restore_long_lines` 时，只恢复被压扁的长句递进，不要扩成新回合。
4. `problem_family=delete_fill_blocks` 时，只删除填充/多余块，不要改写成另一种新填充。
5. `problem_family=externalize_lines` 时，只把抽象总结句改写成可拍反应；不要继续保留“彻底打醒了所有人”“现场恢复平静”“光芒万丈”“只剩敬畏”这类总结句。
6. 若 `scene_modes` 含 `reveal_scene`，不得保留揭露前额外铺垫、寒暄、场面话。
7. 若 `scene_modes` 含 `pressure_scene`，优先删掉模板短句回合，恢复原文长压迫句。
8. 若当前行块里还留着“眼里是……激动和心疼”“眼底满是……”“盛满了……情绪”这类句式，必须改成可拍反应。

只返回局部 patch JSON。
"""


def _resolve_cli_executable(cli: str) -> str | None:
    names = (cli,)
    if os.name == "nt":
        names = (f"{cli}.cmd", f"{cli}.exe", f"{cli}.bat", cli)

    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    return None


def _resolve_llm_cli() -> tuple[str, str] | None:
    requested = os.environ.get(LLM_CLI_ENV, "").strip().lower()
    if requested and requested not in SUPPORTED_LLM_CLIS:
        raise ValueError(
            f"{LLM_CLI_ENV} must be one of: {', '.join(SUPPORTED_LLM_CLIS)} (got: {requested})"
        )

    candidates = [requested] if requested else []
    candidates.extend(cli for cli in SUPPORTED_LLM_CLIS if cli not in candidates)

    for cli in candidates:
        executable = _resolve_cli_executable(cli)
        if executable:
            return cli, executable
    return None


def _build_llm_invocation(cli: str, executable: str, prompt: str) -> tuple[list[str], str | None]:
    if cli == "codex":
        return (
            [executable, "exec", "--dangerously-bypass-approvals-and-sandbox", "-C", str(ROOT), "-"],
            prompt,
        )
    if cli == "qwen":
        return [executable, "-p", prompt, "-y"], None
    if cli == "claude":
        return [executable, "-p", "--dangerously-skip-permissions", prompt], None
    raise ValueError(f"Unsupported LLM CLI: {cli}")


def _emit_completed_output(result: subprocess.CompletedProcess[str] | object) -> None:
    stdout = getattr(result, "stdout", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    if stdout:
        print(stdout, end="" if stdout.endswith(("\n", "\r")) else "\n")
    if stderr:
        print(stderr, end="" if stderr.endswith(("\n", "\r")) else "\n", file=sys.stderr)


def _prompt_text_from_invocation(command: list[str], stdin_text: str | None) -> str | None:
    if stdin_text is not None:
        return stdin_text
    for index, arg in enumerate(command):
        if arg == "-p" and index + 1 < len(command):
            return command[index + 1]
    return None


def _prompt_dump_slug(context_label: str | None, attempt: int) -> str:
    base = context_label or "llm_request"
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._-") or "llm_request"
    return f"{slug}.attempt{attempt}"


def _maybe_dump_llm_prompt(
    command: list[str],
    *,
    stdin_text: str | None,
    context_label: str | None,
    attempt: int,
) -> Path | None:
    dump_root = os.environ.get(PROMPT_DUMP_DIR_ENV, "").strip()
    if not dump_root:
        return None
    prompt_text = _prompt_text_from_invocation(command, stdin_text)
    if prompt_text is None:
        return None
    dump_dir = Path(dump_root)
    dump_dir.mkdir(parents=True, exist_ok=True)
    global _PROMPT_DUMP_COUNTER
    _PROMPT_DUMP_COUNTER += 1
    dump_path = dump_dir / f"{_PROMPT_DUMP_COUNTER:03d}_{_prompt_dump_slug(context_label, attempt)}.txt"
    dump_path.write_text(prompt_text, encoding="utf-8")
    return dump_path


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return
    process.kill()


def _run_llm_subprocess(
    command: list[str],
    *,
    stdin_text: str | None = None,
    timeout_seconds: int | None = None,
) -> tuple[int, str, str]:
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_llm_subprocess_env(),
    )
    try:
        stdout, stderr = process.communicate(input=stdin_text, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        _terminate_process_tree(process)
        stdout, stderr = process.communicate()
        return LLM_TIMEOUT_RETURNCODE, stdout, stderr
    return process.returncode, stdout, stderr


def _is_transient_llm_failure(result: subprocess.CompletedProcess[str] | object) -> bool:
    if getattr(result, "returncode", 1) == 0:
        return False
    combined = "\n".join(
        part for part in (
            getattr(result, "stdout", "") or "",
            getattr(result, "stderr", "") or "",
        ) if part
    ).lower()
    return any(marker in combined for marker in TRANSIENT_LLM_FAILURE_MARKERS)


def _run_llm_command_with_retry(
    cli: str,
    command: list[str],
    *,
    stdin_text: str | None = None,
    timeout_seconds: int | None = None,
    context_label: str | None = None,
) -> int:
    context_suffix = f" for {context_label}" if context_label else ""
    for attempt in range(1, TRANSIENT_LLM_RETRY_ATTEMPTS + 1):
        _maybe_dump_llm_prompt(
            command,
            stdin_text=stdin_text,
            context_label=context_label,
            attempt=attempt,
        )
        returncode, stdout, stderr = _run_llm_subprocess(
            command,
            stdin_text=stdin_text,
            timeout_seconds=timeout_seconds,
        )
        result = subprocess.CompletedProcess(command, returncode, stdout, stderr)
        _emit_completed_output(result)
        if result.returncode == 0:
            return 0
        if result.returncode == LLM_TIMEOUT_RETURNCODE:
            print(
                f"WARNING: {cli} writer command timed out after {timeout_seconds}s{context_suffix}.",
                file=sys.stderr,
            )
            return LLM_TIMEOUT_RETURNCODE
        if attempt == TRANSIENT_LLM_RETRY_ATTEMPTS or not _is_transient_llm_failure(result):
            return result.returncode
        print(
            f"WARNING: transient {cli} writer failure detected{context_suffix}; retrying ({attempt}/{TRANSIENT_LLM_RETRY_ATTEMPTS - 1})...",
            file=sys.stderr,
        )
        time.sleep(min(attempt, 2))
    return 1


def _run_llm_command_capture_with_retry(
    cli: str,
    command: list[str],
    *,
    stdin_text: str | None = None,
    timeout_seconds: int | None = None,
    context_label: str | None = None,
) -> tuple[int, str]:
    context_suffix = f" for {context_label}" if context_label else ""
    for attempt in range(1, TRANSIENT_LLM_RETRY_ATTEMPTS + 1):
        _maybe_dump_llm_prompt(
            command,
            stdin_text=stdin_text,
            context_label=context_label,
            attempt=attempt,
        )
        returncode, stdout, stderr = _run_llm_subprocess(
            command,
            stdin_text=stdin_text,
            timeout_seconds=timeout_seconds,
        )
        result = subprocess.CompletedProcess(command, returncode, stdout, stderr)
        _emit_completed_output(result)
        if result.returncode == 0:
            return 0, result.stdout
        if result.returncode == LLM_TIMEOUT_RETURNCODE:
            print(
                f"WARNING: {cli} writer command timed out after {timeout_seconds}s{context_suffix}.",
                file=sys.stderr,
            )
            return LLM_TIMEOUT_RETURNCODE, result.stdout
        if attempt == TRANSIENT_LLM_RETRY_ATTEMPTS or not _is_transient_llm_failure(result):
            return result.returncode, result.stdout
        print(
            f"WARNING: transient {cli} writer failure detected{context_suffix}; retrying ({attempt}/{TRANSIENT_LLM_RETRY_ATTEMPTS - 1})...",
            file=sys.stderr,
        )
        time.sleep(min(attempt, 2))
    return 1, ""


def _apply_fidelity_patch_task(
    batch_id: str,
    episode: str,
    brief_path: Path,
    *,
    source_excerpt_path: Path,
    cli: str,
    executable: str,
) -> int:
    draft_path = _drafts_dir() / f"{episode}.md"
    if not draft_path.exists():
        print(f"ERROR: draft not found for fidelity patch: {draft_path}")
        return 1

    draft_text = draft_path.read_text(encoding="utf-8")
    profile = _episode_rule_profile(source_excerpt_path)
    patch_spec = _build_rewrite_patch_spec(profile)
    candidate_blocks = _find_patch_candidate_blocks(draft_text, patch_spec)
    candidate_families = _summarize_candidate_families(candidate_blocks)
    excerpt_tier = str(profile.get("excerpt_tier", "baseline"))
    candidate_span = _candidate_blocks_total_span(candidate_blocks)
    _, family_priority = _candidate_family_priority(candidate_families)
    print(
        "  → Fidelity patch scope: "
        f"{episode} (excerpt_tier={excerpt_tier}, "
        f"candidate_blocks={len(candidate_blocks)}, "
        f"candidate_span={candidate_span}, "
        f"family_priority={family_priority}, "
        f"families={', '.join(candidate_families) if candidate_families else 'none'})"
    )
    should_run_patch, skip_reason = _should_run_fidelity_patch(
        profile,
        draft_text,
        candidate_blocks,
        candidate_families,
    )
    if not should_run_patch:
        print(
            "  → Skip fidelity patch: "
            f"{episode} (skip_reason={skip_reason}; keeping the draft as-is)"
        )
        return 0
    patch_prompt = _build_fidelity_rewrite_prompt(
        batch_id,
        episode,
        brief_path,
        source_excerpt_path=source_excerpt_path,
        draft_text=draft_text,
        patch_spec=patch_spec,
        candidate_blocks=candidate_blocks,
    )
    patch_prompt_bytes = len(patch_prompt.encode("utf-8"))
    if patch_prompt_bytes > PATCH_FIDELITY_MAX_PROMPT_BYTES:
        print(
            "  → Skip fidelity patch: "
            f"{episode} (skip_reason=patch_prompt_bytes={patch_prompt_bytes}>max_prompt_bytes={PATCH_FIDELITY_MAX_PROMPT_BYTES}; keeping the draft as-is)"
        )
        return 0
    print(
        "  → Fidelity patch prompt: "
        f"{episode} (patch_prompt_bytes={patch_prompt_bytes}, timeout={SINGLE_EPISODE_REWRITE_TIMEOUT_SECONDS}s)"
    )
    command, stdin_text = _build_llm_invocation(cli, executable, patch_prompt)
    try:
        returncode, stdout = _run_llm_command_capture_with_retry(
            cli,
            command,
            stdin_text=stdin_text,
            timeout_seconds=SINGLE_EPISODE_REWRITE_TIMEOUT_SECONDS,
            context_label=f"{episode} fidelity patch",
        )
    except FileNotFoundError:
        print(f"ERROR: `{cli}` CLI is not installed or not on PATH")
        return 1
    if returncode == LLM_TIMEOUT_RETURNCODE:
        print(
            f"WARNING: fidelity patch timed out for {episode}; "
            "keeping the draft and continuing without patch."
        )
        return 0
    if returncode != 0:
        return returncode

    try:
        payload = _extract_json_payload(stdout)
        operations = _normalize_patch_operations(payload, candidate_blocks)
        rewritten = _apply_patch_operations_to_text(draft_text, operations)
    except Exception as exc:
        print(
            f"WARNING: invalid fidelity patch output for {episode}: {exc}; "
            "keeping the draft and continuing without patch."
        )
        return 0

    draft_path.write_text(rewritten, encoding="utf-8")
    touched_families = sorted({str(operation.get("problem_family", "")) for operation in operations if operation.get("problem_family")})
    print(
        "  → Applied fidelity patch: "
        f"{episode} (ops: {len(operations)}, "
        f"families_touched={', '.join(touched_families) if touched_families else 'none'})"
    )
    return 0


def _run_writer_task(
    batch_id: str,
    episode: str,
    brief_path: Path,
    *,
    batch_context_path: Path,
    source_excerpt_path: Path,
    cli: str,
    executable: str,
    syntax_first: bool = False,
) -> tuple[str, int]:
    rule_profile = _episode_rule_profile(source_excerpt_path)
    rewrite_reasons = _fidelity_rewrite_reasons(rule_profile)
    observed_signals = _rule_profile_signals(rule_profile)
    excerpt_tier = str(rule_profile.get("excerpt_tier", "baseline"))
    signal_text = ", ".join(observed_signals) if observed_signals else "baseline_only"
    print(f"  → Draft profile: {episode} (excerpt_tier={excerpt_tier}, signals={signal_text})")
    prompt = _build_writer_prompt(
        batch_id,
        episode,
        brief_path,
        batch_context_path=batch_context_path,
        source_excerpt_path=source_excerpt_path,
        syntax_first=syntax_first,
    )
    command, stdin_text = _build_llm_invocation(cli, executable, prompt)
    try:
        returncode = _run_llm_command_with_retry(
            cli,
            command,
            stdin_text=stdin_text,
            context_label=f"{episode} draft",
        )
    except FileNotFoundError:
        print(f"ERROR: `{cli}` CLI is not installed or not on PATH")
        return episode, 1
    if returncode != 0:
        return episode, returncode
    if syntax_first:
        return episode, 0
    if not rewrite_reasons:
        print(
            f"  → Skip fidelity rewrite: {episode} "
            f"(excerpt_tier={excerpt_tier}, signals={signal_text}; trigger: none)"
        )
        return episode, 0
    print(
        f"  → Run fidelity patch: {episode} "
        f"(excerpt_tier={excerpt_tier}, reasons={', '.join(rewrite_reasons)})"
    )
    return episode, _apply_fidelity_patch_task(
        batch_id,
        episode,
        brief_path,
        source_excerpt_path=source_excerpt_path,
        cli=cli,
        executable=executable,
    )


def _run_sequential_batch_task(
    batch_id: str,
    episodes: list[str],
    brief_path: Path,
    *,
    batch_context_path: Path,
    source_excerpt_paths: dict[str, Path],
    cli: str,
    executable: str,
    syntax_first: bool = False,
) -> tuple[list[str], int]:
    rewrite_reasons_by_episode = {
        episode: _fidelity_rewrite_reasons(_episode_rule_profile(source_excerpt_paths[episode]))
        for episode in episodes
    }
    prompt = _build_sequential_batch_writer_prompt(
        batch_id,
        episodes,
        brief_path,
        batch_context_path=batch_context_path,
        source_excerpt_paths=source_excerpt_paths,
        syntax_first=syntax_first,
    )
    command, stdin_text = _build_llm_invocation(cli, executable, prompt)
    try:
        returncode = _run_llm_command_with_retry(
            cli,
            command,
            stdin_text=stdin_text,
            timeout_seconds=SEQUENTIAL_BATCH_WRITE_TIMEOUT_SECONDS,
            context_label=f"{batch_id} batch draft",
        )
    except FileNotFoundError:
        print(f"ERROR: `{cli}` CLI is not installed or not on PATH")
        return episodes, 1
    if returncode != 0:
        return episodes, returncode
    if syntax_first:
        return episodes, 0
    rewrite_targets = [episode for episode in episodes if rewrite_reasons_by_episode[episode]]
    if not rewrite_targets:
        print("  → Skip batch fidelity patch (no strong source-fidelity signals)")
        return episodes, 0
    print("  → Run batch fidelity patch:")
    for episode in rewrite_targets:
        episode_profile = _episode_rule_profile(source_excerpt_paths[episode])
        episode_tier = str(episode_profile.get("excerpt_tier", "baseline"))
        print(f"    - {episode}: excerpt_tier={episode_tier}; reasons={', '.join(rewrite_reasons_by_episode[episode])}")
    for episode in rewrite_targets:
        returncode = _apply_fidelity_patch_task(
            batch_id,
            episode,
            brief_path,
            source_excerpt_path=source_excerpt_paths[episode],
            cli=cli,
            executable=executable,
        )
        if returncode != 0:
            return episodes, returncode
    return episodes, 0


def _run_episode_tasks_sequentially(
    batch_id: str,
    episodes: list[str],
    brief_path: Path,
    *,
    batch_context_path: Path,
    source_excerpt_paths: dict[str, Path],
    cli: str,
    executable: str,
    syntax_first: bool = False,
) -> list[tuple[str, int]]:
    results: list[tuple[str, int]] = []
    for episode in episodes:
        results.append(
            _run_writer_task(
                batch_id,
                episode,
                brief_path,
                batch_context_path=batch_context_path,
                source_excerpt_path=source_excerpt_paths[episode],
                cli=cli,
                executable=executable,
                syntax_first=syntax_first,
            )
        )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Harness V2 writer backend")
    parser.add_argument("--batch", required=True, dest="batch_id")
    parser.add_argument("--episodes", required=True, help="Comma-separated episode ids")
    parser.add_argument("--parallelism", type=int, default=DEFAULT_WRITER_PARALLELISM)
    parser.add_argument("--syntax-first", action="store_true")
    args = parser.parse_args(argv)

    episodes = _parse_episodes(args.episodes)
    if not episodes:
        print("ERROR: no episodes were provided")
        return 1

    brief_path = _find_batch_brief(args.batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for {args.batch_id}")
        return 1

    targets = sorted(_missing_drafts(episodes), key=_episode_sort_key)
    if not targets:
        print(f"  ✓ All target drafts already exist for {args.batch_id}")
        return 0

    try:
        resolved_cli = _resolve_llm_cli()
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    if resolved_cli is None:
        print(f"ERROR: no supported LLM CLI found on PATH (tried: {', '.join(SUPPORTED_LLM_CLIS)})")
        return 1
    cli, executable = resolved_cli

    parallelism = max(1, min(args.parallelism, len(targets)))
    batch_context_path = _build_batch_context_bundle(args.batch_id, brief_path)
    source_excerpt_paths = {
        episode: _build_episode_source_excerpt(args.batch_id, episode)
        for episode in targets
    }
    print(f"  → Writer backend: {cli}")
    print(f"  → Writer target: {', '.join(targets)}")
    print(f"  → Batch brief: {_rel(brief_path)}")
    print(f"  → Batch context: {_rel(_batch_context_runtime_path(batch_context_path))}")
    print("  → Source excerpts:")
    for episode in targets:
        print(f"    - {episode}: {_rel(_source_excerpt_runtime_path(source_excerpt_paths[episode]))}")
    print(f"  → Parallelism: {parallelism}")
    if args.syntax_first:
        print("  → Mode: syntax-first")

    if parallelism == 1 and len(targets) > 1:
        _, returncode = _run_sequential_batch_task(
            args.batch_id,
            targets,
            brief_path,
            batch_context_path=batch_context_path,
            source_excerpt_paths=source_excerpt_paths,
            cli=cli,
            executable=executable,
            syntax_first=args.syntax_first,
        )
        if returncode == LLM_TIMEOUT_RETURNCODE:
            print(
                "WARNING: sequential batch writer timed out; falling back to sequential per-episode writer.",
                file=sys.stderr,
            )
            results = _run_episode_tasks_sequentially(
                args.batch_id,
                targets,
                brief_path,
                batch_context_path=batch_context_path,
                source_excerpt_paths=source_excerpt_paths,
                cli=cli,
                executable=executable,
                syntax_first=args.syntax_first,
            )
            failed = [episode for episode, episode_returncode in results if episode_returncode != 0]
            if failed:
                print(f"ERROR: writer failed for episodes: {', '.join(failed)}")
                return 1
            return 0
        if returncode != 0:
            print(f"ERROR: writer failed for episodes: {', '.join(targets)}")
            return 1
        return 0

    with ThreadPoolExecutor(max_workers=parallelism) as pool:
        futures = [
            pool.submit(
                _run_writer_task,
                args.batch_id,
                episode,
                brief_path,
                batch_context_path=batch_context_path,
                source_excerpt_path=source_excerpt_paths[episode],
                cli=cli,
                executable=executable,
                syntax_first=args.syntax_first,
            )
            for episode in targets
        ]
        results = [future.result() for future in futures]

    failed = [episode for episode, returncode in results if returncode != 0]
    if failed:
        print(f"ERROR: writer failed for episodes: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

