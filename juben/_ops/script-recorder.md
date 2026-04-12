# Script Recorder

本文件是 harness v2 的 record 执行规范。
模板权威来自 `memory-contract.md`；本文件定义执行顺序、抽取逻辑和验证步骤。

## Authoritative Inputs
- [memory-contract.md](../harness/framework/memory-contract.md)
- [promote-contract.md](../harness/framework/promote-contract.md)
- [run.manifest.md](../harness/project/run.manifest.md)

## Write Targets
- [script.progress.md](../harness/project/state/script.progress.md)
- [story.state.md](../harness/project/state/story.state.md)
- [relationship.board.md](../harness/project/state/relationship.board.md)
- [open_loops.md](../harness/project/state/open_loops.md)
- [quality.anchor.md](../harness/project/state/quality.anchor.md)
- [process.memory.md](../harness/project/state/process.memory.md)
- [run.log.md](../harness/project/state/run.log.md)

## Preconditions（record 执行前必须全部成立）
- controller 身份确认
- promote 已完成（batch brief 状态为 `promoted`）
- `state.lock` 为 `unlocked`
- 任一条不满足 → 拒绝执行，输出原因

## Execution Steps

### Step 1：Lock & Load
- 将 `state.lock` 写为 `locked`，owner 为当前 session
- 读取 `run.manifest.md` 获取当前 batch 范围
- 读取 promoted episodes（`episodes/EP-XX.md`）
- 读取 aligner 检查结果（lint JSON + aligner 判定）
- 读取现有 state 文件做增量基准

### Step 2：抽取（从 promoted episodes 中）
对每集抽取：
- 核心内容（一句话剧情概要）
- 前情衔接摘要（2-3 句：主要角色当前处境、未解决悬念、情感状态）
- 爽点
- 伏笔埋设与回收
- 人物状态变化
- aligner 检查记录：检查次数、首次结果、主要问题、薄弱原因标签（主标签/次标签/类型）

薄弱原因标签映射规则：
- lint `dialogue_rounds` / `pure_dialogue_run` → `对话不足`
- lint `triangle_sentence_count` / `triangle_visible_detail` → `描写空洞`
- lint `environment_anchor` / `ending_hook` / `scene_count` / `camera_count` / `sfx` / `sfx_total` → `成片感缺失`
- lint `psychological_comment_count` / 情绪层次失败 → `情绪单一` 或 `△心理评论`
- lint `os_vo_count` / `camera_count` / `sfx_total` → `标记缺失`
- lint `metaphor_count` → `比喻过密`
- lint `imagery_dense:*` / `imagery_repeat:*` → `意象单一`
- 角色区分度 / 禁用表达 / 声纹偏离 → `角色同腔`

### Step 3：写入 script.progress.md
按 `memory-contract.md` > State File Templates > script.progress.md 的必备 section 写入：
- 更新 `## 项目信息` 的进度百分比
- 更新 `## 基础文档` 时间戳
- 更新 `## 当前整季状态` 的当前批次
- 在 `## 分集记录` 中新增/更新本批各集
- 更新 `## 全局记录`（创作决策、伏笔总表）
- 更新 `## 质量统计`（检查记录表、高频问题 TOP3、质量趋势）
- 更新 `## 版本记录`

### Step 4：写入 story.state.md
按 `memory-contract.md` > State File Templates > story.state.md 的必备 section 写入：
- `## 当前阶段`：更新批次和阶段标签
- `## 权力格局`：更新角色当前位份/势力
- `## 主要角色位置`：更新物理位置/情感状态
- `## 最近关键转折（最近5集内）`：替换为本批转折
- `## 下一批关键预期`：基于 `source.map.md` 的下一批 must-keep beats 推导

触发条件：每 5 集更新，或批次结束时。

### Step 5：写入 relationship.board.md
按 `memory-contract.md` > State File Templates > relationship.board.md 的必备 section 写入：
- `## 核心关系网`：更新表格
- `## 最近关系变动`：替换为最近 5 集内
- `## 待爆关系线`：从 `source.map.md` 下一批推导

触发条件：每 5 集更新，或批次结束时。

### Step 6：写入 open_loops.md
按 `memory-contract.md` > State File Templates > open_loops.md 的必备 section 写入：
- `## 未回收伏笔`：新增本批埋设，标记已回收
- `## 未爆真相`：更新
- `## 待解冲突`：更新
- `## 已超期伏笔`：检查埋设超过 20 集的

触发条件：每次 promote 后实时更新。

### Step 7：条件写入 quality.anchor.md
按 `memory-contract.md` > State File Templates > quality.anchor.md 的必备 section 写入：
- 触发条件：首批 3-5 集通过后初次建立，或用户认可新基准时重置
- 从本批 promoted episodes 和 lint 数据中计算：
  - 场景厚度（平均行数、△句数）
  - 对话节奏（最长连续纯对白）
  - os 使用方式（数量、用途分类）
  - 表情/镜头/音效密度
  - 代表性打法（代表性台词风格、场景打法、留白手法）

### Step 8：写入 process.memory.md
- 仅当本批出现新的流程问题时更新
- 按 `memory-contract.md` > State File Templates > process.memory.md 的必备 section：
  - `## 活跃流程问题`：新增条目（日期、问题、归类、防复发）
  - `## 当前执行准则`：如有变化则更新

### Step 9：写入 run.log.md
按 `memory-contract.md` > Run Log Contract 追加本批 log entries：
- 为本批每集的 draft_write / verify / promote 各追加一条
- 为本次 record 追加一条
- 如本批有 recovery 事件（context reset / 人工介入），追加对应条目
- 只追加，不修改历史条目

### Step 10：Validate & Unlock
- 对每个写入的 state 文件，检查 `memory-contract.md` 要求的必备 section 是否全部存在
- 缺失任一必备 section → 记录到 `process.memory.md` 并告警
- 将 `state.lock` 写回 `unlocked`
- 输出本次 record 摘要

## Output Format

```
[RECORD COMPLETE]
- batch: EP-XX ~ EP-YY
- script.progress.md: ✓ 更新（进度 N%）
- story.state.md: ✓ 更新 / ⊘ 未触发
- relationship.board.md: ✓ 更新 / ⊘ 未触发
- open_loops.md: ✓ 更新
- quality.anchor.md: ✓ 建立/更新 / ⊘ 未触发
- process.memory.md: ✓ 更新 / ⊘ 无新问题
- run.log.md: ✓ 追加 N 条
- state.lock: unlocked
```

