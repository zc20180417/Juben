from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_BLUEPRINT = ROOT / "harness" / "project" / "book.blueprint.md"
SOURCE_MAP = ROOT / "harness" / "project" / "source.map.md"
RUN_MANIFEST = ROOT / "harness" / "project" / "run.manifest.md"
ENTRY = ROOT / "harness" / "framework" / "entry.md"
MAP_PROMPT_TEMPLATE = ROOT / "harness" / "framework" / "map-book-prompt.template.md"
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


def _build_map_prompt(
    novel_path: Path,
    *,
    episodes: int,
    batch_size: int,
    strategy: str,
    intensity: str,
) -> str:
    manifest = _read_manifest_values()
    target_total_minutes = _manifest_int(manifest, "target_total_minutes", DEFAULT_TARGET_TOTAL_MINUTES)
    target_episode_minutes = _manifest_int(manifest, "target_episode_minutes", DEFAULT_TARGET_EPISODE_MINUTES)
    episode_minutes_min = _manifest_int(manifest, "episode_minutes_min", DEFAULT_EPISODE_MINUTES_MIN)
    episode_minutes_max = _manifest_int(manifest, "episode_minutes_max", DEFAULT_EPISODE_MINUTES_MAX)
    return _render_template_text(
        MAP_PROMPT_TEMPLATE,
        {
            "entry_rel": _rel(ENTRY),
            "run_manifest_rel": _rel(RUN_MANIFEST),
            "novel_rel": _rel(novel_path),
            "blueprint_rel": _rel(BOOK_BLUEPRINT),
            "source_map_rel": _rel(SOURCE_MAP),
            "episodes": str(episodes),
            "batch_size": str(batch_size),
            "target_total_minutes": str(target_total_minutes),
            "target_episode_minutes": str(target_episode_minutes),
            "episode_minutes_min": str(episode_minutes_min),
            "episode_minutes_max": str(episode_minutes_max),
            "strategy": strategy,
            "intensity": intensity,
        },
    )


def _prompt_output_path(kind: str) -> Path:
    return PROMPTS_DIR / f"{kind}.prompt.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run source-map generation backend")
    parser.add_argument("--novel-file", required=True)
    parser.add_argument("--episodes", required=True, type=int)
    parser.add_argument("--batch-size", required=True, type=int)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--intensity", required=True)
    parser.add_argument("--prompt-only", action="store_true", help="Only write the model prompt file and stop")
    args = parser.parse_args(argv)

    novel_path = ROOT / args.novel_file
    if not novel_path.exists():
        print(f"ERROR: novel file not found: {novel_path}")
        return 1
    if not BOOK_BLUEPRINT.exists():
        print(f"ERROR: blueprint file not found: {BOOK_BLUEPRINT}")
        return 1

    prompt = _build_map_prompt(
        novel_path,
        episodes=args.episodes,
        batch_size=args.batch_size,
        strategy=args.strategy,
        intensity=args.intensity,
    )
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_path = _prompt_output_path("map-book")
    prompt_path.write_text(prompt, encoding="utf-8")
    print(f"OK: prompt written -> {_rel(prompt_path)}")
    print(f"  target: {_rel(SOURCE_MAP)}")
    print("  model execution: external agent only; this script does not call model CLIs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
