# Input Contract

## Required Inputs
- `harness/project/run.manifest.md`
- `harness/project/book.blueprint.md`
- `harness/project/source.map.md`
- `harness/project/batch-briefs/batchNN_*.md`
- 原著正文
- 项目层角色与声纹资料

## Run Manifest Contract
必须字段：
- `total_episodes`
- `recommended_total_episodes`
- `episode_count_source`
- `target_total_minutes`
- `target_episode_minutes`
- `episode_minutes_min`
- `episode_minutes_max`
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

## Book Blueprint Contract
全书级蓝图至少包含：
- 集数建议（含 `recommended_total_episodes`）
- 主线
- 角色弧光
- 关系变化
- 关键反转
- 结局闭环
- 章节索引（仅定位）

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
