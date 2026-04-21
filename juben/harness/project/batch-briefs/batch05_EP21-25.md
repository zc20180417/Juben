# Batch Brief: EP-21 ~ EP-25

- owned episodes: EP-21, EP-22, EP-23, EP-24, EP-25
- source excerpt range: 被弃真千金：总裁不好惹.md 第10章后半 ~ 第12章前半
- adjacent continuity: 【动作】姐妹连夜改方案、重做定位和风控，不靠傅斯年代打，而是自己把项目架起来。 -> 【信息】苏家设家宴对外庆祝项目成功和姐妹归位，表面必须是久违的团圆感。 -> 【信息】父母必须亲口说出：当年姐妹失散并非意外，而是商业仇家针对苏家的绑架报复。 -> 【关系】时鸢对父母的判断从“只有偏心”改成“做错了的保护”，但这个变化必须带着保留和伤痕。 -> 【信息】苏清月拿出整理好的资料，第一次明确指出当年绑架与报复的关键名字是林振雄。
- draft output paths:
  - drafts/episodes/EP-21.md
  - drafts/episodes/EP-22.md
  - drafts/episodes/EP-23.md
  - drafts/episodes/EP-24.md
  - drafts/episodes/EP-25.md

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
- EP-21：第10章后半
  - 【动作】姐妹连夜改方案、重做定位和风控，不靠傅斯年代打，而是自己把项目架起来。 -> 【权力】董事会上她们用数据和盈利逻辑压住老股东，拿下项目正式启动权。 -> 【关系】时鸢明确告诉傅斯年“这次我想和姐姐一起完成”，把姐妹并肩关系写实。 -> 【钩子】项目一经官宣就爆热，也逼出苏家想借家宴正式宣告“姐妹归位”。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-22：第11章前段
  - 【信息】苏家设家宴对外庆祝项目成功和姐妹归位，表面必须是久违的团圆感。 -> 【关系】傅斯年寸步不离挡掉无效应酬，继续以稳定守护站在时鸢身侧。 -> 【动作】一位老友提起“当年两个孩子同时失踪”，直接戳中父母最不想碰的旧伤。 -> 【钩子】时鸢精准捕捉到父母眼神里的慌乱，当场意识到过去并不是普通走失。
  - 功能目标：opening=emotional_payoff；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-23：第11章中段
  - 【信息】父母必须亲口说出：当年姐妹失散并非意外，而是商业仇家针对苏家的绑架报复。 -> 【信息】说清时鸢曾被救下后以“外人身份”留在苏家，是他们自以为的保护，而不是单纯嫌弃。 -> 【关系】时鸢听到这些后不能立刻原谅，只能先被巨大的信息冲击打懵。 -> 【钩子】再往下翻，苏雨柔和当年那股势力之间还有更深的血缘与布局关联。
  - 功能目标：opening=setup；middle=reveal, escalation；ending=reveal_pending；irreversibility=hard
  - 强功能补齐：escalation, hook
- EP-24：第11章后段
  - 【关系】时鸢对父母的判断从“只有偏心”改成“做错了的保护”，但这个变化必须带着保留和伤痕。 -> 【动作】苏清月和傅斯年分别从亲情与爱情位置稳住时鸢，接住她的崩塌时刻。 -> 【权力】父母第一次真正把解释权和决定权交给两个女儿，不再强行要求原谅。 -> 【钩子】时鸢与苏清月明确表态：当年欠她们的，这次要一起讨回来。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=locked_in；irreversibility=hard
  - 强功能补齐：escalation, hook
- EP-25：第12章前半
  - 【信息】苏清月拿出整理好的资料，第一次明确指出当年绑架与报复的关键名字是林振雄。 -> 【信息】同步说破苏雨柔被送进苏家从一开始就是卧底布局，彻底抬高她的反派级别。 -> 【关系】姐妹俩不再只是事后安慰，而是正式进入并肩查案模式。 -> 【钩子】傅斯年补上“路线已封、人在暗处”的信息，让这场对决进入可执行的收网阶段。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook

## Hard Constraints
- 不让事业成功只靠男主资源
- 不跳过股东阻力直接庆功
- 不提前揭旧案答案
- 不把家宴写成纯庆功水戏
- 不让父母继续糊弄
- 不提前出现林振雄名字
- 不把父母直接洗白
- 不跳过时鸢的震荡反应
- 不在这一集抓到幕后黑手
- 不把这集写成彻底和解
- 不削弱姐姐支点作用
- 不直接跳到收网执行
- 不让林振雄立刻现身
- 不把苏雨柔写成单纯被利用
- 不跳过三人分工部署
