# Script Aligner

本文件是 harness v2 的 verify 执行规范。
规则权威来自 `verify-contract.md`；本文件定义执行顺序、判定逻辑和输出格式。

## Authoritative Inputs
- [verify-contract.md](../harness/framework/verify-contract.md)
- [regression-contract.md](../harness/framework/regression-contract.md)
- [regressions/](../harness/project/regressions/)
- [run.manifest.md](../harness/project/run.manifest.md)
- [source.map.md](../harness/project/source.map.md)
- [voice-anchor.md](../voice-anchor.md)（优先）→ 回退 [character.md](../character.md)
- [quality.anchor.md](../harness/project/state/quality.anchor.md)（如存在）
- [script.progress.md](../harness/project/state/script.progress.md)
- [story.state.md](../harness/project/state/story.state.md)
- [relationship.board.md](../harness/project/state/relationship.board.md)
- [open_loops.md](../harness/project/state/open_loops.md)

## Scope
- 只校验 `drafts/episodes/EP-XX.md`
- published lane `episodes/` 不作为当前候选正文
- 输出语言：中文

## Execution Steps

### Step 1：Lint Gate
- 对目标 draft 运行 `_ops/episode-lint.py`
- 读取 JSON 输出的 `checks.scene_failures` / `checks.episode_failures` / `checks.warnings`
- 有 failure → 直接 FAIL，不进入后续步骤
- lint warnings 带入 Step 6 的 WARNING 累计

### Step 2：Fail Closed Gate
逐条检查 `verify-contract.md` 的 Fail Closed 列表：
1. 回应句是否失去触发语义
2. 原著自然事件是否被无依据改成设计局
3. 原著概述性信息是否被擅自扩成具体事故
4. 原著强闭环是否被只为造钩子硬切断
5. 即时动作钩子是否在相邻下一集第一场未兑现
6. draft 是否直写了 publish lane

检查方法：读取 `source.map.md` 对应集的 `must-keep beats` / `must-not-add` / `must-not-jump` / `ending type`，逐项比对 draft 正文。
任一命中 → FAIL，附具体位置和违反条目。

### Step 3：对抗性检查（6 项）
按 `verify-contract.md` 的 Verify Checklist > 对抗性检查执行：

1. **角色替换测试**
   - 操作：抽取 2 组不同角色对话段（各 3-5 句），假设互换
   - 判定：毫无违和感 → FAIL，指出哪些对话缺乏角色特征

2. **删除测试**
   - 操作：逐场假设删除
   - 判定：剧情完全不受影响 → FAIL，指出该场无不可替代叙事功能

3. **逻辑反推测试**
   - 操作：从每场结果反推原因
   - 判定：找不到前文因果链 → FAIL，指出断裂环节

4. **钩子有效性测试**
   - 操作：读集尾最后一段
   - 判定：没有"接下来会怎样"的疑问 → FAIL（注意：`ending type: 强闭环` 的集允许无 cliffhanger，但必须有情感/叙事完成感）

5. **画面感测试**
   - 操作：抽取任意 2 条 `△` 描写
   - 判定：闭眼无法想象具体画面 → FAIL
   - 追加摄影机测试：无法用镜头呈现 → 作者评论混入 → FAIL
   - 典型违规句式：`他/她一向知道……`、`对他而言……`、`可就是这副……反而让……`

6. **表里不一测试**（仅限有 os 角色）
   - os 与对话无反差 → os 无效 → FAIL
   - 删掉 os 后观众仍看得懂 → os 多余 → WARNING（同集累计 3 条 → FAIL）
   - 删掉全部 os 后观众看不懂角色在做什么 → 台词潜台词不足 → FAIL

每项给出 ✓ / ✗ 判定。

### Step 4：声纹硬查
按 `verify-contract.md` 的 Verify Checklist > 声纹硬查执行：

- 声纹基准加载：优先 `voice-anchor.md`，缺失/未列当前角色时回退 `character.md`
- **句长分布检查**：
  - 短句型角色：单句超 15 字台词不超过 10%
  - 长句/绕弯型角色：定性检查，看是否明显多于同场其他角色的复合句、转折句
  - 直来直去型角色：不应出现迂回、暗示型句式
  - 样本量门槛：本集有效台词 ≥ 5 句时硬查；不足时只做定性抽查
- **角色区分度测试**：抽取至少 2 组不同角色台词段（各 3-5 句），遮盖角色名后无法区分 → FAIL
- **禁用表达检查**：声纹基准中标注的禁用表达出现即 FAIL
- **原著声纹锚**（有原著时）：抽查是否保持称呼习惯、拐弯程度、常用词一致性

### Step 5：表情密度与对白漂移
按 `verify-contract.md` 的 Verify Checklist > 表情与密度检查 + 对白语义漂移检查执行：

- 表情/微表情特写：每集 ≥ 2 处 → 不足即 FAIL
- 冲突/反转：每集 ≥ 1 个 → 必须指出是哪个
- 情绪层次：2-3 场时至少 2 个不同主情绪；1 场时场内必须有情绪转折

- **对白语义漂移**（`preserve` / `light` 档）：
  - 台词不得新增原著没有的态度、挑衅、机锋、判断
  - 命中后指出：漂移场次、对应原著语义、漂移类型（态度增强/机锋增强/关系温度偏移/说明化）

### Step 6：WARNING 累计与回归 Gate
- 收集 Step 1 lint warnings + Step 2-5 中产生的所有 WARNING
- 按 `verify-contract.md` 的 Escalation 规则判定：
  - 同集 2 处及以上 `os` 语义悬空 → 升级 FAIL
  - 单点关系被明显冲淡到改变场景核心功能 → 直接 FAIL
  - 连续 3 集同类 warning → 当前批次不得 promote
- 检查 `harness/project/regressions/` 下的活跃回归 pack：
  - P1 + active → 阻断 promote
  - P2 同批累计 2 条及以上 → 阻断 promote

### Step 7：质量锚对标（条件执行）
- 前提：Step 1-6 全部通过，且 `quality.anchor.md` 存在
- 读取质量锚，对比最近一批（默认 5 集）：
  - 场景厚度是否明显变薄
  - os 是否从"暴露真实意图"退化成"重复表面意思"
  - 表情/镜头/动作是否只剩模板化点缀
  - 场尾钩子是否失去冲击力
  - 角色台词是否越来越像同一个人
- 最近一批 3 集及以上明显弱于锚点 → 批量模式 FAIL

### Step 8：判定与输出
- Step 1-7 全部通过 → **PASS**
- 任一步骤 FAIL → **FAIL** + 具体位置与修改方向
- FAIL 后由 controller 按 `entry.md` > Recovery Protocol 决定下一步：
  - 第 1-2 次 FAIL：writer 在当前上下文修改后重新提交
  - 第 3 次 FAIL：触发 context reset，writer 从干净上下文重写
  - 第 4 次 FAIL：升级到人工介入
- 每次 verify 结果（PASS 或 FAIL）由 controller 记录到 `run.log.md`

## Output Format

```
[PASS]
1. lint：✓（totals 关键数值）
2. fail-closed gate：✓（逐项）
3. 对抗性检查：✓×6
4. 声纹硬查：✓（句长/区分度/禁用/原著锚）
5. 表情密度与漂移：✓（特写/冲突/情绪/漂移）
6. warning 累计与回归：✓（WARNING 列表或"无"）
7. 质量锚对标：✓ 或 N/A

[FAIL]
（同上结构，未通过项标 ✗ 并附具体数值与阈值）

**需要修改的问题**：
- 位置：<场次/行>
- 违反：<规则条目>
- 方向：<修改建议>
```

