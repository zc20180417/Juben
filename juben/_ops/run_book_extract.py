from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_BLUEPRINT = ROOT / "harness" / "project" / "book.blueprint.md"
RUN_MANIFEST = ROOT / "harness" / "project" / "run.manifest.md"
ENTRY = ROOT / "harness" / "framework" / "entry.md"


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _build_extract_prompt(novel_path: Path) -> str:
    blueprint_rel = _rel(BOOK_BLUEPRINT)
    novel_rel = _rel(novel_path)
    return f"""你现在只处理 Harness V2 的全书级抽取阶段，不写 draft，不写 source.map，不做 promote。

开始前先阅读：
- AGENTS.md
- CLAUDE.md
- { _rel(ENTRY) }
- { _rel(RUN_MANIFEST) }
- {novel_rel}
- {blueprint_rel}

本次唯一目标：
- 读取整本小说
- 完整覆盖写入 `{blueprint_rel}`

硬约束：
- 只允许修改 `{blueprint_rel}`
- 不得修改 `source.map.md`
- 不得修改 `drafts/episodes/`
- 不得修改 `episodes/`
- 不得修改 `harness/project/state/`
- 不得改动其他无关文件

输出要求：
- 保留文件头里的 `source_file`
- 将 `extraction_status` 改成 `extracted`
- 保留文件头里的 `target_episode_minutes`、`episode_minutes_min`、`episode_minutes_max`
- 把文件头里的 `recommended_total_episodes` 改成纯数字
- 必须完整填写这些章节：
  - `## 集数建议`
  - `## 主线`
  - `## 角色弧光`
  - `## 关系变化`
  - `## 关键反转`
  - `## 结局闭环`
- 集数建议必须基于：
  - 单集时长按 1-3 分钟动态浮动
  - 平均按 2 分钟/集估算
  - 保证每集能成立有效推进和集尾钩子
- `## 集数建议` 里必须解释：
  - 为什么这个总集数合理
  - 为什么不是明显更短或更长
- 章节只作为定位信息，不作为主要思考单位
- `## 章节索引（仅定位）` 只用于回查原著位置
- 删除或替换所有 `AGENT_EXTRACT_REQUIRED`
- 用中文写，追求全书级理解，不按单章流水账复述

写完 `{blueprint_rel}` 后立即停止。
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run whole-book extraction backend")
    parser.add_argument("--novel-file", required=True)
    args = parser.parse_args(argv)

    novel_path = ROOT / args.novel_file
    if not novel_path.exists():
        print(f"ERROR: novel file not found: {novel_path}")
        return 1
    if not BOOK_BLUEPRINT.exists():
        print(f"ERROR: blueprint file not found: {BOOK_BLUEPRINT}")
        return 1

    prompt = _build_extract_prompt(novel_path)
    print(f"  → Claude extract-book target: {_rel(BOOK_BLUEPRINT)}")
    print(f"  → Source novel: {_rel(novel_path)}")

    try:
        result = subprocess.run(
            ["claude", "-p", "--dangerously-skip-permissions", prompt],
            cwd=ROOT,
            check=False,
        )
    except FileNotFoundError:
        print("ERROR: `claude` CLI is not installed or not on PATH")
        return 1

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
