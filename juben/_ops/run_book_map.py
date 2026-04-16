from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

OPS_DIR = Path(__file__).resolve().parent
if str(OPS_DIR) not in sys.path:
    sys.path.insert(0, str(OPS_DIR))

from agent_backend import AgentBackendError, build_agent_command


ROOT = Path(__file__).resolve().parents[1]
BOOK_BLUEPRINT = ROOT / "harness" / "project" / "book.blueprint.md"
SOURCE_MAP = ROOT / "harness" / "project" / "source.map.md"
RUN_MANIFEST = ROOT / "harness" / "project" / "run.manifest.md"
ENTRY = ROOT / "harness" / "framework" / "entry.md"


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _build_map_prompt(
    novel_path: Path,
    *,
    episodes: int,
    batch_size: int,
    strategy: str,
    intensity: str,
) -> str:
    blueprint_rel = _rel(BOOK_BLUEPRINT)
    source_map_rel = _rel(SOURCE_MAP)
    novel_rel = _rel(novel_path)
    return f"""你现在只处理 Harness V2 的 source.map 生成阶段，不写 draft，不写 state，不做 promote。

开始前先阅读：
- AGENTS.md
- CLAUDE.md
- { _rel(ENTRY) }
- { _rel(RUN_MANIFEST) }
- {novel_rel}
- {blueprint_rel}

本次唯一目标：
- 基于整本小说 + `book.blueprint.md`
- 完整覆盖写入 `{source_map_rel}`

硬约束：
- 只允许修改 `{source_map_rel}`
- 不得修改 `{blueprint_rel}`
- 不得修改 `drafts/episodes/`
- 不得修改 `episodes/`
- 不得修改 `harness/project/state/`
- 不得改动其他无关文件

映射要求：
- 总集数：{episodes}
- batch_size：{batch_size}
- adaptation_strategy：{strategy}
- dialogue_adaptation_intensity：{intensity}
- 单集时长按 1-3 分钟动态浮动，平均按 2 分钟/集理解节奏密度
- 先依据全书级蓝图分配主线推进、角色弧光、关系变化、关键反转、结局闭环
- 章节只作为定位信息，不作为主要思考单位
- 允许一章拆多集，也允许相邻章节合拍，但不得抢跑后续大事件

输出格式要求：
- 生成完整的 `source.map.md`
- 批次头必须使用这种骨架：`## Batch 01 (EP01-05): 批次标题`
- 每集头必须使用这种骨架：`### EP01: 集标题`
- 每个 episode 都必须填写：
  - `**source_chapter_span**:`
  - `**must-keep_beats**:`
  - `**must-not-add / must-not-jump**:`
  - `**ending_type**:`
- 为兼容旧解析与结构检查，文件中仍需保留这些 legacy 绑定词：
  - `source chapter span`
  - `must-keep beats`
  - `must-not-add / must-not-jump`
  - `ending type`
- 删除或替换所有占位标记
- 不再保留 `mapping_status: pending_book_extraction`
- 用中文写，面向后续 batch/episode 生产

写完 `{source_map_rel}` 后立即停止。
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run source-map generation backend")
    parser.add_argument("--novel-file", required=True)
    parser.add_argument("--episodes", required=True, type=int)
    parser.add_argument("--batch-size", required=True, type=int)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--intensity", required=True)
    parser.add_argument("--agent-backend", choices=["auto", "claude", "codex"], default="auto")
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
    try:
        backend_label, command = build_agent_command(prompt, args.agent_backend)
        print(f"  → {backend_label} map-book target: {_rel(SOURCE_MAP)}")
        print(f"  → Blueprint: {_rel(BOOK_BLUEPRINT)}")
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
        )
    except AgentBackendError as exc:
        print(f"ERROR: {exc}")
        return 1

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
