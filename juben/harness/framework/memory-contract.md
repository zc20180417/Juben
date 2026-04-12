# Memory Contract

## Story Memory
项目剧情上下文只允许写入：
- `harness/project/state/script.progress.md`
- `harness/project/state/story.state.md`
- `harness/project/state/relationship.board.md`
- `harness/project/state/open_loops.md`
- `harness/project/state/quality.anchor.md`

## Process Memory
流程层失败模式、误差类型、临时补强规则只允许写入：
- `harness/project/state/process.memory.md`

## Memory Rules
- story memory 只记录剧情与角色事实
- process memory 只记录执行层问题与防复发规则
- 不得把流程失败模式塞进 story memory
- 不得把剧情事实写进 process memory

## State File Templates

### script.progress.md
必备 section：
- `## 项目信息`：剧名、类型、adaptation_mode、adaptation_strategy、dialogue_adaptation_intensity、集数、进度
- `## 基础文档`：各素材文件状态与时间戳
- `## 当前整季状态`：active profile、当前阶段、当前批次、质量锚状态
- `## 分集记录`：每集包含状态、核心内容、前情衔接摘要、爽点、伏笔（埋设/回收）、人物、aligner 检查记录（检查次数、首次结果、主要问题、薄弱原因标签：主标签/次标签/类型）
- `## 全局记录`：创作决策、创作规则、待处理事项、伏笔总表
- `## 质量统计`：检查记录表（集数/检查次数/首次结果/主标签/次标签/类型/最终通过）、高频问题 TOP3、质量趋势
- `## 版本记录`：当前版本序号、最近变更

### story.state.md
必备 section：
- `## 当前阶段`：active profile、阶段标签、当前批次、下一批次
- `## 权力格局`：各角色当前位份/势力/靠山/筹码，当前最大威胁
- `## 主要角色位置`：物理位置/情感状态/当前目标
- `## 最近关键转折（最近5集内）`
- `## 下一批关键预期`：预期爽点、反派动作、关系变化

### relationship.board.md
必备 section：
- `## 核心关系网`：表格（角色A/角色B/关系类型/当前状态/变化趋势）
- `## 最近关系变动`：最近5集内
- `## 待爆关系线`：埋了什么线、预计什么时候爆

### open_loops.md
必备 section：
- `## 未回收伏笔`：表格（埋设集/内容/计划回收/紧急度/备注）
- `## 未爆真相`
- `## 待解冲突`
- `## 已超期伏笔（埋设超过20集未回收）`

### quality.anchor.md
必备 section：
- 基准样集与建立时间
- `## 场景厚度`：平均每场行数、△描写平均句数
- `## 对话节奏`：平均最长连续纯对白、对话主特征
- `## os 使用方式`：平均每集 os 数、os 典型用途
- `## 表情 / 镜头 / 音效密度`：每集镜头数、每场音效数
- `## 代表性打法`：代表性台词风格、场景打法、留白手法

### process.memory.md
必备 section：
- `## 活跃流程问题`：每条包含日期、问题描述、归类、防复发规则
- `## 当前执行准则`

### run.log.md
必备 section：
- `## Log Entries`：每条包含时间戳、batch、episode、phase、event、result、备注

## Run Log Contract

`harness/project/state/run.log.md` 是 harness v2 的运行日志。

### 记录范围
每次以下事件发生时必须追加一条 log entry：
- `plan_inputs`：batch brief 冻结
- `draft_write`：writer 提交 draft
- `verify`：aligner 输出 PASS/FAIL（附 FAIL 原因摘要）
- `promote`：controller 执行 promote
- `record`：recorder 完成状态写入
- `recovery`：context reset / 人工介入 / 回滚

### Entry 格式
```
| 时间戳 | batch | episode | phase | event | result | 备注 |
```

### 管理规则
- recorder 在 Step 9 之前写入本批的 log entries
- aligner 在 Step 8 输出后由 controller 补记 verify entry
- log 只追加，不删除、不修改历史条目
- 超过 200 行时，将已完成 batch 的条目归档到 `run.log.archive.md`
