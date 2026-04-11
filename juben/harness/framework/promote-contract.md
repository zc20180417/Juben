# Promote Contract

## Draft -> Verify -> Promote
- writer 只能写 `drafts/episodes/EP-XX.md`
- verify 只能检 draft
- promote 只能由 controller 执行
- promote 后才允许 record

## Promote Preconditions
- 当前 `batch brief` 状态为 `frozen`
- 当前 batch 的 draft 全部存在
- 当前 batch 的 draft 全部 lint PASS
- aligner / regression gate PASS
- `state.lock` 为空闲

## Promote Effects
- 将对应 draft 覆盖写入 `episodes/EP-XX.md`
- 更新 batch brief 为 `promoted`
- 更新 `run.manifest.md`
- 更新 `harness/project/state/*`

## Forbidden
- writer 直接覆盖 `episodes/EP-XX.md`
- verify 阶段读取 published lane 作为当前候选结果
- promote 后回写 legacy v1 文件作为权威
