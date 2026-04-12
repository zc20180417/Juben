# Harness V2 Entry

本文件是 harness v2 的总入口。

## Role Architecture

本 harness 采用三角色分离架构，防止"自己写自己判"的认知偏差：

| 角色 | 职责 | 执行主体 | 不得做 |
|---|---|---|---|
| **Controller** | 调度 phase、冻结 batch brief、执行 promote 和 record | 主控 agent / 人 | 不得直接写正文 |
| **Writer** | 在 draft lane 写候选正文 | writer subagent | 不得 promote、不得写 state、不得读 published lane 作为当前输入 |
| **Verifier** | 校验 draft lane，输出 PASS/FAIL | aligner | 不得修改 draft、不得 promote |

- Controller 指派 Writer 写 → Verifier 校 → Controller 决定 promote/打回
- 三个角色不得由同一个 agent 在同一轮中兼任
- 人可以担任 Controller 角色，直接下达 promote/打回决策

## Source Of Truth
- 运行时总线：`harness/project/run.manifest.md`
- 输入装配：`harness/framework/input-contract.md`
- 写作约束：`harness/framework/write-contract.md`
- 校验约束：`harness/framework/verify-contract.md`
- 发布通道：`harness/framework/promote-contract.md`
- 记忆与状态：`harness/framework/memory-contract.md`
- 回归阻断：`harness/framework/regression-contract.md`

## Runtime Phases
1. `plan_inputs`
   - 读取 `run.manifest.md`
   - 解析 `source.map.md`
   - 冻结当前 `batch brief`
   - 获取对应 lock
2. `draft_write`
   - writer 只允许写 `drafts/episodes/EP-XX.md`
   - 不得直写 `episodes/EP-XX.md`
3. `verify`
   - 只读取 draft lane
   - 机械计数由 `_ops/episode-lint.py` 承担
   - 定性 gate 由 `verify-contract.md` + `harness/project/regressions/` 下的活跃回归 pack 承担
4. `promote`
   - 只有 controller 可以把 draft promote 到 `episodes/`
   - promote 后才允许记录状态文件
5. `record`
   - 只更新 `harness/project/state/*`
   - 不回写 legacy v1 文件
   - 每次 record 必须追加 `run.log.md` 条目

## Fail Closed Rules
- batch brief 未冻结：禁止写作
- episode lock 被占用：禁止写作
- draft 未通过 verify：禁止 promote
- state lock 被占用：禁止 record
- `episodes/` 中的正式稿永不作为当前候选结果的写作输入

## Context Reset Protocol

长任务上下文过载时的防御机制：

- **batch 边界即 context 边界**：每个 batch（默认 5 集）是一个独立的执行单元；batch 切换时，writer subagent 应从干净上下文启动，只加载：
  - `run.manifest.md`
  - `source.map.md`（当前 batch 对应区段）
  - 当前 `batch brief`
  - `write-contract.md`
  - `voice-anchor.md` / `character.md`
  - 前一个 batch 的 `story.state.md` + `relationship.board.md` + `open_loops.md`（只读摘要，不加载全部正文）
- **不跨 batch 累积正文上下文**：writer 不得把前 batch 的全部 episode 正文带入当前 batch 的生成上下文
- **verify 独立上下文**：verifier 每次校验从干净上下文启动，只加载 draft + 合同 + source.map + state 摘要
- **context reset 触发条件**：
  - batch 切换时强制 reset
  - 单集 verify 连续 FAIL 3 次时，controller 应 reset writer 上下文后重试
  - controller 判断 writer 输出开始跑偏（重复模式、无视合同）时可主动 reset

## Recovery Protocol

verify FAIL 后的恢复策略：

### 单集恢复
1. **第 1 次 FAIL**：writer 在当前上下文中修改，重新提交 verify
2. **第 2 次 FAIL**：writer 仍在当前上下文修改，但 controller 必须审查 FAIL 原因是否重复
3. **第 3 次 FAIL**：触发 context reset — writer 从干净上下文重写该集，不带入前两次的失败稿
4. **第 4 次 FAIL**：升级到人工介入 — controller 暂停该集，输出累计 FAIL 原因摘要，等待人决策

### 批次恢复
- 同一 batch 内 3 集及以上进入第 3 次 FAIL：整个 batch 暂停，controller 输出批次问题摘要
- 连续 2 个 batch 出现批次暂停：controller 建议重新审视 `source.map.md` 的映射是否合理

### 回滚
- promote 前的所有失败都在 draft lane 内解决，不影响 published lane
- 若 promote 后发现问题（极端情况）：controller 可回退 `run.manifest.md` 的 `active_batch` 到上一个状态，但已 promote 的 `episodes/` 文件不自动删除，需人确认

### 日志
- 每次 FAIL → 修改 → 重新 verify 的循环必须记录到 `run.log.md`
- recovery 升级（context reset / 人工介入）必须记录到 `process.memory.md`

## Entry Routing
- root `AGENTS.md` 只路由到本文件和 `harness/project/run.manifest.md`
- root `OPENAI.md` / `CLAUDE.md` 只路由到本文件
