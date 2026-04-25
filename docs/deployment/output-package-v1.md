# Juben Output 包结构

`juben/output/` 是 V1 的稳定交付面。它可以被删除并通过 `python .\juben\_ops\controller.py export` 重建。

## 必看文件

- `SUMMARY.md`：给人看的总览。先看这里判断项目状态、下一步、已发布剧集。
- `manifest.json`：给工具看的索引。包含 source、目标集数、批次状态、成稿路径和下一步动作。
- `README.md`：解释各子目录用途。

## 子目录

- `episodes/`：正式发布稿，只放 `EP-xx.md`。
- `drafts/`：当前草稿镜像，不代表已发布。
- `reviews/`：批次评审 JSON/Markdown。
- `prompts/`：给 agent 执行的 prompt packet。
- `briefs/`：批次任务说明。
- `maps/`：全书蓝图、source map、run manifest。
- `anchors/`：角色和声纹锚点。
- `state/`：故事连续性、关系、open loop 等状态摘要。

## 对外交付建议

只需要给编剧或制片看时，打包：

- `SUMMARY.md`
- `episodes/`
- `maps/book.blueprint.md`
- `maps/source.map.md`

需要让另一个 agent 接手时，再加：

- `manifest.json`
- `reviews/`
- `prompts/`
- `briefs/`
- `state/`
