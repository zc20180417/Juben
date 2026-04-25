# Juben Agent Runbook

本文件写给执行 Juben prompt packet 的大模型 agent。适用于 Codex、Claude Code、Qwen Code、DeepSeek agent，或任何能读取并写入本地文件的 agent。

## 核心边界

- 你只执行 prompt packet 指定的任务。
- 你必须把结果写入 prompt packet 指定的目标文件。
- 你不要调用另一个模型 CLI，不要嵌套启动其它 agent。
- 你不要自行 `run`、`promote`、`record`、改锁、改 manifest，除非 prompt packet 明确要求。
- 你不要只在聊天窗口回复生成内容；聊天窗口只汇报完成状态、写入文件和阻塞原因。

## 每次执行前

1. 先读 `harness/framework/prompt-packet-protocol.md`。
2. 再读当前 prompt packet。
3. 按 prompt packet 中的“必读文件”读取上下文。
4. 确认“目标文件”和“允许写入范围”。
5. 只写入这些目标文件。

## 常见任务

### Extract

输入通常是 `harness/project/prompts/extract-book.prompt.md`。

你要写回：

- `harness/project/book.blueprint.md`
- `character.md`
- `voice-anchor.md`

完成后停止，让操作者运行：

```powershell
.\~map.cmd
```

### Map

输入通常是 `harness/project/prompts/map-book.prompt.md`。

你要写回：

- `harness/project/source.map.md`

完成后停止，让操作者运行：

```powershell
.\~start.cmd batch01 --write
```

### Writer

输入通常是 `harness/project/prompts/batchXX.writer.batch.prompt.md` 或单集 writer prompt。

你要写回：

- `drafts/episodes/EP-xx.md`

写作时优先遵守：

- batch brief 的当前集任务与 beats。
- source map 的 source 顺序、边界和禁止越界信息。
- `write-contract.md` 与 `writer-style.md`。

完成后停止，让操作者运行：

```powershell
.\~start.cmd batchXX --write
```

### Reviewer

输入通常是 `harness/project/reviews/batchXX.review.prompt.md`。

你要写回：

- `harness/project/reviews/batchXX.review.json`
- `harness/project/reviews/batchXX.review.md`

你只判断质量，不改稿。完成后让操作者按结论运行：

```powershell
.\~review.cmd batchXX PASS --reviewer <name>
```

或：

```powershell
.\~review.cmd batchXX FAIL --reviewer <name> --reason "具体阻塞原因"
```

### Polish

输入通常是 `harness/project/prompts/batchXX.polish.prompt.md`。

你只允许编辑指定 draft，并写回 polish report。不要改 `episodes/`。

## 完成标准

- 每个目标文件都存在。
- 目标文件不是空文件或占位说明。
- writer 任务中每个目标 episode 都有独立 Markdown 文件。
- review 任务中 JSON 和 Markdown 结论一致。
- polish 任务中 draft 和 polish report 同时存在。

## 失败时必须说明

- 哪个目标文件没有写入。
- 缺少哪个输入文件或权限。
- 是否已有部分文件写入。
- 操作者下一步应该运行哪个 `~` 命令或修复哪个文件。
