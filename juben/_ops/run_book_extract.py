from __future__ import annotations

import argparse
import re
import sys
from math import ceil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_BLUEPRINT = ROOT / "harness" / "project" / "book.blueprint.md"
RUN_MANIFEST = ROOT / "harness" / "project" / "run.manifest.md"
ENTRY = ROOT / "harness" / "framework" / "entry.md"
EXTRACT_PROMPT_TEMPLATE = ROOT / "harness" / "framework" / "extract-book-prompt.template.md"
PROMPTS_DIR = ROOT / "harness" / "project" / "prompts"
DEFAULT_TARGET_TOTAL_MINUTES = 50
DEFAULT_TARGET_EPISODE_MINUTES = 2
DEFAULT_EPISODE_MINUTES_MIN = 1
DEFAULT_EPISODE_MINUTES_MAX = 3


def _configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except ValueError:
                pass


_configure_stdio()


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _render_template_text(template_path: Path, replacements: dict[str, str]) -> str:
    text = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def _chapter_count_from_blueprint() -> int | None:
    if not BOOK_BLUEPRINT.exists():
        return None
    content = BOOK_BLUEPRINT.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^- chapter_count:\s*(\d+)\s*$", content, re.MULTILINE)
    if not match:
        return None
    return int(match.group(1))


def _read_manifest_values() -> dict[str, str]:
    if not RUN_MANIFEST.exists():
        return {}
    content = RUN_MANIFEST.read_text(encoding="utf-8", errors="replace")
    values: dict[str, str] = {}
    for line in content.splitlines():
        match = re.match(r"^- (\w[\w_]*):\s*(.+?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def _manifest_int(values: dict[str, str], key: str, default: int) -> int:
    raw = values.get(key, "").strip()
    return int(raw) if raw.isdigit() else default


def _episode_range_hint(
    *,
    target_total_minutes: int,
    target_episode_minutes: int,
) -> tuple[int, int, int]:
    center = max(1, round(target_total_minutes / max(1, target_episode_minutes)))
    lower = max(1, round(center * 0.8))
    upper = max(lower, ceil(center * 1.25))
    return lower, center, upper


def _build_extract_prompt(novel_path: Path) -> str:
    blueprint_rel = _rel(BOOK_BLUEPRINT)
    chapter_count = _chapter_count_from_blueprint()
    manifest = _read_manifest_values()
    target_total_minutes = _manifest_int(manifest, "target_total_minutes", DEFAULT_TARGET_TOTAL_MINUTES)
    target_episode_minutes = _manifest_int(manifest, "target_episode_minutes", DEFAULT_TARGET_EPISODE_MINUTES)
    episode_minutes_min = _manifest_int(manifest, "episode_minutes_min", DEFAULT_EPISODE_MINUTES_MIN)
    episode_minutes_max = _manifest_int(manifest, "episode_minutes_max", DEFAULT_EPISODE_MINUTES_MAX)
    range_low, range_center, range_high = _episode_range_hint(
        target_total_minutes=target_total_minutes,
        target_episode_minutes=target_episode_minutes,
    )
    runtime_hint_line = (
        f"\n本次项目目标总时长约 {target_total_minutes} 分钟，"
        f"单集动态范围 {episode_minutes_min}-{episode_minutes_max} 分钟，"
        f"中心估算 {target_episode_minutes} 分钟/集；"
        f"建议先以 {range_center} 集为中心，合理区间约 {range_low}-{range_high} 集，"
        "再由原著有效戏剧单元校正。"
    )
    explicit_cap_line = runtime_hint_line
    if chapter_count is not None:
        explicit_cap_line += (
            f"\n本书当前已知 chapter_count={chapter_count}。"
            "章节只用于定位，不作为硬性集数上限；"
            "如果最终集数明显偏离上述时长区间，必须在“为什么不是更短/更长”中说明有效戏剧单元依据。"
        )
    blueprint_template = BOOK_BLUEPRINT.read_text(encoding="utf-8", errors="replace")
    novel_text = novel_path.read_text(encoding="utf-8", errors="replace")
    return _render_template_text(
        EXTRACT_PROMPT_TEMPLATE,
        {
            "blueprint_rel": blueprint_rel,
            "explicit_cap_line": explicit_cap_line,
            "target_total_minutes": str(target_total_minutes),
            "target_episode_minutes": str(target_episode_minutes),
            "episode_minutes_min": str(episode_minutes_min),
            "episode_minutes_max": str(episode_minutes_max),
            "episode_range_low": str(range_low),
            "episode_range_center": str(range_center),
            "episode_range_high": str(range_high),
            "blueprint_template": blueprint_template,
            "novel_text": novel_text,
        },
    )


def _prompt_output_path(kind: str) -> Path:
    return PROMPTS_DIR / f"{kind}.prompt.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run whole-book extraction backend")
    parser.add_argument("--novel-file", required=True)
    parser.add_argument("--prompt-only", action="store_true", help="Only write the model prompt file and stop")
    args = parser.parse_args(argv)

    novel_path = ROOT / args.novel_file
    if not novel_path.exists():
        print(f"ERROR: novel file not found: {novel_path}")
        return 1
    if not BOOK_BLUEPRINT.exists():
        print(f"ERROR: blueprint file not found: {BOOK_BLUEPRINT}")
        return 1

    prompt = _build_extract_prompt(novel_path)
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_path = _prompt_output_path("extract-book")
    prompt_path.write_text(prompt, encoding="utf-8")
    print(f"OK: prompt written -> {_rel(prompt_path)}")
    print(f"  target: {_rel(BOOK_BLUEPRINT)}")
    print("  model execution: external agent only; this script does not call model CLIs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
