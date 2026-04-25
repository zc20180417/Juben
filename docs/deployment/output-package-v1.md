# Juben Output 包结构

`juben/output/` 是 V1 的稳定交付面。它可以被删除，并通过下面命令完整重建：

```powershell
.\~export.cmd
```

## 公开交付层

- `SUMMARY.md`：给人看的项目摘要，包含状态、下一步、已发布剧集入口。
- `episodes/`：正式发布成稿，只放 `EP-xx.md`。
- `anchors/`：角色与声纹锚点，可给人工精修或审稿 agent 使用。
- `manifest.json`：给工具或平台读取的机器可读索引。

普通交付优先只看这几项。

## 内部诊断层

`_runtime/` 只给继续接手的 agent 或工程维护者看，普通交付可以忽略。

- `_runtime/drafts/`：当前草稿镜像。
- `_runtime/reviews/`：批次评审结论，包含 Markdown 与 JSON。
- `_runtime/prompts/`：已经生成过的 prompt packet。
- `_runtime/protocols/`：agent 执行 prompt packet 时必须读取的协议。
- `_runtime/briefs/`：批次 brief。
- `_runtime/maps/`：全书蓝图、source map、run manifest。
- `_runtime/state/`：连续性、关系、open loop 等状态摘要。

## 对外交付建议

只给编剧或制片看时，打包：

- `SUMMARY.md`
- `episodes/`
- `anchors/`

需要让另一个 agent 接手时，再加：

- `manifest.json`
- `_runtime/`
