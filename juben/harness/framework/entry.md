# Harness V2 Entry

本文件是 harness v2 的总入口。

## Smoke-First Semantics

Harness V2 的默认前置语义是 `smoke-first`：先确认剧本壳层、文件路径和 lane 形态都正确，再把注意力放到正文内容与情节推进上。

- `smoke` 检查优先覆盖壳层标记、样例对齐和最小可写结构
- 只要壳层不完整，就应按 fail-closed 处理，不进入后续正文修饰
- `passing-episode.sample.md` 是最小通过样例，后续 writer stage 应优先对齐它的结构而不是自由发挥

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
- 写作风格：`harness/framework/writer-style.md`
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
   - 不写回任何根目录旧 workflow 文件
   - 每次 record 必须追加 `run.log.md` 条目

## Fail Closed Rules
- batch brief 未冻结：禁止写作
- episode lock 被占用：禁止写作
- draft 未通过 verify：禁止 promote
- state lock 被占用：禁止 record
- `episodes/` 中的正式稿永不作为当前候选结果的写作输入

## Chat Command Aliases

在 agent 聊天界面里，用户消息如果以 `~` 开头，应先按本节解释成 workflow 命令，再决定是否执行 shell。

| 聊天命令 | 规范含义 | 对应 controller 命令 |
|---|---|---|
| `~init "<novel_file>" [--episodes <n>] --batch-size <n> --strategy <name> --intensity <name> [--key-episodes <ids>] [--force]` | 初始化/重建项目 scaffold；`--episodes` 是可选人工覆盖，默认由模型在 `extract-book` 后推荐并直接采用 | `python _ops/controller.py init "<novel_file>" [--episodes <n>] --batch-size <n> --strategy <name> --intensity <name> [--key-episodes <ids>] [--force]` |
| `~extract-book` | 基于整本原著生成 `book.blueprint.md`，先锁全书主线/弧光/反转/结局 | `python _ops/controller.py extract-book` |
| `~map-book` | 基于 `book.blueprint.md` 生成完整 `source.map.md` | `python _ops/controller.py map-book` |
| `~start <batch_id>` | 启动总入口：prepare → writer stage → run | `python _ops/controller.py start <batch_id>` |
| `~run <batch_id>` | 对已有 draft 执行快路径 | `python _ops/controller.py run <batch_id>` |
| `~check <batch_id>` | 只跑 lint gate + verify 计划输出 | `python _ops/controller.py check <batch_id>` |
| `~finish <batch_id>` | 完成 promote / validate / review / next | `python _ops/controller.py finish <batch_id>` |
| `~record <batch_id>` | 进入 record phase | `python _ops/controller.py record <batch_id>` |
| `~clean` | 备份并清理当前项目 runtime 数据缓存 | `python _ops/controller.py clean` |
| `~clear` | 与 `~clean` 同义；在本仓库里不是清空聊天记录 | `python _ops/controller.py clean` |
| `~status` | 查看当前 pipeline 状态 | `python _ops/controller.py status` |

解释规则：
- `~command` 在本仓库优先视为 harness workflow 命令，不优先按普通闲聊文本处理
- `~clear` 在本仓库中不是清空聊天记录，而是 `clean` 的聊天别名
- `~init` 需要的 `novel_file`、`--batch-size`、`--strategy`、`--intensity` 等参数按 `controller.py init` 语义处理；`--episodes` 是可选人工覆盖，不再是默认必填控制项
- 默认节奏约束是单集 1-3 分钟动态区间、平均按 2 分钟/集；`~extract-book` 需先给出推荐总集数，并默认直接写回 `run.manifest.md`
- `~extract-book` 先完成全书级抽取；`~map-book` 再把全书蓝图落成 `source.map.md`
- 若参数缺失且无法安全推断，先要求用户补全，而不是猜测 batch id
- root `AGENTS.md` / `CLAUDE.md` 只负责把 `~command` 路由到本节，不在根文件里重复维护命令语义

## Context Reset Protocol

长任务上下文过载时的防御机制：

- **batch 边界即 context 边界**：每个 batch（默认 5 集）是一个独立的执行单元；batch 切换时，writer subagent 应从干净上下文启动，只加载：
  - `run.manifest.md`
  - `source.map.md`（当前 batch 对应区段）
  - 当前 `batch brief`
  - `write-contract.md`
  - `writer-style.md`
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
- root `OPENAI.md` / `CLAUDE.md` 只路由到本文件和 `harness/project/run.manifest.md`
