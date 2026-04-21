# Batch Brief: EP-11 ~ EP-15

- owned episodes: EP-11, EP-12, EP-13, EP-14, EP-15
- source excerpt range: 被弃真千金：总裁不好惹.md 第6章前半 ~ 第7章后半
- adjacent continuity: 【动作】傅斯年换下锋利总裁壳子，拎着食盒和白桔梗独自上门，姿态要明显转成温柔追求。 -> 【动作】傅斯年送出真正对时鸢有用的定制裁剪刀，证明他记得她工作里的细枝末节。 -> 【信息】时鸢的新品发布会是她事业高光场，必须先立住“这是她真正的主场”。 -> 【动作】大屏幕放出苏雨柔潜入后台划坏礼裙的完整监控，让她的恶意无法抵赖。 -> 【动作】苏振宏当众扇苏雨柔一巴掌并解除收养关系，彻底把她从苏家踢出去。
- draft output paths:
  - drafts/episodes/EP-11.md
  - drafts/episodes/EP-12.md
  - drafts/episodes/EP-13.md
  - drafts/episodes/EP-14.md
  - drafts/episodes/EP-15.md

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
- EP-11：第6章前半
  - 【动作】傅斯年换下锋利总裁壳子，拎着食盒和白桔梗独自上门，姿态要明显转成温柔追求。 -> 【关系】他不再强拉强拽，而是承认“我知道你不需要，但我还是想照顾你”，追妻方式必须降压。 -> 【信息】他从时鸢的工作状态里看见她长期独撑的生活面，开始把照顾落到具体细节。 -> 【钩子】定制礼物还没拿出来，时鸢对他的防线也还没真正松动。
  - 功能目标：opening=escalation；middle=escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-12：第6章后半
  - 【动作】傅斯年送出真正对时鸢有用的定制裁剪刀，证明他记得她工作里的细枝末节。 -> 【权力】苏家打来电话求恢复合作时，他必须当着时鸢面冷硬回绝，明确“合作永远终止”。 -> 【关系】他把“别人都可以不管你，但我不行”落到实处，让时鸢第一次感到被稳定护着。 -> 【钩子】时鸢终于坐下吃他带来的饭，表示心防被撬开了第一道缝。
  - 功能目标：opening=reversal；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-13：第7章前半
  - 【信息】时鸢的新品发布会是她事业高光场，必须先立住“这是她真正的主场”。 -> 【动作】苏雨柔混进现场，对压轴礼裙下手，把高定礼裙当众划坏。 -> 【权力】全场舆论瞬间要把事故算到时鸢头上，形成短暂失控。 -> 【钩子】时鸢只说一句“调监控”，把主动权硬生生拽回来。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-14：第7章中段
  - 【动作】大屏幕放出苏雨柔潜入后台划坏礼裙的完整监控，让她的恶意无法抵赖。 -> 【权力】傅斯年带着律师和证据进场，把她买通工作人员、造谣、抄袭的账一次性砸下去。 -> 【关系】时鸢明确按法律程序追责，和过去那种被动受气彻底切开。 -> 【钩子】苏家必须在“继续护她”还是“彻底割席”之间作出选择。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=reveal_pending；irreversibility=hard
  - 强功能补齐：escalation, hook
- EP-15：第7章后半
  - 【动作】苏振宏当众扇苏雨柔一巴掌并解除收养关系，彻底把她从苏家踢出去。 -> 【权力】苏雨柔从“被偏爱的养女”翻成人人唾弃的过街老鼠，彻底失去上流立足点。 -> 【关系】发布会风波平息后，时鸢第一次没有躲开傅斯年的守护，关系再往前推一步。 -> 【钩子】苏家门口出现一位与时鸢眉眼相似的陌生女人，直接把“姐姐归来”推到门前。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook

## Hard Constraints
- 不写成油腻表白局
- 不让时鸢当场给恋爱承诺
- 不让苏家抢主功能
- 不直接跳到正式在一起
- 不把追妻写成重复送礼
- 不提前引出姐姐回归
- 不把破坏写成意外
- 不让傅斯年先于监控解决
- 不提前赶出苏雨柔
- 不让苏雨柔继续维持白莲形象
- 不把时鸢写成只靠傅斯年
- 不提前出现姐姐相认
- 不让苏雨柔这一集就彻底坐牢
- 不把姐妹关系写成无缝亲密
- 不让傅斯年和时鸢直接定情
