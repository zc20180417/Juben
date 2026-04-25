# Juben V1 本地部署说明

V1 是 agent-native 本地工具包：Python 只负责初始化、生成 prompt packet、维护状态和导出结果；真正的抽取、分集、写剧本、评审由具备文件读写能力的大模型 agent 执行。

## 适用对象

- 使用 Windows 的编剧、制片或运营同事。
- 有 Codex、Claude Code、Qwen Code 等本地 agent 环境。
- 希望把一篇小说 Markdown 改编成约 50 分钟竖屏短剧剧本。

## 快速开始

在仓库根目录运行：

```powershell
.\~init.cmd "被弃真千金：总裁不好惹.md" --episodes 25 --target-total-minutes 50
```

之后按 agent 提示执行三类工作：

```powershell
python .\juben\_ops\controller.py extract-book
python .\juben\_ops\controller.py map-book
.\~start.cmd batch01 --write
```

每批写完后：

```powershell
.\~review.cmd batch01 PASS --reviewer codex
.\~run.cmd batch01
.\~record.cmd batch01
.\~next.cmd
```

## 交付目录

`juben/output/` 是给人看的固定交付入口。每次 `run` 或 `export` 后刷新：

- `SUMMARY.md`：项目摘要、下一步、已发布剧集索引。
- `episodes/`：已发布剧本。
- `anchors/`：角色与声纹锚点。
- `manifest.json`：平台或工具可读取的机器索引。
- `_runtime/`：内部诊断材料，包含 prompts、reviews、briefs、maps、state、drafts。

普通交付只需要 `SUMMARY.md`、`episodes/`、`anchors/`。需要让另一个 agent 接手时，再交付 `manifest.json` 和 `_runtime/`。

手动刷新：

```powershell
python .\juben\_ops\controller.py export
```

## 命令边界

- `~init`：初始化当前项目。
- `~start`：准备批次；加 `--write` 生成 writer prompt packet。
- `~review`：回填批次评审结论。
- `~run`：正式发布当前批次到 `episodes/` 并刷新 `output/`。
- `~record`：把已发布批次写入状态摘要。
- `~next`：查看当前进度和下一步。
- `~clean`：备份并清理当前运行产物，用于重新测试工程能力。

## 使用原则

- 不让 Python 调模型 CLI，避免编码、超时、日志污染和嵌套 agent 不稳定。
- 不把 `harness/project/` 当交付目录；对外只交付 `output/`。
- 不把 reviewer 伪装成 lint；评审标准在 `juben/harness/framework/review-standard.md`，提示词在 `reviewer-prompt.template.md`。
- 换模型时只需要让新 agent 读取 prompt packet，并按文件路径写回指定 Markdown。
