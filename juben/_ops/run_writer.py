from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PASSING_SAMPLE = ROOT / "harness" / "framework" / "passing-episode.sample.md"
DEFAULT_WRITER_PARALLELISM = 3


def _batch_briefs_dir() -> Path:
    return ROOT / "harness" / "project" / "batch-briefs"


def _drafts_dir() -> Path:
    return ROOT / "drafts" / "episodes"


def _parse_episodes(raw: str) -> list[str]:
    return [episode.strip() for episode in raw.split(",") if episode.strip()]


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


def _build_writer_prompt(batch_id: str, episode: str, brief_path: Path, *, syntax_first: bool = False) -> str:
    draft_target = f"drafts/episodes/{episode}.md"
    brief_rel = _rel(brief_path)
    sample_rel = _rel(PASSING_SAMPLE)
    episode_num = str(int(episode.split("-")[1]))
    syntax_guidance = (
        "语法壳优先：先把语法壳和排版写对，先对齐壳层和排版，再考虑剧情润色。\n"
        "- 不确定剧情细节时，宁可保守，不要写成 Markdown 场记。\n"
    ) if syntax_first else ""

    return f"""你现在只扮演 Harness V2 的 Writer 角色，不扮演 Controller、Verifier 或 Recorder。

开始写稿前，先阅读这些文件：
- AGENTS.md
- CLAUDE.md
- harness/framework/entry.md
- harness/project/run.manifest.md
- harness/project/source.map.md
- {brief_rel}
- harness/framework/write-contract.md
- harness/framework/writer-style.md
- harness/project/state/story.state.md
- harness/project/state/relationship.board.md
- harness/project/state/open_loops.md
- voice-anchor.md（如果存在）
- character.md（如果存在）
- {sample_rel}（本仓库通过 lint 的剧本壳样例）

本次只处理 batch：{batch_id}
本次只补齐这个缺失草稿：{episode}

你只能写这个目标文件：
- {draft_target}

硬约束：
- 只能写 drafts/episodes/EP-XX.md
- 不得 promote
- 不得写 state
- 不得修改 episodes/
- 不得修改 harness/project/run.manifest.md
- 不得修改 harness/project/source.map.md
- 不得修改 harness/project/state/
- 不得修改 locks、tests、docs 或其他无关文件
- 不得跨越 source.map 里的 must-not-add / must-not-jump
- 写完目标草稿后立即停止，不要继续做 verify、promote、record
- 第一优先级不是“写得像小说”，而是把 Harness V2 剧本语法壳写正确

输出要求：
- 为这个目标集数生成完整草稿
- 保持 original_fidelity + light 对话改编力度
- 如果信息不足，只能保守贴合 batch brief 与 source.map，不得擅自补设定
- 必须使用并严格对齐这些语法壳：
  - `场{episode_num}-1：` / `场{episode_num}-2：` / `场{episode_num}-3：`
  - `日/夜`
  - `外/内`
  - `场景：`
  - `♪：`
  - `△：`
  - `【镜头】：`
  - `角色（os）：`
- 当前集是 `{episode}`，所以第一位场次编号必须固定为 `{episode_num}`；整集最多 3 个场次标题
- 不要写成分幕式编号；例如当前集禁止出现 `场1-1 / 场1-2 / 场2-1` 这种首位数字乱跳的写法
- 先参考 `{sample_rel}` 的排版和壳层结构
{syntax_guidance}
"""


def _run_writer_task(batch_id: str, episode: str, brief_path: Path, *, syntax_first: bool = False) -> tuple[str, int]:
    prompt = _build_writer_prompt(batch_id, episode, brief_path, syntax_first=syntax_first)
    try:
        result = subprocess.run(
            ["claude", "-p", "--dangerously-skip-permissions", prompt],
            cwd=ROOT,
            check=False,
        )
    except FileNotFoundError:
        print("ERROR: `claude` CLI is not installed or not on PATH")
        return episode, 1
    return episode, result.returncode


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

    targets = _missing_drafts(episodes)
    if not targets:
        print(f"  ✓ All target drafts already exist for {args.batch_id}")
        return 0

    parallelism = max(1, min(args.parallelism, len(targets)))
    print(f"  → Claude writer target: {', '.join(targets)}")
    print(f"  → Batch brief: {_rel(brief_path)}")
    print(f"  → Parallelism: {parallelism}")
    if args.syntax_first:
        print("  → Mode: syntax-first")

    with ThreadPoolExecutor(max_workers=parallelism) as pool:
        futures = [
            pool.submit(_run_writer_task, args.batch_id, episode, brief_path, syntax_first=args.syntax_first)
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
