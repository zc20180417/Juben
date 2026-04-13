# Batch Brief: EP-06 ~ EP-10

- batch status: promoted
- owned episodes: EP-06, EP-07, EP-08, EP-09, EP-10
- source excerpt range: 墨凰谋：庶女上位录.md 第6章 ~ 第8章
- adjacent continuity: 宸妃设宴 -> 当众献舞羞辱 -> 宸妃巫蛊设局 -> 搜宫反转 -> 家书催命
- draft output paths:
  - drafts/episodes/EP-06.md
  - drafts/episodes/EP-07.md
  - drafts/episodes/EP-08.md
  - drafts/episodes/EP-09.md
  - drafts/episodes/EP-10.md

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

## Episode Mapping
- EP-06：第6章前半
  - 宸妃设宴 -> 沈青鸾明知鸿门宴仍去 -> 不去即示弱
  - 集尾类型：前推力
- EP-07：第6章后半
  - 当众献舞羞辱 -> 皇帝撞见 -> 护短落下 -> 宸妃受挫
  - 集尾类型：前推力
- EP-08：第7章前半
  - 宸妃巫蛊设局 -> 沈青鸾提前识破
  - 集尾类型：前推力
- EP-09：第7章后半
  - 搜宫反转 -> 证据指向宸妃 -> 降位冷宫 -> "以其人之道还治其人之身"
  - 集尾类型：强闭环
- EP-10：第8章
  - 家书催命 -> 回信伪孝 -> 给沈明珠递毒婚约 -> "就让他们狗咬狗吧"
  - 集尾类型：前推力

## Hard Constraints
- 不得跳过宴前压迫直接写羞辱
- 不得把这场写成普通嘴仗
- 不得跳过皇帝亲见
- 不得直接写宸妃冷宫
- 不得提前宣布反制成功
- 不得把送冷宫写成过度工整说教
- 不得跳过家书直接进入婚约成毒结果

## verify checklist
- `_ops/episode-lint.py` on each draft: PASS
- `verify-contract.md` high-severity gates: PASS
- `harness/project/regressions/` active pack items: no active hit
- batch ready for promote: yes
