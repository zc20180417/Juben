# Juben（剧本）— AI-Native 短剧工业化生产系统

## 一句话定义

Juben 是全球首个将长篇网文改编为微短剧剧本的 AI 多 Agent 协作生产线。它把一个需要编剧团队数月完成的工作，压缩为一条可控、可评审、可迭代的自动化流水线。

---

## 1. 核心痛点

### 行业背景：短剧市场的产能瓶颈

2024–2026 年，中国微短剧市场规模突破 500 亿元，但产能端存在结构性矛盾：

- **改编需求量大**：平台每月需要数百部新剧本，但合格编剧供给严重不足
- **网文改编难度高**：网络小说动辄 80–200 章、50–150 万字，改编为 40–60 集 × 2 分钟的短剧需要大量取舍和重构
- **质量一致性难保证**：即使有编剧团队，中后期集数质量衰减、人物声纹漂移、剧情断线是普遍问题
- **同质化风险高**：简单"改名换行业"式的改编会导致版权纠纷，需要系统性的"功能保留 + 外壳原创化"方法论

### Juben 解决的四个具体问题

| 痛点 | Juben 方案 |
|------|-----------|
| **长文本→短剧的结构映射** | 全书抽取 + Source Map 逐集转译，每集锁定 `source_function → new_episode_event → setting_translation → must_change_surface → do_not_copy` 五层映射 |
| **多集一致性衰减** | 批次级 Review Gate + Story State 持久化追踪，保证人物关系、伏笔、权力位移跨批次连续 |
| **改编同源风险** | 角色替换测试、原句近似测试、设定重构测试——系统性防止"改名式抄袭" |
| **单 Agent 质量天花板** | Writer / Reviewer 角色分离，Reviewer 不写稿、Writer 不评审，形成对抗性质量闭环 |

---

## 2. 核心逻辑流

### 2.1 全流程概览

```
原著小说 (.txt)
    │
    ▼
┌─────────────────┐
│ ① Extract-Book  │  Agent 通读全书 → 提取主线/人物/关键事件/情绪曲线
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ② Map-Book      │  章节→剧集映射 → 生成 Source Map（每集五层转译）
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ③ Start Batch   │  冻结批次 Brief → 生成 Writer Prompt Packet + Reviewer Prompt Packet
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│ ④ Writer Agent  │ ───▶ │ ⑤ Reviewer Agent│
│  写 drafts/      │      │  结构评审/质量判定 │
│  episodes/      │ ◀─── │  PASS/FAIL/WARN   │
└─────────────────┘      └────────┬────────┘
         │                        │
         │              ┌─────────▼──────────┐
         │              │ FAIL → 回写修稿意见  │
         │              │ PASS → 进入 Promote  │
         │              └────────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐      ┌─────────────────┐
│ ⑥ Promote       │      │ ⑦ Record        │
│  drafts → episodes│     │  更新 Story State │
│  正式发布         │      │  /Relationship/   │
└─────────────────┘      │  Open Loops       │
                          └─────────────────┘
```

### 2.2 长链推理设计

Juben 的核心技术特征是 **跨越数万 token 的多跳因果推理链**：

**（1）全书级推理（Extract + Map 阶段）**

Agent 需要一次性处理 80 章原文（数十万字），完成以下推理：

- 识别主线叙事功能（哪些是驱动性事件，哪些是解释性/填充性内容）
- 提取人物关系的位置和功能（谁是压力源、谁是升级锚、谁是情感线）
- 判断每章的情绪曲线和阶段性爽点落点
- 将原著章节压缩/合并/重排为 40 集（而不是 80 集的等比例缩放）
- 为每集定义 `must_keep_function`（保留什么叙事功能）和 `must_change_surface`（替换什么表面设定）

这是一个**全局优化问题**——不是逐章缩写，而是理解整个故事的因果骨架后用新的设定重新构建。

**（2）批次级推理（Write 阶段）**

每个 batch 撰写 5 集时，Writer Agent 需要同时考虑：

- 本批次的 Brief（本批关键 beats、角色弧光位置、必须完成的 payoff）
- 前续集数的已发布正文（确保连续性，不出现角色知识偷跑）
- Source Map 中每集的五层转译约束
- Write Contract 中的硬边界（禁用原文台词、标志性道具、事件组合）
- Writer Style 中的风格规范（`△` 镜头语言、对白排版、OS 使用限制）

这要求 Agent 在**约 15K–25K token 的上下文窗口内维持精确的多维约束**。

**（3）跨批次状态推理（Record 阶段）**

每批完成后，Agent 自动更新 Story State，追踪：

- 权力格局变化（谁压制、谁反击、力量对比如何位移）
- 人物关系演进（父子/合作伙伴/政商/市场对手的多线关系变化）
- 开放伏笔（已埋未收的悬念、承诺、风险线）
- 质量锚对标（与 quality.anchor.md 对比，检测结构性退化）

这些状态文件成为下一批次 Writer 和 Reviewer 的输入，形成**跨批次记忆链**。

### 2.3 多 Agent 协作架构

Juben 是一个 **同构多 Agent 系统**（所有 Agent 都基于 Claude，但通过不同的 Prompt Packet 实现角色分化）：

| Agent 角色 | 输入 | 输出 | 不可越界行为 |
|-----------|------|------|------------|
| **Extractor** | 原著全文 + 蓝图模板 | Book Blueprint（主线/阶段/弧光/反转） | 不写剧本，只做信息提取 |
| **Mapper** | Book Blueprint + 原著 | Source Map（每集五层转译） | 不写正文，只定义约束 |
| **Writer** | Brief + Source Map + Contract + Style + 前续正文 | drafts/episodes/*.md | 不看 Reviewer 意见，只执行写作合同 |
| **Reviewer** | drafts + Brief + Source Map + Quality Anchor | Verdict（PASS/FAIL/WARN + blocking_reasons） | 不改稿、不润色、不提"还能更好" |
| **Controller** | Python 编排逻辑 | 流程调度 + Promote + Record | 不判断内容质量，只做结构校验和流程控制 |

**关键设计原则：**

1. **角色隔离**：Writer 不接触 Review 标准（防止"应试写作"），Reviewer 不接触 Writer Prompt（防止先入为主）
2. **对抗性质量**：Reviewer 的判准矩阵包含 14 条 FAIL 条件和 8 条 WARNING 条件，每项 blocking 结论必须附带 `evidence_ref`
3. **可恢复性**：每条指令都有幂等入口（`~check` 重建 review packet、`~promote` 恢复中断的发布、`~record` 重新写入状态）
4. **人机协作**：Reviewer 产出 verdict 后由人工确认，`~start --write` 生成的 prompt packet 也可以由外部 Agent 消费

---

## 3. 具体成果

### 3.1 已完成作品

**《实业帝国：从继承养猪场开始》→ 40 集短剧完整改编**

| 指标 | 数据 |
|------|------|
| 原文字数 | 约 50 万字 / 80 章 |
| 改编集数 | 40 集 |
| 目标总时长 | 55 分钟（单集 1–3 分钟） |
| 生产批次 | 8 批（每批 5 集） |
| 角色数量 | 11 个主要人物（全部改名 + 行业身份重构） |
| 改编策略 | **Transformative Adaptation**（功能保留 + 行业/场景/道具/事件外壳完全原创化） |
| 成品格式 | 每集 3 场，包含人物表 + `△` 动作描写 + 对白 + OS（旁白） |

**改编转译示例：**

```
原著产业链：  养猪 → 饲料 → 猪价行情 → 屠宰 → 期货对冲 → 大豆 → 农机
新剧产业链：  冷库 → 制冰 → 速冻食品 → 冷链配送 → 包装 → 便利店终端 → 原料风控 → 食品装备 → 科研合作
```

### 3.2 产出资产清单

```
juben/
├── episodes/          ← 40 集已发布成品（每集约 60-90 行标准格式）
├── drafts/episodes/   ← 对应草稿（评审通过后 promote 到 episodes/）
├── character.md        ← 完整人物表（功能定位/欲望/软肋/镜头抓手/写作边界）
├── harness/project/
│   ├── book.blueprint.md    ← 全书改编蓝图（主线/弧光/反转/角色弧/关系变化）
│   ├── source.map.md        ← 40 集 × 五层转译映射表
│   ├── run.manifest.md      ← 运行配置（批次/时长/改编策略/质量模式）
│   └── state/
│       ├── story.state.md         ← 跨批次故事状态追踪
│       ├── relationship.board.md  ← 人物关系演进记录
│       ├── open_loops.md          ← 伏笔/悬念/未收线管理
│       ├── quality.anchor.md      ← 质量锚点（防退化基准）
│       ├── process.memory.md      ← 流程记忆
│       └── run.log.md             ← 完整运行日志
└── harness/framework/
    ├── write-contract.md     ← 写作合同（硬边界/标记格式/对白规则/OS规则）
    ├── writer-style.md       ← 风格规范（叙事姿态/场景打法/对话工艺）
    ├── review-standard.md    ← 评审标准（14 条 FAIL + 8 条 WARNING 矩阵 + 16 项测试）
    └── *.template.md         ← Prompt 模板（Writer/Reviewer/Batch/Extract/Map）
```

### 3.3 方法论沉淀

Juben 产出的不仅是一部 40 集剧本，更是一套**可复用的改编工程方法论**：

- **功能保留 + 外壳原创化**：定义了"什么必须保留"（叙事功能、人物关系功能、情绪曲线）和"什么必须改写"（行业、场景、道具、事件触发方式、原文台词）的清晰边界
- **五层转译映射**：每集通过 `source_function → new_episode_event → setting_translation → must_change_surface → do_not_copy` 建立可追溯、可验证的改编链路
- **16 项质量测试矩阵**：角色替换测试、人名改编测试、设定重构测试、同源风险测试、原句近似测试、知识边界测试、删除测试、钩子有效性测试等——形成可操作的评审标准
- **对抗性多 Agent 审查**：Writer 和 Reviewer 使用独立 Prompt Packet、互不可见，以对抗方式保证质量而不是自我审查

---

## 4. 技术特点总结

- **长链推理**：从原著 80 章到 40 集成品的全流程，需要跨提取→映射→批次规划→逐集写作→跨批次状态追踪的多跳因果推理，单次决策的上下文窗口需求在 15K–60K token
- **多 Agent 协作**：5 个角色化 Agent 通过独立的 Prompt Packet 实现分工，通过状态文件系统实现协作，通过 Controller 实现流程编排
- **约束满足**：每集剧本的生成需要在 Write Contract（硬边界）、Writer Style（风格规范）、Source Map（转译约束）、Story State（连续性约束）、Quality Anchor（不退化约束）五重约束下完成
- **可复现性**：所有 Prompt Packet、状态文件和配置均为纯文本 Markdown，整套流水线可在新项目上从零复现
