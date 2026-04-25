# Prompt Packet 通用协议

本协议定义任意大模型 agent 执行 Juben prompt packet 时必须遵守的输入、输出和完成约定。它适用于 Codex、Claude Code、Qwen Code、DeepSeek agent 或其他能读写本地文件的 agent。

## 角色边界

- Python/controller 只负责初始化、生成 prompt packet、维护状态、发布和导出。
- Agent 只负责读取 prompt packet、执行其中指定的创作或评审任务、写回目标文件。
- Agent 不要调用另一个模型 CLI，不要嵌套启动其它 agent，不要把模型输出只留在聊天窗口。
- Agent 不要自行 promote、record、改锁、改 manifest，除非 prompt packet 明确要求。

## 执行流程

1. 读取 prompt packet 顶部列出的所有必读输入。
2. 确认目标文件列表和允许写入范围。
3. 逐个写回目标文件，文件必须真实落盘。
4. 写完后做最小自检：目标文件是否存在、是否为空、是否覆盖了本任务要求。
5. 在聊天里只汇报完成状态、写入文件、阻塞原因或下一步命令，不要长篇复述生成内容。

## 输入约定

Prompt packet 会明确列出：

- 必读文件：如 batch brief、source map、source excerpt、review standard、角色/声纹锚点。
- 当前任务：如 extract、map、writer、review、polish。
- 目标文件：必须写回的文件路径。
- 写入边界：允许和禁止修改的目录。
- 完成后下一步：例如 `.\~start.cmd batch01 --write`、`.\~review.cmd batch01 PASS --reviewer <name>`。

如果 prompt packet 和其它文件冲突，以 prompt packet 的“目标文件 / 写入边界 / 当前任务”优先。

## 输出约定

Agent 必须直接写入 prompt packet 指定的目标文件。常见目标包括：

- `harness/project/book.blueprint.md`
- `harness/project/source.map.md`
- `drafts/episodes/EP-xx.md`
- `harness/project/reviews/*.review.json`
- `harness/project/reviews/*.review.md`
- `harness/project/reviews/*.polish.md`

输出不能只出现在聊天回复里。聊天回复只能作为状态说明。

## 失败约定

如果无法完成，必须明确说明：

- 哪个目标文件没有写入。
- 缺少哪个输入文件或权限。
- 是否已有部分文件写入。
- 用户下一步应运行哪个 `~命令` 或修复哪个文件。

不要在失败时伪造 PASS、不要写空文件冒充完成、不要跳过目标文件。

## 完成判定

任务完成的最低标准：

- prompt packet 指定的每个目标文件都存在。
- 文件内容不是占位说明。
- writer 任务中每个目标 episode 都有独立 Markdown 文件。
- review 任务中 JSON 与 Markdown 结论一致。
- polish 任务中被改 draft 与 polish report 同时存在。

## 命令约定

对用户展示时优先使用根目录 `~命令`：

- `.\~extract.cmd`
- `.\~map.cmd`
- `.\~start.cmd batch01 --write`
- `.\~check.cmd batch01`
- `.\~polish.cmd batch01`
- `.\~review.cmd batch01 PASS --reviewer <name>`
- `.\~run.cmd batch01`
- `.\~promote.cmd batch01`
- `.\~record.cmd batch01`
- `.\~next.cmd`
- `.\~status.cmd`
- `.\~export.cmd`

底层 `python _ops/controller.py ...` 是实现细节，不作为普通用户入口。
