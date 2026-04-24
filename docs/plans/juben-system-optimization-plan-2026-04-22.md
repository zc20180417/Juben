---
title: Juben 系统性优化落地计划
status: active
created: 2026-04-22
owner: Codex
origin: 基于 2026-04-20 至 2026-04-22 对 extract-book / map-book / controller / run_writer / episode-lint 的连续回归与架构整理
---

# Juben 系统性优化落地计划

## 目标

把当前链路从“writer 临场理解并补锅”升级成“上游明确编排、writer 负责执行、lint 负责验收”的分层架构。

本轮优化追求 5 个结果：

1. 分集正确：总集数和单集切点由有效戏剧单元决定，而不是按章节平均切。
2. 单集够密：首集和强冲突集不再写成 60-90 秒提纲稿。
3. writer 去题材依赖：writer 不靠题材词表、关系词表、桥段词表做语义判断。
4. lint 回归验收本职：结构 fail / 结构 warn / 风格 warn 分层，而不是替代创作。
5. 运行可控：`extract-book` / `map-book` / `writer` / `fidelity patch` 的等待策略和失败语义一致。

## 当前判断

### 已跑通的主线

- `extract-book -> map-book -> batch brief -> writer` 已围绕 `function_signals / density_anchor / ending_function / irreversibility_level`
- 总集数推荐已从不合理的 `42` 收缩到更接近实际容量的 `18`
- `scene_count` 已不再硬卡为失败
- `fidelity patch` 触发已从“大段 fallback”收紧成“精准局部问题才跑”
- writer 已移除题材词表和关系抢跑词表依赖

### 当前真正的系统瓶颈

- `scene_function_plan` 仍主要在 `run_writer.py` 临时生成，上游契约还不够强
- `source.map` 的功能字段已经存在，但还没有成为真正的“场次任务单”
- lint 还偏向文本规则警察，尚未完全转成结构验收器
- 质量评估仍依赖单次人工观察，缺少固定样本集

## 落地阶段

### Phase 1：把 scene plan 前移到上游

目标：

- `source.map.md` 每集显式携带 `scene_plan`
- `controller.py` 负责归一化和兜底推断
- `batch brief` 直接输出场次任务单
- `run_writer.py` 优先消费上游 plan，而不是自行拼装

范围：

- `juben/_ops/run_book_map.py`
- `juben/_ops/controller.py`
- `juben/_ops/run_writer.py`
- `juben/_ops/test_run_book_map.py`
- `juben/_ops/test_controller_cli.py`
- `juben/_ops/test_run_writer.py`

交付物：

- `scene_plan` schema
- 上游归一化逻辑
- brief 渲染
- writer 消费链

验收：

- `source.map` 质量检查要求每集存在 `scene_plan`
- writer prompt 中 `scene_function_plan` 来自 episode facts，而不是临时推断
- batch brief 显式展示每场主功能与收尾条件

### Phase 2：收缩 writer 为执行器

目标：

- writer 不再承担场型推断、关系状态猜测、题材词识别
- writer 只做：
  - 读取当前集任务单
  - 渲染剧本壳
  - 执行最小运行时约束

范围：

- `juben/_ops/run_writer.py`
- `juben/_ops/test_run_writer.py`

交付物：

- 删除临时 scene plan 推断主路径
- 最小规则包进一步收口
- prompt 改成“按 plan 执行”，而不是“理解功能哲学”

验收：

- writer 不再是“中层编排器”
- 同一集的 prompt 结构更稳定，规则包继续缩短

### Phase 3：重写验收职责分层（已被 reviewer-only 方案替代）

目标：

- 结构硬约束只保留在 `controller.py`
- 内容质量交给 reviewer 判定
- 不再维护独立 `episode-lint.py`

范围：

- `juben/_ops/controller.py`
- `juben/harness/framework/review-standard.md`

交付物：

- `hard fail`
  - beats 缺失
  - 关键功能缺失
  - source 顺序越界
  - 壳层损坏
- `structural warn`
  - 单场偏瘦
  - 终场钩子偏弱
  - 节奏过齐
- `stylistic warn`
  - 解释句偏多
  - AI 味偏重
  - OS 多余

验收：

- lint 不再硬卡无关创作细节
- lint 输出更能说明“结构问题”还是“风格问题”

### Phase 4：建立固定评估集

目标：

- 每次系统改动都跑固定样本，而不是只看一次单集运气

建议样本：

- `EP-01`：误认入局型
- `EP-03`：结果确认型
- `EP-05`：公开掉马型
- 再补 2 个跨题材样本：
  - 权谋/古言
  - 情感/身份反转

验收维度：

- 总集数是否合理
- `source.map` 功能与密度是否合理
- `scene_plan` 是否稳定
- writer 是否仍依赖补丁式提示
- lint 是否过严/过松

## 执行顺序

1. Phase 1：scene plan 前移到上游
2. Phase 2：writer 收缩为执行器
3. Phase 3：lint 分层
4. Phase 4：固定评估集

## 本轮立即执行项

当前直接开始 Phase 1，具体动作：

1. 在 `run_book_map.py` 的 prompt schema 中新增 `scene_plan`
2. 在 `controller.py` 中新增：
   - `scene_plan` 解析
   - `scene_plan` 归一化
   - `scene_plan` 质量门禁
   - batch brief 渲染
3. 在 `run_writer.py` 中优先读取上游 `scene_plan`
4. 跑定向测试与一次真实链路检查
