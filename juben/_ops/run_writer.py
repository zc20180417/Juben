from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PASSING_SAMPLE = ROOT / "harness" / "framework" / "passing-episode.sample.md"
WRITE_CONTRACT_PATH = ROOT / "harness" / "framework" / "write-contract.md"
WRITER_STYLE_PATH = ROOT / "harness" / "framework" / "writer-style.md"
WRITER_PROMPT_TEMPLATE = ROOT / "harness" / "framework" / "writer-prompt.template.md"
WRITER_BATCH_PROMPT_TEMPLATE = ROOT / "harness" / "framework" / "writer-batch-prompt.template.md"
PROMPTS_DIR = ROOT / "harness" / "project" / "prompts"
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
    "AGENT_POLISH",
    "STYLE_RED_LINES",
)
DEFAULT_WRITER_PARALLELISM = 1
CHAPTER_HEADING_RE = re.compile(
    r"^第\s*([0-9一二三四五六七八九十百千零两]+)\s*章(?:\s+|[：:、-]|$)[^\n\r。！？!?]*$",
    re.MULTILINE,
)
SOURCE_QUOTE_RE = re.compile(r"[“\"]([^”\"\n]{2,80})[”\"]")
DECORATIVE_PARAGRAPH_RE = re.compile(r"^[-=*_~·•]{6,}$")
HEADING_LEVEL3_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
JSON_FENCE_RE = re.compile(r"```json\s*(.*?)```", re.DOTALL | re.IGNORECASE)
ABSTRACT_LINE_PATTERNS = (
    re.compile(r"眼[里底].{0,8}(是|满是|盛满)"),
    re.compile(r"像[^，。！？]{0,8}一样"),
    re.compile(r"最[^，。！？]{0,8}(风光|耀眼|体面)"),
    re.compile(r"只剩[^，。！？]{0,12}$"),
    re.compile(r"(恢复|重新归于)[^，。！？]{0,8}(平静|死寂|安静)"),
)
FILL_LINE_PATTERNS = (
    re.compile(r"^(先|等|进去|出去|回来|过去)[^。！？]{0,16}(再说|再谈|安排|准备|说清)"),
    re.compile(r"(流程|环节|候场|后台|对讲|耳麦)"),
    re.compile(r"(寒暄|附和|介绍)[^。！？]{0,12}$"),
)


def _configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except ValueError:
                pass


_configure_stdio()
GENERIC_ROLE_TOKENS = (
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
    "工作人员",
    "保安",
    "主持人",
    "老板",
    "经理",
    "前台",
    "路人",
)


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


def _prompt_output_path(name: str) -> Path:
    return PROMPTS_DIR / f"{name}.prompt.md"


def _render_template_text(template_path: Path, replacements: dict[str, str]) -> str:
    text = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


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
    span_match = re.search(r"^\s*-?\s*\*\*source_chapter_span\*\*:\s*(.+?)\s*$", block, re.MULTILINE)
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
    match = re.search(r"([0-9]+)", label)
    if match:
        return int(match.group(1))
    numeral_match = re.search(r"[零一二三四五六七八九十百千两]+", label)
    if numeral_match:
        return _chinese_chapter_number_to_int(numeral_match.group(0))
    return None


def _chinese_chapter_number_to_int(raw: str) -> int | None:
    digits = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    units = {"十": 10, "百": 100, "千": 1000}
    total = 0
    current = 0
    seen = False
    for char in raw:
        if char in digits:
            current = digits[char]
            seen = True
            continue
        if char in units:
            unit = units[char]
            total += (current or 1) * unit
            current = 0
            seen = True
            continue
        return None
    if not seen:
        return None
    return total + current


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


def _extract_reusable_source_lines(excerpt_text: str) -> list[str]:
    all_lines = _extract_all_source_quote_lines(excerpt_text)
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
    candidate_lines = _extract_all_source_quote_lines(excerpt_text)
    for raw_line in excerpt_text.splitlines():
        dialogue = _split_dialogue_line(raw_line.strip())
        if dialogue is None:
            continue
        candidate_lines.append(dialogue[1].strip())

    indexed: list[tuple[int, str]] = []
    seen_candidates: set[str] = set()
    for index, line in enumerate(candidate_lines):
        cleaned = line.strip()
        if len(cleaned) < 18 or cleaned in seen_candidates:
            continue
        seen_candidates.add(cleaned)
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
        seen.add(cleaned)
        candidates.append(cleaned)

    for sentence in re.split(r"[。！？!?]", excerpt_text):
        cleaned = sentence.strip("“”\" \t\r\n")
        if len(cleaned) < 24 or cleaned in seen:
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
        if not any(pattern.search(cleaned) for pattern in ABSTRACT_LINE_PATTERNS):
            continue
        if cleaned in seen:
            continue
        seen.add(cleaned)
        candidates.append(cleaned)
    return candidates[:10]


def _forbidden_fill_hints(scene_modes: list[str]) -> list[str]:
    hints = [
        "新承接对白",
        "额外宾客台词",
        "额外角色OS",
        "过程性扩写",
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


def _split_fact_list(raw: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;,??]+", raw) if item.strip()]


def _beat_lines_from_raw(beats: str | list[str]) -> list[str]:
    if isinstance(beats, list):
        return [str(item).strip() for item in beats if str(item).strip()]
    return [part.strip(" -") for part in re.split(r"[\n?;]+", str(beats)) if part.strip(" -")]


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
                    "**scene_plan**:",
                    "**ending_function**:",
                    "**irreversibility_level**:",
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
                    "**scene_plan**:",
                    "**ending_function**:",
                    "**irreversibility_level**:",
                ),
            )
        )
        must_not_add = _extract_block_bullets(
            _extract_marked_block(
                block,
                "**must-not-add / must-not-jump**:",
                ("**function_signals**:", "**scene_plan**:", "**ending_function**:", "**irreversibility_level**:"),
            )
        )
        ending_function = _clean_inline_fact_text(
            _extract_marked_block(block, "**ending_function**:", ("**irreversibility_level**:",))
        )
        episode_facts = {
            "episode": episode_id,
            "source_span": source_span,
            "must_keep_beats": must_keep_beats,
            "must_not_add": must_not_add,
            "ending_function": ending_function,
        }
        episodes.append(
            episode_facts
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
    batch_source_map_facts = _extract_batch_facts_from_source_map(batch_id)
    episode_facts = next(
        (
            item
            for item in batch_source_map_facts.get("episodes", [])
            if isinstance(item, dict) and str(item.get("episode", "")).strip() == episode
        ),
        {},
    )
    reusable_lines = _extract_reusable_source_lines(excerpt_body)
    scene_modes: list[str] = []
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


def _rule_profile_signals(
    profile: dict[str, object],
    episode_facts: dict[str, object] | None = None,
) -> list[str]:
    signals: list[str] = []
    excerpt_tier = str(profile.get("excerpt_tier", "baseline"))
    signals.append(f"tier:{excerpt_tier}")
    scene_modes = {item for item in profile.get("scene_modes", []) if isinstance(item, str)}
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

def _build_minimal_rule_pack(
    profile: dict[str, object],
    episode_facts: dict[str, object],
    *,
    include_adjacent_boundary: bool,
) -> str:
    excerpt_tier = str(profile.get("excerpt_tier", "baseline"))
    bullets = [
        "- `event_anchors` 定顺序；已发生事件不得后拖。",
        "- 默认禁新事件、禁新流程、禁新职业说明、禁新后台调度、禁新承接对白。",
        "- 角色只按当场已公开信息行动；模型知道不等于角色知道。",
        "- `voice-anchor.md` 只看气质和禁区，不复用例句。",
        "- 场次数按 beats 和 source 推进自然决定；整集至少 2 场，不要为凑格式硬拆或硬并。",
        "- 非终场最后一个 `△` 必须带新增推进，别停在静态结果或环境余波。",
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

    scene_modes = set(profile.get("scene_modes", []))
    if profile.get("must_keep_names"):
        bullets.append("- `must_keep_names` 非空时，人名别退化成泛称。")
    if profile.get("must_keep_long_lines"):
        bullets.append("- `must_keep_long_lines` 非空时，至少保住 1 句长句递进。")
    if excerpt_tier == "strong_scene":
        bullets.append("- `△` 优先落手、眼、肩背、站位、道具或声场变化，别只写“冷静”“漠然”“惊艳”“死寂”这类抽象判断。")
        bullets.append("- 未公开的关系词、身份词、真名别抢跑；没到那一步时别替角色下确认性称谓或身份结论。")
        bullets.append("- `event_anchors` 里的关系称谓若还没确认，只保句意和施压方向，别逐字照抄成抢跑称呼。")
    if "result_confirmation_scene" in scene_modes:
        bullets.append("- `result_confirmation_scene`：结果确认拍别压成单场总结；整集至少 2 场、至少 2 个 `【镜头】`。")
        bullets.append("- `result_confirmation_scene`：第一场先落结果与第一反应，后续场再写压迫升级、去留决定或关系断裂。")
    if "pressure_scene" in scene_modes:
        bullets.append("- `pressure_scene`：别把整轮施压拆成模板短句。")
        bullets.append("- `pressure_scene`：非终场结尾要让压迫继续往下一拍顶上来，优先写空间侵入、动作压制、话语打断或下一句更重的威胁已经顶到嘴边。")
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
    bullets = [
        "- beats：`【信息】/【关系】/【动作】/【钩子】` 一项不缺。",
        "- 收尾：最后推进已经落到正文，不停在解释或总结。",
        "- 顺序：`event_anchors` 不后拖；不越过 `must-not-add / must-not-jump`。",
        "- 壳层：`△ / ♪ / 【镜头】： / 角色： / 角色（os）：` 各自独行。",
        "- 场次：整集至少 2 场；非终场最后一个 `△` 留新增推进。",
        "- 叙述：禁新增第一人称 `OS` / “我……”旁白；能不用 `OS` 就不用。",
        "- 节奏：按当前戏的需要自然拆分，别写成解释清单。",
    ]

    if excerpt_tier in {"low_risk", "strong_scene"} and profile.get("reusable_lines_present"):
        bullets.append("- 原句：有 `reusable_source_lines` 就优先保；否则贴着 `event_anchors` 句意写。")
    else:
        bullets.append("- 原句：贴着 `event_anchors` 句意写。")

    if profile.get("must_keep_long_lines"):
        bullets.append("- 长句：`must_keep_long_lines` 至少保住 1 句长句递进。")

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

    return _render_template_text(
        WRITER_PROMPT_TEMPLATE,
        {
            "draft_target": draft_target,
            "reads_block": reads_block,
            "brief_rel": brief_rel,
            "batch_id": batch_id,
            "episode": episode,
            "contract_style_reference_block": contract_style_reference_block,
            "rule_priority": rule_priority,
            "episode_num": episode_num,
            "sample_rel": sample_rel,
            "must_keep_beats_block": must_keep_beats_block,
            "rule_pack": rule_pack,
            "minimal_self_check": minimal_self_check,
            "syntax_guidance": syntax_guidance,
        },
    )

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
            f"  - 场次：首场 `场{int(episode.split('-')[1])}-1`；整集至少 2 场；按 beats 与 source 推进自然拆场\n"
            f"  - beats：{'; '.join(_batch_context_episode_facts(batch_context_path, episode).get('must_keep_beats', [])) or '以 batch brief 当前集任务为准'}；`【信息】/【关系】/【动作】/【钩子】` 不能缺"
        )
        for episode in episodes
    )
    syntax_guidance = (
        "语法壳优先：先把语法壳和排版写对，先对齐壳层和排版，再考虑剧情润色。\n"
        "- 不确定剧情细节时，宁可保守，不要写成 Markdown 场记。\n"
    ) if syntax_first else ""
    sequence_runtime_lines = [
        "批次顺序写作最小规则：",
        "- 每集只读自己的 excerpt，并完成自己在 batch brief / batch_facts 里的全部 beats；压场数不能成为缺 beat 的理由。",
        "- `event_anchors` 定顺序；`must_keep_names`、`forbidden_fill` 守边界；有 `reusable_source_lines` 就先保原句。",
        "- 整集至少 2 场；按当前戏的推进自然拆场，不为凑格式硬拆或硬并。",
        "- 非终场最后一个 `△` 必须带服务 beats 的新增推进，别停在静态结果。",
        "- 禁新增第一人称叙述；`角色（os）：` 也不能写成“我……”式内心旁白。",
        "- 上一集只给边界；承接最多 1-2 个镜头。模型知道不等于角色知道；身份、关系、真名只按当场已公开信息写。",
        "- `voice-anchor` 只看气质与禁区，优先级低于当前集 beats 和 source 边界。",
    ]
    sequence_runtime_pack = "\n".join(sequence_runtime_lines)
    return _render_template_text(
        WRITER_BATCH_PROMPT_TEMPLATE,
        {
            "reads_block": reads_block,
            "brief_rel": brief_rel,
            "batch_id": batch_id,
            "contract_style_reference_block": contract_style_reference_block,
            "rule_priority": rule_priority,
            "targets_block": targets_block,
            "sequence_runtime_pack": sequence_runtime_pack,
            "syntax_guidance": syntax_guidance,
        },
    )

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Harness V2 writer backend")
    parser.add_argument("--batch", required=True, dest="batch_id")
    parser.add_argument("--episodes", required=True, help="Comma-separated episode ids")
    parser.add_argument("--parallelism", type=int, default=DEFAULT_WRITER_PARALLELISM)
    parser.add_argument("--syntax-first", action="store_true")
    parser.add_argument("--prompt-only", action="store_true", help="Only write model prompt file(s) and stop")
    args = parser.parse_args(argv)

    episodes = _parse_episodes(args.episodes)
    if not episodes:
        print("ERROR: no episodes were provided")
        return 1

    brief_path = _find_batch_brief(args.batch_id)
    if brief_path is None:
        print(f"ERROR: batch brief not found for {args.batch_id}")
        return 1

    all_targets = sorted(episodes, key=_episode_sort_key)
    batch_context_path = _build_batch_context_bundle(args.batch_id, brief_path)
    source_excerpt_paths = {
        episode: _build_episode_source_excerpt(args.batch_id, episode)
        for episode in all_targets
    }
    targets = all_targets if args.prompt_only else sorted(_missing_drafts(episodes), key=_episode_sort_key)
    if not targets:
        print(f"  ✓ All target drafts already exist for {args.batch_id}")
        print("  ✓ Refreshed batch context and source excerpts")
        return 0

    parallelism = max(1, min(args.parallelism, len(targets)))
    print("  → Writer backend: external agent prompt packet")
    print(f"  → Writer target: {', '.join(targets)}")
    print(f"  → Batch brief: {_rel(brief_path)}")
    print(f"  → Batch context: {_rel(_batch_context_runtime_path(batch_context_path))}")
    print("  → Source excerpts:")
    for episode in targets:
        print(f"    - {episode}: {_rel(_source_excerpt_runtime_path(source_excerpt_paths[episode]))}")
    print(f"  → Parallelism: {parallelism}")
    if args.syntax_first:
        print("  → Mode: syntax-first")

    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    if parallelism == 1 and len(targets) > 1:
        prompt_path = _prompt_output_path(f"{args.batch_id}.writer.batch")
        prompt_path.write_text(
            _build_sequential_batch_writer_prompt(
                args.batch_id,
                targets,
                brief_path,
                batch_context_path=batch_context_path,
                source_excerpt_paths=source_excerpt_paths,
                syntax_first=args.syntax_first,
            ),
            encoding="utf-8",
        )
        print(f"OK: prompt written -> {_rel(prompt_path)}")
        print(f"  target episodes: {', '.join(targets)}")
    else:
        for episode in targets:
            prompt_path = _prompt_output_path(f"{args.batch_id}.{episode}.writer")
            prompt_path.write_text(
                _build_writer_prompt(
                    args.batch_id,
                    episode,
                    brief_path,
                    batch_context_path=batch_context_path,
                    source_excerpt_path=source_excerpt_paths[episode],
                    syntax_first=args.syntax_first,
                ),
                encoding="utf-8",
            )
            print(f"OK: prompt written -> {_rel(prompt_path)}")
    print("  model execution: external agent only; this script does not call model CLIs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

