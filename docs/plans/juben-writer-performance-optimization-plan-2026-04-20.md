---
title: Juben Writer 性能优化计划
status: active
created: 2026-04-20
owner: Codex
origin: 基于当前 `juben/_ops/run_writer.py` 的真实复杂度、批次耗时与保真优先目标整理
---

# Juben Writer 性能优化计划

## 背景

当前 Writer 慢，不是因为 Python 本身慢，而是因为我们把“小说转短剧剧本”做成了一条高保真、强门禁、重上下文的远程生成流水线。主要耗时点集中在三条主线：

1. 运行时 prompt 仍然偏重  
   即使已经从“大而全规则展开”收到了“当前集最小规则包”，模型仍然要同时处理 source excerpt、batch context、brief 与多层保真约束。

2. second pass 过去过于粗粒度  
   之前 second pass 是整集 rewrite。即使只想修 2 句，也要重新理解整集并重写整份草稿。

3. 中间表示仍以 Markdown 为主  
   `source.map.md`、`source excerpt`、`batch context` 过去都更像说明文，而不是机器优先的运行时输入。

## 目标

- 保持保真优先，不为提速牺牲 `source-compare`
- 减少普通集的远程调用成本
- 把 second pass 从“整集 rewrite”推进到“局部 patch”
- 逐步把 writer 运行时输入从松散 Markdown 收成更紧的结构化输入

## 当前进度

### 已完成

- [x] Writer 首稿 prompt 改成运行时最小规则包
- [x] 顺序 batch prompt 改成按每集规则信号驱动
- [x] second pass 改成按需触发，不再每集默认执行
- [x] 单集 second pass 有独立超时
- [x] source excerpt 已做成稳定 tier 分层  
  当前按 `baseline / low_risk / strong_scene` 三档注入。
- [x] second pass 增加可观测日志  
  当前日志会明确显示：
  - `excerpt_tier`
  - `signals`
  - `reasons`
  - `candidate_blocks`
  - `families`
  - `families_touched`
- [x] rewrite 输入改成 patch spec 第一阶段  
  当前 patch spec 已覆盖：
  - `restore_names`
  - `restore_long_lines`
  - `delete_fill_blocks`
  - `externalize_lines`
  - `scene_modes`
  - `reuse_original_lines`
- [x] second pass 已不再要求模型整份重写文件  
  当前路径是：
  - 模型读取 source excerpt + 候选输入
  - 只返回局部 patch JSON
  - 本地代码按行号应用 patch
- [x] patch spec 做了保守收紧  
  当前 second pass 已稳定：
  - `problem_family`
  - `block_id`
  - family -> action 白名单约束
- [x] patch family 命中条件收紧  
  当前只在这些情况下命中：
  - `restore_names`：泛称标签或明显弱化的人名标签
  - `restore_long_lines`：`pressure_scene` 下的短对白，或与 `must_keep_long_lines` 显式重合
  - `delete_fill_blocks`：命中真实填充关键词或 reveal 专用填充 token
  - `externalize_lines`：命中抽象总结 pattern，且 excerpt 中确有外化要求
- [x] second pass 输入缩窄到“候选句段”  
  当前会先在本地根据 patch spec 和 draft 内容筛出疑似命中的行块，再把这些带全局行号的候选块交给模型。
- [x] 普通集 excerpt 再压一档  
  `baseline / low_risk` 不再整段透传原文，而是压成“首尾 + 人名/原句锚点段落”；`strong_scene` 保持完整 excerpt。

### 接近完成

- [~] second pass 局部化  
  已经从“整集 rewrite”推进到“patch JSON + 本地应用 + 候选块输入”，但当本地无法可靠缩窄候选句段时，仍保留整份编号 draft fallback。

### 本轮已落地：Runtime Input V2

- [x] source excerpt 新增结构化运行时产物  
  每集现在同时落：
  - `harness/project/state/source-excerpts/<batch>/<episode>.source.md`
  - `harness/project/state/source-excerpts/<batch>/<episode>.source.json`
- [x] source excerpt JSON 结构固定  
  固定字段按 tier 输出：
  - 始终保留：`episode`、`source_span`、`excerpt_tier`、`event_anchors`、`must_keep_names`、`forbidden_fill`
  - `low_risk / strong_scene` 额外保留：`reusable_source_lines`
  - `strong_scene` 额外保留：`scene_modes`、`must_keep_long_lines`、`abstract_narration`
- [x] `event_anchors` 改成机器优先锚点数组  
  当前规则：
  - 始终保留首段
  - 始终保留末段
  - 保留命中 `must_keep_names` 的段落
  - `low_risk` 额外保留命中 `reusable_source_lines` 或直接引号台词的段落
  - 不再输出中间自然语言占位段
- [x] `forbidden_fill` 改成短 token / 短规则项  
  不再输出大段解释性说明文。
- [x] batch context 新增结构化运行时产物  
  每个 batch 现在同时落：
  - `harness/project/state/batch-context/<batch>.writer-context.md`
  - `harness/project/state/batch-context/<batch>.writer-context.json`
- [x] batch context JSON 改成 digest/facts 结构  
  固定分区：
  - `batch_id`
  - `authority`
  - `batch_facts`
  - `contract_digest`
  - `style_digest`
  - `quality_digest`
  - `reference_names`
- [x] writer prompt 切到 JSON 优先  
  首稿 prompt、顺序 batch prompt、fidelity rewrite prompt 现在都优先引用 `.source.json` / `.writer-context.json`，并按 JSON key 描述运行时契约。
- [x] second pass profile 改成 JSON 优先读取  
  `_episode_rule_profile()` 现在先读 JSON sidecar；缺失时再 fallback 旧 Markdown。

### 未完成

- [ ] patch spec 虽然已经有 `problem_family + block_id + action whitelist`，但 family 粒度仍偏粗，还没继续细化到更窄的 block-level 协议
- [ ] Markdown sidecar 仍然保留，迁移还没有收尾到“纯结构化运行时输入”
- [ ] `batch_context` 的 digest 仍有进一步压缩空间，尤其是默认提示与规则文本长度

## 当前实现形态

当前 second pass 的真实路径已经变成：

1. 首稿生成  
   Writer 先完成当前集或当前批次的结构化草稿。

2. 本地判断是否需要 second pass  
   只有命中这些高风险信号才进入 second pass：
   - `reveal_scene`
   - `pressure_scene`
   - `must_keep_long_lines`
   - `abstract_externalization`

3. 本地提取候选句段  
   根据 patch spec 与草稿内容，先筛出疑似命中的行块，并保留全局行号。

4. 模型只输出 patch JSON  
   不再返回整份草稿。返回格式固定为：

```json
{
  "operations": [
    {
      "block_id": "B01",
      "problem_family": "restore_names",
      "start_line": 12,
      "end_line": 12,
      "action": "replace",
      "content": "替换后的内容",
      "reason": "restore_names"
    },
    {
      "block_id": "B01",
      "problem_family": "delete_fill_blocks",
      "start_line": 18,
      "end_line": 19,
      "action": "delete",
      "reason": "delete_fill_blocks"
    }
  ]
}
```

5. 本地按行应用 patch  
   本地只允许：
   - `replace`
   - `delete`  
   不允许 patch pass 在本地层凭空插入新场面。

## Runtime Input V2 设计

### Source Excerpt V2

- writer 运行时优先消费 `.source.json`
- 事件顺序以 `event_anchors` 为最高权威
- 人名约束以 `must_keep_names` 为准
- 原句复用只看 `reusable_source_lines`
- 禁增只看 `forbidden_fill`
- 强场才继续注入 `scene_modes / must_keep_long_lines / abstract_narration`

### Batch Context V2

- batch context 的职责现在是“静态共享事实摘要”
- 不再承担 `run.manifest`、`source.map`、brief、合同、风格文档的全文镜像备份
- 运行时 prompt 只引用 digest/facts，不再要求模型先读大块说明文 bundle

### 兼容策略

迁移顺序固定：

1. 先新增 JSON 生成与读取
2. writer prompt 切到 JSON 优先
3. 测试 fixtures 迁到 JSON
4. 最后再决定是否删除 Markdown 产物

本轮默认保留 `.md` fallback，不做删除动作。

## 接下来最值的 3 步

### Unit 1：继续压缩默认规则包

目标：

- 继续压 `baseline / low_risk` 的运行时输入体积
- 收短 `forbidden_fill` 与默认自检提示文本
- 保持强场 source authority 不回退

做法：

- 压缩 `contract_digest / style_digest / quality_digest` 的默认措辞
- 评估哪些规则能只在强场或高风险集注入
- 用固定字节对比测试守住“新产物小于旧产物”

收益：

- 普通集 prompt 更短
- 首稿读取更轻

### Unit 2：让 patch spec 再结构化一步

目标：

- 把 patch spec 从“稳定 family + action”推进成更窄的 block-level 协议

做法：

- 继续在当前一阶段基础上收紧 family 粒度
- 保留现有稳定 `problem_family` 与 `block_id`
- 保留不同 family 只能做对应动作：
  - `restore_names` -> `replace`
  - `restore_long_lines` -> `replace`
  - `delete_fill_blocks` -> `delete`
  - `externalize_lines` -> `replace`

收益：

- second pass 更稳
- 更容易追踪“为什么修这一块”

### Unit 3：决定何时移除 Markdown sidecar

目标：

- 在不影响排障的前提下，确认 `.md` 是否还值得继续保留

做法：

- 先观察 JSON 优先路径的稳定性
- 若日志与回归都足够稳定，再评估是否把 `.md` 降级为调试产物或直接移除

收益：

- 运行时产物更单一
- 代码路径更少

## 风险

- 候选句段收得太窄，可能漏掉真实需要修的块
- excerpt 缩得太狠，可能让强场失去足够 source authority
- 本地规则继续增长，可能再次把 `run_writer.py` 做重
- JSON 与 Markdown 双轨期过长，会增加维护负担

## 约束

- 不重写 `write-contract.md` / `writer-style.md` 作为规则源
- 不改 `controller.py` 的 batch review 机制
- 不在这一批更换 writer 模型
- 性能优化不能以牺牲 `source-compare` 结果为代价

## 完成标准

当以下条件同时满足时，这份计划才算完成：

- 普通集默认只需一次远程调用
- second pass 只在强场或高风险集触发
- second pass 稳定使用局部 patch，而不是整集 rewrite
- second pass 默认只看候选句段，不再重读整份 draft
- writer 首稿运行时优先读取结构化 JSON，而不是全文 Markdown bundle
- 普通集与代表性强场的 `source-compare` 结果不回退
- operator 能直接从日志看出：
  - 本集是否触发 second pass
  - 为什么触发
  - 是否命中 patch 超时或重试

## 2026-04-20 增量补记

- `baseline / low_risk` 的 `Original Excerpt` 已压成锚点式原文片段，不再整段透传
- `strong_scene` 仍保留完整 excerpt，以维持强场 source authority
- excerpt 运行时元数据已从说明文段迁到 `.source.json`
- batch context 已同步新增 `.writer-context.json`
- writer prompt 与 second pass profile 已切到 JSON 优先，Markdown 仅保留兼容 fallback
- `contract_digest / style_digest / quality_digest` 与默认规则包文案已继续瘦身
- 体积验收测试已固定比较 `baseline / low_risk excerpt` 与 `batch_context` 的新旧字节数
