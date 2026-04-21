from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_BLUEPRINT = ROOT / "harness" / "project" / "book.blueprint.md"
SOURCE_MAP = ROOT / "harness" / "project" / "source.map.md"
RUN_MANIFEST = ROOT / "harness" / "project" / "run.manifest.md"
ENTRY = ROOT / "harness" / "framework" / "entry.md"
LLM_CLI_ENV = "JUBEN_LLM_CLI"
SUPPORTED_LLM_CLIS = ("codex", "qwen", "claude")


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
- 返回完整的 `{source_map_rel}` 正文

硬约束：
- 输出内容里只能是 `source.map.md` 正文
- 不要模拟 controller，不要汇报状态，不要写“初始化快照”“下一步建议”“我已读取”“运行态还停在”这类句子
- 不要描述 lock、draft、state、promote、run.log 状态
- 不要给用户下命令，不要说“如果你要我继续”
- 不要返回解释，不要返回补充说明，不要返回 Markdown 代码块，不要返回链接
- 最终输出必须满足外部给定的 JSON Schema
- 把完整的 `source.map.md` 正文放进 `source_map` 字段
- `source_map` 字段里的正文必须以 `# Source Map` 开头
- 严格沿用 `{source_map_rel}` 当前已有的标题顺序、字段名和骨架；只填内容，不要自创结构
- 删除或替换所有占位标记
- 不再保留 `mapping_status: pending_book_extraction`

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
  - `**function_signals**:`
  - `**ending_function**:`
  - `**irreversibility_level**:`
  - `**must-not-add / must-not-jump**:`
- `must-keep_beats` 必须写成 3-5 条“可直接执行的改编任务”，不能只复述集标题或抽象氛围词
- `must-keep_beats` 的每一条都必须以标签开头，只允许使用这些标签：
  - `【信息】`
  - `【关系】`
  - `【动作】`
  - `【权力】`
  - `【钩子】`
- 推荐做法：同一集至少覆盖其中 2-3 种标签，避免所有 beats 都是同一种功能
- 每条 `must-keep_beats` 至少要落到以下之一：
  - 新信息被谁得知
  - 关系发生了什么变化
  - 权力位置/主导权发生了什么变化
  - 有什么不可逆动作或明确决定
  - 本集结尾钩子是靠什么具体事件立住
- 可接受示例：
  - `【信息】傅斯年第一次明确知道时鸢不是苏清月，只是长得像`
  - `【关系】时鸢对苏家从保留观察转为明确切割`
  - `【动作】亲子鉴定结果被当众拆封，时鸢当场转身离开`
  - `【钩子】主持人即将喊出“鸢”出场，卡黑`
- 禁止把 beat 写成这种空话：
  - “冷静拒认”
  - “埋下钩子”
  - “矛盾升级”
  - “情绪拉扯”
  除非后面紧跟具体动作、信息变化或关系变化
- 相邻两集如果只是重复同一种羞辱、盘问、试探、误会，而没有新的信息变化/关系变化/动作结果，映射阶段就要压缩或合并，不能硬拆成两集
- 必须保护角色知识边界；某集的 beat 只能要求角色说出当时已经获得的信息，不能把作者已知信息提前塞进该集
- 如果某集的 `source_chapter_span` 已经包含硬事件本体，当前集就必须正面承载这个事件，不能故意拖到下一集。这里的硬事件包括但不限于：
  - 鉴定结果被揭晓
  - 真名/真实身份被正式说破
  - 关键人物公开登场
  - 关系被正式确认或正式切断
  - 公开场合的打脸/揭露已经发生
- `【钩子】` 可以卡在硬事件发生后的余波、反应、决定、后果上，但不能在 source span 已经写出事件本体时，还把本集写成“等待期间”“掉马前夜”“即将介绍出场”“马上就要揭晓”
- 如果你发现当前切给某一集的 source span 已经跨过了一个硬事件，而原定集功能却想把它留到下一集，那么必须调整映射切分或重写本集 beat；不得用 `must-not-add / must-not-jump` 人为压住 source span 已经发生的主事件
- 禁止出现这种自相矛盾的映射：
  - `source_chapter_span` 已含鉴定结果正文，但 `must-keep_beats` 还写“鉴定等待期间”
  - `source_chapter_span` 已含公开揭露或正式登场，但 `【钩子】` 还写“即将介绍出场”
  - `source_chapter_span` 已含明确身份揭露，但本集 beat 还写“保持身份未揭露”
- 每集都要让 writer 看完后知道“这一集必须完成什么变化”，而不是让 writer 自己脑补集功能
- 为兼容旧解析与结构检查，文件中仍需保留这些 legacy 绑定词：
- 用中文写，面向后续 batch/episode 生产

- 你要返回的是一份完整的新 `source.map.md`，不是在旧答案上做局部修补
- 保持下面这类最小骨架，不要扩展新字段：
  - 文件头：
    - `# Source Map`
    - `- mapping_status: complete`
    - `- total_episodes: ...`
    - `- batch_size: ...`
    - `- total_batches: ...`
    - `- target_episode_minutes: ...`
    - `- episode_minutes_min: ...`
    - `- episode_minutes_max: ...`
    - `- adaptation_strategy: ...`
    - `- dialogue_adaptation_intensity: ...`
  - 批次头：
    - `## Batch 01 (EP01-05): 批次标题`
    - `原著范围：第X章前半 ~ 第Y章后半`
  - ??????
    - `### EP01: ?????
    - `**source_chapter_span**: ...`
    - `source chapter span??..`
    - `**must-keep_beats**:`
    - `**function_signals**:`
    - `**ending_function**: ...`
    - `**irreversibility_level**: ...`
    - `**must-not-add / must-not-jump**:`
    - `function_signals` ???????????pening_function / middle_functions / strong_function_tags
    - `ending_function` ????????arrival / confrontation_pending / reveal_pending / locked_in / reversal_triggered / emotional_payoff / closure
    - `irreversibility_level` ????????soft / medium / hard

写完后立刻停止；不要再补一句说明。
"""


def _extract_source_map_markdown(stdout: str) -> str:
    text = stdout.strip()
    if "```" in text:
        fenced = text.split("```")
        if len(fenced) >= 3:
            text = "".join(fenced[1:-1]).strip()
            if text.lower().startswith("markdown"):
                text = text[len("markdown"):].lstrip()
    marker = "# Source Map"
    idx = text.find(marker)
    if idx != -1:
        text = text[idx:]
    return text.strip() + "\n"


def _safe_preview(text: str, limit: int = 1000) -> str:
    preview = text[:limit]
    return preview.encode("ascii", "backslashreplace").decode("ascii")


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


def _build_llm_command(
    cli: str,
    executable: str,
    prompt: str,
    output_path: Path | None = None,
    schema_path: Path | None = None,
) -> list[str]:
    if cli == "codex":
        command = [executable, "exec", "--dangerously-bypass-approvals-and-sandbox", "-C", str(ROOT)]
        if schema_path is not None:
            command.extend(["--output-schema", str(schema_path)])
        if output_path is not None:
            command.extend(["-o", str(output_path)])
        command.append(prompt)
        return command
    if cli == "qwen":
        return [executable, "-p", prompt, "-y"]
    if cli == "claude":
        return [executable, "-p", "--dangerously-skip-permissions", prompt]
    raise ValueError(f"Unsupported LLM CLI: {cli}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run source-map generation backend")
    parser.add_argument("--novel-file", required=True)
    parser.add_argument("--episodes", required=True, type=int)
    parser.add_argument("--batch-size", required=True, type=int)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--intensity", required=True)
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
        resolved_cli = _resolve_llm_cli()
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    if resolved_cli is None:
        print(f"ERROR: no supported LLM CLI found on PATH (tried: {', '.join(SUPPORTED_LLM_CLIS)})")
        return 1
    cli, executable = resolved_cli

    print(f"  -> Map backend: {cli}")
    print(f"  -> map-book target: {_rel(SOURCE_MAP)}")
    print(f"  -> Blueprint: {_rel(BOOK_BLUEPRINT)}")

    output_path: Path | None = None
    schema_path: Path | None = None
    if cli == "codex":
        temp_dir = Path(tempfile.mkdtemp(prefix="juben-map-"))
        output_path = temp_dir / "map-output.json"
        schema_path = temp_dir / "map-schema.json"
        schema_path.write_text(
            json.dumps(
                {
                    "type": "object",
                    "properties": {
                        "source_map": {
                            "type": "string",
                            "description": "Complete contents of source.map.md as Markdown",
                        }
                    },
                    "required": ["source_map"],
                    "additionalProperties": False,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    try:
        result = subprocess.run(
            _build_llm_command(cli, executable, prompt, output_path=output_path, schema_path=schema_path),
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=_llm_subprocess_env(),
        )
    except FileNotFoundError:
        print(f"ERROR: `{cli}` CLI is not installed or not on PATH")
        return 1

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")
        return result.returncode

    raw_output = result.stdout or ""
    if cli == "codex" and output_path is not None and output_path.exists():
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        raw_output = payload.get("source_map", "")

    final_markdown = _extract_source_map_markdown(raw_output)
    if not final_markdown.startswith("# Source Map"):
        print("ERROR: map backend did not return a complete source map document")
        if raw_output:
            print(_safe_preview(raw_output))
        return 1

    SOURCE_MAP.write_text(final_markdown, encoding="utf-8")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
