# Batch Brief: EP-16 ~ EP-20

- owned episodes: EP-16, EP-17, EP-18, EP-19, EP-20
- source excerpt range: 被弃真千金：总裁不好惹.md 第8章前半 ~ 第10章前半
- adjacent continuity: 【信息】苏清月正式站到时鸢面前，先让全家确认“她真的回来了”。 -> 【关系】时鸢必须先问清“你现在回来为了什么”，把这场相认写成有边界的试探。 -> 【信息】苏雨柔被赶走后立刻勾连苏家对手，拿时鸢项目内部资料换反扑筹码。 -> 【动作】苏清月和时鸢亲自带律师找到苏雨柔，把赔偿、返还财产、法律责任一项项宣读清楚。 -> 【权力】苏父苏母把公司核心项目决策权交给时鸢和苏清月，正式承认姐妹才是新主导。
- draft output paths:
  - drafts/episodes/EP-16.md
  - drafts/episodes/EP-17.md
  - drafts/episodes/EP-18.md
  - drafts/episodes/EP-19.md
  - drafts/episodes/EP-20.md

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
- EP-16：第8章前半
  - 【信息】苏清月正式站到时鸢面前，先让全家确认“她真的回来了”。 -> 【关系】她看向时鸢的第一反应必须是失而复得的心疼，而不是争主角位。 -> 【动作】时鸢被这份血缘熟悉感击中，却仍保持克制，不立刻扑上去认亲。 -> 【钩子】苏清月一句“对不起，姐姐回来晚了”，把时鸢最深的防线顶到临界点。
  - 功能目标：opening=reveal；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：intrusion, escalation, confrontation_or_reversal, hook
- EP-17：第8章后半
  - 【关系】时鸢必须先问清“你现在回来为了什么”，把这场相认写成有边界的试探。 -> 【动作】苏清月给出清晰答案：护着妹妹、追究苏雨柔、替她把该讨的讨回来。 -> 【关系】傅斯年在旁边保持审视与保护，但最终认可苏清月对时鸢的真心。 -> 【钩子】时鸢的防线第一次松动，可暗处的苏雨柔绝不会就此收手。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-18：第9章前半
  - 【信息】苏雨柔被赶走后立刻勾连苏家对手，拿时鸢项目内部资料换反扑筹码。 -> 【关系】苏清月主动提出这次由姐妹亲自处理，不再让时鸢独自扛。 -> 【动作】姐妹二人开始整合苏雨柔侵占财产、泄密、陷害的证据链。 -> 【钩子】法院传票和合作方同步收到材料，表示这一轮反击已经出手。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-19：第9章后半
  - 【动作】苏清月和时鸢亲自带律师找到苏雨柔，把赔偿、返还财产、法律责任一项项宣读清楚。 -> 【权力】竞争对手见势不妙立刻切割，苏雨柔第一次发现自己已经没有任何牌可打。 -> 【关系】姐妹站在同一阵线公开清算过去，让“姐姐只是回来看看”升级成“姐姐会并肩作战”。 -> 【钩子】清算结束后，苏家与商圈都开始重新看见这对姐妹组合的价值。
  - 功能目标：opening=setup；middle=confrontation, reveal；ending=closure；irreversibility=soft
- EP-20：第10章前半
  - 【权力】苏父苏母把公司核心项目决策权交给时鸢和苏清月，正式承认姐妹才是新主导。 -> 【信息】立住两人的分工优势：时鸢擅长市场与策略，苏清月擅长管理与谈判。 -> 【动作】她们接下被搁置许久的高端综合体项目，准备以此做成苏家翻盘样板。 -> 【钩子】老股东、合作方和内部团队全在质疑她们，董事会硬仗马上开打。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook

## Hard Constraints
- 不把姐姐写成抢戏
- 不让时鸢立刻无条件信任
- 不提前讨论旧案真相
- 不把姐妹一见面写成闺蜜热聊
- 不让傅斯年突然吃姐姐醋
- 不提前展开事业大战结果
- 不让苏雨柔还有内部保护伞
- 不让傅斯年一手包办
- 不提前让她彻底败诉坐牢
- 不让苏雨柔靠哭求翻盘
- 不把姐妹联手写成单纯嘴仗
- 不提前跳旧案真相
- 不一接手就直接成功
- 不让父母重新主导
- 不把事业线写空
