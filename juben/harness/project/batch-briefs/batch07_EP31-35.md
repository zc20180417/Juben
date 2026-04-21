# Batch Brief: EP-31 ~ EP-35

- owned episodes: EP-31, EP-32, EP-33, EP-34, EP-35
- source excerpt range: 被弃真千金：总裁不好惹.md 第14章中段 ~ 第16章
- adjacent continuity: 【动作】大屏幕先放出假助理深夜见神秘女人的高清监控，直接砸烂刚才的指控链。 -> 【信息】苏清月放出完整时间线、录音和资金链，实锤苏雨柔才是失散、渗透、栽赃的真正黑手。 -> 【关系】恶人被带走后的第一拍必须给到苏父苏母和两姐妹，让“终于平安”真实落地。 -> 【动作】傅斯年单膝跪地，戒指、承诺和“往后我不缺席”的话必须正面发生，不能写成转述。 -> 【信息】陆知衍必须以“苏清月的丈夫”身份强势落场，让姐姐这条爱情线从幕后变前台。
- draft output paths:
  - drafts/episodes/EP-31.md
  - drafts/episodes/EP-32.md
  - drafts/episodes/EP-33.md
  - drafts/episodes/EP-34.md
  - drafts/episodes/EP-35.md

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
- EP-31：第14章中段
  - 【动作】大屏幕先放出假助理深夜见神秘女人的高清监控，直接砸烂刚才的指控链。 -> 【信息】那位神秘女人必须正面揭脸成苏雨柔，把“已下线反派”强行拉回终局。 -> 【权力】苏清月明确说出她早就知道林振雄只是小角色，这一局是她故意引蛇出洞。 -> 【钩子】假助理还嘴硬时，苏清月第二份更致命的证据已经准备投屏。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：escalation, confrontation_or_reversal, hook
- EP-32：第14章后半
  - 【信息】苏清月放出完整时间线、录音和资金链，实锤苏雨柔才是失散、渗透、栽赃的真正黑手。 -> 【动作】警察押着苏雨柔进场，她彻底疯癫失态，再也装不出柔弱体面。 -> 【关系】时鸢和苏清月必须并肩站到一起，完成“被撕裂的姐妹线”重新锁死。 -> 【钩子】林振雄、假助理、苏雨柔全部被带走后，留下的是家人和爱人终于能松一口气的余波。
  - 功能目标：opening=setup；middle=escalation, escalation；ending=closure；irreversibility=soft
- EP-33：第15章前半
  - 【关系】恶人被带走后的第一拍必须给到苏父苏母和两姐妹，让“终于平安”真实落地。 -> 【动作】时鸢在姐姐怀里真正卸力，情绪要从强撑切到释然，而不是继续硬扛。 -> 【关系】傅斯年始终守着她，看准时机把她从姐姐怀里牵出来，准备把爱情线推到最后一步。 -> 【钩子】全场都意识到他接下来要说的，不会只是安慰，而是更正式的承诺。
  - 功能目标：opening=intrusion；middle=escalation, escalation；ending=emotional_payoff；irreversibility=soft
- EP-34：第15章后半
  - 【动作】傅斯年单膝跪地，戒指、承诺和“往后我不缺席”的话必须正面发生，不能写成转述。 -> 【关系】求婚成立的前提是时鸢已经认可他是能并肩走未来的人，而不是被热闹推着答应。 -> 【动作】时鸢说出“我愿意”，并让戒指真正戴上，爱情线闭环必须落地。 -> 【钩子】掌声和祝福刚起，门外又传来一位只属于苏清月的重要人影，为双CP开门。
  - 功能目标：opening=setup；middle=emotional_payoff, escalation；ending=emotional_payoff；irreversibility=soft
- EP-35：第16章
  - 【信息】陆知衍必须以“苏清月的丈夫”身份强势落场，让姐姐这条爱情线从幕后变前台。 -> 【关系】他与苏清月的拥抱、解释和默契要说明：这些年她并不是孤身硬撑。 -> 【动作】陆知衍与傅斯年完成第一次对面，形成两位男主共同护住两姐妹的新格局。 -> 【钩子】他提出“双婚礼”后，故事顺势一跳，进入终章时间切换。
  - 功能目标：opening=reveal；middle=escalation, escalation；ending=confrontation_pending；irreversibility=medium
  - 强功能补齐：intrusion, escalation, confrontation_or_reversal, hook

## Hard Constraints
- 不把苏雨柔回归写突兀
- 不让假助理立刻认输
- 不在这一集结束全部抓捕
- 不把苏雨柔写成小反派
- 不跳过姐妹重新对上眼的情感落点
- 不提前进入婚礼结局
- 不把这一集直接写成求婚完成
- 不跳过时鸢情绪过渡
- 不让家人余波轻轻带过
- 不把求婚写成霸总硬压
- 不让时鸢答应得毫无铺垫
- 不直接跳到婚礼当天
- 不把陆知衍写成抢戏新男主
- 不弱化他与苏清月的稳定关系
- 不在这一集走完婚礼
