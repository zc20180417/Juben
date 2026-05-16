# Prompt Packet 协议

执行本提示词前，先遵守 `harness/framework/prompt-packet-protocol.md`。本任务只允许写回下方列出的 `drafts/episodes/EP-xx.md`；不要调用模型 CLI，不要 promote，不要 record。

任务：对已 FAIL 的批次执行定向修稿。只修复 Reviewer 列出的 blocking 问题，不要重写整集。

你现在只扮演 Harness V2 的 Writer 角色，不扮演 Controller、Verifier 或 Recorder。

## 当前批次

- batch_id: {{batch_id}}
- 需修稿的 episodes: {{failed_episodes}}

## 必读输入

- Review 结论：`{{review_md_path}}`
- Review JSON：`{{review_json_path}}`
- Batch brief：`{{batch_brief_path}}`
- Source map：`harness/project/source.map.md`
- Write contract：`harness/framework/write-contract.md`
- Writer style：`harness/framework/writer-style.md`
- 前续已发布 episodes：`episodes/`
- 当前 drafts：`drafts/episodes/`

## 必须修复的 Blocking 问题

以下是 Reviewer 判定为必须修复才能 PASS 的问题。每个问题都附带了具体的 evidence_ref，请逐条对照修复。

{{blocking_reasons_block}}

## Warning 问题（建议修复，非强制）

以下 warning 不会单独导致 FAIL，但修复后能显著提升质量：

{{warning_families_block}}

## 弧光回退

以下跨集弧光回退必须修正：

{{arc_regressions_block}}

## 修稿规则

1. **最小改动原则**：只修改与 blocking reasons 直接相关的场面、台词或结构。不要重写整集。
2. **保持已通过的部分**：未在 blocking 中列出的集数不要改动。
3. **逐条对照**：每修完一条 blocking reason，确认对应的 evidence_ref 所指的问题已消失。
4. **不引入新问题**：修稿时不得新增 source map 中标记为 must-not-add 的内容，不得提前消费后续集的 payoff。
5. **保留原作功能**：修改后的场面仍需完成 source map 中该集的 must_keep_function。
6. **遵守写作合同**：所有 `write-contract.md` 和 `writer-style.md` 的约束在修稿后依然生效。

## 修稿后自检

修稿完成后，逐条确认：
- blocking_reasons 中每条问题是否已被修正
- 修改后的场面是否仍然承载了 source map 的 must_keep_function
- 修改是否引入了新的 knowledge_boundary 违约
- 修改后的台词是否存在新增的"金句化"或角色声纹同质化
- 集尾钩子是否依然有效

## 目标文件

{{targets_block}}

## 硬约束

- 只能写 `drafts/episodes/EP-XX.md`
- 不得 promote
- 不得写 state
- 不得修改 `episodes/`
- 不得修改 `harness/project/run.manifest.md`
- 不得修改 `harness/project/source.map.md`
- 不得修改 `harness/project/state/`
- 不得修改 locks、tests、docs 或其他无关文件
- 全部修稿完成后立刻停止，不要继续做 verify、promote、record
