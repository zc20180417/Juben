---
title: Juben Writer Prompt 瘦身与测试解耦技术债计划
status: proposed
created: 2026-04-21
owner: Codex
origin: 基于 2026-04-20 到 2026-04-21 对 `juben/_ops/run_writer.py` 的真实 EP-01 回归、prompt dump 与测试耦合现状整理
---

# Juben Writer Prompt 瘦身与测试解耦技术债计划

## 背景

当前 writer prompt 的体积和维护成本，已经不再只是“文案太长”问题，而是三层契约重复叠加：

1. `harness/framework/write-contract.md`
2. `harness/framework/writer-style.md`
3. `juben/_ops/run_writer.py` 里运行时 prompt 的最小规则包与自检

这三层并不完全重复，但存在明显重叠：

- contract 负责壳层、边界、禁增、知识边界
- style 负责叙事姿态、场景打法、对白打法
- prompt 又重复写了一遍其中最关键的运行时规则

直接结果：

- draft prompt 体积长期维持在 `5.8KB` 左右
- 测试对 prompt 字面短语绑定过深
- 想压 prompt 时，经常先打破测试，再为了过测试把短语补回来
- 即使 prompt 变短，也不一定换来更好的真实生成质量

## 现状判断

### 已验证有效的优化

- `whole-draft fallback => skip fidelity patch`
  这条是真实有效的性能优化，应该保留。

### 尚未稳定证明有效的优化

- 继续压 draft prompt 文案
- 压缩“开始前先读”提示
- 把自检收成更短的 5 条

这些改动在单测里可以通过，但在真实 `EP-01` 运行里并没有稳定带来更好的速度或质量结果。

### 当前核心矛盾

不是“prompt 太长所以一定慢”，而是：

- prompt 里确实有重复契约
- 但有一部分运行时规则又必须直接留在 prompt 里，不能完全下放给 contract/style
- 测试目前没有区分“必要的行为契约”和“可替换的字面表述”

因此后续不能走极端：

- 不能继续把短语越堆越多
- 也不能把 prompt 简化成“去读文档”然后删掉运行时 guard

## 技术债定义

本技术债不是“把 prompt 尽量压短”，而是做两件事：

1. 把真正的运行时最小契约从重复文案里剥离出来
2. 把测试从字面量短语检查，重构为更稳定的行为/结构检查

目标不是最短 prompt，而是：

- prompt 更短
- contract 分层更清楚
- 测试不再卡固定短语
- 真实生成质量不回退

## 分层原则

### 1. 必须继续留在 prompt 的内容

这些内容属于运行时最小契约，不建议完全下放到 `write-contract.md` 或 `writer-style.md`：

- 当前集任务目标
- 当前集 beats 清单
- 冲突优先级
- source 顺序与边界的最小规则
- 场次最低要求
- 非终场推进要求
- 第一人称 OS 禁令
- `strong_scene` 下仍然会明显改变输出行为的 guard

一句话说：凡是会直接改变本次生成行为的规则，都应该继续保留一层 prompt 内显式约束。

### 2. 可以下放到 contract/style 的内容

这些内容可以不在 prompt 里长篇重复，只保留引用或短标签：

- 壳层规则的解释性描述
- 风格打法的扩展说明
- 典型反例与示例句
- 长段落的“为什么这样写”
- 非当前 episode 不会触发的泛化说明

### 3. 测试不该再硬绑的内容

以下内容不应再以固定短语做强绑定断言：

- 某个具体中文措辞
- 某句完整的解释性规则
- 同义可替换的提醒句
- 纯说明性的 prompt 排版文案

## 后续目标形态

后续理想结构应该是：

### Prompt 层

只保留 6 块：

1. 任务目标
2. 必读输入
3. 冲突优先级
4. 输出壳与场次规则
5. 当前集 beats 清单
6. 最小运行时规则 + 最小自检

### Contract 层

`write-contract.md` 保留：

- 壳层完整规范
- source fidelity 完整边界
- 禁增与知识边界的完整定义
- 示例与反例

### Style 层

`writer-style.md` 保留：

- 叙事姿态
- 场景打法
- 对白打法
- 节奏与镜头感偏好

## 测试解耦原则

### 当前问题

现在一部分测试本质上是在检查：

- prompt 是否出现短语 A
- prompt 是否出现短语 B
- prompt 是否出现完整句子 C

这种方式的问题是：

- prompt 只要换个说法，测试就会失败
- 测试无法区分“行为缺失”和“文案改写”

### 重构方向

后续测试应按三层拆开：

#### A. 结构存在性测试

检查 prompt 是否仍包含：

- 任务目标块
- 冲突优先级块
- beats 块
- 最小规则包块
- 最小自检块

#### B. 运行时契约测试

检查 prompt 是否仍表达这些行为，而不是卡完整句子：

- beats 必须完成
- source 不得后拖
- 非终场必须留推进
- 禁新增第一人称 OS
- `strong_scene` 仍有边界 guard

#### C. 文件引用测试

检查 prompt 是否正确引用：

- `batch-context.json`
- `source.json`
- contract/style 相关来源

而不是要求 prompt 重复 contract/style 的整句内容。

## 建议实施顺序

### Phase 1：标注最小运行时契约

先在 `run_writer.py` 内部明确标出哪些规则是“必须继续留在 prompt”的。

验收标准：

- 能列出一份不超过 `5-8` 条的核心运行时 guard 清单
- 不依赖字面表述，只依赖行为定义

### Phase 2：重构测试

把 `test_run_writer.py` 里对 prompt 的固定短语断言，逐步改成：

- 结构断言
- 契约断言
- 引用断言

验收标准：

- prompt 改写同义文案时，测试不应无意义失败
- 删除关键行为约束时，测试仍会失败

### Phase 3：收 prompt 冗余

只有在测试解耦后，才开始继续压：

- “开始前先读”的详细说明
- 重复的 contract/style 描述
- 自检里的解释性文字

验收标准：

- prompt bytes 下降
- `EP-01` 真实回归不退化

### Phase 4：真实回归裁决

每次收 prompt 后，必须至少验证：

- `EP-01` 真跑
- 生成耗时
- `controller lint EP-01`
- 是否仍触发 `whole-draft skip patch`

没有真实回归收益，就不保留。

## 明确不做的事

本技术债文档不主张：

- 把 prompt 完全降成“去读 contract/style”
- 以 bytes 最小化作为唯一目标
- 为了过测试继续堆更多固定短语
- 在没有真实 batch 回归前，凭单测判断 prompt 优化成功

## 近期结论

截至 `2026-04-21`，更合理的结论是：

- 当前 `~5.8KB` draft prompt 不是理想终态
- 但在测试尚未解耦前，不值得继续激进压缩
- 真正该优先处理的是“prompt 最小运行时契约”和“测试字面量耦合”之间的边界

因此这份技术债的优先级应低于：

- 真正能稳定提升 wall-clock 的改动
- 真正能稳定提升 batch 通过率的改动

但它适合作为后续 prompt 收缩前的前置整理项。
