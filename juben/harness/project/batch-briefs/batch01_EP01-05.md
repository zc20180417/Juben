# Batch Brief: EP-01 ~ EP-05

- batch status: promoted
- owned episodes: EP-01, EP-02, EP-03, EP-04, EP-05
- source excerpt range: 墨凰谋：庶女上位录.md 第1章 ~ 第5章
- adjacent continuity: 家仇原点 -> 入宫入口 -> 低位被看见 -> 御园偶遇 -> 初次承宠
- draft output paths:
  - drafts/episodes/EP-01.md
  - drafts/episodes/EP-02.md
  - drafts/episodes/EP-03.md
  - drafts/episodes/EP-04.md
  - drafts/episodes/EP-05.md

## Run Context
- adaptation_strategy: original_fidelity
- dialogue_adaptation_intensity: light
- generation_execution_mode: orchestrated_subagents
- generation_reset_mode: clean_rebuild

## Source Priority
1. `harness/project/run.manifest.md`
2. `harness/project/source.map.md`
3. `harness/framework/write-contract.md`
4. 原著正文 `墨凰谋：庶女上位录.md`
5. `voice-anchor.md`
6. `character.md`

## Batch Goals
- 重建家仇原点、入宫入口、低位被看见、初次承宠这四步。
- 修复 v1 清单里的 EP-01~05 核心硬伤。
- 不再用 cliffhanger 切断第一章更强闭环。

## Episode Mapping
- EP-01：第1章完整闭环
  - 窗外听刑 -> 柳姨娘惨死 -> 沈丞相冷反应 -> 后山埋母 -> 母坟立誓
  - 集尾类型：强闭环
- EP-02：第2章
  - 选秀旨意 -> 沈明珠拒绝 -> 沈青鸾替姐入宫 -> 沈夫人把她当眼线/弃子
  - 集尾类型：前推
- EP-03：第3章
  - 扮丑扮病 -> 选秀 -> 皇帝因朱砂痣与眼神留牌 -> 低位入住
  - 集尾类型：前推
- EP-04：第4章
  - 深居简出 -> 新人承压 -> 御园偶遇 -> 点侍寝
  - 集尾类型：前推
- EP-05：第5章
  - 初次承宠 -> 借宸妃威胁递刀 -> 升常在/赐居 -> 宸妃震怒
  - 集尾类型：前推

## Hard Constraints
- 回应句必须保留上句触发语义。
- 不把天然偶遇改成半设计局。
- 不把概述性后宫压力扩写成新的人名、具体事故或完整事件链。
- 不把女主前期写得过早透明、过早会控局。
- 不把受压/求生语义改成聪明压人或挑衅回击。
- 对白保持完整气口，不压成碎句机。

## verify checklist
- `_ops/episode-lint.py` on each draft: PASS
- `verify-contract.md` high-severity gates: PASS
- `harness/project/regressions/` active pack items: no active hit
- batch ready for promote: yes
