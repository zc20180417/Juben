# Batch Brief: EP-26 ~ EP-30

- owned episodes: EP-26, EP-27, EP-28, EP-29, EP-30
- source excerpt range: 被弃真千金：总裁不好惹.md 第12章后半 ~ 第14章前段
- adjacent continuity: 【动作】傅斯年、苏清月、时鸢兵分三路：封壳公司、找海外证人、清内部眼线。 -> 【动作】三人以苏氏动荡为诱饵布空会议室陷阱，先立住“这是她们主动设的局”。 -> 【动作】苏清月必须当场甩出绑架、非法交易、勾连苏雨柔的铁证，把林振雄先按进失败位。 -> 【动作】假助理当众摘下口罩，直接改写案情，把林振雄从“终极黑手”降成“前台棋子”。 -> 【权力】假助理与林振雄联手把矛头全指向苏清月，会议室气氛必须真的压到她身上。
- draft output paths:
  - drafts/episodes/EP-26.md
  - drafts/episodes/EP-27.md
  - drafts/episodes/EP-28.md
  - drafts/episodes/EP-29.md
  - drafts/episodes/EP-30.md

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
- EP-26：第12章后半
  - 【动作】傅斯年、苏清月、时鸢兵分三路：封壳公司、找海外证人、清内部眼线。 -> 【权力】三人都要有明确任务，不能把收网写成一句“大家都在努力”。 -> 【信息】林振雄察觉危机，直接给时鸢发出“你们会一起陪葬”的威胁短信。 -> 【钩子】时鸢删掉短信、冷回一句“看你有没有那个命”，表示终局对撞正式开始。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-27：第13章前半
  - 【动作】三人以苏氏动荡为诱饵布空会议室陷阱，先立住“这是她们主动设的局”。 -> 【信息】林振雄带着伪造股权文件和手下闯入，证明他真想趁乱夺权。 -> 【权力】灯光亮起后，时鸢、苏清月、傅斯年三角站位压住全场，主导权完全在他们这边。 -> 【钩子】苏清月手里的证据马上要摊开，林振雄的退路也已经被封死。
  - 功能目标：opening=setup；middle=intrusion, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-28：第13章中段
  - 【动作】苏清月必须当场甩出绑架、非法交易、勾连苏雨柔的铁证，把林振雄先按进失败位。 -> 【权力】警方和保安封死出口，傅斯年一个眼神就能让人上前铐他，压迫感要足。 -> 【关系】时鸢不是旁观者，她要在场确认“旧债终于有人正面偿还”。 -> 【钩子】就在手铐即将扣上的一刻，苏清月身后的助理突然伸手拦下警方。
  - 功能目标：opening=setup；middle=escalation, reveal；ending=reversal_triggered；irreversibility=hard
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-29：第13章后半
  - 【动作】假助理当众摘下口罩，直接改写案情，把林振雄从“终极黑手”降成“前台棋子”。 -> 【信息】他抛出录音、资金流、会面照，所有证据都指向苏清月才是操盘者。 -> 【关系】时鸢必须被这一刀正面刺中，第一次怀疑一直护着自己的姐姐是不是也在演戏。 -> 【钩子】苏清月没有立刻反驳，只留下一句“不是你想的那样”，把痛点悬在下一集。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=closure；irreversibility=soft
- EP-30：第14章前段
  - 【权力】假助理与林振雄联手把矛头全指向苏清月，会议室气氛必须真的压到她身上。 -> 【关系】傅斯年先护时鸢再审视苏清月，时鸢陷在“想信却不敢全信”的撕裂里。 -> 【动作】苏清月拍开阻拦、自己走向假助理，先用一句“演完了”稳住全场。 -> 【钩子】她按下遥控器，大屏幕即将从伪证切换成真正的反证。
  - 功能目标：opening=setup；middle=escalation, intrusion；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook

## Hard Constraints
- 不让林振雄这一集就落网
- 不让威胁短信变成空吓唬
- 不削弱时鸢主动性
- 不把设局写成偶然撞见
- 不让林振雄提前知道全部底牌
- 不提前翻出假助理反转
- 不让林振雄还有洗白空间
- 不把抓捕轻飘带过
- 不提前揭出苏雨柔是真黑手
- 不让时鸢毫无波动地相信姐姐
- 不让傅斯年一秒看穿全局
- 不提前放出苏清月反证
- 不让假终局敷衍
- 不在本集就把真相说完
- 不让时鸢直接替姐姐辩护
