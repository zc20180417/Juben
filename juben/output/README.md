# Juben Output

这里是给人看的固定入口。内部流程仍使用 `harness/project`、`drafts`、`episodes` 等运行目录，本目录只保存可随时重建的导出镜像。

## 常用入口

- `episodes/`：已发布成稿，只放 `EP-xx.md`
- `drafts/`：当前草稿镜像，只放 `EP-xx.md`
- `reviews/`：批次评审结论，包含 Markdown 与 JSON
- `prompts/`：可交给 agent 执行的提示词包
- `briefs/`：批次 brief
- `maps/`：全书蓝图、source map、run manifest
- `anchors/`：角色与声纹锚点
- `state/`：连续性、关系、open loop 等状态摘要

## 刷新方式

```powershell
python _ops/controller.py export
```

## 当前导出统计

- episodes: 20
- drafts: 20
- reviews: 8
- prompts: 5
- briefs: 4
- maps: 3
- anchors: 2
- state: 7
