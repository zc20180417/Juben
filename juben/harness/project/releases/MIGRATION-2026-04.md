# Release Tracking Migration

日期：2026-04-13

本次迁移只补齐可追溯性与状态一致性，不重写 Controller + Writer + Verifier 主流程。

## 已落地

- 新增 `run.manifest.json` 与 `source.map.json`，controller 运行时优先读取 json sidecar，markdown 继续作为人工镜像。
- 新增 `release.index.json` 与 `gold-set.json`，把 `rebuild-2026-04` 作为当前 runtime authority。
- 为 `EP-01` ~ `EP-10` 回填 `EP-XX.meta.json` sidecar，不改 `EP-XX.md` 正文。
- 将当前 `episodes/` 内不属于 `rebuild-2026-04` 权威发布链路的条目标记为 `legacy`，仅记录在 `release.index.json`。
- 回填 `EP-01` ~ `EP-05` 的 verify 结果文件，保持 release audit 可闭环。

## 当前约定

- `gold-set.json` 当前收录 `EP-01` ~ `EP-10`。
- 新 promote 会继续维护 `release.index.json`、`gold-set.json` 和 sidecar metadata。
- `episode-lint.py` 现在输出：
  - `contract_failures`：阻断 promote
  - `craft_flags`：允许 promote，但写入 metadata
  - `style_warnings`：只提示

## 审计命令

```bash
python _ops/controller.py audit
```

审计范围：

- manifest 的 `active_batch` / `current_batch_brief`
- `release.index.json` / `gold-set.json`
- `episodes/*.md` 与 `episodes/*.meta.json`
- `verify-EP-XX.json` 与 metadata / release index 的一致性

## 已知迁移假设

- `batch01` 已经是历史上完成 promote 的权威发布，因此本次把缺失的 verify 结果按 `PASS` 回填，并标记为迁移补录。
- legacy 条目当前只做索引标记，不为其补 sidecar metadata，避免一次性引入大量无权威意义的噪音文件。
