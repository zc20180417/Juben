# Input Contract

## Required Inputs
- `harness/project/run.manifest.md`
- `harness/project/source.map.md`
- `harness/project/batch-briefs/batchNN_*.md`
- 原著正文
- 项目层角色与声纹资料

## Run Manifest Contract
必须字段：
- `adaptation_mode`
- `adaptation_strategy`
- `dialogue_adaptation_intensity`
- `generation_execution_mode`
- `generation_reset_mode`
- `run_status`
- `active_batch`
- `source_authority`
- `draft_lane`
- `publish_lane`
- `promotion_policy`

## Source Map Contract
每个 batch / episode 至少包含：
- batch 范围
- episode 范围
- source chapter span
- must-keep beats
- must-not-add
- must-not-jump
- ending type

## Batch Brief Contract
每份 `batchNN_*.md` 至少包含：
- `batch status`
- `owned episodes`
- `source excerpt range`
- `adjacent continuity`
- `draft output paths`
- `verify checklist`

## Lane Contract
- candidate lane：`drafts/episodes/`
- publish lane：`episodes/`
- verify 阶段只允许读 candidate lane
- published lane 只允许作为已发布历史结果被引用，不允许作为当前候选正文覆盖写作

## Lock Contract
- `batch.lock`：当前批次唯一主控锁
- `episode-XX.lock`：单集写作锁
- `state.lock`：状态文件写入锁
