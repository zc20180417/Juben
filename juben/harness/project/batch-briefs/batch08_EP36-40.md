# Batch Brief: EP-36 ~ EP-40

- owned episodes: EP-36, EP-37, EP-38, EP-39, EP-40
- source excerpt range: 被弃真千金：总裁不好惹.md 第17章前段 ~ 第17章尾声
- adjacent continuity: 【信息】先立住三个月后与顶级庄园婚礼的巨大场面感，让终章气氛和前面阴谋线彻底区分开。 -> 【动作】苏父牵着两个女儿步入礼堂，这个动作要承担“迟到的父爱补位”。 -> 【关系】傅斯年与时鸢的誓言要回应“从误认到认定”的完整爱情弧线。 -> 【动作】双吻落下、全场沸腾、父母落泪，这一拍必须正面给足婚礼的完成感。 -> 【信息】明确交代苏雨柔、林振雄等恶人都已失去翻身可能，阴谋线彻底封口。
- draft output paths:
  - drafts/episodes/EP-36.md
  - drafts/episodes/EP-37.md
  - drafts/episodes/EP-38.md
  - drafts/episodes/EP-39.md
  - drafts/episodes/EP-40.md

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
- EP-36：第17章前段
  - 【信息】先立住三个月后与顶级庄园婚礼的巨大场面感，让终章气氛和前面阴谋线彻底区分开。 -> 【关系】时鸢与傅斯年、苏清月与陆知衍各自有一段婚前对视或短交流，确认两条感情线都已稳定。 -> 【动作】婚礼不是纯堆画面，要让观众看见姐妹并肩、两位男主守候的当下状态。 -> 【钩子】婚礼进行曲响起，苏父即将牵着两个女儿走向红毯。
  - 功能目标：opening=emotional_payoff；middle=reveal；ending=arrival；irreversibility=medium
- EP-37：第17章中前段
  - 【动作】苏父牵着两个女儿步入礼堂，这个动作要承担“迟到的父爱补位”。 -> 【关系】傅斯年看向时鸢、陆知衍看向苏清月，两对关系都要写出“终于等到今天”。 -> 【权力】全城名流见证下，曾经被轻贱的姐妹站到了最高光的位置，地位翻盘要可见。 -> 【钩子】两对新人站定后，誓言环节马上开始。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-38：第17章中段
  - 【关系】傅斯年与时鸢的誓言要回应“从误认到认定”的完整爱情弧线。 -> 【关系】陆知衍与苏清月的誓言要回应“从失散到归位”的成熟伴侣线。 -> 【动作】两对新人都必须完成交换戒指，把承诺落到身体动作上。 -> 【钩子】誓言之后的双吻即将落下，把婚礼推到情绪顶点。
  - 功能目标：opening=intrusion；middle=escalation, escalation；ending=closure；irreversibility=soft
- EP-39：第17章中后段
  - 【动作】双吻落下、全场沸腾、父母落泪，这一拍必须正面给足婚礼的完成感。 -> 【信息】晚宴上两位男主分别正式介绍“我的妻子”“我的太太”，把姐妹的新身份公开到所有人面前。 -> 【关系】姐妹并肩、两对夫妻同框，要形成真正的“双CP镜像终章”。 -> 【钩子】镜头要往更远处推，带出恶人伏法后的事业和家庭新秩序。
  - 功能目标：opening=emotional_payoff；middle=reveal, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-40：第17章尾声
  - 【信息】明确交代苏雨柔、林振雄等恶人都已失去翻身可能，阴谋线彻底封口。 -> 【权力】点明苏家企业在两姐妹与两位爱人的助力下走向新高度，新的家族秩序由她们定义。 -> 【关系】时鸢最后的落点不是“嫁出去”而是终于同时拥有亲情、爱情与自我价值的完整人生。 -> 【钩子】终章收在两对璧人并肩的光亮画面上，把“被弃真千金”彻底反写成“被坚定接住的人”。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=closure；irreversibility=soft

## Hard Constraints
- 不直接从转场跳到礼成
- 不让婚礼场只剩空镜
- 不忘记姐姐线是主终章
- 不把父母补位写成轻飘原谅
- 不只拍一对新人
- 不提前跳到晚宴
- 不把誓言写成空泛套话
- 不只给时鸢一对誓言
- 不把交换戒指一句略过
- 不把礼成和晚宴一句带过
- 不让终章只剩爱情
- 不重新插入无关波折
- 不留下核心悬案
- 不把终章写成单纯婚礼纪实
- 不把时鸢闭环弱化成靠男人翻身
