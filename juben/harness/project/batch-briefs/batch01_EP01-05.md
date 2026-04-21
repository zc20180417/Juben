# Batch Brief: EP-01 ~ EP-05

- owned episodes: EP-01, EP-02, EP-03, EP-04, EP-05
- source excerpt range: 被弃真千金：总裁不好惹.md 第1章前半 ~ 第3章前半
- adjacent continuity: 【信息】夜色街头，傅斯年把时鸢错认成失踪的苏清月。 -> 【信息】到苏家后，苏家父母第一反应是审视与盘问，不是心疼。 -> 【信息】亲子鉴定报告送到苏家并当场确认：时鸢确实是苏家失散多年的亲生女儿。 -> 【信息】苏振宏与刘美兰延续嫌恶姿态，继续拿“学规矩、别给苏家丢人”来规训时鸢，认亲后的冷酷彻底坐实。 -> 【信息】苏家为攀附商圈名流举办晚宴，对外只拿苏雨柔充门面。
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

## Writer Authority
- 当前 batch brief：决定本批每集的任务、beats、功能目标与 ending function
- `harness/project/source.map.md`：决定 source 顺序、must-not-add、must-not-jump 边界
- `harness/project/run.manifest.md`：只提供运行参数，不裁决内容冲突
- `voice-anchor.md` / `character.md`：仅作气质、禁区与称谓参考，不覆盖当前集任务

## Function Policy
- 场次数由功能完成决定，不得为了压场数省略功能槽位。
- 首集和强冲突集必须补齐适用的强功能，不得把多个强功能糊成总结场。

## Episode Mapping
- EP-01：第1章前半
  - 【信息】夜色街头，傅斯年把时鸢错认成失踪的苏清月。 -> 【关系】时鸢被强行带上车，始终冷静拒认，不演受惊失措。 -> 【动作】点出时鸢隐藏的设计师身份与强硬底色，但不能让苏家知晓。 -> 【钩子】埋下“同脸误认会把她卷进苏家漩涡”的总钩子。
  - 功能目标：opening=intrusion；middle=confrontation, reveal；ending=locked_in；irreversibility=hard
  - 强功能补齐：intrusion, escalation, confrontation_or_reversal, hook
- EP-02：第1章后半
  - 【信息】到苏家后，苏家父母第一反应是审视与盘问，不是心疼。 -> 【关系】苏雨柔柔弱插话，把“真千金回归”导向自己受威胁的局面。 -> 【动作】时鸢当场看清亲情凉薄，同意做鉴定但明确表示不认这个家。 -> 【钩子】傅斯年第一次察觉，时鸢与苏清月性格完全不同。
  - 功能目标：opening=setup；middle=escalation, reveal；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-03：第2章前半
  - 【信息】亲子鉴定报告送到苏家并当场确认：时鸢确实是苏家失散多年的亲生女儿。 -> 【关系】结果落地后，刘美兰与苏振宏仍先要求她激动、感恩、懂事，苏雨柔继续假意圆场、实则加深偏心。 -> 【动作】时鸢明确说出“既然确认了，那我就不打扰了”，并指出自己从未享受过苏家千金的待遇，谈不上感恩。 -> 【钩子】苏家在认亲刚落定的当口，就继续拿苏雨柔的懂事体面压她，把“确认血缘不等于接纳回家”的寒意钉死。
  - 功能目标：opening=reveal；middle=escalation；ending=reveal_pending；irreversibility=hard
  - 强功能补齐：intrusion, escalation, hook
- EP-04：第2章后半
  - 【信息】苏振宏与刘美兰延续嫌恶姿态，继续拿“学规矩、别给苏家丢人”来规训时鸢，认亲后的冷酷彻底坐实。 -> 【关系】时鸢正式与苏家切断情感期待，苏家则把她视作碍眼的亲生女儿而非失而复得的孩子。 -> 【动作】时鸢正面说出“生而不养，何以为父母”，留下“从此我与苏家，两不相干”后转身离开。 -> 【钩子】傅斯年在一旁彻底看清苏家的短视与失格，落下“你们会后悔的”的判断。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-05：第3章前半
  - 【信息】苏家为攀附商圈名流举办晚宴，对外只拿苏雨柔充门面。 -> 【关系】苏家完全不提时鸢，进一步坐实他们的短视与功利，也把“亲生女儿被无视”推到最满。 -> 【动作】主持人必须在本集直接介绍“鸢设计创始人，时鸢女士”，时鸢当场从后台走出，不得再拖成“即将出场”。 -> 【权力】刘美兰、苏振宏、苏雨柔必须在现场完成“怎么是你 / 你就是鸢 / 全场哗然”的即时翻车。 -> 【钩子】时鸢必须在台上直接落下“很意外吗”或同等强度的公开身份反打，把掉马写成本集闭环而不是前夜。
  - 功能目标：opening=setup；middle=escalation, escalation, reversal；ending=reversal_triggered；irreversibility=hard
  - 强功能补齐：escalation, confrontation_or_reversal, hook

## Hard Constraints
- 不提前出亲子鉴定
- 不提前公开设计师身份
- 不把傅斯年直接写成真爱已定
- 不让父母立刻后悔
- 不提前进晚宴打脸
- 不让时鸢马上心软
- 不把已发生的鉴定结果继续后拖
- 不提前给时鸢外部强援
- 不让苏家先求和
- 不提前公开身份反打
- 不让傅斯年当场追求成功
- 不让父母一集洗白
- 不把原文片段里已经发生的公开掉马继续拖到 EP06
- 不提前让傅斯年公开站队
- 不让苏家提前认错
