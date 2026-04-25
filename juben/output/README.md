# Juben Output

这里是给外部使用者看的交付入口。每次运行 `export` 都会完整重建本目录。

## 常用入口

- `SUMMARY.md`：项目摘要、状态和成稿入口
- `episodes/`：正式成稿，只放 `EP-xx.md`
- `anchors/`：角色与声纹锚点，可用于人工精修
- `manifest.json`：给工具或平台读取的机器可读索引
- `_runtime/`：内部诊断包，普通交付可忽略

## `_runtime/` 内容

- `_runtime/drafts/`：当前草稿镜像
- `_runtime/reviews/`：批次评审结论，包含 Markdown 与 JSON
- `_runtime/prompts/`：可交给 agent 执行的提示词包
- `_runtime/briefs/`：批次 brief
- `_runtime/maps/`：全书蓝图、source map、run manifest
- `_runtime/protocols/`：agent 执行 prompt packet 时必须读取的协议
- `_runtime/state/`：连续性、关系、open loop 等状态摘要

## 刷新方式

```powershell
.\~export.cmd
```

## 当前导出统计

- episodes: 25
- drafts: 25
- reviews: 10
- prompts: 8
- briefs: 5
- maps: 3
- anchors: 2
- protocols: 1
- state: 7
