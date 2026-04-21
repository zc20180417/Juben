# Batch Brief: EP-06 ~ EP-10

- owned episodes: EP-06, EP-07, EP-08, EP-09, EP-10
- source excerpt range: 被弃真千金：总裁不好惹.md 第3章后半 ~ 第5章后半
- adjacent continuity: 【信息】主持人正式喊出“鸢设计创始人时鸢”，台下众人和苏家同时被打懵。 -> 【动作】傅斯年穿过人群把时鸢从舞台边扶下来，姿态必须是明目张胆的偏爱。 -> 【权力】傅斯年正面否认苏家有资格当长辈，把“生而不养”的账当众翻出来。 -> 【信息】苏家三人第一次走进时鸢真正的生活场域，直观看到她并非他们以为的落魄真千金。 -> 【关系】时鸢逐条翻旧账，把“从未被爱过”的事实掰开讲清，明确自己与苏家没有亲情可回头。
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

## Writer Authority
- 当前 batch brief：决定本批每集的任务、beats、功能目标与 ending function
- `harness/project/source.map.md`：决定 source 顺序、must-not-add、must-not-jump 边界
- `harness/project/run.manifest.md`：只提供运行参数，不裁决内容冲突
- `voice-anchor.md` / `character.md`：仅作气质、禁区与称谓参考，不覆盖当前集任务

## Function Policy
- 场次数由功能完成决定，不得为了压场数省略功能槽位。
- 首集和强冲突集必须补齐适用的强功能，不得把多个强功能糊成总结场。

## Episode Mapping
- EP-06：第3章后半
  - 【信息】主持人正式喊出“鸢设计创始人时鸢”，台下众人和苏家同时被打懵。 -> 【权力】时鸢当众点破自己既是顶级设计师，也是被苏家嫌弃的亲生女儿，完成第一轮身份反打。 -> 【动作】会所老板与商圈大佬立刻围上来递合作，把苏家直接晾成笑柄。 -> 【钩子】时鸢用一句“苏家我高攀不起”收尾，把苏家的脸面彻底撕开。
  - 功能目标：opening=setup；middle=reveal, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-07：第4章前半
  - 【动作】傅斯年穿过人群把时鸢从舞台边扶下来，姿态必须是明目张胆的偏爱。 -> 【关系】他当众宣布从今天起正式追求时鸢，把“误认对象”彻底转成“公开追求的人”。 -> 【权力】他明确放话，谁敢为难时鸢，就是与傅斯年为敌，让全场重新站队。 -> 【钩子】苏家试图拿“她是清月妹妹”压他，逼出下一轮更狠的回击。
  - 功能目标：opening=setup；middle=intrusion, reversal；ending=reversal_triggered；irreversibility=hard
  - 强功能补齐：confrontation_or_reversal, hook
- EP-08：第4章后半
  - 【权力】傅斯年正面否认苏家有资格当长辈，把“生而不养”的账当众翻出来。 -> 【动作】他宣布傅氏立即终止与苏家全部合作，把威胁从口头站队升级为实打实的商业制裁。 -> 【关系】时鸢坚持“我的事我自己能解决”，傅斯年则给出“清月是过去，你才是我的现在和未来”的明牌偏爱。 -> 【钩子】苏家在全场指指点点里彻底沦为笑柄，为后续上门求和蓄势。
  - 功能目标：opening=setup；middle=reversal, escalation；ending=reversal_triggered；irreversibility=hard
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-09：第5章前半
  - 【信息】苏家三人第一次走进时鸢真正的生活场域，直观看到她并非他们以为的落魄真千金。 -> 【关系】刘美兰和苏振宏放低姿态认错，苏雨柔继续用“都怪我”抢占受害者位置。 -> 【动作】时鸢直接切断“姐”“一家人”这些称呼，把苏雨柔的白莲表演当场掐断。 -> 【钩子】时鸢准备把“你们认我只是因为我有用”这句话彻底说死，推动下一集断亲。
  - 功能目标：opening=arrival；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：intrusion, escalation, confrontation_or_reversal, hook
- EP-10：第5章后半
  - 【关系】时鸢逐条翻旧账，把“从未被爱过”的事实掰开讲清，明确自己与苏家没有亲情可回头。 -> 【动作】她说出“没有父母，没有家人，从此一刀两断”，并直接让助理送客。 -> 【权力】苏家只能在门外崩溃，却再没有资格逼她回头，关系主导权完全倒挂。 -> 【钩子】门刚关上，下一次再响门铃的人不再是苏家，而会是另一路追求。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=closure；irreversibility=soft

## Hard Constraints
- 不提前写傅斯年公开追求
- 不让苏家立刻补救成功
- 不把掉马写轻
- 不让时鸢当场接受追求
- 不断合作提前落锤
- 不让苏家重新控场
- 不让时鸢一秒心软
- 不让苏家当晚求和成功
- 不提前写上门照顾
- 不把苏家认错写成真心纯粹
- 不把时鸢写成借势羞辱
- 不断亲提前落地
- 不让父母这一集被原谅
- 不让苏雨柔抢到道德高位
- 不断亲收成和解
